"""Pattern class.
"""
from __future__ import unicode_literals

import re
import weakref

from .utils import pick


class PatternUnit(object):
    """Sub-piece of pattern."""

    __slots__ = ('pattern_unit_string', 'rules', 'num', '_fuzzy_rule')

    def __init__(self, pattern_unit_string):
        self.pattern_unit_string = pattern_unit_string
        from .parse_utils import parse_pattern_unit_string
        self.rules, self.num = parse_pattern_unit_string(pattern_unit_string)
        self._fuzzy_rule = None

    def is_literal(self):
        """Whether this unit string is literal or not.

        Note:
            According to the char representation, fixed-length
            single sign is literal, like:  [\\.]{2}  [\\-]

        Returns:
            bool: Whether it is literal.
        """

        from .definition import DIGIT_AND_ASCII_RULE_SET, Symbols
        r = False
        if not self.pattern_unit_string.startswith(Symbols.BRACKETS_L):
            r = True
        elif len(self.rules) == 1:
            if self.num > 0:
                rule = pick(self.rules)
                if rule not in DIGIT_AND_ASCII_RULE_SET:
                    r = True
        return r

    @property
    def fuzzy_rule(self):
        if self._fuzzy_rule is None:
            self._fuzzy_rule = ''.join(sorted(self.rules))
        return self._fuzzy_rule

    def __str__(self):
        return ' '.join((self.pattern_unit_string, self.fuzzy_rule, str(self.num)))

    __repr__ = __str__


class Pattern(object):
    """Pattern for handle pattern string. """

    __slots__ = ('pattern_string', '_pattern_regex',
                 '_pattern_units', '_fuzzy_rule')

    def __init__(self, pattern_string):
        self.pattern_string = pattern_string
        self._pattern_regex = None
        self._pattern_units = None
        self._fuzzy_rule = None

    @property
    def pattern_units(self):
        """tuple: Pattern units."""

        from .parse_utils import parse_pattern_string
        if self._pattern_units is None:
            self._pattern_units = tuple([PatternUnit(
                u) for u in parse_pattern_string(self.pattern_string)])
        return self._pattern_units

    def __str__(self):
        return self.pattern_string

    __repr__ = __str__

    def __hash__(self):
        return hash(self.pattern_string)

    def __eq__(self, o):
        return self.pattern_string == o.pattern_string

    def match(self, piece):
        if not self._pattern_regex:
            self._pattern_regex = re.compile(
                ''.join(('^', self.pattern_string, '$')))
        return True if re.match(self._pattern_regex, piece) else False

    @property
    def fuzzy_rule(self):
        """str: All rules of the pattern join into a string."""
        if self._fuzzy_rule is None:
            self._fuzzy_rule = ''.join(sorted(set.union(
                *[u.rules for u in self.pattern_units])))
        return self._fuzzy_rule
