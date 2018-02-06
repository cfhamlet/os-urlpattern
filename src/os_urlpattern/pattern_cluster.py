import copy
from collections import Counter
from pattern import Pattern
from urlparse_utils import number_rule, wildcard_rule, URLMeta
from piece_pattern_tree import PiecePatternTree
from definition import BasePatternRule
from cluster_node import ClusterNode, PieceView, LengthView, LastDotSplitFuzzyView, \
    BaseView, MixedView, FuzzyView


class ClusterNodeViewBag(object):
    def __init__(self):
        self._nodes = []
        self._count = 0

    def add_node(self, node_view):
        self._nodes.append(node_view)
        self._count += node_view.count

    @property
    def count(self):
        return self._count

    def __iter__(self):
        return iter(self._nodes)

    def set_pattern(self, pattern, cluster_name):
        for node in self._nodes:
            node.set_pattern(pattern, cluster_name)


class ClusterNodeViewPack(object):
    def __init__(self):
        self._packs = {}
        self._count = 0

    def add_node(self, node_view):
        c_name = node_view.cluster_name
        if c_name not in self._packs:
            self._packs[c_name] = ClusterNodeViewBag()
        self._packs[c_name].add_node(node_view)
        self._count += node_view.count

    def iter_nodes(self):
        for view_bag in self._packs.itervalues():
            for node_view in view_bag:
                yield node_view

    def iter_items(self):
        return self._packs.iteritems()

    def iter_values(self):
        return self._packs.itervalues()

    @property
    def count(self):
        return self._count

    def set_pattern(self, pattern, cluster_name):
        for bag in self._packs.itervalues():
            bag.set_pattern(pattern, cluster_name)

    def pick_node_view(self):
        for node_view in self.iter_nodes():
            return node_view

    def __len__(self):
        return len(self._packs)


class ViewPack(object):
    def __init__(self, view_class):
        self._view_class = view_class
        self._packs = {}
        self._count = 0

    def pick_node_view(self):
        for node_view in self.iter_nodes():
            return node_view

    def add_node(self, cluster_node):
        node_view = self._view_class(cluster_node)
        v = node_view.view()
        if v not in self._packs:
            self._packs[v] = ClusterNodeViewPack()
        self._packs[v].add_node(node_view)
        self._count += cluster_node.count

    def iter_nodes(self):
        for view_pack in self._packs.itervalues():
            for node_view in view_pack.iter_nodes():
                yield node_view

    def iter_values(self):
        return self._packs.itervalues()

    def iter_items(self):
        return self._packs.iteritems()

    @property
    def count(self):
        return self._count

    def set_pattern(self, pattern, cluster_name):
        for pack in self._packs.itervalues():
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

    def add_node(self, cluster_node):
        self._view_pack.add_node(cluster_node)

    def iter_nodes(self):
        for node_view in self._view_pack.iter_nodes():
            yield node_view.cluster_node

    def _cluster(self):
        pass

    def _forward_cluster(self):
        pass

    def cluster(self):
        self._cluster()
        return self._forward_cluster()

    def _set_pattern(self, obj, pattern):
        obj.set_pattern(pattern, self._cluster_name)

    def _create_cluster(self, cluster_cls):
        c = cluster_cls(self._config, self._meta_info)
        for cluster_node in self.iter_nodes():
            c.add_node(cluster_node)
        return c

    def _can_be_clustered(self, pack):
        for bag in pack.iter_values():
            p_set = set([node.pattern for node in bag])
            if len(p_set) >= self._min_cluster_num:
                return True
        return False


class PiecePatternCluster(PatternCluster):
    def __init__(self, config, meta_info):
        super(PiecePatternCluster, self).__init__(config, meta_info)
        self._view_pack = ViewPack(PieceView)

    def _cluster(self):
        for piece, pack in self._view_pack.iter_items():
            if pack.count >= self._min_cluster_num:
                self._set_pattern(pack, Pattern(piece))

    def _forward_cluster(self):
        if len(self._view_pack) < self._min_cluster_num:
            return None

        forward_cls = LengthPatternCluster
        node_view = self._view_pack.pick_node_view()
        if len(node_view.view_parsed_pieces()) > 1:
            forward_cls = BasePatternCluster
        return self._create_cluster(forward_cls)


class LengthPatternCluster(PatternCluster):
    def __init__(self, config, meta_info):
        super(LengthPatternCluster, self).__init__(config, meta_info)
        self._view_pack = ViewPack(LengthView)

    def _can_be_clustered(self, pack):
        node_view = pack.pick_node_view()
        if node_view.piece.isdigit():
            p_set = set([node.pattern for node in pack.iter_nodes()])
            if len(p_set) >= self._min_cluster_num:
                return True
            return False

        for bag in pack.iter_values():
            p_set = set([node.pattern for node in bag])
            if len(p_set) >= self._min_cluster_num:
                return True
        return False

    def _cluster(self):
        for length, pack in self._view_pack.iter_items():
            if self._can_be_clustered(pack):
                node_view = pack.pick_node_view()
                pattern = Pattern(number_rule(
                    node_view.parsed_piece.fuzzy_rule, length))
                self._set_pattern(pack, pattern)

    def _forward_cluster(self):
        p_set = set([node.pattern for node in self.iter_nodes()])
        if len(p_set) < self._min_cluster_num:
            return None
        return self._create_cluster(FuzzyPatternCluster)


