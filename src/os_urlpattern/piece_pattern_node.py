from .compat import itervalues
from .parse_utils import EMPTY_PARSED_PIECE
from .pattern import Pattern
from .utils import TreeNode


class PiecePatternNode(TreeNode):
    __slots__ = ('_pattern')

    def __init__(self, parsed_piece, pattern=None):
        super(PiecePatternNode, self).__init__(parsed_piece)
        self._pattern = Pattern(self.piece) if pattern is None else pattern

    def set_pattern(self, pattern):
        change = not (self._pattern == pattern)
        if change:
            self._pattern = pattern
        return change

    @property
    def pattern(self):
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

    def add_child(self, parsed_piece, pattern, count):
        if self._children is None:
            self._children = {}
        piece = parsed_piece.piece
        is_new = False
        if piece not in self._children:
            child = PiecePatternNode(parsed_piece, pattern)
            child.parrent = self
            self._children[piece] = child
            is_new = True
        child = self._children[piece]
        child.incr_count(count)
        return child, is_new

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
    node = root
    node.incr_count(count)
    is_new = None
    for parsed_piece in parsed_pieces:
        node, is_new = node.add_child(parsed_piece, None, count)
    if uniq and not is_new:
        node.incr_count(0 - count, True)
    node.add_meta(meta)
    return node, is_new


def build_from_piece_pattern_nodes(root, piece_pattern_nodes):
    leaf = piece_pattern_nodes[-1]
    count = leaf.count
    node = root
    node.incr_count(count)
    is_new = None
    for p_node in piece_pattern_nodes:
        node, is_new = node.add_child(
            p_node.parsed_piece, p_node.pattern, count)
    node.update_meta(leaf.meta)
    return node, is_new
