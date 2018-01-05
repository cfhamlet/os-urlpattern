from os_urlpattern.pattern import Pattern
from os_urlpattern.urlparse_utils import PieceParser


def _test_parse(parser, data):
    for piece, expected_pieces, expected_rules in data:
        parsed = parser.parse(piece)
        assert parsed.rules == expected_rules
        assert parsed.pieces == expected_pieces
        assert parsed.piece_length == len(piece)


def test_parse():
    parser = PieceParser()
    data = [
        ('abc', ('abc',), ('a-z',)),
        ('abc.exe', ('abc', '[\\.]', 'exe'), ('a-z', '\\.', 'a-z')),
        ('%' * 10, ('[%]{10}',), ('%',)),
        ('abc1D..exe',  ('abc', '1', 'D',
                         '[\\.]{2}', 'exe'), ('a-z', '0-9', 'A-Z', '\\.', 'a-z')),
        ('@<>..', ('[@]', '[<]', '[>]', '[\\.]{2}'), ('@', '<', '>', '\\.')),
    ]
    _test_parse(parser, data)
