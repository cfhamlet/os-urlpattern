from collections import Counter, OrderedDict, namedtuple

from .compat import iteritems, itervalues
from .parse_utils import URLMeta, digest, number_rule, wildcard_rule
from .parsed_piece_viewer import (BaseViewer, LastDotSplitFuzzyViewer,
                                  MixedViewer)
from .pattern import Pattern
from .piece_pattern_tree import PiecePatternNode, PiecePatternTree
from .utils import Bag


class TBag(Bag):
    def __init__(self):
        super(TBag, self).__init__()
        self._stats = Counter()

    @property
    def count(self):
        return self._stats['count']

    @property
    def stats(self):
        return self._stats

    def add(self, obj):
        super(TBag, self).add(obj)
        self._stats['count'] += obj.count

    def set_pattern(self, pattern):
        for obj in self:
            obj.set_pattern(pattern)


class TBucket(TBag):

    def __init__(self):
        super(TBucket, self).__init__()
        self._objs = {}

    def __getitem__(self, key):
        return self._objs[key]

    def __contains__(self, key):
        return key in self._objs

    def _pick(self):
        for obj in itervalues(self._objs):
            return obj

    def __iter__(self):
        return itervalues(self._objs)

    def add(self, obj):
        raise NotImplementedError


class PieceBag(TBag):

    def __init__(self):
        super(PieceBag, self).__init__()
        self._p_nodes = set()

    def add(self, piece_pattern_node):
        super(PieceBag, self).add(piece_pattern_node)
        self._p_nodes.add(piece_pattern_node.parrent)
        self._stats['p_nodes_count'] += piece_pattern_node.parrent.count \
            if piece_pattern_node.parrent is not None \
            else piece_pattern_node.count

    @property
    def p_nodes(self):
        return self._p_nodes


class PieceBagBucket(TBucket):

    def __init__(self):
        super(PieceBagBucket, self).__init__()
        self._p_nodes = set()

    def add(self, obj):
        if isinstance(obj, PiecePatternNode):
            piece = obj.piece
            if piece not in self._objs:
                self._objs[piece] = PieceBag()
            self._objs[piece].add(obj)
        elif isinstance(obj, PieceBag):
            piece = obj.pick().piece
            if piece in self._objs:
                raise ValueError('duplicated')
            self._objs[piece] = obj
        else:
            raise ValueError('not PiecePatternNode nor PieceBag')

        self._stats['count'] += obj.count

    @property
    def p_nodes(self):
        if not self._p_nodes:
            for piece_bag in self:
                self._p_nodes.update(piece_bag.p_nodes)
        return self._p_nodes


class ViewerPieceBag(namedtuple('ViewerPieceBag', ['viewer', 'piece_bag'])):
    __slots__ = ()

    def set_pattern(self, pattern):
        return self.piece_bag.set_pattern(pattern)


class ViewerPieceBagBucket(PieceBagBucket):
    def __init__(self):
        super(ViewerPieceBagBucket, self).__init__()
        self._tree = PiecePatternTree()

    def add(self, viewer_piece_bag, build_tree=True):
        piece_bag = viewer_piece_bag.piece_bag
        self._objs[piece_bag.pick().piece] = viewer_piece_bag
        self.stats['count'] += piece_bag.count

        if not build_tree:
            return
        viewer = viewer_piece_bag.viewer
        self._tree.add_from_parsed_pieces(
            viewer.parsed_pieces,
            count=piece_bag.count,
            uniq=False)

    def cluster(self, config):
        p_num = len(self.pick().viewer.parsed_pieces)
        url_meta = URLMeta(p_num, [], False)
        for tree in cluster(config, url_meta, self._tree):
            yield self._transfer(tree)

    def _transfer(self, tree):
        pattern = None
        bucket = ViewerPieceBagBucket()
        for path in tree.dump_paths():
            piece = ''.join([p.piece for p in path[1:]])
            viewer_piece_bag = self[piece]
            bucket.add(viewer_piece_bag, False)
            if pattern is None:
                pattern = Pattern(''.join([str(p.pattern) for p in path[1:]]))
        return bucket, pattern


def confused(total, part, threshold):
    if total < threshold:
        return False
    o_part = total - part
    if part >= threshold and o_part >= threshold:
        return True
    return abs(part - o_part) < threshold - 1


class SeekResult(object):
    FOUND = 1
    IMPOSSIBLE = 2
    UNKNOW = 3
    BACKWARD = 4


