from .compat import itervalues
from .definition import DIGIT_AND_ASCII_RULE_SET, BasePatternRule
from .node_viewer import BaseViewer, LengthViewer, MixedViewer, PieceViewer
from .parse_utils import URLMeta, number_rule, wildcard_rule
from .pattern import Pattern
from .piece_pattern_tree import PiecePatternTree
from .utils import Bag

NOT_PATTERN = (False, None)


class CBag(Bag):
    def __init__(self):
        super(CBag, self).__init__()
        self._count = 0

    @property
    def count(self):
        return self._count

    def add(self, obj):
        super(CBag, self).add(obj)
        self._count += obj.count

    def set_pattern(self, pattern):
        for obj in self:
            obj.set_pattern(pattern)


class PatternCluster(object):
    def __init__(self, config, meta_info):
        self._config = config
        self._meta_info = meta_info
        self._min_cluster_num = config.getint('make', 'min_cluster_num')

    def _cluster(self):
        pass

    def _forward_clusters(self):
        yield

    def cluster(self):
        self._cluster()
        for c in self._forward_clusters():
            yield c

    def add(self, obj):
        pass


class TBucket(object):
    def __init__(self, viewer_cls_list):
        self._viewer_cls_list = viewer_cls_list
        self._viewer_cls_idx = 0
        self._last_viewer = None
        self._nodes = set()

    def nodes(self):
        return self._nodes

    def _get_viewer_cls(self):
        return self._viewer_cls_list[self._viewer_cls_idx]

    def _next_viewer_cls(self):
        if self._get_viewer_cls() is None:
            return None
        self._viewer_cls_idx += 1
        return self._get_viewer_cls()

    def check(self, node):
        if self._last_viewer is None:
            return True
        v_cls = self._get_viewer_cls()
        viewer = v_cls(node)
        return self._last_viewer.view() == viewer.view()

    def add_and_check(self, node):
        if self._last_viewer is None:
            v_cls = self._get_viewer_cls()
            self._last_viewer = v_cls(node)
            self._nodes.add(node)
            return True

        while self._get_viewer_cls() is not None:
            if self.check(node):
                self._nodes.add(node)
                return True
            else:
                self._next_viewer_cls()
        return False


def create_tbucket(node):
    cls_list = None
    if len(node.parsed_piece.pieces) > 1:
        cls_list = [PieceViewer,
                    BaseViewer,
                    MixedViewer,
                    LengthViewer,
                    None, ]
    else:
        cls_list = [PieceViewer,
                    LengthViewer,
                    None, ]
    return TBucket(cls_list)


class PBag(CBag):
    def __init__(self):
        super(PBag, self).__init__()
        self._skip = False
        self._p_nodes = set()

    @property
    def skip(self):
        return self._skip

    @skip.setter
    def skip(self, skip):
        self._skip = skip

    def add(self, piece_node):
        super(PBag, self).add(piece_node)
        self._p_nodes.add(piece_node.parrent)

    @property
    def p_nodes(self):
        return self._p_nodes


class PiecePatternCluster(PatternCluster):
    def __init__(self, config, meta_info):
        super(PiecePatternCluster, self).__init__(config, meta_info)
        self._piece_bags = {}
        self._forward_cluster = None

    def iter_nodes(self):
        for bag in itervalues(self._piece_bags):
            for node in bag.iter_all():
                yield node

    def add(self, piece_pattern_node):
        piece = piece_pattern_node.piece
        if piece not in self._piece_bags:
            self._piece_bags[piece] = PBag()
        bag = self._piece_bags[piece]
        bag.add(piece_pattern_node)
        if bag.skip or bag.count < self._min_cluster_num:
            return

        p_node = piece_pattern_node.parrent
        if p_node is None or p_node.children_num == 1:
            return

        for b_node in p_node.iter_children():
            b_piece = b_node.piece
            if b_piece == piece:
                continue
            if b_piece not in self._piece_bags:
                continue
            b_bag = self._piece_bags[b_piece]
            if b_bag.count >= self._min_cluster_num:
                b_bag.skip = True
                bag.skip = True
                break

    def _create_forward_cluster(self):
        cluster_cls = LengthPatternCluster
        piece_pattern_node = self._piece_bags.values()[0].pick()
        if len(piece_pattern_node.parsed_piece.pieces) > 1:
            cluster_cls = BasePatternCluster
        return cluster_cls(self._config, self._meta_info)

    def _cluster(self):
        n = len(self._piece_bags)
        if n == 1:
            return

        if self._forward_cluster is None:
            self._forward_cluster = self._create_forward_cluster()

        for piece_bag in itervalues(self._piece_bags):
            if piece_bag.skip or piece_bag.count < self._min_cluster_num:
                self._forward_cluster.add(piece_bag)

    def _forward_clusters(self):
        yield self._forward_cluster


