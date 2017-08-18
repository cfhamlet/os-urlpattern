import pytest
from os_urlpattern.config import Config
from os_urlpattern.piece_pattern_tree import PiecePatternTree
from os_urlpattern.urlparse_utils import parse_url
from os_urlpattern.piece_pattern_parser import PiecePatternParser


@pytest.fixture(scope='function')
def config():
    c = Config()
    c.add_section('make')
    c.set('make', 'reserved_ext_names', 'exe')
    c.set('make', 'merge_multi_piece_threshold', '7')
    c.set('make', 'keep_piece_as_pattern', 'true')
    c.set('make', 'level_combiner_class',
          'tests.test_piece_pattern_tree.FakeCombiner')
    return c


class FakeCombiner(object):
    def __init__(self, config, piece_pattern_tree, level):
        pass

    def add_node(self, node, is_new, count):
        pass


def test_count(config):
    num = 100
    urls = ['http://test.com/abc/%d' % i for i in range(num)]
    url_meta, _ = parse_url(urls[0])
    parser = PiecePatternParser(config)
    tree = PiecePatternTree(config, url_meta)
    for url in urls:
        _, pieces = parse_url(url)
        tree.add_pieces(parser, pieces)
    assert tree.count == num
