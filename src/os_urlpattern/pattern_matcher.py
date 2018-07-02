"""Pattern matching APIs.
"""
from __future__ import unicode_literals

from functools import total_ordering

from .definition import BasePatternRule
from .parse_utils import MIXED_RULE_SET, PieceParser, fuzzy_join
from .parsed_piece_view import (FuzzyView, LastDotSplitFuzzyView, LengthView,
                                MixedView, MultiView, PieceView,
                                view_cls_from_pattern)
from .parser import fuzzy_digest, parse
from .pattern import Pattern
from .utils import TreeNode, build_tree


@total_ordering
class MatchPattern(Pattern):
    """Pattern used for matching.

    It is comparable and has a view_cls property to
    identify the pattern type.
    """
    __slots__ = ('_view_cls', '_cmp_key')

    def __init__(self, pattern_string, is_last_path=False):
        super(MatchPattern, self).__init__(pattern_string)
        self._view_cls = view_cls_from_pattern(self, is_last_path)
        self._cmp_key = None

    @property
    def cmp_key(self):
        """str: Used for sort."""

        if self._cmp_key is None:
            l = [MatchPattern(u.pattern_unit_string)
                 for u in reversed(self.pattern_units)]
            self._cmp_key = ''.join([str(VIEW_ORDER[p.view_cls]) for p in l])
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


class ViewMatcher(object):
    """Base class for different type of view matcher.

    Init with a specified ParsedPieceView class.
    Filled with same view-type match node.
    Get all matched nodes.    
    """
    __slots__ = ('_view_cls', '_matchers')

    def __init__(self, view_cls):
        self._view_cls = view_cls
        self._matchers = {}

    @property
    def view_cls(self):
        return self._view_cls

    def add_match_node(self, match_node):
        pass

    def match(self, parsed_piece):
        view = self._view_cls(parsed_piece)
        if view.view not in self._matchers:
            return []
        parsed_pieces = view.parsed_pieces
        matched_result = []
        self._matchers[view.view].match(
            parsed_pieces, 0, matched_result)
        return [n.meta for n in matched_result]


class PiecePatternViewMatcher(ViewMatcher):

    def add_match_node(self, match_node):
        if match_node.pattern.pattern_string not in self._matchers:
            self._matchers[match_node.pattern.pattern_string] = [match_node]

    def match(self, parsed_piece):
        return [] if parsed_piece.piece not in self._matchers \
            else self._matchers[parsed_piece.piece]


class LengthPatternViewMatcher(ViewMatcher):

    def add_match_node(self, match_node):
        length = match_node.pattern.pattern_units[0].num
        self._matchers[length] = [match_node]

    def match(self, parsed_piece):
        return [] if parsed_piece.piece_length not in self._matchers \
            else self._matchers[parsed_piece.piece_length]


class MultiPatternViewMatcher(ViewMatcher):

    def add_match_node(self, match_node):
        pattern = match_node.pattern
        r = fuzzy_join(pattern.pattern_units)
        if r not in self._matchers:
            self._matchers[r] = PatternMatchNode(EMPTY_MATCH_PATTERN)
        patterns = [MatchPattern(p.pattern_unit_string)
                    for p in pattern.pattern_units]
        matcher = self._matchers[r]
        build_tree(matcher, patterns, meta=match_node)


class MixedPatternViewMatcher(MultiPatternViewMatcher):

    def _pattern(self, pattern_units):
        return MatchPattern(''.join([p.pattern_unit_string for p in pattern_units]))

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

        r = fuzzy_join(patterns)
        if r not in self._matchers:
            self._matchers[r] = PatternMatchNode(EMPTY_MATCH_PATTERN)
        matcher = self._matchers[r]
        build_tree(matcher, patterns, meta=match_node)


class FuzzyPatternViewMatcher(ViewMatcher):

    def __init__(self, view_cls):
        super(FuzzyPatternViewMatcher, self).__init__(view_cls)
        self._matchers = []

    def add_match_node(self, match_node):
        self._matchers.append(match_node)

    def match(self, parsed_piece):
        return self._matchers


VIEW_MATCHERS = [
    (PieceView, PiecePatternViewMatcher),
    (MultiView, MultiPatternViewMatcher),
    (MixedView, MultiPatternViewMatcher),
    (LastDotSplitFuzzyView, MultiPatternViewMatcher),
    (LengthView, LengthPatternViewMatcher),
    (FuzzyView, FuzzyPatternViewMatcher),
]