class LengthPatternCluster(PatternCluster):
    def __init__(self, config, meta_info):
        super(LengthPatternCluster, self).__init__(config, meta_info)
        self._forward_cluster = FuzzyPatternCluster(config, meta_info)
        self._length_bags = {}

    def add(self, piece_bag):
        piece_length = piece_bag.pick().parsed_piece.piece_length
        if piece_length not in self._length_bags:
            self._length_bags[piece_length] = CBag()
        self._length_bags[piece_length].add(piece_bag)

    def _cluster(self):

        for length_bag in itervalues(self._length_bags):
            patterned, bucket = self._direct_check(length_bag)
            if not patterned or not self._deep_check(bucket):
                self._forward_cluster.add(length_bag)

    def _set_pattern(self, length_bag):
        parsed_piece = length_bag.pick().parsed_piece
        length = parsed_piece.piece_length
        pattern = Pattern(number_rule(parsed_piece.fuzzy_rule, length))
        length_bag.set_pattern(pattern)

    def _forward_clusters(self):
        yield self._forward_cluster


class MultiPartPatternCluster(PatternCluster):
    pass


class BasePatternCluster(MultiPartPatternCluster):
    def __init__(self, config, meta_info):
        super(BasePatternCluster, self).__init__(config, meta_info)

    def add(self, piece_bag):
        pass


class FuzzyPatternCluster(PatternCluster):
    def __init__(self, config, meta_info):
        super(FuzzyPatternCluster, self).__init__(config, meta_info)
        self._cached_bag = CBag()
        self._force_pattern = False
        self._fuzzy_pattern = None

    def add(self, bag):
        if self._force_pattern:
            self._set_pattern(bag)
        else:
            self._cached_bag.add(bag)
            if len(self._cached_bag) > 1 \
                    and self._cached_bag.count >= self._min_cluster_num:
                self._force_pattern = True

    def _cluster(self):
        if self._force_pattern:
            self._set_pattern(self._cached_bag)

    def _set_pattern(self, bag):
        if self._fuzzy_pattern is None:
            self._fuzzy_pattern = Pattern(
                wildcard_rule(bag.pick().parsed_piece.fuzzy_rule))
        bag.set_pattern(self._force_pattern)


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
    def __init__(self, config, meta_info, global_processing):
        self._config = config
        self._meta_info = meta_info
        self._global_processing = global_processing
        self._entry_cluster = PiecePatternCluster(config, meta_info)

    def add_node(self, node):
        self._entry_cluster.add(node)

    def add_children(self, node):
        for child in node.iter_children():
            self.add_node(child)

    def _process(self, pattern_cluster):
        if pattern_cluster is not None:
            for c in pattern_cluster.cluster():
                self._process(c)

    def _preprocess(self):
        pass

    def process(self):
        self._process(self._entry_cluster)
        if self._meta_info.is_last_level():
            return
        next_level_processors = {}
        next_level_meta_info = self._meta_info.next_level_meta_info()
        for node in self._entry_cluster.iter_nodes():
            pattern = node.pattern
            if pattern not in next_level_processors:
                next_level_processors[pattern] = ClusterProcessor(
                    self._config, next_level_meta_info, self._global_processing)
            next_level_processor = next_level_processors[pattern]
            next_level_processor.add_children(node)
        for processor in itervalues(next_level_processors):
            processor.process()


def split(piece_pattern_tree):
    yield


def cluster(config, url_meta, piece_pattern_tree, **kwargs):
    global_processing = kwargs.get('global_processing', True)
    if global_processing and \
            piece_pattern_tree.count < config.getint('make', 'min_cluster_num'):
        return

    meta_info = MetaInfo(url_meta, 0)
    processor = ClusterProcessor(
        config, meta_info, global_processing)
    processor.add_node(piece_pattern_tree.root)
    processor.process()

    return
    if global_processing:
        for sub_piece_pattern_tree in split(piece_pattern_tree):
            cluster(config, url_meta, sub_piece_pattern_tree,
                    global_processing=False)
