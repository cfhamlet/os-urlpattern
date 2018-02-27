from os_urlpattern.parse_utils import PieceParser, parse_url
from os_urlpattern.piece_pattern_tree import PiecePatternTree


def test_count():
    num = 100
    urls = ['http://test.com/abc/%d' % i for i in range(num)]
    parser = PieceParser()
    tree = PiecePatternTree()
    for url in urls:
        _, pieces = parse_url(url)
        parsed_pieces = [parser.parse(piece) for piece in pieces]
        tree.add_from_parsed_pieces(parsed_pieces)
    assert tree.count == num
    for url in urls:
        _, pieces = parse_url(url)
        parsed_pieces = [parser.parse(piece) for piece in pieces]
        tree.add_from_parsed_pieces(parsed_pieces)
    assert tree.count == num
