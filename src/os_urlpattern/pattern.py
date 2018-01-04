import re


class Pattern(object):
    __slots__ = ['_pattern_string', '_pattern_regex']

    def __init__(self, pattern_string):
        self._pattern_string = pattern_string
        self._pattern_regex = None

    def __str__(self):
        return self.pattern_string

    __repr__ = __str__

    @property
    def pattern_string(self):
        return self._pattern_string

    def __hash__(self):
        return hash(self.pattern_string)

    def __eq__(self, o):
        if not isinstance(o, Pattern):
            return False
        return self.pattern_string == o.pattern_string

    def match(self, string):
        if not self._pattern_regex:
            self._pattern_regex = re.compile(
                ''.join(('^', self._pattern_string, '$')))
        return True if re.match(self._pattern_regex, string) else False


_PATTERN_CACHE = {}


def get_pattern_from_cache(pattern_string):
    if pattern_string not in _PATTERN_CACHE:
        _PATTERN_CACHE[pattern_string] = Pattern(pattern_string)
    return _PATTERN_CACHE[pattern_string]
