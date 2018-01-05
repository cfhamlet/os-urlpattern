from os_urlpattern.urlparse_utils import parse_url, struct_id, PieceParser
from os_urlpattern.piece_pattern_tree import PiecePatternTree
from os_urlpattern.pattern_tree import PatternTree


class PatternMaker(object):
    def __init__(self, config):
        self._config = config
        self._parser = PieceParser()
        self._makers = {}
        self._cluster_method = self._load_cluster_method()

    def _load_cluster_method(self):
        from importlib import import_module
        module_path, method_name = self._config.get(
            'make', 'cluster_method').rsplit('.', 1)
        mod = import_module(module_path)
        return getattr(mod, method_name)

    def load(self, url):
        url_meta, pieces = parse_url(url)
        parsed_pieces = [self._parser.parse(piece) for piece in pieces]
        sid = struct_id(url_meta, parsed_pieces)
        if sid not in self._makers:
            self._makers[sid] = Maker(self._config, url_meta, self._cluster_method)
        return self._makers[sid].load(parsed_pieces)

    def process(self):
        for maker in self._makers.values():
            yield maker.make()

    def process_and_dump(self):
        for pattern_tree in self.process():
            for pattern_path in pattern_tree.dumps():
                yield pattern_path


class Maker(object):
    def __init__(self, config, url_meta, cluster_method):
        self._config = config
        self._url_meta = url_meta
        self._piece_pattern_tree = PiecePatternTree()
        self._cluster_method = cluster_method

    def load(self, parsed_pieces, count=1, uniq_path=True):
        return self._piece_pattern_tree.add_from_parsed_pieces(
            parsed_pieces, count, uniq_path)

    def _path_dump_and_load(self, src, dest, index=0):
        for path in src.dump_paths():
            if path:
                dest.load_path(path[index:])

    def make(self):
        self._cluster_method(self._config, self._url_meta,
                             self._piece_pattern_tree)

        pattern_tree = PatternTree(self._url_meta)
        self._path_dump_and_load(self._piece_pattern_tree, pattern_tree, 1)
        return pattern_tree
