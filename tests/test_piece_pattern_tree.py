from os_urlpattern.piece_pattern_tree import PiecePatternTree
from os_urlpattern.urlparse_utils import parse_url
from os_urlpattern.piece_pattern_parser import PiecePatternParser


def test_count():
    num = 100
    urls = ['http://test.com/abc/%d' % i for i in range(num)]
    parser = PiecePatternParser()
    tree = PiecePatternTree()
    for url in urls:
        _, pieces = parse_url(url)
        piece_patterns = [parser.parse(piece) for piece in pieces]
        tree.add_piece_patterns(piece_patterns)
    assert tree.count == num
    for url in urls:
        _, pieces = parse_url(url)
        piece_patterns = [parser.parse(piece) for piece in pieces]
        tree.add_piece_patterns(piece_patterns)
    assert tree.count == num
