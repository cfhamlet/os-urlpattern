from pattern import Pattern
from urlparse_utils import ParsedPiece


class ClusterNode(object):
    __slots__ = ('_node', '_cluster_name')

    def __init__(self, node, cluster_name=''):
        self._node = node
        self._cluster_name = cluster_name

    @property
    def node(self):
        return self._node

    @property
    def cluster_name(self):
        return self._cluster_name

    @property
    def count(self):
        return self._node.count

    def set_pattern(self, pattern, cluster_name):
        self._node.set_pattern(pattern)
        self._cluster_name = cluster_name


class ClusterNodeView(object):
    __slots__ = ('_cluster_node')

    def __init__(self, cluster_node):
        self._cluster_node = cluster_node

    @property
    def cluster_node(self):
        return self._cluster_node

    def view(self):
        raise NotImplementedError

    def parsed_pieces(self):
        raise NotImplementedError

    @property
    def cluster_name(self):
        return self._cluster_node.cluster_name

    @property
    def count(self):
        return self._cluster_node.count

    def set_pattern(self, pattern, cluster_name):
        self._cluster_node.set_pattern(pattern, cluster_name)


class PieceView(ClusterNodeView):
    def view(self):
        return self._cluster_node.node.piece

    def parsed_pieces(self):
        parsed_piece = self._cluster_node.node.parsed_piece
        if len(parsed_piece.rules) <= 1:
            return [parsed_piece]

        return [ParsedPiece([piece], [rule])
                for piece, rule in zip(parsed_piece.pieces, parsed_piece.rules)]


class LengthView(ClusterNodeView):
    def view(self):
        return self._cluster_node.node.parsed_piece.piece_length


class FuzzyView(ClusterNodeView):
    def view(self):
        return self._cluster_node.node.parsed_piece.fuzzy_rule


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

    @property
    def count(self):
        return self._count

    def set_pattern(self, pattern, cluster_name):
        for bag in self._packs.itervalues():
            bag.set_pattern(pattern, cluster_name)


class ViewPack(object):
    def __init__(self, view_class):
        self._view_class = view_class
        self._packs = {}
        self._count = 0

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

    def add_node(self, cluster_node):
        self._view_pack.add_node(cluster_node)

    def iter_nodes(self):
        for node_view in self._view_pack.iter_nodes():
            yield node_view.cluster_node

    def cluster(self):
        pass

    def set_pattern(self, obj, pattern):
        obj.set_pattern(pattern, self._cluster_name)

    def create_cluster(self, cluster_cls):
        c = cluster_cls(self._config, self._meta_info)
        for cluster_node in self.iter_nodes():
            c.add_node(cluster_node)


class PiecePatternCluster(PatternCluster):
    def __init__(self, config, meta_info):
        super(PiecePatternCluster, self).__init__(config, meta_info)
        self._view_pack = ViewPack(PieceView)

    def cluster(self):
        for piece, pack in self._view_pack.iter_items():
            if pack.count >= self._min_cluster_num:
                self.set_pattern(pack, Pattern(piece))
        if len(self._view_pack) < self._min_cluster_num:
            return

        next_cluster_cls = LengthPatternCluster
        for node_view in self._view_pack.iter_nodes():
            if len(node_view.parsed_pieces()) > 1:
                next_cluster_cls = BasePatternCluster
                break

        return self.create_cluster(next_cluster_cls)


class LengthPatternCluster(PatternCluster):
    def __init__(self, config, meta_info):
        super(LengthPatternCluster, self).__init__(config, meta_info)
        self._view_pack = ViewPack(LengthView)

    def cluster(self):
        for length, pack in self._view_pack.iter_items():
            pass

        if len(self._view_pack) < self._min_cluster_num:
            return
        return self.create_cluster(FuzzyPatternCluster)


class BasePatternCluster(PatternCluster):
    pass


class MixedPatternCluster(PatternCluster):
    pass


class LastDotSplitFuzzyPatternCluster(PatternCluster):
    pass


class FuzzyPatternCluster(PatternCluster):
    pass


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
