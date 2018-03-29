import copy
from collections import Counter

from .cluster_node import (BaseView, ClusterNode, FuzzyView,
                           LastDotSplitFuzzyView, LengthView, MixedView,
                           PieceView)
from .compat import iteritems, itervalues
from .definition import DIGIT_AND_ASCII_RULE_SET, BasePatternRule
from .parse_utils import URLMeta, number_rule, wildcard_rule
from .pattern import Pattern
from .piece_pattern_tree import PiecePatternTree


def is_digital(pack):
    nv = pack.pick_node_view()
    rules = nv.parsed_piece.rules
    if len(rules) == 1 and BasePatternRule.DIGIT in rules:
        return True
    return False


class ClusterNodeViewBag(object):
    def __init__(self):
        self._node_views = []
        self._count = 0

    def add_node_view(self, node_view):
        self._node_views.append(node_view)
        self._count += node_view.count

    @property
    def count(self):
        return self._count

    def __iter__(self):
        return iter(self._node_views)

    def set_pattern(self, pattern, cluster_name):
        for node_view in self._node_views:
            node_view.set_pattern(pattern, cluster_name)

    def pick_node_view(self):
        return self._node_views[0]

    def __len__(self):
        return len(self._node_views)


class ClusterNodeViewPack(object):
    def __init__(self):
        self._packs = {}
        self._count = 0

    def get_cluster_bag(self, cluster_name):
        return self._packs.get(cluster_name, None)

    def add_node_view(self, node_view):
        c_name = node_view.cluster_name
        if c_name not in self._packs:
            self._packs[c_name] = ClusterNodeViewBag()
        self._packs[c_name].add_node_view(node_view)
        self._count += node_view.count

    def iter_node_views(self):
        for view_bag in itervalues(self._packs):
            for node_view in view_bag:
                yield node_view

    def iter_items(self):
        return iteritems(self._packs)

    def iter_values(self):
        return itervalues(self._packs)

    @property
    def count(self):
        return self._count

    def set_pattern(self, pattern, cluster_name):
        for bag in itervalues(self._packs):
            bag.set_pattern(pattern, cluster_name)

    def pick_node_view(self):
        for node_view in self.iter_node_views():
            return node_view

    def __len__(self):
        return len(self._packs)


class ViewPack(object):
    def __init__(self, view_class):
        self._view_class = view_class
        self._packs = {}
        self._count = 0

    def pick_node_view(self):
        for node_view in self.iter_node_views():
            return node_view

    def add_cluster_node(self, cluster_node):
        node_view = self._view_class(cluster_node)
        v = node_view.view()
        if v not in self._packs:
            self._packs[v] = ClusterNodeViewPack()
        self._packs[v].add_node_view(node_view)
        self._count += node_view.count

    def iter_node_views(self):
        for view_pack in itervalues(self._packs):
            for node_view in view_pack.iter_node_views():
                yield node_view

    def iter_values(self):
        return itervalues(self._packs)

    def iter_items(self):
        return iteritems(self._packs)

    @property
    def count(self):
        return self._count

    def set_pattern(self, pattern, cluster_name):
        for pack in itervalues(self._packs):
            pack.set_pattern(pattern, cluster_name)

    def __len__(self):
        return len(self._packs)


class PatternCluster(object):
    def __init__(self, config, meta_info):
        self._config = config
        self._meta_info = meta_info
        self._min_cluster_num = config.getint('make', 'min_cluster_num')
        self._cluster_name = self.__class__.__name__
        self._view_pack = None

    @property
    def view_pack(self):
        return self._view_pack

    def add_cluster_node(self, cluster_node):
        self._view_pack.add_cluster_node(cluster_node)

    def iter_cluster_nodes(self):
        for node_view in self._view_pack.iter_node_views():
            yield node_view.cluster_node

    def _cluster(self):
        pass

    def _forward_cluster(self):
        yield

    def cluster(self):
        self._cluster()
        for c in self._forward_cluster():
            yield c

    def _set_pattern(self, obj, pattern):
        obj.set_pattern(pattern, self._cluster_name)

    def _create_cluster(self, cluster_cls):
        c = cluster_cls(self._config, self._meta_info)
        for cluster_node in self.iter_cluster_nodes():
            c.add_cluster_node(cluster_node)
        return c


class PiecePatternCluster(PatternCluster):
    def __init__(self, config, meta_info):
        super(PiecePatternCluster, self).__init__(config, meta_info)
        self._view_pack = ViewPack(PieceView)
        self._wildcard_digital_pattern = self._config.getboolean(
            'make', 'wildcard_digital_pattern')

    def _cluster(self):
        for piece, pack in self.view_pack.iter_items():
            if pack.count >= self._min_cluster_num:
                self._set_pattern(pack, Pattern(piece))

    def _forward_cluster(self):
        l_view_pack = len(self.view_pack)
        if l_view_pack <= 1:
            return
        elif l_view_pack < self._min_cluster_num:
            if self._wildcard_digital_pattern and is_digital(self.view_pack):
                pass
            else:
                return

        forward_cluster_cls = LengthPatternCluster
        node_view = self.view_pack.pick_node_view()
        if len(node_view.view_parsed_pieces()) > 1:
            forward_cluster_cls = BasePatternCluster
        yield self._create_cluster(forward_cluster_cls)


