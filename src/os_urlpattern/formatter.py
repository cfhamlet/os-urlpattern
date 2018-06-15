import json

from .compat import StringIO
from .definition import BasePatternRule, Symbols
from .parse_utils import pack
from .utils import get_ete_tree


class Formatter(object):

    def format(self, url_meta, tree, **kwargs):
        pass


class PatternFormatter(Formatter):
    def format(self, url_meta, clusterd_tree, **kwargs):
        for node_path in clusterd_tree.dump_paths():
            yield pack(url_meta, [p.pattern for p in node_path[1:]])
            break


class ClusterFormatter(PatternFormatter):
    def format(self, url_meta, clusterd_tree, **kwargs):
        for r in super(ClusterFormatter, self).format(url_meta, clusterd_tree, **kwargs):
            yield r

        for node_path in clusterd_tree.dump_paths():
            for url in node_path[-1].extra_data:
                yield u'\t'.join((u'', url))


class JsonFormatter(Formatter):
    def format(self, url_meta, clusterd_tree, **kwargs):
        for node_path in clusterd_tree.dump_paths():
            p = pack(url_meta, [p.pattern for p in node_path[1:]])
            yield json.dumps({'ptn': p, 'cnt': clusterd_tree.count})
            break


class ETEFormatter(Formatter):
    def format(self, url_meta, pattern_tree, **kwargs):

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

        if pattern_tree.root.count <= 0:
            return

        ete_tree = get_ete_tree(pattern_tree.root, format=f)
        yield ete_tree.get_ascii(show_internal=True)


FORMATTERS = {
    'PATTERN': PatternFormatter,
    'CLUSTER': ClusterFormatter,
    'JSON': JsonFormatter,
}
try:
    import ete3
    FORMATTERS['ETE'] = ETEFormatter
except:
    pass
