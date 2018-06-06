import json

from .definition import Symbols
from .pattern_tree import PatternPath, PatternTree
from .utils import get_ete_tree


class Formatter(object):
    def __init__(self, config):
        self._config = config
        self._dump_isolate_pattern = self._config.getboolean(
            'make', 'dump_isolate_pattern')

    def format(self, pattern_tree):
        pass


class PatternPathEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, PatternPath):
            return {'count': o.count, 'pat': o.pattern_path_string, 'pid': o.pattern_id}
        return json.JSONEncoder.default(o)


class JsonFormatter(Formatter):
    def format(self, pattern_tree):
        for pattern_path in pattern_tree.dumps():
            if pattern_path.count <= 1 and not self._dump_isolate_pattern:
                continue
            print(json.dumps(pattern_path, cls=PatternPathEncoder))


class ETEFormatter(Formatter):
    def format(self, pattern_tree):
        url_meta = pattern_tree.url_meta

        def f(pattern_node):
            sep = Symbols.EMPTY
            query_key = Symbols.EMPTY
            if url_meta.path_depth < pattern_node.current_level <= (url_meta.path_depth + url_meta.query_depth):
                sep = Symbols.AMPERSAND
                if pattern_node.current_level == url_meta.path_depth + 1:
                    sep = u'[\\?]'
                query_key = url_meta.query_keys[pattern_node.current_level -
                                                url_meta.path_depth - 1]
            elif pattern_node.current_level == url_meta.path_depth + url_meta.query_depth + 1:
                sep = Symbols.NUMBER
            return u' {sep}{query_key}{pattern_string}({count}) '.format(
                count=pattern_node.count,
                pattern_string=pattern_node,
                query_key=query_key,
                sep=sep)
        root_node = pattern_tree.root
        o_pattern_tree = PatternTree(url_meta)
        if not self._dump_isolate_pattern:
            for pattern_path in root_node.dump_paths():
                if pattern_path[-1].count <= 1:
                    continue
                o_pattern_tree.load_path(pattern_path[1:])
            root_node = o_pattern_tree.root
        if root_node.count <= 0:
            return

        ete_tree = get_ete_tree(root_node, format=f)
        print(ete_tree.get_ascii(show_internal=True))


FORMATTERS = {'JSON': JsonFormatter}
try:
    import ete3
    FORMATTERS['ETE'] = ETEFormatter
except:
    pass