class PatternCluster(object):
    def __init__(self, processor):
        self._processor = processor
        self._min_cluster_num = processor.config.getint(
            'make', 'min_cluster_num')
        self._patterns = set()

    @property
    def pre_level_processor(self):
        return self._processor.pre_level_processor

    def cluster(self):
        pass

    def add(self, obj):
        pass

    @property
    def pattern_num(self):
        return len(self._patterns)

    def seek_cluster(self, package):
        return SeekResult.UNKNOW


class PiecePatternCluster(PatternCluster):
    def __init__(self, processor):
        super(PiecePatternCluster, self).__init__(processor)
        self._bucket = PieceBagBucket()

    def seek_cluster(self, package):
        p_nodes_count = sum([p.count for p in package.p_nodes])
        if p_nodes_count - package.count >= self._min_cluster_num:
            return SeekResult.IMPOSSIBLE
        
        return SeekResult.UNKNOW

    def iter_nodes(self):
        return self._bucket.iter_all()

    def add(self, piece_pattern_node):
        self._bucket.add(piece_pattern_node)

    def _set_pattern(self, piece_bag, update_patterns=False):
        pattern = Pattern(piece_bag.pick().piece)
        piece_bag.set_pattern(pattern)
        if update_patterns:
            self._patterns.add(pattern)

    def cluster(self):
        mcn = self._min_cluster_num
        if len(self._bucket) < mcn:
            max_count = max(self._bucket, key=lambda x: x.count).count
            if not confused(self._bucket.count, max_count, mcn):
                for piece_bag in self._bucket:
                    self._set_pattern(piece_bag, True)
                return

        for piece_bag in self._bucket:
            stats = piece_bag.stats
            count = piece_bag.count
            if count < mcn \
                    or stats['p_nodes_count'] - count >= mcn \
                    or not self.pre_level_processor.seek_cluster(piece_bag):
                self._set_pattern(piece_bag)
                self._add_to_forward_cluster(piece_bag)
            else:
                self._set_pattern(piece_bag, True)

    def _add_to_forward_cluster(self, piece_bag):
        parsed_piece = piece_bag.pick().parsed_piece
        if len(parsed_piece.pieces) == 1:
            self._processor.get_cluster(LengthPatternCluster).add(piece_bag)
            return

        viewer = BaseViewer(parsed_piece)
        p_cls = BasePatternCluster
        if len(viewer.parsed_pieces) > self._min_cluster_num:
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
                    self._processor.get_cluster(p_cls).add(
                        ViewerPieceBag(viewer, piece_bag))
                    return

            if len(viewer.parsed_pieces) - mvl >= self._min_cluster_num:
                viewer = mixed_viewer
                p_cls = MixedPatternCluster
        else:
            if len(viewer.parsed_pieces) == 3 \
                    and self._processor.meta_info.is_last_path():
                ldsf_viewer = LastDotSplitFuzzyViewer(parsed_piece)
                if viewer.view == ldsf_viewer.view:
                    viewer = ldsf_viewer
                    p_cls = LastDotSplitFuzzyPatternCluster

        self._processor.get_cluster(p_cls).add(
            ViewerPieceBag(viewer, piece_bag))


class LengthPatternCluster(PatternCluster):
    def __init__(self, processor):
        super(LengthPatternCluster, self).__init__(processor)
        self._length_buckets = {}

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

    def _update_patterns(self, bucket):
        for piece_bag in bucket:
            self._patterns.add(piece_bag.pick().pattern)

    def cluster(self):
        if not self._length_buckets:
            return
        mcn = self._min_cluster_num
        if len(self._length_buckets) < mcn:
            total = sum([c.count for c in itervalues(self._length_buckets)])
            max_bucket = max(itervalues(self._length_buckets),
                             key=lambda x: x.count)
            if not confused(total, max_bucket.count, mcn):
                for bucket in itervalues(self._length_buckets):
                    if self._length_as_cluster(bucket):
                        self._set_pattern(bucket, True)
                    else:
                        self._update_patterns(bucket)
                return

        forward_cluster = self._processor.get_cluster(FuzzyPatternCluster)
        for length_bucket in itervalues(self._length_buckets):
            if self._length_as_cluster(length_bucket):
                if self.pre_level_processor.seek_cluster(length_bucket):
                    self._set_pattern(length_bucket, True)
                    continue
                self._set_pattern(length_bucket)

            forward_cluster.add(length_bucket)

    def _set_pattern(self, length_bucket, update_patterns=False):
        parsed_piece = length_bucket.pick().parsed_piece
        length = parsed_piece.piece_length
        pattern = Pattern(number_rule(parsed_piece.fuzzy_rule, length))
        if update_patterns:
            length_bucket.set_pattern(pattern)


