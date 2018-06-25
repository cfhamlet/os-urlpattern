from collections import Counter, OrderedDict, namedtuple

from .compat import itervalues
from .parse_utils import (EMPTY_PARSED_PIECE, URLMeta, specify_rule,
                          wildcard_rule)
from .parsed_piece_view import BaseView, LastDotSplitFuzzyView, MixedView
from .pattern import Pattern
from .piece_pattern_node import (PiecePatternNode, build_from_parsed_pieces,
                                 build_from_piece_pattern_nodes)
from .utils import Bag, cached_property, dump_tree, pick


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
        return iter(itervalues(self._objs))

    def add(self, obj):
        raise NotImplementedError


class PieceBag(TBag):
    """A bag contain all of the nodes with same piece.

    The nodes should on the same branch of a tree at the same level.
    """

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


class ViewPieceBag(namedtuple('ViewPieceBag', ['view', 'piece_bag'])):
    __slots__ = ()

    def set_pattern(self, pattern):
        return self.piece_bag.set_pattern(pattern)


class ViewPieceBagBucket(PieceBagBucket):
    def __init__(self, url_meta):
        super(ViewPieceBagBucket, self).__init__()
        self._url_meta = url_meta
        self._root = PiecePatternNode((EMPTY_PARSED_PIECE, None))

    def add(self, view_piece_bag, build_tree=True):
        piece_bag = view_piece_bag.piece_bag
        self._objs[piece_bag.pick().piece] = view_piece_bag
        self.stats['count'] += piece_bag.count

        if not build_tree:
            return
        view = view_piece_bag.view

        build_from_parsed_pieces(
            self._root, view.parsed_pieces, count=piece_bag.count, uniq=False)

    def cluster(self, config, **kwargs):
        for clustered in cluster(config, self._url_meta, self._root, **kwargs):
            yield self._transfer(clustered)

    def _transfer(self, root):
        pattern = None
        bucket = ViewPieceBagBucket(self._url_meta)
        for nodes in dump_tree(root):
            piece = u''.join([p.piece for p in nodes[1:]])
            view_piece_bag = self[piece]
            bucket.add(view_piece_bag, False)
            if pattern is None:
                pattern = Pattern(
                    u''.join([str(p.pattern) for p in nodes[1:]]))
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
    """Base class of cluster."""

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
        if not self._bucket:
            return
        procesor = self._processor
        if procesor.is_last_level() \
                and 'last_path_as_pattern' in procesor.kwargs \
                and procesor.kwargs['last_path_as_pattern']:
            for piece_bag in self._bucket:
                self._set_pattern(piece_bag, True)
            return

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

        view = BaseView(parsed_piece)
        p_cls = BasePatternCluster
        vl = len(view.parsed_pieces)

        if vl == 3 and self._processor.is_last_path():
            ldsf_view = LastDotSplitFuzzyView(parsed_piece)
            if view == ldsf_view:
                view = ldsf_view
                p_cls = LastDotSplitFuzzyPatternCluster
        elif vl > 3:
            mixed_view = MixedView(parsed_piece)
            mvl = len(mixed_view.parsed_pieces)
            if mvl == 1:
                self._processor.get_cluster(
                    LengthPatternCluster).add(piece_bag)
                return
            elif vl - mvl >= self._min_cluster_num:
                if mvl == 3 and self._processor.is_last_path():
                    ldsf_view = LastDotSplitFuzzyView(parsed_piece)
                    if mixed_view == ldsf_view:
                        view = ldsf_view
                        p_cls = LastDotSplitFuzzyPatternCluster
                    else:
                        view = mixed_view
                        p_cls = MixedPatternCluster
                else:
                    view = mixed_view
                    p_cls = MixedPatternCluster

        self._processor.get_cluster(p_cls).add(
            ViewPieceBag(view, piece_bag))


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
        pattern = Pattern(specify_rule(parsed_piece.fuzzy_rule, length))
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
            for b, pattern in self._cluster(bucket):
                if self._as_cluster(b, pattern):
                    self._set_pattern(b, pattern)
                else:
                    self._to_forward_cluster(b)

    def _cluster(self, bucket):
        for b, pattern in bucket.cluster(self._processor.config):
            yield b, pattern

    def _to_forward_cluster(self, bucket):
        for view_piece_bag in bucket:
            self._add_to_forward_cluster(view_piece_bag)

    def _add_to_forward_cluster(self, view_piece_bag):
        pass

    def _as_cluster(self, bucket, pattern):
        if bucket.count < self._min_cluster_num:
            return False
        return True

    def _set_pattern(self, bucket, pattern):
        bucket.set_pattern(pattern)
        self._patterns.add(pattern)

    def add(self, view_piece_bag):
        view = view_piece_bag.view
        if view not in self._buckets:
            url_meta = URLMeta(len(view.parsed_pieces), [], False)
            self._buckets[view] = ViewPieceBagBucket(url_meta)
        self._buckets[view].add(view_piece_bag)


class BasePatternCluster(MultiPatternCluster):

    def _add_to_forward_cluster(self, view_piece_bag):
        view = view_piece_bag.view
        piece_bag = view_piece_bag.piece_bag
        parsed_piece = piece_bag.pick().parsed_piece

        mixed_view = MixedView(parsed_piece)
        mvl = len(mixed_view.parsed_pieces)

        p_cls = MixedPatternCluster

        if view == mixed_view:
            if self._processor.is_last_path():
                ldsf_view = LastDotSplitFuzzyView(parsed_piece)
                if len(ldsf_view.parsed_pieces) == 1:
                    self._processor.get_cluster(
                        LengthPatternCluster).add(piece_bag)
                    return
                else:
                    view = ldsf_view
                    p_cls = LastDotSplitFuzzyPatternCluster
            else:
                self._processor.get_cluster(
                    LengthPatternCluster).add(piece_bag)
                return
        else:
            view = mixed_view
            if mvl == 1:
                self._processor.get_cluster(
                    LengthPatternCluster).add(piece_bag)
                return
            elif mvl == 3 and self._processor.is_last_path():
                ldsf_view = LastDotSplitFuzzyView(parsed_piece)
                if mixed_view == ldsf_view:
                    view = ldsf_view
                    p_cls = LastDotSplitFuzzyPatternCluster

        self._processor.get_cluster(p_cls).add(
            ViewPieceBag(view, piece_bag))


