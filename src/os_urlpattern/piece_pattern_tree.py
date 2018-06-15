from .parse_utils import EMPTY_PARSED_PIECE
from .pattern import Pattern
from .compat import itervalues


class PiecePatternNode(object):
    __slots__ = ('_parrent', '_children', '_count',
                 '_pattern', '_parsed_piece', '_extra_data')

    def __init__(self, parsed_piece, pattern=None):
        self._parrent = None
        self._children = None
        self._count = 0
        self._parsed_piece = parsed_piece
        self._pattern = Pattern(self.piece) if pattern is None else pattern
        self._extra_data = None

    def set_pattern(self, pattern):
        change = not (self._pattern == pattern)
        if change:
            self._pattern = pattern
        return change

    @property
    def pattern(self):
        return self._pattern

    def get_parrent(self, up_count=1):
        parrent = self.parrent
        while up_count > 1:
            parrent = parrent.parrent
            up_count -= 1

        return parrent

    @property
    def piece(self):
        return self._parsed_piece.piece

    @property
    def parsed_piece(self):
        return self._parsed_piece

    @property
    def children_num(self):
        return len(self._children)

    def iter_children(self):
        return itervalues(self._children)

    @property
    def count(self):
        return self._count

    def incr_count(self, count, recur=False):
        self._count += count
        node = self.parrent if recur else None
        while node:
            node.incr_count(count)
            node = node.parrent

    def add_child_node_from_parsed_piece(self, parsed_piece, count, pattern=None):
        if self._children is None:
            self._children = {}
        piece = parsed_piece.piece
        is_new = False
        if piece not in self._children:
            child = PiecePatternNode(parsed_piece, pattern)
            child.set_parrent(self)
            self._children[piece] = child
            is_new = True
        child = self._children[piece]
        child.incr_count(count)
        return child, is_new

    def __str__(self):
        return u' '.join((self.piece, str(self.pattern)))

    def set_parrent(self, parrent):
        if not self._parrent:
            self._parrent = parrent

    def _dump_paths(self, path_list):
        path_list.append(self)
        if not self._children:
            yield path_list
            return
        for child in self.iter_children():
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

    def add_extra_data(self, data):
        if data is None:
            return
        if self._extra_data is None:
            self._extra_data = set()
        self._extra_data.add(data)

    def update_extra_data(self, extra_data):
        if not extra_data:
            return
        if self._extra_data is None:
            self._extra_data = set()
        self._extra_data.update(extra_data)

    @property
    def extra_data(self):
        return self._extra_data


class PiecePatternTree(object):
    def __init__(self, url_meta):
        self._root = PiecePatternNode(EMPTY_PARSED_PIECE)
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

    def add_from_piece_pattern_node_path(self, piece_pattern_node_path):
        count = piece_pattern_node_path[-1].count
        node = self._root
        node.incr_count(count)
        is_new = None
        for p_node in piece_pattern_node_path:
            node, is_new = node.add_child_node_from_parsed_piece(
                p_node.parsed_piece, count, p_node.pattern)
        node.update_extra_data(piece_pattern_node_path[-1].extra_data)
        return is_new

    def add_from_parsed_pieces(self, parsed_pieces, count=1, uniq=True, data=None):
        node = self._root
        node.incr_count(count)
        is_new = None
        for parsed_piece in parsed_pieces:
            node, is_new = node.add_child_node_from_parsed_piece(
                parsed_piece, count)
        if uniq and not is_new:
            node.incr_count(0 - count, True)
        node.add_extra_data(data)
        return is_new

    def dump_paths(self):
        for path in self._root.dump_paths():
            yield path
