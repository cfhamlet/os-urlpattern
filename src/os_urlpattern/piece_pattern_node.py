import math
from pattern import get_pattern_from_cache
from piece_pattern import EMPTY_PIECE_PATTERN


class PiecePatternNode(object):
    __slots__ = ['_parrent', '_children', '_count',
                 '_pattern', '_piece_pattern']

    def __init__(self, piece_pattern, pattern=None):
        self._parrent = None
        self._children = None
        self._count = 0
        self._piece_pattern = piece_pattern
        self._pattern = get_pattern_from_cache(
            self.piece) if pattern is None else pattern

    def piece_eq_pattern(self):
        return True if self.piece == self._pattern.pattern_string else False

    def set_pattern(self, pattern):
        change = not (self._pattern == pattern)
        if change:
            self._pattern = pattern
        return change

    @property
    def base_pattern(self):
        return self._piece_pattern.pattern

    @property
    def pattern(self):
        return self._pattern

    @property
    def piece(self):
        return self._piece_pattern.piece

    @property
    def piece_pattern(self):
        return self._piece_pattern

    @property
    def count(self):
        return self._count

    def incr_count(self, count=1):
        self._count += count

    def add_child_node_from_piece_pattern(self, piece_pattern, count=1, pattern=None):
        if self._children is None:
            self._children = {}
        piece = piece_pattern.piece
        is_new = False
        if piece not in self._children:
            child = PiecePatternNode(piece_pattern, pattern)
            child.set_parrent(self)
            self._children[piece] = child
            is_new = True
        child = self._children[piece]
        child.incr_count(count)
        return child, is_new

    @property
    def children(self):
        return self._children

    def add_child_node_from_piece(self, piece_pattern_parser, piece, last_dot_split=False, count=1):
        piece_pattern = piece_pattern_parser.parse(piece, last_dot_split)
        return self.add_child_node_from_piece_pattern(piece_pattern, count)

    def __str__(self):
        return ' '.join((str(self._piece_pattern), self.pattern.pattern_string))

    __repr__ = __str__

    def set_parrent(self, parrent):
        self._parrent = parrent

    def _dump_paths(self, path_list):
        path_list.append(self)
        if not self._children:
            yield path_list
            return
        for piece in self._children:
            for path in self._children[piece]._dump_paths(path_list):
                yield path
            path_list.pop(-1)

    def dump_paths(self):
        path_list = []
        for path in self._dump_paths(path_list):
            yield path

    def _entropy(self, count):
        if not self._children:
            p = float(self._count) / count
            return 0 - p * math.log(p, 2)
        entropy = 0
        for node in self._children.values():
            entropy += node._entropy(count)
        return entropy

    def entropy(self, count=-1):
        if count > 0:
            if count < self._count:
                return None
            return self._entropy(count)
        if self._count <= 0:
            return None
        return self._entropy(self._count)

    @property
    def parrent(self):
        return self._parrent
