from collections import OrderedDict
from functools import total_ordering

from .compat import itervalues
from .definition import BasePatternRule
from .parse_utils import (MIXED_RULE_SET, PieceParser, digest,
                          parse_pattern_path_string, parse_url)
from .parsed_piece_view import (BaseView, FuzzyView, LastDotSplitFuzzyView,
                                LengthView, MixedView, PieceView, fuzzy_view,
                                view_cls_from_pattern)
from .pattern import Pattern
from .utils import TreeNode, build_tree


@total_ordering
class MatchPattern(Pattern):
    def __init__(self, pattern_string, is_last_path=False):
        super(MatchPattern, self).__init__(pattern_string)
        self._view_cls = view_cls_from_pattern(self, is_last_path)
        self._cmp_key = None

    @property
    def cmp_key(self):
        if self._cmp_key is None:
            l = [MatchPattern(u.pattern_unit_string)
                 for u in self.pattern_units[::-1]]
            self._cmp_key = u''.join([str(VIEW_ORDER[p.view_cls]) for p in l])
        return self._cmp_key

    @property
    def view_cls(self):
        return self._view_cls

    def __ne__(self, other):
        return self._pattern_string != other.pattern_string

    def __lt__(self, other):
        if self.view_cls == other.view_cls:
            return self.cmp_key > other.cmp_key
        return VIEW_ORDER[self.view_cls] > VIEW_ORDER[other.view_cls]


EMPTY_MATCH_PATTERN = MatchPattern(BasePatternRule.EMPTY)


class _ViewMatcher(object):
    def __init__(self, view_cls):
        self._view_cls = view_cls
        self._matchers = {}

    def empty(self):
        return len(self._matchers) == 0

    def preprocess(self):
        pass

    @property
    def view_cls(self):
        return self._view_cls

    def add_match_node(self, match_node):
        pass

    def match(self, parsed_piece):
        pass


class ViewMatcher(_ViewMatcher):

    def preprocess(self):
        for matcher in itervalues(self._matchers):
            matcher.preprocess()

    def add_match_node(self, match_node):
        pattern = match_node.pattern
        r = fuzzy_view([u.fuzzy_rule for u in pattern.pattern_units])
        if r not in self._matchers:
            self._matchers[r] = PatternMatchNode(EMPTY_MATCH_PATTERN)
        patterns = [MatchPattern(p.pattern_unit_string)
                    for p in pattern.pattern_units]
        matcher = self._matchers[r]
        build_tree(matcher, patterns, meta=match_node)

    def match(self, parsed_piece):
        view = self._view_cls(parsed_piece)
        if view.view not in self._matchers:
            return []
        parsed_pieces = view.parsed_pieces
        matched_result = []
        self._matchers[view.view].match(
            parsed_pieces, 0, matched_result)
        return [n.meta for n in matched_result]


class PiecePatternViewMatcher(_ViewMatcher):

    def add_match_node(self, match_node):
        if match_node.pattern.pattern_string not in self._matchers:
            self._matchers[match_node.pattern.pattern_string] = [match_node]

    def match(self, parsed_piece):
        return [] if parsed_piece.piece not in self._matchers \
            else self._matchers[parsed_piece.piece]


class LengthPatternViewMatcher(_ViewMatcher):

    def add_match_node(self, match_node):
        length = match_node.pattern.pattern_units[0].num
        self._matchers[length] = [match_node]

    def match(self, parsed_piece):
        return [] if parsed_piece.piece_length not in self._matchers \
            else self._matchers[parsed_piece.piece_length]


class MixedPatternViewMatcher(ViewMatcher):

    def _pattern(self, pattern_units):
        return MatchPattern(u''.join([p.pattern_unit_string for p in pattern_units]))

    def add_match_node(self, match_node):
        patterns = []
        t = []
        for pattern_unit in match_node.pattern.pattern_units:
            if not pattern_unit.is_literal() \
                    or pattern_unit.fuzzy_rule not in MIXED_RULE_SET:
                if t:
                    patterns.append(self._pattern(t))
                    t = []
                patterns.append(self._pattern([pattern_unit]))
            else:
                t.append(pattern_unit)

        if t:
            patterns.append(self._pattern(t))

        r = fuzzy_view([u.fuzzy_rule for u in patterns])
        if r not in self._matchers:
            self._matchers[r] = PatternMatchNode(EMPTY_MATCH_PATTERN)
        matcher = self._matchers[r]
        build_tree(matcher, patterns, meta=match_node)


