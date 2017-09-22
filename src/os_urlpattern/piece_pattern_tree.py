import math
from piece_pattern_node import PiecePatternNode
from piece_pattern_parser import EMPTY_PIECE_PATTERN


class PiecePatternTree(object):
    def __init__(self, url_meta):
        self._root = PiecePatternNode(EMPTY_PIECE_PATTERN)
        self._url_meta = url_meta

    @property
    def url_meta(self):
        return self._url_meta

    @property
    def root(self):
        return self._root

    @property
    def count(self):
        return self._root.count

    def add_piece_patterns(self, piece_patterns, count=1, uniq_path=True):
        node = self._root
        node.incr_count(count)
        is_new = None
        for piece_pattern in piece_patterns:
            node, is_new = node.add_child_node_from_piece_pattern(
                piece_pattern, count)
        if uniq_path and not is_new:
            node.incr_count(0 - count, True)
        return is_new

    def dump_paths(self):
        for path in self._root.dump_paths():
            yield path
