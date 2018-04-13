from .definition import DIGIT_AND_ASCII_RULE_SET, BasePatternRule
from .parse_utils import ParsedPiece, mix


class PiecePatternNodeMix(object):
    __slot__ = ()

    def __init__(self, node):
        self._node = node

    @property
    def parsed_piece(self):
        return self._node.parsed_piece

    @property
    def pattern(self):
        return self._node.pattern

    @property
    def piece(self):
        return self._node.piece

    @property
    def count(self):
        return self._node.count

    def set_pattern(self, pattern):
        self._node.set_pattern(pattern)

    @property
    def node(self):
        return self._node


class PiecePatternNodeViewer(PiecePatternNodeMix):

    __slot__ = ()

    def __init__(self, node):
        super(PiecePatternNodeViewer, self).__init__(node)
        self._parsed_pieces = None

    def view(self):
        return ' '.join([p.fuzzy_rule for p in self.view_parsed_pieces()])

    def view_parsed_pieces(self):
        if self._parsed_pieces:
            return self._parsed_pieces

        self._parsed_pieces = [ParsedPiece([piece], [rule]) for piece, rule in zip(
            self.parsed_piece.pieces, self.parsed_piece.rules)]
        return self._parsed_pieces


class PieceViewer(PiecePatternNodeViewer):
    def view(self):
        return self.piece


class LengthViewer(PiecePatternNodeViewer):
    def view(self):
        return self.parsed_piece.piece_length


class BaseViewer(PiecePatternNodeViewer):
    pass


class MixedViewer(PiecePatternNodeViewer):

    def view_parsed_pieces(self):
        if self._parsed_pieces:
            return self._parsed_pieces

        if len(self.parsed_piece.rules) <= 1:
            self._parsed_pieces = [self.parsed_piece]
        else:
            mixed_pieces, mixed_rules = mix(
                self.parsed_piece.pieces, self.parsed_piece.rules)

            self._parsed_pieces = [ParsedPiece(
                [piece], [rule]) for piece, rule in zip(mixed_pieces, mixed_rules)]
        return self._parsed_pieces


class LastDotSplitFuzzyViewer(PiecePatternNodeViewer):

    def view_parsed_pieces(self):
        if self._parsed_pieces:
            return self._parsed_pieces
        rules = self.parsed_piece.rules
        dot_idx = None
        part_num = len(rules)
        for idx, rule in enumerate(rules[::-1]):
            if idx > 2:
                break
            if rule == BasePatternRule.DOT:
                dot_idx = part_num - idx - 1
                break
        self._parsed_pieces = [ParsedPiece([self.parsed_piece.piece],
                                           [self.parsed_piece.fuzzy_rule])]
        if dot_idx is not None:
            skip = False
            for rule in self.parsed_piece.rules[dot_idx + 1:]:
                if rule not in DIGIT_AND_ASCII_RULE_SET:
                    skip = True
                    break
            if not skip:
                pieces = []
                rules = []
                pieces.append(''.join(self.parsed_piece.pieces[0:dot_idx]))
                pieces.append(self.parsed_piece.pieces[dot_idx])
                rules.append(
                    ''.join(sorted(set(self.parsed_piece.rules[0:dot_idx]))))
                rules.append(self.parsed_piece.rules[dot_idx])
                mixed_pieces, mixed_rules = mix(
                    self.parsed_piece.pieces[dot_idx + 1:], self.parsed_piece.rules[dot_idx + 1:])
                pieces.extend(mixed_pieces)
                rules.extend(mixed_rules)
                self._parsed_pieces = [ParsedPiece(
                    [piece], [rule]) for piece, rule in zip(pieces, rules)]
        return self._parsed_pieces


class FuzzyViewer(PiecePatternNodeViewer):
    def view(self):
        return self.parsed_piece.fuzzy_rule

    def view_parsed_pieces(self):
        if self._parsed_pieces:
            return self._parsed_pieces
        self._parsed_pieces = [ParsedPiece([self.parsed_piece.piece],
                                           [self.parsed_piece.fuzzy_rule])]
        return self._parsed_pieces
