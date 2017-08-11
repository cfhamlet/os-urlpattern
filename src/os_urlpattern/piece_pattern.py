from pattern import Pattern
from definition import BasePattern, BasePatternRule
from pattern import get_pattern_from_cache


class PiecePattern(object):
    def __init__(self, piece, pattern):
        self._piece = piece
        self._pattern = pattern

    @property
    def piece(self):
        return self._piece

    def __str__(self):
        return ' '.join((self.piece, self.pattern_string))

    __repr__ = __str__

    @property
    def pattern(self):
        return self._pattern

    @property
    def pattern_string(self):
        return self._pattern.pattern_string

    def has_multi_part(self):
        return False

    @property
    def part_num(self):
        return 1

    def __hash__(self):
        return hash(self.pattern_string)

    def __eq__(self, o):
        if not isinstance(o, PiecePattern):
            return False
        return self.pattern == o.pattern


class MultiPiecePattern(PiecePattern):
    def __init__(self, piece_pattern_list):
        self._piece = ''.join([pp.piece for pp in piece_pattern_list])
        self._pattern = get_pattern_from_cache(
            ''.join([pp.pattern_string for pp in piece_pattern_list]))
        self._piece_pattern_list = piece_pattern_list

    def has_multi_part(self):
        return True if self.part_num > 1 else False

    @property
    def part_num(self):
        return sum([p.part_num for p in self._piece_pattern_list])

    @property
    def piece_pattern_list(self):
        return self._piece_pattern_list

EMPTY_PIECE_PATTERN = PiecePattern(BasePatternRule.EMPTY, BasePattern.EMPTY)