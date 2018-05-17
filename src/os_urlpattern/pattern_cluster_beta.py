from collections import Counter, OrderedDict, defaultdict, namedtuple
from types import MethodType

from .compat import iteritems, itervalues
from .definition import DIGIT_AND_ASCII_RULE_SET, BasePatternRule
from .parse_utils import URLMeta, number_rule, wildcard_rule
from .parsed_piece_viewer import (BaseViewer, LastDotSplitFuzzyViewer,
                                  MixedViewer)
from .pattern import Pattern
from .piece_pattern_tree import PiecePatternNode, PiecePatternTree
from .utils import Bag


class TBag(Bag):
    def __init__(self):
        super(TBag, self).__init__()
        self._count = 0

    @property
    def count(self):
        return self._count

    def add(self, obj):
        super(TBag, self).add(obj)
        self._count += obj.count

    def set_pattern(self, pattern):
        for obj in self:
            obj.set_pattern(pattern)


class PieceBag(TBag):
    def __init__(self):
        super(PieceBag, self).__init__()
        self._p_nodes = set()
        self._p_counter = None

    def incr(self, incr):
        self._count += incr

    def add(self, piece_node):
        super(PieceBag, self).add(piece_node)
        self._p_nodes.add(piece_node.parrent)

    @property
    def p_nodes(self):
        return self._p_nodes

    @property
    def p_counter(self):
        if self._p_counter is None:
            self._p_counter = Counter()
            for p in self:
                self._p_counter[p.parrent.parsed_piece] += p.count
        return self._p_counter


class Bucket(TBag):

    def __init__(self):
        super(Bucket, self).__init__()
        self._objs = {}

    def __getitem__(self, key):
        return self._objs[key]

    def __contains__(self, key):
        return key in self._objs

    def _get(self):
        for obj in itervalues(self._objs):
            return obj

    def __iter__(self):
        return itervalues(self._objs)

    def add(self, obj):
        raise NotImplementedError


class PieceNodeBucket(Bucket):

    def add(self, piece_pattern_node):
        piece = piece_pattern_node.piece
        if piece not in self._objs:
            self._objs[piece] = PieceBag()
        self._objs[piece].add(piece_pattern_node)
        self._count += piece_pattern_node.count


class PieceBagBucket(Bucket):

    def __init__(self):
        super(PieceBagBucket, self).__init__()
        self._p_counter = None

    @property
    def p_counter(self):
        if self._p_counter is None:
            self._p_counter = Counter()
            for p in self:
                self._p_counter.update(p.p_counter)
        return self._p_counter

    def add(self, piece_bag):
        piece = piece_bag.pick().piece
        if piece in self._objs:
            raise ValueError('duplicated')
        self._objs[piece] = piece_bag
        self._count += piece_bag.count


class PieceBagMixin(object):
    @property
    def p_counter(self):
        return self.piece_bag.p_counter

    @property
    def count(self):
        return self.piece_bag.count

    def pick(self):
        return self.piece_bag.pick()


class PieceViewerBag(PieceBagMixin,
                     namedtuple('PieceViewerBag', ['piece_bag', 'viewer'])):
    __slots__ = ()


class PieceViewerBagBucket(PieceBagBucket):
    def __init__(self):
        super(PieceViewerBagBucket, self).__init__()
        self._tree = PiecePatternTree()

    def add(self, piece_viewer_bag):
        super(PieceViewerBagBucket, self).add(piece_viewer_bag)
        viewer = piece_viewer_bag.viewer
        self._tree.add_from_parsed_pieces(
            viewer.parsed_pieces,
            count=piece_viewer_bag.count,
            uniq=False)


def confused(total, part, threshold):
    if total < threshold:
        return False
    o_part = total - part
    if part >= threshold and o_part >= threshold:
        return True
    return abs(part - o_part) < threshold - 1