class MultiPatternCluster(PatternCluster):
    def __init__(self, processor):
        super(MultiPatternCluster, self).__init__(processor)
        self._buckets = {}

    def cluster(self):
        for bucket in itervalues(self._buckets):
            if bucket.count < self._min_cluster_num:
                self._to_forward_cluster(bucket)
                continue
            for b, pattern in bucket.cluster(self._processor.config):
                if self._as_cluster(b, pattern):
                    self._set_pattern(b, pattern)
                else:
                    self._to_forward_cluster(b)

    def _to_forward_cluster(self, bucket):
        for viewer_piece_bag in bucket:
            self._add_to_forward_cluster(viewer_piece_bag)

    def _add_to_forward_cluster(self, viewer_piece_bag):
        pass

    def _as_cluster(self, bucket, pattern):
        if bucket.count < self._min_cluster_num:
            return False
        return True

    def _set_pattern(self, bucket, pattern):
        bucket.set_pattern(pattern)
        self._patterns.add(pattern)

    def add(self, viewer_piece_bag):
        viewer = viewer_piece_bag.viewer
        view = viewer.view
        if view not in self._buckets:
            self._buckets[view] = ViewerPieceBagBucket()
        self._buckets[view].add(viewer_piece_bag)


class BasePatternCluster(MultiPatternCluster):

    def _add_to_forward_cluster(self, viewer_piece_bag):
        viewer = viewer_piece_bag.viewer
        piece_bag = viewer_piece_bag.piece_bag
        parsed_piece = piece_bag.pick().parsed_piece

        mixed_viewer = MixedViewer(parsed_piece)
        mvl = len(mixed_viewer.parsed_pieces)

        p_cls = MixedPatternCluster

        if viewer.view == mixed_viewer.view:
            if self._processor.meta_info.is_last_path():
                ldsf_viewer = LastDotSplitFuzzyViewer(parsed_piece)
                if len(ldsf_viewer.parsed_pieces) == 1:
                    self._processor.get_cluster(
                        LengthPatternCluster).add(piece_bag)
                    return
                else:
                    viewer = ldsf_viewer
                    p_cls = LastDotSplitFuzzyPatternCluster
            else:
                self._processor.get_cluster(
                    LengthPatternCluster).add(piece_bag)
                return
        else:
            viewer = mixed_viewer
            if mvl == 1:
                self._processor.get_cluster(
                    LengthPatternCluster).add(piece_bag)
                return
            elif mvl == 3 and self._processor.meta_info.is_last_path():
                ldsf_viewer = LastDotSplitFuzzyViewer(parsed_piece)
                if mixed_viewer.view == ldsf_viewer.view:
                    viewer = ldsf_viewer
                    p_cls = LastDotSplitFuzzyPatternCluster

        self._processor.get_cluster(p_cls).add(
            ViewerPieceBag(viewer, piece_bag))


class MixedPatternCluster(MultiPatternCluster):

    def _add_to_forward_cluster(self, viewer_piece_bag):
        viewer = viewer_piece_bag.viewer
        piece_bag = viewer_piece_bag.piece_bag
        parsed_piece = piece_bag.pick().parsed_piece

        if self._processor.meta_info.is_last_path():
            ldsf_viewer = LastDotSplitFuzzyViewer(parsed_piece)
            if len(ldsf_viewer.parsed_pieces) == 1:
                self._processor.get_cluster(
                    LengthPatternCluster).add(piece_bag)
                return
            else:
                viewer = ldsf_viewer
                p_cls = LastDotSplitFuzzyPatternCluster
        else:
            self._processor.get_cluster(
                LengthPatternCluster).add(piece_bag)
            return

        self._processor.get_cluster(p_cls).add(
            ViewerPieceBag(viewer, piece_bag))


