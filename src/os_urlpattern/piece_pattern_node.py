import math
from pattern import get_pattern_from_cache


class PiecePatternNode(object):
    __slots__ = ['_parrent', '_children', '_count',
                 '_pattern', '_piece_pattern', '_current_level']

    def __init__(self, piece_pattern, pattern=None):
        self._parrent = None
        self._children = None
        self._count = 0
        self._piece_pattern = piece_pattern
        self._pattern = get_pattern_from_cache(
            self.piece) if pattern is None else pattern
        self._current_level = 0

    @property
    def current_level(self):
        return self._current_level

    def use_piece_as_pattern(self):
        self._pattern = get_pattern_from_cache(self.piece)

    def piece_eq_pattern(self):
        return True if self.piece == self._pattern.pattern_string else False

    def set_pattern(self, pattern):
        change = not (self._pattern == pattern)
        if change:
            self._pattern = pattern
        return change

    @property
    def base_pattern(self):
        return self._piece_pattern.base_pattern

    @property
    def fuzzy_pattern(self):
        return self._piece_pattern.fuzzy_pattern

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
    def children(self):
        if not self._children:
            return None
        return self._children.values()

    @property
    def count(self):
        return self._count

    def incr_count(self, count, recur=False):
        self._count += count
        node = self.parrent if recur else None
        while node:
            node.incr_count(count)
            node = node.parrent

    def add_child_node_from_piece_pattern(self, piece_pattern, count, pattern=None):
        if self._children is None:
            self._children = {}
        piece = piece_pattern.piece
        is_new = False
        if piece not in self._children:
            child = PiecePatternNode(piece_pattern, pattern)
            child.set_parrent(self)
            child._current_level = self._current_level + 1
            self._children[piece] = child
            is_new = True
        child = self._children[piece]
        child.incr_count(count)
        return child, is_new

    def __str__(self):
        return ' '.join((str(self._piece_pattern), str(self.pattern)))

    def set_parrent(self, parrent):
        if not self._parrent:
            self._parrent = parrent

    def _dump_paths(self, path_list):
        path_list.append(self)
        if not self._children:
            yield path_list
            return
        for child in self.children:
            for path in child._dump_paths(path_list):
                yield path
            path_list.pop(-1)

    def dump_paths(self):
        path_list = []
        for path in self._dump_paths(path_list):
            yield path

    @property
    def parrent(self):
        return self._parrent