class PatternCluster(object):
    def __init__(self, processor):
        self._processor = processor
        self._min_cluster_num = processor.config.getint(
            'make', 'min_cluster_num')

    def get_processor(self, n):
        processor = self._processor
        while n > 0 and processor is not None:
            processor = processor.pre_level_processor
            n -= 1
        return processor

    @property
    def pre_level_processor(self):
        return self._processor.pre_level_processor

    def as_cluster(self, p_counter):
        return False

    def cluster(self):
        pass

    def add(self, obj):
        pass


class PiecePatternCluster(PatternCluster):
    def __init__(self, processor):
        super(PiecePatternCluster, self).__init__(processor)
        self._piece_bucket = PieceNodeBucket()
        self._piece_skip = defaultdict(lambda: False)

    def revise(self, p_counter):
        for parsed_piece, count in iteritems(p_counter):
            self._piece_bucket[parsed_piece.piece].incr(0 - count)

    def as_cluster(self, p_counter):
        if len(p_counter) >= self._min_cluster_num or len(self._piece_bucket) <= 1:
            return False
        total = sum([self._piece_bucket[p.piece].count for p in p_counter])
        _, max_count = p_counter.most_common(1)[0]
        return not confused(total, max_count, self._min_cluster_num)

    def iter_nodes(self):
        return self._piece_bucket.iter_all()

    def add(self, piece_pattern_node):
        piece = piece_pattern_node.piece
        self._piece_bucket.add(piece_pattern_node)
        bag = self._piece_bucket[piece]
        if self._piece_skip[piece] or bag.count < self._min_cluster_num:
            return

        p_node = piece_pattern_node.parrent
        if p_node is None or p_node.children_num == 1:
            return

        if p_node.count - piece_pattern_node.count >= self._min_cluster_num:
            self._piece_skip[piece] = True
            return

        for b_node in p_node.iter_children():
            b_piece = b_node.piece
            if b_piece == piece or b_piece not in self._piece_bucket:
                continue
            b_bag = self._piece_bucket[b_piece]
            if b_bag.count >= self._min_cluster_num:
                self._piece_skip[b_piece] = True
                self._piece_skip[piece] = True
                break

    def cluster(self):
        if len(self._piece_bucket) < self._min_cluster_num:
            if self._piece_bucket.count < self._min_cluster_num:
                return
            max_count = max(self._piece_bucket, key=lambda x: x.count).count
            if not confused(self._piece_bucket.count, max_count, self._min_cluster_num):
                return

        for piece_bag in self._piece_bucket:
            piece = piece_bag.pick().piece
            if self._piece_skip[piece] \
                    or piece_bag.count < self._min_cluster_num \
                    or not self.get_processor(1).seek_cluster(piece_bag.p_counter):
                self._add_to_forward_cluster(piece_bag)
            else:
                self.get_processor(1).revise(piece_bag.p_counter)

    def _add_to_forward_cluster(self, piece_bag):
        parsed_piece = piece_bag.pick().parsed_piece
        if len(parsed_piece.pieces) == 1:
            self._processor.get_cluster(LengthPatternCluster).add(piece_bag)
            return

        viewer = BaseViewer(parsed_piece)
        p_cls = BasePatternCluster
        if len(viewer.parsed_pieces) >= self._min_cluster_num:
            mixed_viewer = MixedViewer(parsed_piece)
            mvl = len(mixed_viewer.parsed_pieces)
            if mvl == 1:
                self._processor.get_cluster(
                    LengthPatternCluster).add(piece_bag)
                return
            elif mvl == 3 and self._processor.meta_info.is_last_path():
                ldsf_viewer = LastDotSplitFuzzyViewer(parsed_piece)
                if mixed_viewer.view == ldsf_viewer.view:
                    viewer = ldsf_viewer
                    p_cls = LastDotSplitFuzzyPatternCluster
                    return

            if len(viewer.parsed_pieces) - mvl >= self._min_cluster_num:
                viewer = mixed_viewer
                p_cls = MixedPatternCluster

        self._processor.get_cluster(p_cls).add(
            PieceViewerBag(piece_bag, viewer))