class FuzzyPatternViewMatcher(_ViewMatcher):

    def __init__(self, view_cls):
        super(FuzzyPatternViewMatcher, self).__init__(view_cls)
        self._matchers = []

    def add_match_node(self, match_node):
        self._matchers.append(match_node)

    def match(self, parsed_piece):
        return self._matchers


VIEW_MATCHERS = [
    (PieceView, PiecePatternViewMatcher),
    (BaseView, ViewMatcher),
    (MixedView, ViewMatcher),
    (LastDotSplitFuzzyView, ViewMatcher),
    (LengthView, LengthPatternViewMatcher),
    (FuzzyView, FuzzyPatternViewMatcher),
]

VIEW_ORDER = dict([(item[0], idx) for idx, item in enumerate(VIEW_MATCHERS)])


@total_ordering
class PatternMatchNode(TreeNode):

    def __init__(self, value):
        super(PatternMatchNode, self).__init__(value)
        self._view_matchers = OrderedDict([(view_cls, matcher_cls(view_cls))
                                           for view_cls, matcher_cls in VIEW_MATCHERS])

    @property
    def view_cls(self):
        return self.pattern.view_cls

    def preprocess(self):
        if not self._children:
            self._view_matchers = {}
            return

        for view_cls, _ in VIEW_MATCHERS:
            matcher = self._view_matchers[view_cls]
            if matcher.empty():
                self._view_matchers.pop(view_cls)
            else:
                matcher.preprocess()

        for child in self.children:
            child.preprocess()

    def match(self, parsed_pieces, idx, matched_nodes):
        parsed_piece = parsed_pieces[idx]
        for matcher in itervalues(self._view_matchers):
            nodes = matcher.match(parsed_piece)
            self._deep_match(nodes, parsed_pieces, idx,
                             matched_nodes)

    def _deep_match(self, nodes, parsed_pieces, idx, matched_nodes):
        for node in nodes:
            if node.leaf():
                matched_nodes.append(node)
            else:
                node.match(parsed_pieces, idx + 1, matched_nodes)

    @property
    def pattern(self):
        return self._value

    def add_child(self, pattern):
        if self._children is None:
            self._children = {}
        is_new = False
        if pattern not in self._children:
            is_new = True
            child = PatternMatchNode(pattern)
            child.parrent = self
            self._children[pattern] = child
            self._view_matchers[child.view_cls].add_match_node(child)

        return self._children[pattern], is_new

    def __lt__(self, other):
        if id(self) == id(other) or self.parrent is None:
            return False
        if self.pattern == other.pattern:
            return self.parrent < other.parrent
        return self.pattern < other.pattern


class PatternMatcher(object):

    def __init__(self):
        self._parser = PieceParser()
        self._roots = {}

    def load(self, pattern_path_string, meta=None):
        url_meta, pattern_strings = parse_pattern_path_string(
            pattern_path_string)
        patterns = [MatchPattern(p, i + 1 == url_meta.path_depth)
                    for i, p in enumerate(pattern_strings)]
        sid = digest(url_meta, [p.fuzzy_rule for p in patterns])
        if sid not in self._roots:
            self._roots[sid] = PatternMatchNode(EMPTY_MATCH_PATTERN)
        root = self._roots[sid]
        build_tree(root, patterns,
                   meta=pattern_path_string if meta is None else meta)

    def preprocess(self):
        for root in itervalues(self._roots):
            root.preprocess()

    def match(self, url):
        url_meta, pieces = parse_url(url)
        parsed_pieces = [self._parser.parse(piece) for piece in pieces]
        sid = digest(url_meta, [p.fuzzy_rule for p in parsed_pieces])
        matched_nodes = []
        if sid in self._roots:
            self._roots[sid].match(parsed_pieces, 0, matched_nodes)
        return matched_nodes
