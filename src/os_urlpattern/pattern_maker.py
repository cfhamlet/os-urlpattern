"""Pattern clustering procedure APIs.
"""
from .compat import itervalues
from .config import get_default_config
from .definition import BasePattern
from .parse_utils import EMPTY_PARSED_PIECE, ParsedPiece
from .parser import fuzzy_digest, parse
from .pattern_cluster import cluster
from .piece_pattern_node import PiecePatternNode, build_from_parsed_pieces
from .utils import TreeNode, build_tree, dump_tree, pick


class PatternMaker(object):
    """Scaffold for simplifying clustering.

    After load urls, iterate all sub makers make cluster
    individually or cluster all by calling make method.
    """

    def __init__(self, config=None):
        self._config = get_default_config() if config is None else config
        self._makers = {}

    @property
    def makers(self):
        """iterable: For iterating all sub makers."""
        return itervalues(self._makers)

    def load(self, url, meta=None):
        """Load url and meta.

        Args:
            url (str): The URL to be loaded.
            meta (object, optional): Defaults to None. Meta data will be
                merged at each cluster and can be accessed by clustered
                node's meta property.

        Returns:
            tuple: 2-tules, (node, is_new).
        """
        url_meta, parsed_pieces = parse(url)
        if not isinstance(parsed_pieces[0], ParsedPiece):
            raise ValueError('Invalid URL')
        sid = fuzzy_digest(url_meta, parsed_pieces)
        if sid not in self._makers:
            self._makers[sid] = Maker(url_meta, self._config)
        return self._makers[sid].load(parsed_pieces, meta=meta)

    def make(self, combine=False):
        """Iterate all sub makers, start clustering and yield clustered.

        Args:
            combine (bool, optional): Defaults to False. Combine the
                same url_meta clusters into a patten tree.

        Yields:
            tuple: 2-tuple, (url_meta, clustered). The clustered is the
                root of a clustered tree.
        """
        for maker in self.makers:
            for clustered in maker.make(combine):
                yield maker.url_meta, clustered


class Maker(object):
    """Low-level APIs for clustering.

    Suppose this will only be used for same fuzzy-digest clustering.
    """

    def __init__(self, url_meta, config=None):
        self._url_meta = url_meta
        self._config = get_default_config() if config is None else config
        self._root = PiecePatternNode((EMPTY_PARSED_PIECE, None))

    @property
    def url_meta(self):
        """URLMeta: The URLMeta object."""
        return self._url_meta

    def load(self, parsed_pieces, meta=None):
        """Load parsed pieces and meta.

        Args:
            parsed_pieces (list): The parsed pieces to be loaded.
            meta (object, optional): Defaults to None. Meta data will be
                merged at each cluster and can be accessed by clustered
                node's meta property.

        Returns:
            tuple: 2-tules, (node, is_new).
        """
        return build_from_parsed_pieces(self._root,
                                        parsed_pieces,
                                        meta=meta)

    def _cluster(self):
        for clustered in cluster(self._config,
                                 self._url_meta,
                                 self._root):
            yield clustered

    def _combine_clusters(self):
        root = TreeNode(BasePattern.EMPTY)
        for clustered in self._cluster():
            nodes = pick(dump_tree(clustered))
            build_tree(root, [(n.pattern, n.pattern)
                              for n in nodes[1:]], nodes[0].count)

        yield root

    def make(self, combine=False):
        """Start clustering and yield clustered.

        Args:
            combine (bool, optional): Defaults to False. Combine the
                clusters into a patten tree.

        Yields:
            TreeNode: Root of the clustered tree. If combine=False yield
                all clustered parsed piece trees otherwise yield a
                combined pattern tree.
        """
        if combine:
            return self._combine_clusters()
        return self._cluster()
