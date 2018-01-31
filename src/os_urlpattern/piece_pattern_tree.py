from piece_patern_node import PiecePatternNode
from urlparse_utils import EMPTY_PARSED_PIECE


class PiecePatternTree(object):
    def __init__(self):
        self._root = PiecePatternNode(EMPTY_PARSED_PIECE)

    @property
    def root(self):
        return self._root

    @property
    def count(self):
        return self._root.count

    def add_from_parsed_pieces(self, parsed_pieces, count=1, uniq_path=True):
        node = self._root
        node.incr_count(count)
        is_new = None
        for parsed_piece in parsed_pieces:
            node, is_new = node.add_child_node_from_parsed_piece(
                parsed_piece, count)
        if uniq_path and not is_new:
            node.incr_count(0 - count, True)
        return is_new

    def dump_paths(self):
        for path in self._root.dump_paths():
            yield path
