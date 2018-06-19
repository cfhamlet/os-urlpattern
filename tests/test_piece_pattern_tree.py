from os_urlpattern.parse_utils import PieceParser, parse_url, EMPTY_PARSED_PIECE
from os_urlpattern.piece_pattern_node import (PiecePatternNode,
                                              build_from_parsed_pieces)


def test_count():
    num = 100
    urls = ['http://test.com/abc/%d' % i for i in range(num)]
    parser = PieceParser()
    root = PiecePatternNode(EMPTY_PARSED_PIECE)
    for url in urls:
        _, pieces = parse_url(url)
        parsed_pieces = [parser.parse(piece) for piece in pieces]
        build_from_parsed_pieces(root, parsed_pieces)
    assert root.count == num
    for url in urls:
        _, pieces = parse_url(url)
        parsed_pieces = [parser.parse(piece) for piece in pieces]
        build_from_parsed_pieces(root, parsed_pieces)
    assert root.count == num
