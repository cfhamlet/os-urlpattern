from pattern_util import get_part_pattern_from_raw_string, Pattern, BasePattern, pattern_degree_stats
from util import pattern_path_string_hashcode, parse_url, pattern_path_hashcode
from pattern_util import parse_pattern_string, trans_to_base_patterns
from operator import itemgetter
from config import default_preprocess_config
import copy
import logging

_logger = logging.getLogger('Matcher')

def _sort_match_pattern_node(nodes):
    ns = sorted([(n, n.all_degree, n.mst_degree) for n in nodes], key=itemgetter(1, 2))
    return [n[0] for n in ns]

class MatchPatternNode(object):
    def __init__(self, pattern, nex_dexgree, mst_degree):
        self._pattern = pattern
        self._children = {}
        self._exact_children = {}
        self._parrent = None
        self._pattern_id = None
        self._mst_degree = mst_degree
        self._nex_degree = nex_dexgree
        self._sorted_children = []
        
    @property
    def pattern_str(self):
        return self._pattern.pattern_str
    
    @property
    def all_degree(self):
        return self._mst_degree + self._nex_degree
    
    @property
    def mst_degree(self):
        return self._mst_degree
    
    @property
    def nex_dexgree(self):
        return self._nex_degree
    
    def sort_children(self):
        if not self._children and not self._exact_children:
            return
        self._sorted_children = _sort_match_pattern_node(self._children.values())
        for child in self._sorted_children:
            child.sort_children()
        for child in self._exact_children.values():
            child.sort_children()
    
    @property
    def pattern_id(self):
        return self._pattern_id
    
    def set_pattern_id(self, pattern_id):
        self._pattern_id = pattern_id
                
    def set_parrent(self, parrent):
        self._parrent = parrent
    
    def match(self, part):
        return self._pattern.match(part)
    
    def add_child_from_pattern_part(self, pattern_part, all_match_pat_num_threshold):
        pattern = Pattern(pattern_part)
        pstr = pattern.pattern_str
        nex_degree, mst_degree = pattern_degree_stats(pstr, all_match_pat_num_threshold)
        children = self._children
        if nex_degree + mst_degree == 0:
            children = self._exact_children
        if pstr not in children:
            child = MatchPatternNode(pattern, nex_degree, mst_degree)
            child.set_parrent(self)
            children[pstr] = child
        return children[pstr]
    
    def recursive_match(self, norm_parts, idx):
        if not self._children and not self._exact_children:
            return self._pattern_id
        part = norm_parts[idx][0]
        norm_part = norm_parts[idx][1]
        n = None
        if norm_part in self._exact_children:
            n = self._exact_children[norm_part].recursive_match(norm_parts, idx + 1)
        if n:
            return n
        for child in self._sorted_children:
            if not child.match(part):
                continue
            n = child.recursive_match(norm_parts, idx + 1)
            if n:
                break
        return n        

class MatchPatternTree(object):
    def __init__(self, config, url_struct):
        self._root = MatchPatternNode(BasePattern.EMPTY, 0, 0)
        self._config = config
        self._url_struct = url_struct
    
    def load(self, pattern_parts, pattern_id):
        node = self._root
        for pattern_part in pattern_parts:
            node = node.add_child_from_pattern_part(pattern_part, self._config.all_match_pat_num_threshold)
        node.set_pattern_id(pattern_id)
        
    def match(self, norm_parts):
        return self._root.recursive_match(norm_parts, 0)
        
    def _preprocess(self):
        self._root.sort_children()

class Matcher(object):
    
    def __init__(self, config=None):
        if config is None:
            self._config = default_preprocess_config()
        else:
            self._config = copy.deepcopy(config)
        self._match_pattern_trees = {}
        self._pattern_info = {}
        self._count = 0
    
    @property
    def count(self):
        return self._count
    
    def get_pattern_info_from_id(self, pattern_id):
        return self._pattern_info.get(pattern_id, None)

    def _load(self, pat_info):
        if 'pat' not in pat_info:
            return False
        p = parse_pattern_string(pat_info['pat'])
        if p is None:
            return False
        url_struct, parts = p
        base_parts = trans_to_base_patterns(parts, self._config, url_struct)
        s_hash = pattern_path_hashcode(base_parts, url_struct)
        if s_hash not in self._match_pattern_trees:
            self._match_pattern_trees[s_hash] = MatchPatternTree(self._config, url_struct)
            
        pattern_id = pattern_path_string_hashcode(pat_info['pat'])
        self._match_pattern_trees[s_hash].load(parts, pattern_id)    
        self._count += 1
        self._pattern_info[pattern_id] = pat_info
        return True
    
    def load(self, f):
        import json
        for line in f:
            line = line.strip()
            try:
                pat_info = json.loads(line)
            except Exception, e:
                _logger.error('[LOADING] [FAIL] %s %s' % (line, str(e)))
                continue
            ret = self._load(pat_info)
            if not ret:
                _logger.warn('[LOADING] [INVALID] %s' % line)
        self._preprocess()
        
    def _preprocess(self):
        for tree in self._match_pattern_trees.values():
            tree._preprocess()
    
    def match(self, url):
        p = parse_url(url)
        if p is None:
            return None
        url_struct, parts = p
        k = {'c':0, 'l':url_struct.path_depth}
        
        def _m(part):
            k['c'] += 1
            return get_part_pattern_from_raw_string(part, self._config, k['c'] == k['l'])
        
        part_patterns = map(_m, parts)
        h_hash = pattern_path_hashcode([p.pattern for p in part_patterns], url_struct)
        if h_hash not in self._match_pattern_trees:
            return None
        
        norm_parts = zip(parts, [p.part for p in part_patterns])
        return self.get_pattern_info_from_id(self._match_pattern_trees[h_hash].match(norm_parts))

