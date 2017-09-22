import hashlib
from os_urlpattern.urlparse_utils import parse_url
from os_urlpattern.piece_pattern_parser import PiecePatternParser
from os_urlpattern.piece_pattern_tree import PiecePatternTree
from os_urlpattern.combine import combine
from os_urlpattern.pattern_tree import PatternTree


class PatternMaker(object):
    def __init__(self, config):
        self._config = config
        self._parser = PiecePatternParser()
        self._makers = {}

    def _uniq_hash(self, url_meta, piece_patterns):
        meta_hash = url_meta.hashcode
        pp_hash = '/'.join([pp.fuzzy_pattern.pattern_string for pp in piece_patterns])
        pp_hash = hashlib.md5(pp_hash).hexdigest().upper()
        return '-'.join((meta_hash, pp_hash))

    def load(self, url):
        url_meta, pieces = parse_url(url)
        piece_patterns = [self._parser.parse(piece) for piece in pieces]
        u_hash = self._uniq_hash(url_meta, piece_patterns)
        if u_hash not in self._makers:
            self._makers[u_hash] = Maker(self._config, url_meta)
        self._makers[u_hash].load(piece_patterns)

    def process_and_dump(self):
        for maker in self._makers.values():
            pattern_tree = maker.make()
            for pattern_path in pattern_tree.dumps():
                yield pattern_path


class Maker(object):
    def __init__(self, config, url_meta):
        self._config = config
        self._url_meta = url_meta
        self._piece_pattern_tree = PiecePatternTree(url_meta)

    def load(self, piece_patterns, count=1, uniq_path=True):
        self._piece_pattern_tree.add_piece_patterns(
            piece_patterns, count, uniq_path)

    def _path_dump_and_load(self, src, dest, index=0):
        for path in src.dump_paths():
            if path:
                dest.load_path(path[index:])

    def make(self):
        pattern_tree = PatternTree(self._url_meta)
        combine(self._config, self._piece_pattern_tree)
        self._path_dump_and_load(self._piece_pattern_tree, pattern_tree, 1)
        return pattern_tree