class MultiPartPatternCluster(PatternCluster):
    def _cluster(self):
        for pack in self._view_pack.iter_values():
            if self._can_be_clustered(pack):
                self._deep_cluster(pack)

    def cluster(self):
        self._cluster()
        p_set = set([node.pattern for node in self.iter_nodes()])
        if len(p_set) < self._min_cluster_num:
            return None
        return self._forward_cluster()

    def _deep_cluster(self, pack):
        piece_pattern_tree = PiecePatternTree()
        for node in pack.iter_nodes():
            piece_pattern_tree.add_from_parsed_pieces(
                node.view_parsed_pieces(), node.count, False)
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
            pattern_counter[pattern] += 1

        for node in pack.iter_nodes():
            if node.piece in piece_pattern_dict:
                pattern = piece_pattern_dict[node.piece]
                if pattern_counter[pattern] > 1:
                    self._set_pattern(node, pattern)


class BasePatternCluster(MultiPartPatternCluster):
    def __init__(self, config, meta_info):
        super(BasePatternCluster, self).__init__(config, meta_info)
        self._view_pack = ViewPack(BaseView)

    def _forward_cluster(self):

        c = self._create_cluster(MixedPatternCluster)
        if len(self.view_pack) > len(c.view_pack):
            return c

        forward_cls = LengthPatternCluster
        if self._meta_info.is_last_path():
            forward_cls = LastDotSplitFuzzyPatternCluster
        c = self._create_cluster(forward_cls)
        if len(self.view_pack) > len(c.view_pack):
            return c
        return self._create_cluster(FuzzyPatternCluster)


class MixedPatternCluster(MultiPartPatternCluster):
    def __init__(self, config, meta_info):
        super(MixedPatternCluster, self).__init__(config, meta_info)
        self._view_pack = ViewPack(MixedView)

    def _deep_cluster(self, pack):
        if len(self.view_pack) <= 1 \
                and len(self.view_pack.pick_node_view().view_parsed_pieces()) <= 1:
            return

        super(MixedPatternCluster, self)._deep_cluster(pack)

    def _forward_cluster(self):

        forward_cls = LengthPatternCluster
        if self._meta_info.is_last_path():
            forward_cls = LastDotSplitFuzzyPatternCluster
        c = self._create_cluster(forward_cls)
        if len(self.view_pack) > len(c.view_pack):
            return c
        return self._create_cluster(FuzzyPatternCluster)


class LastDotSplitFuzzyPatternCluster(MultiPartPatternCluster):
    def __init__(self, config, meta_info):
        super(LastDotSplitFuzzyPatternCluster,
              self).__init__(config, meta_info)
        self._view_pack = ViewPack(LastDotSplitFuzzyView)

    def _deep_cluster(self, pack):
        node_view = pack.pick_node_view()
        if len(node_view.view_parsed_pieces()) <= 1:
            c = LengthPatternCluster(self._config, self._meta_info)
            for node_view in pack.iter_nodes():
                c.add_node(node_view.cluster_node)
            while c:
                c = c.cluster()
        else:
            super(LastDotSplitFuzzyPatternCluster, self)._deep_cluster(pack)

    def _forward_cluster(self):
        return None


class FuzzyPatternCluster(PatternCluster):
    def __init__(self, config, meta_info):
        super(FuzzyPatternCluster, self).__init__(config, meta_info)
        self._view_pack = ViewPack(FuzzyView)

    def cluster(self):
        node_view = self._view_pack.pick_node_view()
        if node_view.piece.isdigit():
            p_set = set([node.pattern for node in self.iter_nodes()])
            if len(p_set) >= self._min_cluster_num:
                self._set_pattern(self._view_pack, Pattern(
                    wildcard_rule(BasePatternRule.DIGIT)))
            return
        clusterd = False
        un_clusterd_bags = []
        for fuzzy_rule, pack in self._view_pack.iter_items():

            for c_name, bag in pack.iter_items():
                p_set = set([node.pattern for node in bag])
                if len(p_set) >= self._min_cluster_num:
                    clusterd = True
                    self._set_pattern(bag, Pattern(wildcard_rule(fuzzy_rule)))
                else:
                    if c_name == '' or c_name == 'LengthPatternCluster':
                        un_clusterd_bags.append((fuzzy_rule, bag))
        if clusterd:
            for fuzzy_rule, bag in un_clusterd_bags:
                self._set_pattern(bag, Pattern(wildcard_rule(fuzzy_rule)))


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
        return MetaInfo(self.url_meta, self._current_level + 1)


class ClusterProcessor(object):
    def __init__(self, config, meta_info):
        self._config = config
        self._meta_info = meta_info
        self._entry_cluster = PiecePatternCluster(config, meta_info)

    def iter_nodes(self):
        for cluster_node in self._entry_cluster.iter_nodes():
            yield cluster_node.node

    def add_node(self, node):
        self._entry_cluster.add_node(ClusterNode(node))

    def _process(self):
        c = self._entry_cluster
        while c:
            c = c.cluster()

    def process(self):
        self._process()
        if self._meta_info.is_last_level():
            return
        next_level_processors = {}
        for node in self.iter_nodes():
            n_hash = hash(node.pattern)
            if n_hash not in next_level_processors:
                next_level_processors[n_hash] = ClusterProcessor(
                    self._config, self._meta_info.next_level_meta_info())
            next_processor = next_level_processors[n_hash]
            for child in node.children:
                next_processor.add_node(child)
        for processor in next_level_processors.itervalues():
            processor.process()


def cluster(config, url_meta, piece_pattern_tree):
    meta_info = MetaInfo(url_meta, 0)
    processor = ClusterProcessor(config, meta_info)
    processor.add_node(piece_pattern_tree.root)
    processor.process()