class LengthPatternCluster(PatternCluster):
    def __init__(self, config, meta_info):
        super(LengthPatternCluster, self).__init__(config, meta_info)
        self._view_pack = ViewPack(LengthView)
        self._wildcard_digital_pattern = self._config.getboolean(
            'make', 'wildcard_digital_pattern')

    def _cluster_digital_pattern(self):
        count = 0
        if len(self.view_pack) >= self._min_cluster_num:
            count = len(self.view_pack)
        for length, pack in self.view_pack.iter_items():
            if count > 1:
                break
            p_set = set([node.pattern for node in pack.iter_node_views()])
            if len(p_set) > 1:
                self._set_pattern(pack, Pattern(
                    number_rule(BasePatternRule.DIGIT, length)))
                count += 1
        if count > 1:
            self._set_pattern(self.view_pack, Pattern(
                wildcard_rule(BasePatternRule.DIGIT)))

    def _cluster_length_pattern(self):
        node_view = self._view_pack.pick_node_view()
        for length, pack in self._view_pack.iter_items():
            pattern = Pattern(number_rule(
                node_view.parsed_piece.fuzzy_rule, length))

            for bag in pack.iter_values():
                p_set = set([node.pattern for node in bag])
                if len(p_set) >= self._min_cluster_num:
                    self._set_pattern(pack, pattern)
                    break

    def _cluster(self):
        if self._wildcard_digital_pattern and is_digital(self.view_pack):
            self._cluster_digital_pattern()
        else:
            self._cluster_length_pattern()

    def _forward_cluster(self):
        if self._wildcard_digital_pattern and is_digital(self.view_pack):
            return
        if len(self.view_pack) < self._min_cluster_num:
            return
        yield self._create_cluster(FuzzyPatternCluster)


class MultiPartPatternCluster(PatternCluster):

    def _cluster(self):
        for pack in self._view_pack.iter_values():
            self._deep_cluster(pack)

    def _deep_cluster(self, pack):

        piece_pattern_tree = PiecePatternTree()
        for node_view in pack.iter_node_views():
            piece_pattern_tree.add_from_parsed_pieces(
                node_view.view_parsed_pieces(), count=node_view.count, uniq=False)

        p_num = len(pack.pick_node_view().view_parsed_pieces())
        url_meta = URLMeta(p_num, [], False)
        cluster(self._config, url_meta, piece_pattern_tree)

        piece_pattern_dict = {}
        pattern_counter = Counter()
        for path in piece_pattern_tree.dump_paths():
            pattern = Pattern(''.join([str(node.pattern) for node in path]))
            piece = ''.join([str(node.piece) for node in path])
            if piece == pattern.pattern_string:
                continue
            piece_pattern_dict[piece] = pattern
            pattern_counter[pattern] += path[-1].count

        for node_view in pack.iter_node_views():
            if node_view.piece in piece_pattern_dict:
                pattern = piece_pattern_dict[node_view.piece]
                if pattern_counter[pattern] >= self._min_cluster_num:
                    self._set_pattern(node_view, pattern)


class BasePatternCluster(MultiPartPatternCluster):
    def __init__(self, config, meta_info):
        super(BasePatternCluster, self).__init__(config, meta_info)
        self._view_pack = ViewPack(BaseView)

    def _to_be_filtered(self, pattern):
        n = p = 0
        for pu in pattern.pattern_units:
            inter = pu.rules.intersection(DIGIT_AND_ASCII_RULE_SET)
            if inter:
                if not str(pu).startswith('['):
                    p += 1
                else:
                    if pu.num > 0:
                        p += 1
                    else:
                        n += 1
        if p >= n and n < self._min_cluster_num:
            return True

        return False

    def _forward_cluster(self):

        forward_clusters = [c(self._config, self._meta_info) for c in
                            (LengthPatternCluster,
                             MixedPatternCluster,
                             LastDotSplitFuzzyPatternCluster)]

        filtered_patterns = set()
        for view, pack in self.view_pack.iter_items():
            c = forward_clusters[0]
            nv = MixedView(pack.pick_node_view().cluster_node)
            if view == nv.view():
                if self._meta_info.is_last_path():
                    nv = LastDotSplitFuzzyView(
                        pack.pick_node_view().cluster_node)
                    if len(nv.view_parsed_pieces()) > 1:
                        c = forward_clusters[2]
            else:
                if len(nv.view_parsed_pieces()) > 1:
                    c = forward_clusters[1]

            for node_view in pack.iter_node_views():
                pattern = node_view.pattern
                if pattern in filtered_patterns:
                    continue
                if node_view.cluster_name != '' \
                        and node_view.cluster_name != PiecePatternCluster.__name__:
                    if self._to_be_filtered(pattern):
                        filtered_patterns.add(pattern)
                        continue
                c.add_cluster_node(node_view.cluster_node)

        for c in forward_clusters:
            if len(c.view_pack) > 0:
                yield c


