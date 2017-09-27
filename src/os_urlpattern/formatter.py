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
        ete_tree = get_ete_tree(pattern_tree.root_node, format=' {} '.format)
        print(ete_tree.get_ascii(show_internal=True))


FORMATTERS = {'JSON': JsonFormatter()}
try:
    import ete3
    FORMATTERS['ETE'] = ETEFormatter()
except:
    pass
