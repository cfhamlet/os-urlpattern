from collections import OrderedDict
import os
import hashlib
import StringIO
from pattern_util import char_normlize


class LocalCache(OrderedDict):

    def __init__(self, limit=None):
        super(LocalCache, self).__init__()
        self.limit = limit

    def __setitem__(self, key, value):
        while len(self) >= self.limit:
            self.popitem(last=False)
        super(LocalCache, self).__setitem__(key, value)


class UrlStructMeta(object):
    __slots__ = ['_path_depth', '_query_keys', '_has_fragment', '_hash_code']

    def __init__(self, path_depth, query_keys, has_fragment):
        self._path_depth = path_depth
        self._query_keys = query_keys
        self._has_fragment = has_fragment
        self._hash_code = None

    def __hash__(self):
        return hash(self.hashcode)

    @property
    def hashcode(self):
        if self._hash_code is not None:
            return self._hash_code
        s = StringIO.StringIO()
        s.write(self._path_depth)
        if len(self._query_keys) > 0:
            s.write('?')
            s.write('&'.join(self._query_keys))
        if self._has_fragment:
            s.write('#')
        s.seek(0)
        self._hash_code = hashlib.md5(s.read()).hexdigest().upper()
        return self._hash_code

    @property
    def depths(self):
        return (self.path_depth, self.query_depth, self.fragment_depth)

    @property
    def query_keys(self):
        return self._query_keys

    @property
    def query_depth(self):
        return len(self._query_keys)

    @property
    def fragment_depth(self):
        return 1 if self._has_fragment else 0

    @property
    def path_depth(self):
        return self._path_depth

    @property
    def has_fragment(self):
        return self._has_fragment

    @property
    def all_depth(self):
        return sum((self.path_depth, self.query_depth, self.fragment_depth))


def path_dump_and_load(src, dest, index=0):
    for path in src.dump_paths():
        if path:
            dest.load_path(path[index:])


def filter_useless_part(parts):
    keep = {'c': 0, 'l': len(parts)}

    def _filterd(x):
        keep['c'] += 1
        if not x:
            if keep['c'] == keep['l']:
                return True
            return False
        else:
            return True

    return filter(_filterd, parts)


def _split_pattern_path(pattern_path, url_struct):
    s = 0
    l = []
    for i in url_struct.depths:
        e = s + i
        l.append([p for p in pattern_path[s:e]])
        s = e
    return l


def pattern_path_hashcode(pattern_path, url_struct):
    l = _split_pattern_path(pattern_path, url_struct)
    return _patterns_hashcode(url_struct, *l)


def _patterns_hashcode(url_struct, path_patterns, query_patterns, fragment_patterns):
    return pattern_path_string_hashcode(_pattern_path_string(url_struct, path_patterns, query_patterns, fragment_patterns))


def pattern_path_string(pattern_path, url_struct):
    l = _split_pattern_path(pattern_path, url_struct)
    return _pattern_path_string(url_struct, *l)


def _pattern_path_string(url_struct, path_patterns, query_patterns, fragment_patterns):
    s = StringIO.StringIO()
    s.write('/')
    p = '/'.join([str(p) for p in path_patterns])
    s.write(p)
    if query_patterns:
        s.write('[\\?]')
        s.write('&'.join(["".join((str(k), str(v)))
                          for k, v in zip(url_struct.query_keys, query_patterns)]))
    if fragment_patterns:
        s.write('#')
        s.write(''.join(str(p) for p in fragment_patterns))
    s.seek(0)
    return s.read()


def pattern_path_string_hashcode(pattern_path_str):
    md5 = hashlib.md5(pattern_path_str)
    return md5.hexdigest()


def get_base_part_pattern(parts, config):
    from pattern_util import get_part_pattern_from_raw_string
    l = len(parts)
    if l < 1:
        return None
    k = {'c': 0, 'l': l}

    def _m(part):
        k['c'] += 1
        return get_part_pattern_from_raw_string(part, config, k['c'] == k['l'])
    part_patterns = map(_m, parts)
    return part_patterns


_KEEP_C = set(['='])
_ZERO_DIGEST = hashlib.md5('0').hexdigest().upper()


