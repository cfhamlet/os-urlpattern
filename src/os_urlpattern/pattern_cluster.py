class PatternCluster(object):
    def __init__(self, config, meta_info):
        self._config = config
        self._meta_info = meta_info

    def add_node(self, node):
        pass

    def cluster(self):
        pass


class PiecePatternCluster(PatternCluster):
    def iter_nodes(self):
        pass


class LengthPatternCluster(PatternCluster):
    pass


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
        self._piece_pattern_cluster = PiecePatternCluster(config, meta_info)

    def iter_nodes(self):
        return self._piece_pattern_cluster.iter_nodes()

    def add_node(self, node):
        self._piece_pattern_cluster.add_node(node)

    def _process(self):
        c = self._piece_pattern_cluster
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