class LengthPatternCluster(PatternCluster):
    def __init__(self, processor):
        super(LengthPatternCluster, self).__init__(processor)
        self._length_buckets = {}

    def as_cluster(self, p_counter):
        if not self._length_buckets:
            return False
        length_counter = Counter()
        p_total = 0
        for parsed_piece, count in iteritems(p_counter):
            length = parsed_piece.piece_length
            length_counter[length] += count
            if len(length_counter) >= self._min_cluster_num:
                return False
            p_total += count
        max_length, max_count = length_counter.most_common(1)[0]
        if confused(p_total, max_count, self._min_cluster_num):
            return False

        l_total = sum([c.count for c in self._length_buckets[max_length]])
        return not confused(l_total, max_count, self._min_cluster_num)

    def add(self, piece_bag):
        piece_length = piece_bag.pick().parsed_piece.piece_length
        if piece_length not in self._length_buckets:
            self._length_buckets[piece_length] = PieceBagBucket()
        self._length_buckets[piece_length].add(piece_bag)

    def _length_as_cluster(self, length_bucket):
        if len(length_bucket) < self._min_cluster_num:
            if length_bucket.count < self._min_cluster_num:
                return False
            max_count = max(length_bucket, key=lambda x: x.count).count
            if not confused(length_bucket.count, max_count, self._min_cluster_num):
                return False

        return True

    def cluster(self):
        if len(self._length_buckets) < self._min_cluster_num:
            total = sum([c.count for c in itervalues(self._length_buckets)])
            if total < self._min_cluster_num:
                return
            max_bucket = max(itervalues(self._length_buckets),
                             key=lambda x: x.count)
            if not confused(total, max_bucket.count, self._min_cluster_num):
                if self._length_as_cluster(max_bucket):
                    self._set_pattern(max_bucket)
                    return

        forward_cluster = self._processor.get_cluster(FuzzyPatternCluster)
        for length_bucket in itervalues(self._length_buckets):
            if self._length_as_cluster(length_bucket):
                self._set_pattern(length_bucket)

                p = self.get_processor(1)
                if p.seek_cluster(length_bucket.p_counter):
                    p.revise(length_bucket.p_counter)
                    continue
            forward_cluster.add(length_bucket)

    def _set_pattern(self, length_bucket):
        parsed_piece = length_bucket.pick().parsed_piece
        length = parsed_piece.piece_length
        pattern = Pattern(number_rule(parsed_piece.fuzzy_rule, length))
        length_bucket.set_pattern(pattern)


class BasePatternCluster(PatternCluster):
    def __init__(self, processor):
        super(BasePatternCluster, self).__init__(processor)
        self._buckets = {}

    def as_cluster(self, p_counter):
        pass

    def add(self, piece_viewer_bag):
        viewer = piece_viewer_bag.viewer
        view = viewer.view
        if view not in self._buckets:
            self._buckets[view] = PieceViewerBagBucket()
        self._buckets[view].add(piece_viewer_bag)

    def cluster(self):
        for bucket in itervalues(self._buckets):
            if bucket.count < self._min_cluster_num:
                continue

    def _add_to_forward_cluster(self, bucket):
        pass


class MixedPatternCluster(PatternCluster):
    def __init__(self, processor):
        super(MixedPatternCluster, self).__init__(processor)

    def add(self, piece_bag):
        pass


class LastDotSplitFuzzyPatternCluster(PatternCluster):
    def __init__(self, processor):
        super(LastDotSplitFuzzyPatternCluster, self).__init__(processor)
        self._buckets = {}

    def add(self, piece_viewer_bag):
        viewer = piece_viewer_bag.viewer
        view = viewer.view
        if view not in self._buckets:
            self._buckets[view] = PieceViewerBagBucket()
        self._buckets[view].add(piece_viewer_bag)