class UrlQuery(object):
    def __init__(self, keys, values, norm_key=True):
        self._norm(keys, values, norm_key)

    def _norm(self, keys, values, norm_key):
        if norm_key:
            keys = [char_normlize(k, _KEEP_C) for k in keys]
        z = zip(keys, values)
        self._kv = sorted(z, key=lambda x: x[0])
        self._len = len(self._kv)

    def __len__(self):
        return self._len

    @property
    def hashcode(self):
        if self._len == 0:
            return _ZERO_DIGEST
        c = '&'.join(self.query_keys())
#         c = str(self._len) + c
        return hashlib.md5(c).hexdigest().upper()

    def query_kv(self):
        return self._kv

    def query_keys(self):
        return [kv[0] for kv in self._kv]

    def query_values(self):
        return [kv[1] for kv in self._kv]


EMPYT_URL_QUERY = UrlQuery([], [])


def parse_url_query(url_query, norm_key=True):
    if url_query is None:
        return EMPYT_URL_QUERY
    kv_type = True  # qkey True, qvalue False
    last_c = None
    kv_buf = {True: StringIO.StringIO(), False: StringIO.StringIO()}
    kv_list = {True: [], False: []}
    for i in url_query:
        if (i == '=' and kv_type) or (i == '&' and last_c is not None and i != last_c):
            s = kv_buf[kv_type]
            if i == '=':
                s.write('=')
            s.seek(0)
            kv_list[kv_type].append(s.read())
            kv_buf[kv_type] = StringIO.StringIO()
            if i == '&' and kv_type:  # treat as value-less
                kv_list[False].append('')
            else:
                kv_type = not kv_type
            last_c = i
            continue
        if i == '&':
            return None
        s = kv_buf[kv_type]
        s.write(i)
        last_c = i
    if last_c == '&':
        return None
    elif last_c is not None:
        s = kv_buf[kv_type]
        s.seek(0)
        kv_list[kv_type].append(s.read())
        if kv_type:
            kv_list[False].append('')

    klen = len(kv_list[True])
    vlen = len(kv_list[False])
    if klen != vlen:
        return None
    if klen <= 0:
        return EMPYT_URL_QUERY
    else:
        # first query, treat as key-less
        if not kv_list[True][0].endswith('='):
            kv_list[False][0], kv_list[True][0] = kv_list[True][0], kv_list[False][0]
    return UrlQuery(kv_list[True], kv_list[False], norm_key)


def parse_url_part(path_part, query_part, fragment_part, last_char='', norm_query_key=True):
    parts = filter_useless_part(path_part.split('/')[1:])
    path_depth = len(parts)
    if path_depth < 1:
        return None
    query = parse_url_query(query_part, norm_query_key)
    if query is None:
        return None
    has_fragment = True if fragment_part or last_char[-1] == '#' else False
    url_struct = UrlStructMeta(path_depth, query.query_keys(), has_fragment)
    if len(query) > 0:
        parts.extend(query.query_values())
    if has_fragment:
        parts.append(fragment_part)
    return url_struct, parts


def parse_url(url):
    from urlparse import urlparse
    try:
        p = urlparse(url)
    except:
        return None
    url_path = p.path
    url_query = p.query
    url_fragment = p.fragment
    return parse_url_part(url_path, url_query, url_fragment, last_char=url[-1])


def get_memory_used():
    try:
        import psutil
    except:
        return None
    p = psutil.Process(os.getpid())
    memory = p.memory_info().rss / 1024.0
    for i in ['K', 'M', 'G']:
        if memory < 1024.0:
            return '%.1f%s' % (memory, i)
        memory = memory / 1024.0
    return '%.1fG' % memory


if __name__ == "__main__":
    s = '/a//b/'
    s = '/a///b///c'
    s = '/a'
    s = 'http://lady.163.com/photoview/513O0026/96560.html??'
#     from config import default_preprocess_config
#     print base_pattern_hashcode(s, default_preprocess_config())
#     print pattern_path_hashcode_from_string('/photoview/513O0026/[0-9]{5}[\\.]html')
#     print get_memory_used()
#     print parse_url_query('a_=1').query_kv()
    print parse_url(s)
#     print s.split('/')[1:]
#     print filter_useless_part(s.split('/')[1:])
