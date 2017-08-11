import StringIO
from exceptions import IrregularURLException
from urlparse import urlparse
from url_meta import URLMeta
from definition import QUERY_PART_RESERVED_CHARS, EMPTY_LIST, BLANK_LIST
from definition import ASCII_DIGIT_SET, CHAR_RULE_DICT


class AnalyseResult(object):
    def __init__(self, url):
        self._base_url = url
        self._result = None
        self._base_url_length = len(url)
        self._blank_query = False
        self._blank_fragment = False
        self._analyse()

    def _analyse(self):
        self._result = urlparse(self._base_url)
        if not self._result.fragment:
            if self._base_url[-1] == '#':
                self._blank_fragment = True
                if not self._result.query:
                    if self._base_url[-2] == '?':
                        self._blank_query = True
            elif not self._result.query and self._base_url[-1] == '?':
                self._blank_query = True
        elif not self._result.query:
            index = self._base_url.find('#')
            if self._base_url[index - 1] == '?':
                self._blank_query = True

    def __getattr__(self, attr):
        try:
            super(AnalyseResult, self).__getattr__()
        except AttributeError:
            return getattr(self._result, attr)

    @property
    def blank_query(self):
        return self._blank_query

    @property
    def blank_fragment(self):
        return self._blank_fragment


def _exact_num(rule, num):
    if num == 1:
        return '[%s]' % rule
    return '[%s]{%d}' % (rule, num)


def normalize_str_list(str_list, reserved_chars):
    return [normalize_str(i, reserved_chars) for i in str_list]


def normalize_str(raw_string, reserved_chars=None):
    normal_str = StringIO.StringIO()
    frag = StringIO.StringIO()
    last_c = None
    for c in raw_string:
        if c in ASCII_DIGIT_SET:
            if last_c and last_c not in ASCII_DIGIT_SET:
                frag.seek(0)
                w = frag.read()
                l = len(w)
                if l > 0:
                    if not reserved_chars or w[0] not in reserved_chars:
                        r = CHAR_RULE_DICT.get(w[0])
                        w = _exact_num(r, l)
                    normal_str.write(w)
                    frag = StringIO.StringIO()
        else:
            if last_c != c:
                frag.seek(0)
                w = frag.read()
                l = len(w)
                if l > 0 and w[0] not in ASCII_DIGIT_SET and \
                        (not reserved_chars or w[0] not in reserved_chars):
                    r = CHAR_RULE_DICT.get(w[0])
                    w = _exact_num(r, l)
                normal_str.write(w)
                frag = StringIO.StringIO()
        frag.write(c)
        last_c = c

    frag.seek(0)
    w = frag.read()
    l = len(w)
    if last_c and last_c not in ASCII_DIGIT_SET and \
            (not reserved_chars or w[0] not in reserved_chars):
        r = CHAR_RULE_DICT.get(w[0])
        w = _exact_num(r, l)
    normal_str.write(w)
    normal_str.seek(0)
    return normal_str.read()


def analyze_url(url):
    return AnalyseResult(url)


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


def parse_query_string(query_string):
    assert query_string
    kv_type = True  # qkey True, qvalue False
    last_c = None
    kv_buf = {True: StringIO.StringIO(), False: StringIO.StringIO()}
    kv_list = {True: [], False: []}
    for i in query_string:
        if (i == '=' and kv_type) or (i == '&'
                                      and last_c is not None
                                      and last_c != '&'):
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
            raise IrregularURLException
        s = kv_buf[kv_type]
        s.write(i)
        last_c = i
    if last_c == '&':
        raise IrregularURLException
    elif last_c is not None:
        s = kv_buf[kv_type]
        s.seek(0)
        kv_list[kv_type].append(s.read())
        if kv_type:
            kv_list[False].append('')

    assert len(kv_list[True]) == len(kv_list[False])
    # first query, treat as key-less
    if len(kv_list[True]) == 1 and not kv_list[True][0].endswith('='):
        kv_list[False][0], kv_list[True][0] = kv_list[True][0], kv_list[False][0]
    return kv_list[True], kv_list[False]


def parse_url_structure(result, norm_query_key=True):
    parts = filter_useless_part(result.path.split('/')[1:])
    path_depth = len(parts)
    assert path_depth > 0

    if result.blank_query:
        key_list = value_list = BLANK_LIST
    elif not result.query:
        key_list = value_list = EMPTY_LIST
    else:
        key_list, value_list = parse_query_string(result.query)
        if norm_query_key:
            key_list = normalize_str_list(key_list, QUERY_PART_RESERVED_CHARS)
    has_fragment = True if (
        result.fragment or result.blank_fragment) else False

    url_meta = URLMeta(path_depth, key_list, has_fragment)
    parts.extend(value_list)
    if has_fragment:
        parts.append(result.fragment)
    return url_meta, parts


def parse_url(url):
    result = analyze_url(url)
    return parse_url_structure(result, True)
