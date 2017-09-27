import hashlib
import json
from os_urlpattern.urlparse_utils import split, join


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
            parts = split(self._url_meta, [
                p.pattern for p in self._pattern_node_path[1:]])
            self._pattern_path_string = join(self._url_meta, *parts)
        return self._pattern_path_string


class PatternNode(object):
    def __init__(self, pattern):  # , base_pattern):
        self._pattern = pattern
        self._children = {}
        self._parrent = None
        self._count = 0

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
            child = PatternNode(pattern)  # , part_pattern.base_pattern)
            child.set_parrent(self)
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


from os_urlpattern.definition import BasePattern


class PatternTree(object):
    def __init__(self, url_meta):
        self._url_meta = url_meta
        self._root = PatternNode(BasePattern.EMPTY)

    @property
    def root_node(self):
        return self._root

    def load_path(self, piece_pattern_node_path):
        node = self._root
        count = piece_pattern_node_path[-1].count
        node.incr_count(count)
        for piece_pattern_node in piece_pattern_node_path:
            node = node.add_child(piece_pattern_node.pattern, count)

    def dumps(self):
        for patten_node_path in self._root.dump_paths():
            yield PatternPath(patten_node_path, self._url_meta)