class FuzzyPatternCluster(PatternCluster):
    def __init__(self, processor):
        super(FuzzyPatternCluster, self).__init__(processor)
        self._cached = TBag()
        self._force_pattern = False
        self._fuzzy_pattern = None

    def add(self, bucket):
        if self._force_pattern:
            self._set_pattern(bucket)
        else:
            self._cached.add(bucket)
            if len(self._cached) >= self._min_cluster_num:
                self._force_pattern = True

    def cluster(self):
        if self._force_pattern:
            self._set_pattern(self._cached)
        else:
            if self._cached.count < self._min_cluster_num:
                return
            max_count = max(self._cached, key=lambda x: x.count).count
            if confused(self._cached.count, max_count, self._min_cluster_num):
                self._set_pattern(self._cached)

    def _set_pattern(self, bag):
        if self._fuzzy_pattern is None:
            self._fuzzy_pattern = Pattern(
                wildcard_rule(bag.pick().parsed_piece.fuzzy_rule))
        bag.set_pattern(self._fuzzy_pattern)


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


CLUSTER_CLASSES = [PiecePatternCluster, BasePatternCluster, MixedPatternCluster,
                   LastDotSplitFuzzyPatternCluster, LengthPatternCluster,
                   FuzzyPatternCluster]


class ClusterProcessor(object):
    def __init__(self, config, meta_info, pre_level_processor):
        self._config = config
        self._meta_info = meta_info
        self._pattern_clusters = OrderedDict(
            [(c.__name__, c(self)) for c in CLUSTER_CLASSES])
        self._pre_level_processor = pre_level_processor

    def seek_cluster(self, p_counter):
        for c in self._pattern_clusters.itervalues():
            if c.as_cluster(p_counter):
                return True

        return False

    def revise(self, p_counter):
        self.get_cluster(PiecePatternCluster).revise(p_counter)

    def get_cluster(self, cluster_cls):
        return self._pattern_clusters[cluster_cls.__name__]

    @property
    def meta_info(self):
        return self._meta_info

    @property
    def config(self):
        return self._config

    @property
    def pre_level_processor(self):
        return self._pre_level_processor

    def _process(self, ):
        for c in self._pattern_clusters.itervalues():
            c.cluster()

    def process(self):
        self._process()
        if self._meta_info.is_last_level():
            return

        next_level_processors = self._create_next_level_processors()

        for processor in itervalues(next_level_processors):
            processor.process()

    def _create_next_level_processors(self):
        pp_cluster = self.get_cluster(PiecePatternCluster)
        next_level_processors = {}

        for node in pp_cluster.iter_nodes():
            pattern = node.pattern
            if pattern not in next_level_processors:
                next_level_processors[pattern] = self._create_next_level_processor(
                )
            next_level_processor = next_level_processors[pattern]
            next_pp_cluster = next_level_processor.get_cluster(
                PiecePatternCluster)
            for child in node.iter_children():
                next_pp_cluster.add(child)

        return next_level_processors

    def _create_next_level_processor(self):
        return ClusterProcessor(self._config,
                                self._meta_info.next_level_meta_info(),
                                self)


def split(piece_pattern_tree):
    trees = {}
    for path in piece_pattern_tree.dump_paths():
        pid = hash('/'.join([str(p.pattern) for p in path]))
        if pid not in trees:
            trees[pid] = PiecePatternTree()
        tree = trees[pid]
        tree.add_from_piece_pattern_node_path(path[1:])

    import sys
    print >> sys.stderr, len(trees)


def process(config, url_meta, piece_pattern_tree, **kwargs):
    meta_info = MetaInfo(url_meta, 0)
    processor = ClusterProcessor(config, meta_info, None)
    processor.get_cluster(PiecePatternCluster).add(piece_pattern_tree.root)
    processor.process()


def cluster(config, url_meta, piece_pattern_tree, **kwargs):
    split(piece_pattern_tree)
    #process(config, url_meta, piece_pattern_tree, **kwargs)

    return
    for sub_piece_pattern_tree in split(piece_pattern_tree):
        process(config, url_meta, sub_piece_pattern_tree)
