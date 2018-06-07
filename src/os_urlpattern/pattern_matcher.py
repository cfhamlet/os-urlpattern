from .definition import BasePattern
from .parse_utils import (PieceParser, digest, parse_pattern_path_string,
                          parse_url)
from .pattern import Pattern
from .pattern_tree import PatternTree


class PatternMatchNode(object):
    def __init__(self, pattern, info=None):
        self._pattern = pattern
        self._info = info
        self._children = {}
        self._parrent = None

    @property
    def pattern(self):
        return self._pattern

    @property
    def info(self):
        return self._info

    @info.setter
    def info(self, info):
        self._info = info

    @property
    def parrent(self):
        return self._parrent

    @parrent.setter
    def parrent(self, parrent):
        self._parrent = parrent

    def add_child(self, pattern, info=None):
        if pattern not in self._children:
            child = PatternMatchNode(pattern, info)
            child.parrent = self
            self._children[pattern] = child

        return self._children[pattern]


class PatternMathchTree(object):
    def __init__(self):
        self._root = PatternMatchNode(BasePattern.EMPTY)

    def load_from_patterns(self, patterns, info):
        node = self._root
        for pattern in patterns:
            node = node.add_child(pattern)

        node.info = info

    def match(self, parsed_pieces):
        pass


class PatternMatcher(object):
    def __init__(self):
        self._parser = PieceParser()
        self._pattern_trees = {}

    def load(self, pattern_info):
        pattern_path_string = pattern_info['pat']
        meta, pattern_strings = parse_pattern_path_string(pattern_path_string)
        patterns = [Pattern(p) for p in pattern_strings]
        sid = digest(meta, [p.fuzzy_rule for p in patterns])
        if sid not in self._pattern_trees:
            self._pattern_trees[sid] = PatternMathchTree()
        pattern_tree = self._pattern_trees[sid]
        pattern_tree.load_from_patterns(patterns, pattern_info)

    def match(self, url):
        url_meta, pieces = parse_url(url)
        parsed_pieces = [self._parser.parse(piece) for piece in pieces]
        sid = digest(url_meta, [p.fuzzy_rule for p in parsed_pieces])
        if sid not in self._pattern_trees:
            return None
        pattern_tree = self._pattern_trees[sid]
        return pattern_tree.match(parsed_pieces)
