from os_urlpattern.pattern import Pattern
from os_urlpattern.piece_pattern_parser import PiecePatternParser


def _test_parse(parser, data):
    for piece, respects in data:
        p = parser.parse(piece)
        for attr, respect in respects:
            assert getattr(p, attr) == respect


def test_parse():
    parser = PiecePatternParser()
    data = [
        ('abc', [('base_pattern', Pattern('[a-z]+')), ('piece', 'abc')]),
        ('abc.exe', [
         ('base_pattern', Pattern('[a-z]+[\\.]+[a-z]+')), ('piece', 'abc[\\.]exe')]),
        ('abcD.exe', [
         ('base_pattern', Pattern('[a-z]+[A-Z]+[\\.]+[a-z]+')), ('piece', 'abcD[\\.]exe')]),
        ('abc1D..exe',  [
         ('base_pattern', Pattern('[a-z]+[0-9]+[A-Z]+[\\.]+[a-z]+')), ('piece', 'abc1D[\\.]{2}exe')]),
        ('a1b2c3D4..exe',  [
         ('base_pattern', Pattern('[a-z]+[0-9]+' * 3 + '[A-Z]+[0-9]+' + '[\\.]+[a-z]+')), ('piece', 'a1b2c3D4[\\.]{2}exe')]),
        ('@<>..',  [
         ('base_pattern', Pattern('[@]+[<]+[>]+[\\.]+')), ('piece', '[@][<][>][\\.]{2}')]),
    ]
    _test_parse(parser, data)
