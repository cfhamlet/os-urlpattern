import re


class PatternUnit(object):
    def __init__(self, pattern_unit_string):
        self._pattern_unit_string = pattern_unit_string
        self._num = None
        self._rules = None
        self._fuzzy_rule = None
        self._parse()

    def _parse(self):
        if self._pattern_unit_string == '':
            self._parse_empty()
        elif self._pattern_unit_string[0] != '[':
            self._parse_char()
        else:
            self._parse_complex()

    def _parse_complex(self):
        if self._pattern_unit_string[-1] == ']':
            self._num = 1
        elif self._pattern_unit_string[-1] == '}':
            t = self._pattern_unit_string.rfind('{')
            self._num = int(self._pattern_unit_string[t + 1:-1])
        elif self._pattern_unit_string[-1] == '+':
            self._num = '+'
        t = self._pattern_unit_string.rfind(']')
        p_str = self._pattern_unit_string[1:t]
        l = len(p_str)
        idx = 0
        self._rules = set()
        while idx < l:
            c = p_str[idx]
            n = 3
            if c in set(['0', 'a', 'A']):
                pass
            elif c == '\\':
                n = 2
            else:
                n = 1
            self._rules.add(p_str[idx:idx + n])
            idx += n

    def _parse_empty(self):
        self._rules = set([''])
        self._num = 1

    def _parse_char(self):
        from definition import CHAR_RULE_DICT
        self._rules = set([CHAR_RULE_DICT[self._pattern_unit_string[0]]])
        self._num = 1

    @property
    def rules(self):
        return self._rules

    @property
    def num(self):  # return int or '+', weird design
        return self._num

    def __str__(self):
        return self._pattern_unit_string


class Pattern(object):
    __slots__ = ('_pattern_string', '_pattern_regex',
                 '_pattern_units', '_fuzzy_rule')

    def __init__(self, pattern_string):
        self._pattern_string = pattern_string
        self._pattern_regex = None
        self._pattern_units = None
        self._fuzzy_rule = None

    @property
    def pattern_units(self):
        from parse_utils import parse_pattern_string
        if self._pattern_units is None:
            self._pattern_units = [PatternUnit(
                u) for u in parse_pattern_string(self._pattern_string)]
        return self._pattern_units

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

    def match(self, piece):
        if not self._pattern_regex:
            self._pattern_regex = re.compile(
                ''.join(('^', self._pattern_string, '$')))
        return True if re.match(self._pattern_regex, piece) else False

    @property
    def fuzzy_rule(self):
        if self._fuzzy_rule is None:
            self._fuzzy_rule = ''.join(sorted(set.union(
                *[u.rules for u in self.pattern_units])))
        return self._fuzzy_rule