VIEW_ORDER = dict([(item[0], _idx) for _idx, item in enumerate(VIEW_MATCHERS)])


def get_view_matcher_cls(view_cls):
    """Get specified ViewMatcher class from ParsedPieceView class.

    Args:
        view_cls (ParsedPieceView): Class of a specified ParsedPieceView.

    Returns:
        class(ViewMatcher): The Corresponding ViewMatcher class.
    """
    idx = VIEW_ORDER[view_cls]
    return VIEW_MATCHERS[idx][1]


@total_ordering
class PatternMatchNode(TreeNode):
    """Node for building a match tree."""

    __slots__ = ('_view_matchers',)

    def __init__(self, value):
        super(PatternMatchNode, self).__init__(value)
        self._view_matchers = []

    @property
    def view_cls(self):
        return self.pattern.view_cls

    def match(self, parsed_pieces, idx, matched_nodes):
        """DF find all matched nodes.

        If a path from root to leaf match all the corresponding pieces,
        the leaf node is called matched node.This mathed shoud be called
        by the root node, with idx=0 and a list which will be filled with
        all matched nodes.

        Args:
            parsed_pieces (sequence): All of the parsed pieces to be matched.
            idx (int): Indecate which piece of the whole parsed pieces should
                try to match this node.
            matched_nodes (list of PatternMatchNode): Filled with all of the
                matched leaf nodes.
        """
        parsed_piece = parsed_pieces[idx]
        for matcher in self._view_matchers:
            nodes = matcher.match(parsed_piece)
            if not nodes:
                continue
            if nodes[0].leaf():
                matched_nodes.extend(nodes)
                continue
            self._deep_match(nodes, parsed_pieces, idx,
                             matched_nodes)

    def _deep_match(self, nodes, parsed_pieces, idx, matched_nodes):
        idx_next = idx + 1
        for node in nodes:
            node.match(parsed_pieces, idx_next, matched_nodes)

    def _get_matcher(self, view_cls):
        s = 0
        e = len(self._view_matchers)
        while e > s:
            t = (e - s) // 2 + s
            matcher = self._view_matchers[t]
            if matcher.view_cls == view_cls:
                return matcher
            tid = VIEW_ORDER[matcher.view_cls]
            vid = VIEW_ORDER[view_cls]
            if tid < vid:
                s = t + 1
            else:
                e = t

        matcher = get_view_matcher_cls(view_cls)(view_cls)
        self._view_matchers.insert(e, matcher)
        return matcher

    @property
    def pattern(self):
        return self._value

    def add_child(self, pattern):
        child, is_new = super(PatternMatchNode, self).add_child(
            (pattern, pattern))
        if is_new:
            matcher = self._get_matcher(child.view_cls)
            matcher.add_match_node(child)
        return child, is_new

    def __lt__(self, other):
        if id(self) == id(other) or self.parrent is None:
            return False
        if self.pattern == other.pattern:
            return self.parrent < other.parrent
        return self.pattern < other.pattern


class PatternMatcher(object):
    """Offer match processing APIs.

    Common procedure:
    1. Init a PatternMatcher.
    2. Load pattern string.
    3. Match url.
    """

    def __init__(self):
        self._parser = PieceParser()
        self._roots = {}

    def load(self, url_pattern_string, meta=None):
        """Load URL pattern string.

        Args:
            url_pattern_string (str): URL pattern string.
            meta (any, optional): Defaults to None. It will bind to
                matched result's meta property.
        """
        url_meta, patterns = parse(url_pattern_string)
        if not isinstance(patterns[0], MatchPattern):
            raise ValueError('Invalid URL pattern')
        sid = fuzzy_digest(url_meta, patterns)
        if sid not in self._roots:
            self._roots[sid] = PatternMatchNode(EMPTY_MATCH_PATTERN)
        root = self._roots[sid]
        build_tree(root, patterns,
                   meta=url_pattern_string if meta is None else meta)

    def match(self, url):
        """Match url, get the matched results.

        Args:
            url (str): The URL to be matched.

        Returns:
            list: List of matched pattern nodes, if no match return [].
              Bound meta data can be accessed with node.meta.
        """
        url_meta, parsed_pieces = parse(url)
        sid = fuzzy_digest(url_meta, parsed_pieces)
        matched_nodes = []
        if sid in self._roots:
            self._roots[sid].match(parsed_pieces, 0, matched_nodes)
        return matched_nodes
