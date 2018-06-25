from .compat import itervalues
from .parse_utils import EMPTY_PARSED_PIECE
from .pattern import Pattern
from .utils import TreeNode, build_tree


class PiecePatternNode(TreeNode):
    __slots__ = ('_pattern')

    def __init__(self, parsed_piece_and_pattern):
        parsed_piece, self._pattern = parsed_piece_and_pattern
        super(PiecePatternNode, self).__init__(parsed_piece)

    def set_pattern(self, pattern):
        self._pattern = pattern

    @property
    def pattern(self):
        if self._pattern is None:
            self._pattern = Pattern(self.piece)
        return self._pattern

    @property
    def piece(self):
        return self.parsed_piece.piece

    @property
    def parsed_piece(self):
        return self._value

    @property
    def children_num(self):
        return len(self._children)

    def incr_count(self, count, recur=False):
        self._count += count
        node = self.parrent if recur else None
        while node:
            node.incr_count(count)
            node = node.parrent

    def __str__(self):
        return u' '.join((self.piece, str(self.pattern)))

    def add_meta(self, data):
        if data is None:
            return
        if self._meta is None:
            self._meta = set()
        self._meta.add(data)

    def update_meta(self, data):
        if not data:
            return
        if self._meta is None:
            self._meta = set()
        self._meta.update(data)


def build_from_parsed_pieces(root, parsed_pieces, count=1, meta=None, uniq=True):
    """Build piece pattern tree from parsed pieces.

    Args:
        root (PiecePatternNode): The root node of the a tree.
        parsed_pieces (sequence): The parsed pieces.
        count (int, optional): Defaults to 1. 
        meta ([type], optional): Defaults to None. The meta data will bind to the leaf node.
        uniq (bool, optional): Defaults to True. The duplicated node edge will not add.

    Returns:
        tuple: 2-tuple, (leaf_node, is_new)
    """
    node, is_new = build_tree(root, [(parsed_piece.piece, (parsed_piece, None))
                                     for parsed_piece in parsed_pieces], count)
    if uniq and not is_new:
        node.incr_count(0 - count, True)
    node.add_meta(meta)
    return node, is_new


def build_from_piece_pattern_nodes(root, piece_pattern_nodes):
    """Build piece pattern tree from piece pattern tree edge.
    
    Args:
        root (PiecePatternNode): The root node of the a tree.
        piece_pattern_nodes (sequence): piece pattern tree edge.
    
    Returns:
        tuple: 2-tuple, (leaf_node, is_new)
    """
    last = piece_pattern_nodes[-1]
    node, is_new = build_tree(root, [(p.piece, (p.parsed_piece, p.pattern))
                                     for p in piece_pattern_nodes], last.count)
    node.update_meta(last.meta)
    return node, is_new
