"""Definition of global constant varialbles.
"""

from __future__ import unicode_literals

import hashlib
import string

from .pattern import Pattern

DEFAULT_ENCODING = 'UTF-8'


class Symbols(object):
    PLUS = '+'
    EMPTY = ''
    SLASH = '/'
    EQUALS = '='
    NUMBER = '#'
    PERCENT = '%'
    QUESTION = '?'
    BRACES_L = '{'
    BRACES_R = '}'
    AMPERSAND = '&'
    BACKSLASH = '\\'
    BRACKETS_L = '['
    BRACKETS_R = ']'


class BasePatternRule(object):
    DIGIT = '0-9'
    BASE_ASCII_LOWER = 'a-z'
    BASE_ASCII_UPPER = 'A-Z'
    BASE_ASCII = 'A-Za-z'
    BASE_DIGIT_AND_ASCII_LOWER = '0-9a-z'
    BASE_DIGIT_AND_ASCII_UPPER = '0-9A-Z'
    BASE_DIGIT_AND_ASCII = '0-9A-Za-z'
    SINGLE_DIGIT = '[0-9]'
    SINGLE_ASCII_LOWER = '[a-z]'
    SINGLE_ASCII_UPPER = '[A-Z]'
    MULTI_DIGIT = '[0-9]+'
    MULTI_ASCII_LOWER = '[a-z]+'
    MULTI_ASCII_UPPER = '[A-Z]+'
    MULTI_ASCII = '[A-Za-z]+'
    MULTI_DIGIT_AND_ASCII_LOWER = '[0-9a-z]+'
    MULTI_DIGIT_AND_ASCII_UPPER = '[0-9A-Z]+'
    MULTI_DIGIT_AND_ASCII = '[0-9A-Za-z]+'
    DOT = '\\.'
    EMPTY = ''
    SINGLE_QUESTION = '[\\?]'


ZERO_DIGEST = hashlib.md5(b'0').hexdigest().upper()
QUERY_PART_RESERVED_CHARS = frozenset([Symbols.EQUALS])
EMPTY_TUPLE = ()
BLANK_TUPLE = (BasePatternRule.EMPTY,)

# 26 letters rules
CHAR_AND_RULE_LIST = []
ASCII_AND_RULE_LIST = []
ASCII_AND_RULE_LIST.extend([(i, BasePatternRule.BASE_ASCII_LOWER)
                            for i in string.ascii_lowercase])
ASCII_AND_RULE_LIST.extend([(i, BasePatternRule.BASE_ASCII_UPPER)
                            for i in string.ascii_uppercase])
CHAR_AND_RULE_LIST.extend(ASCII_AND_RULE_LIST)

# digit rules
DIGIT_AND_RULE_LIST = [(i, BasePatternRule.DIGIT)
                       for i in string.digits]
CHAR_AND_RULE_LIST.extend(DIGIT_AND_RULE_LIST)

# digit and 26 letters set
DIGIT_SET = frozenset([i for i in string.digits])
ASCII_LOWER_SET = frozenset([i for i in string.ascii_lowercase])
ASCII_UPPER_SET = frozenset([i for i in string.ascii_uppercase])
ASCII_DIGIT_SET = frozenset([c for c, _ in CHAR_AND_RULE_LIST])

# do not escaped symbol rules
SYMBOL = '%&_@#;:,=<>~/'
SYMBOL_SET = frozenset([i for i in SYMBOL])
SYMBOL_AND_RULE_LIST = [(i, i) for i in SYMBOL_SET]
CHAR_AND_RULE_LIST.extend(SYMBOL_AND_RULE_LIST)

# escaped symbol rules
ESCAPE = '.+\\"\'()[]{}*$^?|!-'
ESCAPE_SET = frozenset([i for i in ESCAPE])
ESCAPE_AND_RULE_LIST = [(i, '\\%s' % i) for i in ESCAPE_SET]
CHAR_AND_RULE_LIST.extend(ESCAPE_AND_RULE_LIST)

# all char and rule mapping
CHAR_RULE_DICT = dict(CHAR_AND_RULE_LIST)
RULE_SET = frozenset([r for _, r in CHAR_AND_RULE_LIST])

# ==
RULE_SIGN_DICT = dict(
    [(v, k) for k, v in SYMBOL_AND_RULE_LIST + ESCAPE_AND_RULE_LIST])
SIGN_RULE_SET = frozenset(RULE_SIGN_DICT.keys())

# ==
DIGIT_AND_ASCII_LOWER_RULE_LIST = [BasePatternRule.DIGIT,
                                   BasePatternRule.BASE_ASCII_LOWER]
DIGIT_AND_ASCII_UPPER_RULE_LIST = [BasePatternRule.DIGIT,
                                   BasePatternRule.BASE_ASCII_UPPER]
DIGIT_AND_ASCII_RULE_LIST = [BasePatternRule.DIGIT,
                             BasePatternRule.BASE_ASCII_LOWER,
                             BasePatternRule.BASE_ASCII_UPPER,
                             BasePatternRule.BASE_ASCII]

DIGIT_AND_ASCII_UPPER_RULE_SET = frozenset(DIGIT_AND_ASCII_UPPER_RULE_LIST)
DIGIT_AND_ASCII_LOWER_RULE_SET = frozenset(DIGIT_AND_ASCII_LOWER_RULE_LIST)
DIGIT_AND_ASCII_RULE_SET = frozenset(DIGIT_AND_ASCII_RULE_LIST)

# ==
BASE_ASCII_RULE_SET = frozenset([BasePatternRule.BASE_ASCII,
                                 BasePatternRule.BASE_ASCII_LOWER,
                                 BasePatternRule.BASE_ASCII_UPPER])

MULTI_ASCII_RULE_SET = frozenset([BasePatternRule.MULTI_ASCII,
                                  BasePatternRule.MULTI_ASCII_LOWER,
                                  BasePatternRule.MULTI_ASCII_UPPER])

MIXED_RULE_SET = DIGIT_AND_ASCII_RULE_SET.union([Symbols.PERCENT])


class BasePattern(object):
    SINGLE_DIGIT = Pattern(BasePatternRule.SINGLE_DIGIT)
    SINGLE_ASCII_LOWER = Pattern(BasePatternRule.SINGLE_ASCII_LOWER)
    SINGLE_ASCII_UPPER = Pattern(BasePatternRule.SINGLE_ASCII_UPPER)
    MULTI_DIGIT = Pattern(BasePatternRule.MULTI_DIGIT)
    MULTI_ASCII_LOWER = Pattern(BasePatternRule.MULTI_ASCII_LOWER)
    MULTI_ASCII_UPPER = Pattern(BasePatternRule.MULTI_ASCII_UPPER)
    MULTI_DIGIT_AND_ASCII_LOWER = Pattern(
        BasePatternRule.MULTI_DIGIT_AND_ASCII_LOWER)
    MULTI_DIGIT_AND_ASCII_UPPER = Pattern(
        BasePatternRule.MULTI_DIGIT_AND_ASCII_UPPER)
    MULTI_DIGIT_AND_ASCII = Pattern(BasePatternRule.MULTI_DIGIT_AND_ASCII)
    DOT = Pattern(BasePatternRule.DOT)
    EMPTY = Pattern(BasePatternRule.EMPTY)
