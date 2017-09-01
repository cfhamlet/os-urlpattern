import StringIO
import hashlib


class URLMeta(object):
    __slots__ = ['_path_depth', '_query_keys', '_has_fragment', '_hash_code']

    def __init__(self, path_depth, query_keys, has_fragment):
        self._path_depth = path_depth
        self._query_keys = query_keys
        self._has_fragment = has_fragment
        self._hash_code = None

    def __hash__(self):
        return hash(self.hashcode)

    def __eq__(self, o):
        return hash(o) == hash(self)

    @property
    def hashcode(self):
        if self._hash_code is not None:
            return self._hash_code
        s = StringIO.StringIO()
        s.write(self._path_depth)
        if self._query_keys:
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
    def depth(self):
        return sum((self.path_depth, self.query_depth, self.fragment_depth))
