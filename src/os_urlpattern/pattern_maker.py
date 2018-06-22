from .compat import itervalues
from .definition import BasePattern
from .parse_utils import EMPTY_PARSED_PIECE, PieceParser, analyze_url, digest
from .pattern_cluster import cluster
from .piece_pattern_node import PiecePatternNode, build_from_parsed_pieces
from .utils import TreeNode, build_tree, dump_tree


class PatternMaker(object):
    def __init__(self, config):
        self._config = config
        self._parser = PieceParser()
        self._makers = {}
        self._drop_url = self._config.getboolean('make', 'drop_url')

    @property
    def makers(self):
        return itervalues(self._makers)

    def load(self, url):
        url_meta, pieces = analyze_url(url)
        parsed_pieces = [self._parser.parse(piece) for piece in pieces]
        sid = digest(url_meta, [p.fuzzy_rule for p in parsed_pieces])
        if sid not in self._makers:
            self._makers[sid] = Maker(self._config, url_meta)
        return self._makers[sid].load(parsed_pieces,
                                      meta=url if not self._drop_url else None)

    def make(self, combine=False):
        for maker in self.makers:
            for url_meta, clustered in maker.make(combine):
                yield url_meta, clustered


class Maker(object):
    def __init__(self, config, url_meta):
        self._config = config
        self._url_meta = url_meta
        self._root = PiecePatternNode(EMPTY_PARSED_PIECE)

    def load(self, parsed_pieces, count=1, meta=None, uniq=True):
        return build_from_parsed_pieces(self._root,
                                        parsed_pieces,
                                        count=count,
                                        meta=meta,
                                        uniq=uniq)

    def _cluster(self):
        for clustered in cluster(self._config,
                                 self._url_meta,
                                 self._root):
            yield clustered

    def _combine_clusters(self):
        root = TreeNode(BasePattern.EMPTY)
        for clustered in self._cluster():
            for nodes in dump_tree(clustered):
                build_tree(root, [(n.pattern, n.pattern)
                                  for n in nodes[1:]], nodes[-1].count)
        return root

    def _make(self, combine=False):
        if combine:
            yield self._combine_clusters()
        else:
            for clustered in self._cluster():
                yield clustered

    def make(self, combine=False):
        for clustered in self._make(combine):
            yield self._url_meta, clustered
