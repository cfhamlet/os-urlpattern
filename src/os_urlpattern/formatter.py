import json
from os_urlpattern.pattern_tree import PatternPath
from os_urlpattern.utils import get_ete_tree


class Formatter(object):
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
            print(json.dumps(pattern_path, cls=PatternPathEncoder))


class ETEFormatter(Formatter):
    def format(self, pattern_tree):
        url_meta = pattern_tree.url_meta

        def f(pattern_node):
            sep = ''
            query_key = ''
            if url_meta.path_depth < pattern_node.current_level <= (url_meta.path_depth + url_meta.query_depth):
                sep = '&'
                if pattern_node.current_level == url_meta.path_depth + 1:
                    sep = '[\\?]'
                query_key = url_meta.query_keys[pattern_node.current_level -
                                                url_meta.path_depth - 1]
            elif pattern_node.current_level == url_meta.path_depth + url_meta.query_depth + 1:
                sep = '#'
            return ' {sep}{query_key}{pattern_string}({count}) '.format(
                count=pattern_node.count,
                pattern_string=pattern_node,
                query_key=query_key,
                sep=sep)
        ete_tree = get_ete_tree(pattern_tree.root_node, format=f)
        print(ete_tree.get_ascii(show_internal=True))


FORMATTERS = {'JSON': JsonFormatter()}
try:
    import ete3
    FORMATTERS['ETE'] = ETEFormatter()
except:
    pass
