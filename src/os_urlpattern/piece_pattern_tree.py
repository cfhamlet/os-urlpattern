import math
from piece_pattern_node import PiecePatternNode
from piece_pattern_parser import EMPTY_PIECE_PATTERN


class PiecePatternTree(object):
    def __init__(self):
        self._root = PiecePatternNode(EMPTY_PIECE_PATTERN)

    @property
    def root(self):
        return self._root

    @property
    def count(self):
        return self._root.count

    def add_piece_patterns(self, piece_patterns, count=1):
        node = self._root
        node.incr_count(count)
        is_new = None
        for piece_pattern in piece_patterns:
            node, is_new = node.add_child_node_from_piece_pattern(
                piece_pattern, count)
        if not is_new:
            node.incr_count(0 - count, True)
        return is_new

    def dump_paths(self):
        for path in self._root.dump_paths():
            yield path