class MixedPatternCluster(BasePatternCluster):
    def __init__(self, config, meta_info):
        super(MixedPatternCluster, self).__init__(config, meta_info)
        self._view_pack = ViewPack(MixedView)

    def _forward_cluster(self):
        forward_clusters = [c(self._config, self._meta_info) for c in
                            (LengthPatternCluster,
                             LastDotSplitFuzzyPatternCluster)]

        filtered_patterns = set()
        for view, pack in self.view_pack.iter_items():
            c = forward_clusters[0]
            if self._meta_info.is_last_path():
                nv = LastDotSplitFuzzyView(pack.pick_node_view().cluster_node)
                if view == nv.view():
                    continue
                else:
                    if len(nv.view_parsed_pieces()) > 1:  # not exactly
                        c = forward_clusters[1]
            for node_view in pack.iter_node_views():
                pattern = node_view.pattern
                if pattern in filtered_patterns:
                    continue
                if node_view.cluster_name != '' \
                        and node_view.cluster_name != PiecePatternCluster.__name__:
                    if self._to_be_filtered(pattern):
                        filtered_patterns.add(pattern)
                        continue
                c.add_cluster_node(node_view.cluster_node)

        for c in forward_clusters:
            if len(c.view_pack) > 0:
                yield c


class LastDotSplitFuzzyPatternCluster(MultiPartPatternCluster):
    def __init__(self, config, meta_info):
        super(LastDotSplitFuzzyPatternCluster,
              self).__init__(config, meta_info)
        self._view_pack = ViewPack(LastDotSplitFuzzyView)


class FuzzyPatternCluster(PatternCluster):
    def __init__(self, config, meta_info):
        super(FuzzyPatternCluster, self).__init__(config, meta_info)
        self._view_pack = ViewPack(FuzzyView)

    def cluster(self):

        clusterd = False
        un_clusterd_bags = []
        for fuzzy_rule, pack in self.view_pack.iter_items():

            for c_name, bag in pack.iter_items():
                p_set = set([node.pattern for node in bag])
                if len(p_set) >= self._min_cluster_num:
                    clusterd = True
                    self._set_pattern(bag, Pattern(wildcard_rule(fuzzy_rule)))
                else:
                    if c_name == '' or c_name == LengthPatternCluster.__name__:
                        un_clusterd_bags.append((fuzzy_rule, bag))
        if clusterd:
            for fuzzy_rule, bag in un_clusterd_bags:
                self._set_pattern(bag, Pattern(wildcard_rule(fuzzy_rule)))
        yield


class MetaInfo(object):
    def __init__(self, url_meta, current_level):
        self._url_meta = url_meta
        self._current_level = current_level

    @property
    def current_level(self):
        return self._current_level

    @property
    def url_meta(self):
        return self._url_meta

    def is_last_level(self):
        return self.url_meta.depth == self._current_level

    def is_last_path(self):
        return self.url_meta.path_depth == self._current_level

    def next_level_meta_info(self):
        return MetaInfo(self.url_meta, self.current_level + 1)


class ClusterProcessor(object):
    def __init__(self, config, meta_info):
        self._config = config
        self._meta_info = meta_info
        self._entry_cluster = PiecePatternCluster(config, meta_info)

    def iter_nodes(self):
        for cluster_node in self._entry_cluster.iter_cluster_nodes():
            yield cluster_node.node

    def add_node(self, node):
        self._entry_cluster.add_cluster_node(ClusterNode(node))

    def _process(self, cluster):
        if cluster is not None:
            for c in cluster.cluster():
                self._process(c)

    def _preprocess(self):
        pass

    def process(self):
        self._process(self._entry_cluster)
        if self._meta_info.is_last_level():
            return
        next_level_processors = {}
        next_level_meta_info = self._meta_info.next_level_meta_info()
        for node in self.iter_nodes():
            pattern = node.pattern
            if pattern not in next_level_processors:
                next_level_processors[pattern] = ClusterProcessor(
                    self._config, next_level_meta_info)
            next_processor = next_level_processors[pattern]
            for child in node.children:
                next_processor.add_node(child)
        for processor in itervalues(next_level_processors):
            processor.process()


def cluster(config, url_meta, piece_pattern_tree, **kwargs):
    min_cluster_num = config.getint('make', 'min_cluster_num')
    if piece_pattern_tree.count < min_cluster_num:
        return
    meta_info = MetaInfo(url_meta, 0)
    processor = ClusterProcessor(config, meta_info)
    processor.add_node(piece_pattern_tree.root)
    processor.process()
