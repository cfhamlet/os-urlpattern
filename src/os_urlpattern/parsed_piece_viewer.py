from .parse_utils import ParsedPiece, mix


class ParsedPieceViewer(object):
    def __init__(self, parsed_piece):
        self._parsed_piece = parsed_piece
        self._parsed_pieces = None

    @property
    def parsed_piece(self):
        return self._parsed_piece

    def __eq__(self, o):
        return self.view == o.view

    def __hash__(self):
        return hash(self.view)

    @property
    def view(self):
        return ' '.join([p.fuzzy_rule for p in self.parsed_pieces])

    @property
    def parsed_pieces(self):
        if self._parsed_pieces:
            return self._parsed_pieces

        self._parsed_pieces = [ParsedPiece([piece], [rule]) for piece, rule in zip(
            self._parsed_piece.pieces, self._parsed_piece.rules)]
        return self._parsed_pieces


class PieceViewer(ParsedPieceViewer):
    def view(self):
        return self._parsed_piece.piece


class LengthViewer(ParsedPieceViewer):
    def view(self):
        return self._parsed_piece.piece_length


class BaseViewer(ParsedPieceViewer):
    pass


class MixedViewer(ParsedPieceViewer):

    def parsed_pieces(self):
        if self._parsed_pieces:
            return self._parsed_pieces

        if len(self._parsed_piece.rules) <= 1:
            self._parsed_pieces = [self._parsed_piece]
        else:
            mixed_pieces, mixed_rules = mix(
                self._parsed_piece.pieces, self._parsed_piece.rules)

            self._parsed_pieces = [ParsedPiece(
                [piece], [rule]) for piece, rule in zip(mixed_pieces, mixed_rules)]
        return self._parsed_pieces


class LastDotSplitFuzzyViewer(ParsedPieceViewer):

    def parsed_pieces(self):
        if self._parsed_pieces:
            return self._parsed_pieces
        rules = self._parsed_piece.rules
        dot_idx = None
        part_num = len(rules)
        for idx, rule in enumerate(rules[::-1]):
            if idx > 2:
                break
            if rule == BasePatternRule.DOT:
                dot_idx = part_num - idx - 1
                break
        self._parsed_pieces = [ParsedPiece([self._parsed_piece.piece],
                                           [self._parsed_piece.fuzzy_rule])]
        if dot_idx is not None:
            skip = False
            for rule in self._parsed_piece.rules[dot_idx + 1:]:
                if rule not in DIGIT_AND_ASCII_RULE_SET:
                    skip = True
                    break
            if not skip:
                pieces = []
                rules = []
                pieces.append(''.join(self._parsed_piece.pieces[0:dot_idx]))
                pieces.append(self._parsed_piece.pieces[dot_idx])
                rules.append(
                    ''.join(sorted(set(self._parsed_piece.rules[0:dot_idx]))))
                rules.append(self._parsed_piece.rules[dot_idx])
                mixed_pieces, mixed_rules = mix(
                    self._parsed_piece.pieces[dot_idx + 1:],
                    self._parsed_piece.rules[dot_idx + 1:])
                pieces.extend(mixed_pieces)
                rules.extend(mixed_rules)
                self._parsed_pieces = [ParsedPiece(
                    [piece], [rule]) for piece, rule in zip(pieces, rules)]
        return self._parsed_pieces


class FuzzyViewer(ParsedPieceViewer):
    def view(self):
        return self._parsed_piece.fuzzy_rule

    def view_parsed_pieces(self):
        if self._parsed_pieces:
            return self._parsed_pieces
        self._parsed_pieces = [ParsedPiece([self._parsed_piece.piece],
                                           [self._parsed_piece.fuzzy_rule])]
        return self._parsed_pieces
