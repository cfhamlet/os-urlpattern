import json

from .compat import StringIO
from .definition import BasePatternRule, Symbols
from .pattern_tree import PatternPath, PatternTree
from .utils import get_ete_tree


class Formatter(object):

    def format(self, pattern_tree, **kwargs):
        pass


class PatternPathEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, PatternPath):
            return {'cnt': o.count, 'ptn': o.pattern_path_string}
        return json.JSONEncoder.default(o)


class JsonFormatter(Formatter):
    def format(self, pattern_tree, **kwargs):
        dump_isolate_pattern = kwargs.get("dump_isolate_pattern", True)
        for pattern_path in pattern_tree.dumps():
            if pattern_path.count <= 1 and not dump_isolate_pattern:
                continue
            yield json.dumps(pattern_path, cls=PatternPathEncoder)


class ETEFormatter(Formatter):
    def format(self, pattern_tree, **kwargs):
        dump_isolate_pattern = kwargs.get("dump_isolate_pattern", True)
        url_meta = pattern_tree.url_meta

        def f(pattern_node):
            sep = Symbols.EMPTY
            query_key = Symbols.EMPTY
            if url_meta.path_depth < pattern_node.current_level <= (url_meta.path_depth + url_meta.query_depth):
                sep = Symbols.AMPERSAND
                if pattern_node.current_level == url_meta.path_depth + 1:
                    sep = BasePatternRule.SINGLE_QUESTION
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
        if not dump_isolate_pattern:
            for pattern_path in root_node.dump_paths():
                if pattern_path[-1].count <= 1:
                    continue
                o_pattern_tree.load_path(pattern_path[1:])
            root_node = o_pattern_tree.root
        if root_node.count <= 0:
            return

        ete_tree = get_ete_tree(root_node, format=f)
        yield ete_tree.get_ascii(show_internal=True)


FORMATTERS = {'JSON': JsonFormatter}
try:
    import ete3
    FORMATTERS['ETE'] = ETEFormatter
except:
    pass
