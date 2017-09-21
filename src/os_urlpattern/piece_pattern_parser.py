import StringIO
import copy
from definition import BasePatternRule, CHAR_RULE_DICT, SIGN_RULE_SET, \
    BASE_ASCII_RULE_SET, DIGIT_AND_ASCII_RULE_SET
from pattern import get_pattern_from_cache

MIXED_RULE_SET = copy.copy(DIGIT_AND_ASCII_RULE_SET)
MIXED_RULE_SET.add('%')


class PiecePattern(object):
    def __init__(self, pieces, rules):
        self._pieces = pieces
        self._rules = rules
        self._piece = None
        self._piece_length = -1
        self._fuzzy_pattern = None
        self._base_pattern = None
        self._sub_piece_patterns = None
        self._mixed_base_pattern = None
        self._mixed_piece_patterns = None

    @property
    def piece_length(self):
        if self._piece_length >= 0:
            return self._piece_length
        length_base = length = len(self.piece)
        idx = 0
        while idx < length_base:
            c = self.piece[idx]
            if c == '[' or c == ']':
                if idx == 0 or self.piece[idx - 1] != '\\':
                    length += -1
            elif c == '\\':
                if self.piece[idx + 1] != '\\':
                    length += -1
            elif c == '{':
                if self.piece[idx - 1] == ']':
                    e = self.piece.index('}', idx)
                    length += int(self.piece[idx + 1:e]) - 1 - (e - idx + 1)
                    idx = e
            idx += 1

        self._piece_length = length
        return self._piece_length

    @property
    def sub_piece_patterns(self):
        if not self._sub_piece_patterns:
            self._sub_piece_patterns = [PiecePattern(
                [piece], [rule]) for piece, rule in zip(self._pieces, self._rules)]
        return self._sub_piece_patterns

    @property
    def mixed_piece_patterns(self):
        if self._mixed_piece_patterns:
            return self._mixed_piece_patterns

        if self.part_num == 1:
            return self.sub_piece_patterns

        mixed_pieces = []
        mixed_rules = []

        pieces = []
        rules = []
        mix = False
        for piece, rule in zip(self._pieces, self._rules):
            if rule in MIXED_RULE_SET:
                if rules and not mix:
                    mixed_pieces.extend(pieces)
                    mixed_rules.extend(rules)
                    pieces = []
                    rules = []
                mix = True
            else:
                if rules and mix:
                    mixed_pieces.append(''.join(pieces))
                    mixed_rules.append(''.join(sorted(set(rules))))
                    pieces = []
                    rules = []
                mix = False
            pieces.append(piece)
            rules.append(rule)
        if mix:
            mixed_pieces.append(''.join(pieces))
            mixed_rules.append(''.join(sorted(set(rules))))
        else:
            mixed_pieces.extend(pieces)
            mixed_rules.extend(rules)

        self._mixed_piece_patterns = [PiecePattern(
            [piece], [rule]) for piece, rule in zip(mixed_pieces, mixed_rules)]
        return self._mixed_piece_patterns

    def __str__(self):
        return ' '.join((self.piece, str(self.base_pattern)))

    __repr__ = __str__

    def __eq__(self, o):
        if not isinstance(o, PiecePattern):
            return False
        return self.piece == o.piece

    @property
    def piece(self):
        if self._piece is None:
            self._piece = ''.join(self._pieces)
        return self._piece

    def _one_or_more(self, rule):
        return '[%s]+' % rule if rule else ''

    def _exact_num(self, rule, num):
        return '[%s]' % rule if num == 1 else '[%s]{%d}' % (rule, num)

    @property
    def fuzzy_pattern(self):
        if self._fuzzy_pattern is None:
            fuzzy_rule = None
            if self.part_num == 1:
                fuzzy_rule = self._rules[0]
            else:
                uniq_rules = sorted(set(self._rules))
                fuzzy_rule = ''.join(uniq_rules)
            self._fuzzy_pattern = get_pattern_from_cache(
                self._one_or_more(fuzzy_rule))
        return self._fuzzy_pattern

    @property
    def base_pattern(self):
        if self._base_pattern is None:
            if self.part_num == 1:
                self._base_pattern = get_pattern_from_cache(
                    self._one_or_more(self._rules[0]))
            else:
                self._base_pattern = get_pattern_from_cache(
                    ''.join([self._one_or_more(rule) for rule in self._rules]))
        return self._base_pattern

    @property
    def mixed_base_pattern(self):
        if self._mixed_base_pattern:
            return self._mixed_base_pattern
        self._mixed_base_pattern = get_pattern_from_cache(
            ''.join([str(p.base_pattern) for p in self.mixed_piece_patterns]))
        return self._mixed_base_pattern

    def exact_num_pattern(self, num):
        assert self.part_num == 1, 'only one part has exact num pattern'
        return get_pattern_from_cache(self._exact_num(self._rules[0], num))

    @property
    def part_num(self):
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
            return self._exact_num(rule, len(letter))
        return letter

    def _create_piece_pattern(self):
        piece_pattern = PiecePattern(self._piece_list, self._rule_list)
        return piece_pattern