class MixedPatternCluster(MultiPatternCluster):

    def _add_to_forward_cluster(self, view_piece_bag):
        view = view_piece_bag.view
        piece_bag = view_piece_bag.piece_bag
        parsed_piece = piece_bag.pick().parsed_piece

        if self._processor.is_last_path():
            ldsf_view = LastDotSplitFuzzyView(parsed_piece)
            if len(ldsf_view.parsed_pieces) == 1:
                self._processor.get_cluster(
                    LengthPatternCluster).add(piece_bag)
                return
            else:
                view = ldsf_view
                p_cls = LastDotSplitFuzzyPatternCluster
        else:
            self._processor.get_cluster(
                LengthPatternCluster).add(piece_bag)
            return

        self._processor.get_cluster(p_cls).add(
            ViewPieceBag(view, piece_bag))


class LastDotSplitFuzzyPatternCluster(MultiPatternCluster):

    def _cluster(self, bucket):
        for b, pattern in bucket.cluster(self._processor.config,
                                         last_path_as_pattern=True):
            yield b, pattern

    def _add_to_forward_cluster(self, view_piece_bag):
        self._processor.get_cluster(LengthPatternCluster).add(
            view_piece_bag.piece_bag)


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


CLUSTER_CLASSES = [PiecePatternCluster,
                   BasePatternCluster,
                   MixedPatternCluster,
                   LastDotSplitFuzzyPatternCluster,
                   LengthPatternCluster,
                   FuzzyPatternCluster]


class ClusterProcessor(object):
    def __init__(self, config, url_meta, pre_level_processor, **kwargs):
        self._config = config
        self._url_meta = url_meta
        self._pattern_clusters = OrderedDict(
            [(c.__name__, c(self)) for c in CLUSTER_CLASSES])
        self._pre_level_processor = pre_level_processor
        self._next_level_processors = {}
        self._kwargs = kwargs

    @cached_property
    def level(self):
        l = 0
        n = self.pre_level_processor
        while n is not None:
            l += 1
            n = n.pre_level_processor
        return l

    def is_last_level(self):
        return self._url_meta.depth == self.level

    def is_last_path(self):
        return self._url_meta.path_depth == self.level

    @property
    def kwargs(self):
        return self._kwargs

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
    def config(self):
        return self._config

    @property
    def pre_level_processor(self):
        return self._pre_level_processor

    def _process(self):
        for c in itervalues(self._pattern_clusters):
            c.cluster()

    def add(self, node, add_children=False):
        c = self.get_cluster(PiecePatternCluster)
        if add_children:
            for child in node.children:
                c.add(child)
        else:
            c.add(node)

    @property
    def pattern_num(self):
        return sum([c.pattern_num for c in itervalues(self._pattern_clusters)])

    def process(self):
        self._process()
        if self.is_last_level():
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
                    self._config,
                    self._url_meta,
                    self, **self.kwargs)
            processor = processors[pattern]
            processor.add(node, add_children=True)


def split_by_pattern(root):
    """Split the piece pattern tree by pattern path.

    Args:
        root (PiecePatternNode): The root of piece pattern tree.

    Returns:
        iterator: Iterator of sub-trees.
    """
    tree_roots = {}
    for nodes in dump_tree(root):
        pid = hash(u"/".join([str(p.pattern) for p in nodes]))
        if pid not in tree_roots:
            tree_roots[pid] = PiecePatternNode((EMPTY_PARSED_PIECE, None))
        sub_root = tree_roots[pid]
        build_from_piece_pattern_nodes(sub_root, nodes[1:])

    return itervalues(tree_roots)


def _can_be_splited(processor):
    """Check whether the processor tree can be splited.

    Args:
        processor (ClusterProcessor): The root node of cluster processor.

    Returns:
        bool: Whether the processor tree can be splited.
    """
    while True:
        pattern_num = processor.pattern_num
        if pattern_num > 1:
            return True
        l = len(processor.next_level_processors)
        if l <= 0:
            break
        elif l > 1:
            return True
        processor = pick(processor.next_level_processors)

    return False


def process(config, url_meta, root, **kwargs):
    """Start clustering.

    Args:
        config (Config): The configure object.
        url_meta (URLMeta): The URLMeta object.
        root (PiecePatternNode): The root of the piece pattern tree.
        **kwargs: Keyword arguments.

    Returns:
        bool: Whether the clustered tree can be split.
    """
    processor = ClusterProcessor(config, url_meta, None, **kwargs)
    processor.add(root)
    processor.process()
    return _can_be_splited(processor)


def cluster(config, url_meta, root, **kwargs):
    """Entrance of the cluster workflow.

    Args:
        config (Config): The configure object.
        url_meta (URLMeta): The URLMeta object.
        root (PiecePatternNode): The root of the piece pattern tree.
        **kwargs: Keyword arguments.

    Yields:
        PiecePatternNode: The clusterd sub piece pattern tree root.

    """
    if not process(config, url_meta, root, **kwargs):
        yield root
        return
    for sub_root in split_by_pattern(root):
        for clustered in cluster(config, url_meta, sub_root, **kwargs):
            yield clustered
