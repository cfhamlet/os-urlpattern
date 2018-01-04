import hashlib
from os_urlpattern.urlparse_utils import parse_url
from os_urlpattern.piece_parser import PieceParser
from os_urlpattern.piece_pattern_tree import PiecePatternTree
from os_urlpattern.combine import combine
from os_urlpattern.pattern_tree import PatternTree


class PatternMaker(object):
    def __init__(self, config):
        self._config = config
        self._parser = PieceParser()
        self._makers = {}

    def _struct_hash(self, url_meta, parsed_pieces):
        meta_hash = url_meta.hashcode
        pieces_hash = hashlib.md5(
            '/'.join([''.join(sorted(set(p.rules))) for p in parsed_pieces])).hexdigest()
        return '-'.join((meta_hash, pieces_hash))

    def load(self, url):
        url_meta, pieces = parse_url(url)
        parsed_pieces = [self._parser.parse(piece) for piece in pieces]
        struct_hash = self._struct_hash(url_meta, parsed_pieces)
        if struct_hash not in self._makers:
            self._makers[struct_hash] = Maker(self._config, url_meta)
        return self._makers[struct_hash].load(parsed_pieces)

    def process(self):
        for maker in self._makers.values():
            yield maker.make()

    def process_and_dump(self):
        for pattern_tree in self.process():
            for pattern_path in pattern_tree.dumps():
                yield pattern_path


class Maker(object):
    def __init__(self, config, url_meta):
        self._config = config
        self._url_meta = url_meta
        self._piece_pattern_tree = PiecePatternTree()

    def load(self, parsed_pieces, count=1, uniq_path=True):
        return self._piece_pattern_tree.add_from_parsed_pieces(
            parsed_pieces, count, uniq_path)

    def _path_dump_and_load(self, src, dest, index=0):
        for path in src.dump_paths():
            if path:
                dest.load_path(path[index:])

    def make(self):
        #        combine(self._config, self._url_meta, self._piece_pattern_tree)

        pattern_tree = PatternTree(self._url_meta)
        self._path_dump_and_load(self._piece_pattern_tree, pattern_tree, 1)
        return pattern_tree
