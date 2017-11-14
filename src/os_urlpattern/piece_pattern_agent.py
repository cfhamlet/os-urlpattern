from definition import BasePatternRule,  DIGIT_AND_ASCII_RULE_SET
from pattern import get_pattern_from_cache
from piece_pattern_parser import PiecePattern


class PiecePatternAgent(object):
    def __init__(self, piece_pattern):
        self._piece_pattern = piece_pattern

    @property
    def piece_patterns(self):
        pass

    @property
    def part_num(self):
        pass


class BasePiecePattern(PiecePatternAgent):
    @property
    def piece_patterns(self):
        return self._piece_pattern.base_piece_patterns

    @property
    def part_num(self):
        return self._piece_pattern.base_part_num


class MixedPiecePattern(PiecePatternAgent):
    @property
    def piece_patterns(self):
        return self._piece_pattern.mixed_piece_patterns

    @property
    def part_num(self):
        return self._piece_pattern.mixed_part_num


class FuzzyPattern(PiecePatternAgent):
    @property
    def piece_patterns(self):
        fuzzy_rule = None
        if len(self._piece_pattern.rules) == 1:
            fuzzy_rule = self._piece_pattern.rules[0]
        else:
            uniq_rules = sorted(set(self._piece_pattern.rules))
            fuzzy_rule = ''.join(uniq_rules)
        return [PiecePattern([self._piece_pattern.piece], [fuzzy_rule])]

    @property
    def part_num(self):
        return 1


class LastDotSplitPiecePattern(PiecePatternAgent):
    def __init__(self, piece_pattern):
        super(LastDotSplitPiecePattern, self).__init__(piece_pattern)
        self._piece_patterns = None

    @property
    def piece_patterns(self):
        if self._piece_patterns is not None:
            return self._piece_patterns
        piece_patterns = self._piece_pattern.base_piece_patterns
        dot_idx = None
        part_num = len(piece_patterns)
        for idx, piece_pattern in enumerate(piece_patterns[::-1]):
            if idx > 2:
                break
            if piece_pattern.rules[0] == BasePatternRule.DOT:
                dot_idx = part_num - idx - 1
                break
        self._piece_patterns = piece_patterns
        if dot_idx is not None:
            skip = False
            for piece_pattern in piece_patterns[dot_idx + 1:]:
                if piece_pattern.rules[0] not in DIGIT_AND_ASCII_RULE_SET:
                    skip = True
                    break
            if not skip:
                pieces = []
                rules = []
                pieces.append(
                    ''.join([p.piece for p in piece_patterns[0:dot_idx]]))
                pieces.append(piece_patterns[dot_idx].piece)
                pieces.extend([p.piece for p in piece_patterns[dot_idx + 1:]])
                rules.append(
                    ''.join(sorted(set([p.rules[0] for p in piece_patterns[0:dot_idx]]))))
                rules.append(piece_patterns[dot_idx].rules[0])
                rules.extend([p.rules[0]
                              for p in piece_patterns[dot_idx + 1:]])
                self._piece_patterns = [PiecePattern(
                    [piece], [rule]) for piece, rule in zip(pieces, rules)]

        return self._piece_patterns

    @property
    def pattern(self):
        return get_pattern_from_cache(
            ''.join([str(p.base_pattern) for p in self.piece_patterns]))

    @property
    def part_num(self):
        return len(self.piece_patterns)
