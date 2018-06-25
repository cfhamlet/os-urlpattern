from os_urlpattern.parse_utils import (EMPTY_PARSED_PIECE, PieceParser,
                                       analyze_url)
from os_urlpattern.piece_pattern_node import (PiecePatternNode,
                                              build_from_parsed_pieces,
                                              build_from_piece_pattern_nodes)
from os_urlpattern.utils import dump_tree, pick


def test_count():
    num = 100
    urls = ['http://test.com/abc/%d' % i for i in range(num)]
    parser = PieceParser()
    root = PiecePatternNode((EMPTY_PARSED_PIECE, None))
    for url in urls:
        _, pieces = analyze_url(url)
        parsed_pieces = [parser.parse(piece) for piece in pieces]
        build_from_parsed_pieces(root, parsed_pieces)
    assert root.count == num
    for url in urls:
        _, pieces = analyze_url(url)
        parsed_pieces = [parser.parse(piece) for piece in pieces]
        build_from_parsed_pieces(root, parsed_pieces)
    assert root.count == num
    root01 = PiecePatternNode((EMPTY_PARSED_PIECE, None))
    for nodes in dump_tree(root):
        build_from_piece_pattern_nodes(root01, nodes[1:])
    assert root01.count == num

    nodes = pick(dump_tree(root))
    assert nodes[-1].parrent.children_num == num
    assert str(nodes[-1].parrent.pattern) == u"abc"
