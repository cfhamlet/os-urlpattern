import StringIO
from definition import BasePatternRule, CHAR_RULE_DICT, SIGN_RULE_SET, \
    BASE_ASCII_RULE_SET, DIGIT_AND_ASCII_RULE_SET
from pattern import get_pattern_from_cache


class PiecePattern(object):
    def __init__(self, pieces, rules):
        self._pieces = pieces
        self._rules = rules

    @property
    def piece(self):
        return ''.join(self._pieces)

    def _one_or_more(self, rule):
        return '[%s]+' % rule if rule else ''

    @property
    def fuzzy_pattern(self):
        uniq_rules = sorted(set(self._rules))
        return get_pattern_from_cache(self._one_or_more(''.join(uniq_rules)))

    @property
    def base_pattern(self):
        return get_pattern_from_cache(''.join([self._one_or_more(rule) for rule in self._rules]))

    def has_multi_part(self):
        return False if self.piece_num <= 1 else True

    @property
    def piece_num(self):
        return len(self._pieces)


EMPTY_PIECE_PATTERN = PiecePattern((), ())


class PiecePatternParser(object):
    def __init__(self):
        self._cache = {}
        self._reset()

    def _reset(self):
        self._rule_list = []
        self._piece_list = []

    def parse(self, string):
        if string in self._cache:
            return self._cache[string]
        self._reset()
        self._pre_process(string)
        pp = self._create_piece_pattern()
        self._cache[string] = pp
        return pp

    def _pre_process(self, string):
        for c in string:
            self._define(c)
        for idx, buf in enumerate(self._piece_list):
            buf.seek(0)
            letter = buf.read()
            self._piece_list[idx] = self._normalize(
                letter, self._rule_list[idx])

    def _define(self, char):
        last_rule = self._rule_list[-1] if self._rule_list else None
        rule = CHAR_RULE_DICT[char]

        if last_rule != rule:
            self._piece_list.append(StringIO.StringIO())
            self._rule_list.append(rule)
        self._piece_list[-1].write(char)

    def _exact_num(self, rule, num):
        if num == 1:
            return '[%s]' % rule
        return '[%s]{%d}' % (rule, num)

    def _normalize(self, letter, rule):
        if rule in SIGN_RULE_SET:
            l = len(letter)
            return self._exact_num(rule, l)
        return letter

    def _create_piece_pattern(self):
        piece_pattern = PiecePattern(self._piece_list, self._rule_list)
        return piece_pattern