class LastDotSplitFuzzyPatternCluster(MultiPatternCluster):

    def _add_to_forward_cluster(self, viewer_piece_bag):
        self._processor.get_cluster(LengthPatternCluster).add(
            viewer_piece_bag.piece_bag)


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

    def _update_patterns(self):
        for bucket in self._cached:
            for piece_bag in bucket:
                self._patterns.add(piece_bag.pick().pattern)

    def cluster(self):
        if self._force_pattern:
            self._set_pattern(self._cached)
        else:
            if self._cached.count < self._min_cluster_num:
                self._update_patterns()
                return
            max_count = max(self._cached, key=lambda x: x.count).count
            if confused(self._cached.count, max_count, self._min_cluster_num):
                self._set_pattern(self._cached)
            else:
                self._update_patterns()

    def _set_pattern(self, package):
        if self._fuzzy_pattern is None:
            self._fuzzy_pattern = Pattern(
                wildcard_rule(package.pick().parsed_piece.fuzzy_rule))
            self._patterns.add(self._fuzzy_pattern)
        package.set_pattern(self._fuzzy_pattern)


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


CLUSTER_CLASSES = [PiecePatternCluster,
                   BasePatternCluster,
                   MixedPatternCluster,
                   LastDotSplitFuzzyPatternCluster,
                   LengthPatternCluster,
                   FuzzyPatternCluster]


class ClusterProcessor(object):
    def __init__(self, config, meta_info, pre_level_processor):
        self._config = config
        self._meta_info = meta_info
        self._pattern_clusters = OrderedDict(
            [(c.__name__, c(self)) for c in CLUSTER_CLASSES])
        self._pre_level_processor = pre_level_processor
        self._next_level_processors = {}

    @property
    def next_level_processors(self):
        return self._next_level_processors.values()

    def _backward_package(self, package):
        bucket = PieceBagBucket()
        for p_node in package.p_nodes:
            if p_node.piece in bucket:
                continue
            bucket.add(p_node)
        return bucket

    def seek_cluster(self, package):
        if self._pre_level_processor is None:
            return False
        for c in itervalues(self._pattern_clusters):
            res = c.seek_cluster(package)
            if res == SeekResult.FOUND:
                return True
            elif res == SeekResult.IMPOSSIBLE:
                break
            elif res == SeekResult.BACKWARD:
                pack = self._backward_package(package)
                return self._pre_level_processor.seek_cluster(pack)
            elif res == SeekResult.UNKNOW:
                continue
            else:
                raise ValueError('invalid seek result')

        return False

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

    def _process(self):
        for c in self._pattern_clusters.itervalues():
            c.cluster()

    def add(self, node, add_children=False):
        c = self.get_cluster(PiecePatternCluster)
        if add_children:
            for child in node.iter_children():
                c.add(child)
        else:
            c.add(node)

    @property
    def pattern_num(self):
        return sum([c.pattern_num for c in itervalues(self._pattern_clusters)])

    def process(self):
        self._process()
        if self._meta_info.is_last_level():
            return

        self._create_next_level_processors()

        for processor in itervalues(self._next_level_processors):
            processor.process()

    def _create_next_level_processors(self):

        pp_cluster = self.get_cluster(PiecePatternCluster)
        processors = self._next_level_processors

        for node in pp_cluster.iter_nodes():
            pattern = node.pattern
            if pattern not in processors:
                processors[pattern] = ClusterProcessor(
                    self._config, self._meta_info.next_level_meta_info(), self)
            processor = processors[pattern]
            processor.add(node, add_children=True)


def split_by_pattern(url_meta, piece_pattern_tree):
    trees = {}
    for path in piece_pattern_tree.dump_paths():
        pid = digest(url_meta, [p.pattern for p in path[1:]])
        if pid not in trees:
            trees[pid] = PiecePatternTree()
        tree = trees[pid]
        tree.add_from_piece_pattern_node_path(path[1:])

    return itervalues(trees)


def _can_be_splited(processor):
    while True:
        pattern_num = processor.pattern_num
        if pattern_num > 1:
            return True
        l = len(processor.next_level_processors)
        if l <= 0:
            break
        elif l > 1:
            return True
        processor = processor.next_level_processors[0]

    return False


def process(config, url_meta, piece_pattern_tree, **kwargs):
    meta_info = MetaInfo(url_meta, 0)
    processor = ClusterProcessor(config, meta_info, None)
    processor.add(piece_pattern_tree.root)
    processor.process()
    return _can_be_splited(processor)


def cluster(config, url_meta, piece_pattern_tree, **kwargs):
    if not process(config, url_meta, piece_pattern_tree, **kwargs):
        yield piece_pattern_tree
        return
    for sub_piece_pattern_tree in split_by_pattern(url_meta, piece_pattern_tree):
        for tree in cluster(config, url_meta, sub_piece_pattern_tree, **kwargs):
            yield tree
