from os_urlpattern.piece_pattern_parser import PiecePatternParser


def _test_parse(parser, data):
    for piece, last_dot_split, respects in data:
        p = parser.parse(piece, last_dot_split)
        for attr, respect in respects:
            assert getattr(p, attr) == respect


def test_parse():
    class TempConfig(object):
        reserved_ext_names = set(['exe'])
        merge_multi_piece_threshold = 7
    parser = PiecePatternParser(TempConfig)
    data = [
        ('abc', True, [('pattern_string', '[a-z]+'), ('piece', 'abc')]),
        ('abc.exe', True, [
         ('pattern_string', '[a-z]+[\\.]+exe'), ('piece', 'abc[\\.]exe')]),
        ('abcD.exe', True, [
         ('pattern_string', '[A-Za-z]+[\\.]+exe'), ('piece', 'abcD[\\.]exe')]),
        ('abcD.exe', False, [
         ('pattern_string', '[A-Za-z]+[\\.]+[a-z]+'), ('piece', 'abcD[\\.]exe')]),
        ('abc1D..exe', True, [
         ('pattern_string', '[a-z]+[0-9]+[A-Z]+[\\.]+exe'), ('piece', 'abc1D[\\.]{2}exe')]),
        ('a1b2c3D4..exe', True, [
         ('pattern_string', '[0-9A-Za-z]+[\\.]+exe'), ('piece', 'a1b2c3D4[\\.]{2}exe')]),
        ('a1b2c3D4..exe', False, [
         ('pattern_string', '[0-9A-Z\\.a-z]+'), ('piece', 'a1b2c3D4[\\.]{2}exe')]),
        ('@<>..', False, [
         ('pattern_string', '[<>@\\.]+'), ('piece', '[@][<][>][\\.]{2}')]),
    ]
    _test_parse(parser, data)
