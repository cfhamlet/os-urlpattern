import hashlib
import json

from .definition import BasePattern
from .parse_utils import pack


class PatternPath(object):
    def __init__(self, pattern_node_path, url_meta):
        self._pattern_node_path = pattern_node_path
        self._url_meta = url_meta
        self._pattern_path_string = None

    @property
    def count(self):
        return self._pattern_node_path[-1].count

    @property
    def pattern_id(self):
        return hashlib.md5(self.pattern_path_string).hexdigest()

    @property
    def pattern_path_string(self):
        if self._pattern_path_string is None:
            self._pattern_path_string = pack(
                self._url_meta, [p.pattern for p in self._pattern_node_path[1:]])
        return self._pattern_path_string


class PatternNode(object):
    __slots__ = ['_pattern', '_children',
                 '_parrent', '_count', '_current_level']

    def __init__(self, pattern):  # , base_pattern):
        self._pattern = pattern
        self._children = {}
        self._parrent = None
        self._count = 0
        self._current_level = 0

    @property
    def current_level(self):
        return self._current_level

    @property
    def pattern(self):
        return self._pattern

    @property
    def count(self):
        return self._count

    def __str__(self):
        return str(self._pattern)

    def incr_count(self, count):
        self._count += count

    def set_parrent(self, parrent):
        self._parrent = parrent

    @property
    def children(self):
        return self._children.values()

    def add_child(self, pattern, count):
        if pattern not in self._children:
            child = PatternNode(pattern)
            child.set_parrent(self)
            child._current_level = self._current_level + 1
            self._children[pattern] = child

        self._children[pattern].incr_count(count)
        return self._children[pattern]

    def _dump_paths(self, p_list):
        p_list.append(self)
        if not self._children:
            yield p_list
            return
        for pattern in self._children:
            for path in self._children[pattern]._dump_paths(p_list):
                yield path
            p_list.pop(-1)

    def dump_paths(self):
        p_list = []
        for path in self._dump_paths(p_list):
            yield path




class PatternTree(object):
    def __init__(self, url_meta):
        self._url_meta = url_meta
        self._root = PatternNode(BasePattern.EMPTY)

    @property
    def url_meta(self):
        return self._url_meta

    @property
    def root(self):
        return self._root

    def load_path(self, pattern_node_path):
        node = self._root
        count = pattern_node_path[-1].count
        node.incr_count(count)
        for piece_pattern_node in pattern_node_path:
            node = node.add_child(piece_pattern_node.pattern, count)

    def dumps(self):
        for patten_node_path in self._root.dump_paths():
            yield PatternPath(patten_node_path, self._url_meta)
