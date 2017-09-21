from os_urlpattern.pattern import Pattern
from os_urlpattern.piece_pattern_parser import PiecePatternParser, PiecePattern


def _test_parse(parser, data):
    for piece, respects in data:
        p = parser.parse(piece)
        for attr, respect in respects:
            assert getattr(p, attr) == respect


def test_parse():
    parser = PiecePatternParser()
    data = [
        ('abc', [('base_pattern', Pattern('[a-z]+')),
                 ('piece', 'abc'), ('piece_length', len('abc'))]),
        ('abc.exe', [
         ('base_pattern', Pattern('[a-z]+[\\.]+[a-z]+')), ('piece', 'abc[\\.]exe')]),
        ('abcD.exe', [
         ('base_pattern', Pattern('[a-z]+[A-Z]+[\\.]+[a-z]+')), ('piece', 'abcD[\\.]exe'), ('piece_length', len('abcD.exe'))]),
        ('abc1D..exe',  [
         ('base_pattern', Pattern('[a-z]+[0-9]+[A-Z]+[\\.]+[a-z]+')), ('piece', 'abc1D[\\.]{2}exe'), ('piece_length', len('abc1D..exe'))]),
        ('a1b2c3D4..exe',  [
         ('base_pattern', Pattern('[a-z]+[0-9]+' * 3 + '[A-Z]+[0-9]+' + '[\\.]+[a-z]+')), ('piece', 'a1b2c3D4[\\.]{2}exe')]),
        ('@<>..',  [
         ('base_pattern', Pattern('[@]+[<]+[>]+[\\.]+')), ('piece', '[@][<][>][\\.]{2}'), ('piece_length', len('@<>..'))]),
        ('abc4abc', [('mixed_piece_patterns', [
         PiecePattern(['abc4abc'], ['0-9a-z'])])]),
        ('abc4abc-123', [('mixed_piece_patterns', [PiecePattern(['abc4abc'], ['0-9a-z']),
                                                   PiecePattern(
                                                       ['[\-]'], ['\-']),
                                                   PiecePattern(['123'], ['0-9'])])]),
        ('abc4abc-123-', [('mixed_piece_patterns', [PiecePattern(['abc4abc'], ['0-9a-z']),
                                                    PiecePattern(
                                                        ['[\-]'], ['\-']),
                                                    PiecePattern(
                                                        ['123'], ['0-9']),
                                                    PiecePattern(['[\-]'], ['\-'])])]),
        ('%12%E4%67', [('piece_length', len('%12%E4%67'))]),
        ('%' * 10, [('piece_length', 10)]),
    ]
    _test_parse(parser, data)
