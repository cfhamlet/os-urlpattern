import math
from piece_pattern_node import PiecePatternNode
from piece_pattern_parser import EMPTY_PIECE_PATTERN
from utils import load_object


class PiecePatternTree(object):
    def __init__(self, config, url_meta):
        self._root = PiecePatternNode(EMPTY_PIECE_PATTERN)
        self._url_meta = url_meta
        level_combiner_class = load_object(
            config.get('make', 'level_combiner_class'))
        self._level_combiners = [level_combiner_class(
            config, self, i) for i in range(self._url_meta.depth + 1)]
        self._keep_piece_as_pattern = config.getboolean(
            'make', 'keep_piece_as_pattern')

    @property
    def url_meta(self):
        return self._url_meta

    def pattern_entropy(self, count=-1):
        if count < self._root.count:
            count = self._root.count
        return sum([p.entropy(count) for p in self._level_combiners])

    def entropy(self, count=-1):
        if count < self._root.count:
            count = self._root.count
        return self._root.entropy(count)

    @property
    def level_combiners(self):
        return self._level_combiners

    @property
    def count(self):
        return self._root.count

    @property
    def depth(self):
        return self._url_meta.depth

    def load_piece_pattern_nodes(self, piece_pattern_nodes):
        node = self._root
        count = piece_pattern_nodes[-1].count
        node.incr_count(count)
        self._level_combiners[0].add_node(node, None, count)
        for idx, piece_pattern_node in enumerate(piece_pattern_nodes):
            node, is_new = node.add_child_node_from_piece_pattern(
                piece_pattern_node.piece_pattern, count, piece_pattern_node.pattern)
            self._level_combiners[idx + 1].add_node(node, is_new, count)

    def load_piece_patterns(self, piece_patterns, count=1):
        node = self._root
        node.incr_count(count)
        self._level_combiners[0].add_node(node, None, count)
        for idx, piece_pattern in enumerate(piece_patterns):
            node, is_new = node.add_child_node_from_piece_pattern(
                piece_pattern, count)
            self._level_combiners[idx + 1].add_node(node, is_new, count)

    def add_pieces(self, piece_pattern_parser, pieces, count=1):
        node = self._root
        node.incr_count(count)
        self._level_combiners[0].add_node(node, None, count)
        for idx, piece in enumerate(pieces):
            node, is_new = node.add_child_node_from_piece(
                piece_pattern_parser, piece, count)
            self._level_combiners[idx + 1].add_node(node, is_new, count)

    def _piece_eq_pattern(self, path):
        return False if False in set([p.piece_eq_pattern() for p in path]) else True

    def dump_paths(self, dump_all=False):
        for path in self._root.dump_paths():
            if not self._keep_piece_as_pattern and not dump_all and \
                    self._piece_eq_pattern(path):
                continue
            yield path

    def combine(self):
        change = False
        for level_combiner in self._level_combiners:
            c = level_combiner.combine()
            if not change and c:
                change = c
        return change
