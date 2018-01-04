import StringIO
from definition import CHAR_RULE_DICT, SIGN_RULE_SET


class PieceRule(object):
    __slots__ = ['_pieces', '_rules', '_piece', '_piece_length']

    def __init__(self, pieces, rules):
        self._pieces = pieces
        self._rules = rules
        self._piece = None
        self._piece_length = -1

    @property
    def rules(self):
        return self._rules

    @property
    def pieces(self):
        return self._pieces

    @property
    def piece_length(self):
        if self._piece_length < 0:
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
                        length += int(self.piece[idx + 1:e]
                                      ) - 1 - (e - idx + 1)
                        idx = e
                idx += 1

            self._piece_length = length
        return self._piece_length

    def __eq__(self, o):
        if not isinstance(o, PieceRule):
            return False
        return self.piece == o.piece

    @property
    def piece(self):
        if self._piece is None:
            self._piece = ''.join(self._pieces)
        return self._piece

    def __str__(self):
        return str(zip(self.pieces, self.rules))


EMPTY_PIECE_RULE = PieceRule((), ())


class PieceRuleParser(object):
    def __init__(self):
        self._cache = {}
        self._rule_list = []
        self._piece_list = []

    def _reset(self):
        self._rule_list[:] = []
        self._piece_list[:] = []

    def parse(self, string):
        if string in self._cache:
            return self._cache[string]
        self._reset()
        self._pre_process(string)
        pp = self._create_piece_rule()
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

    def _create_piece_rule(self):
        piece_rule = PieceRule(
            tuple(self._piece_list), tuple(self._rule_list))
        return piece_rule
