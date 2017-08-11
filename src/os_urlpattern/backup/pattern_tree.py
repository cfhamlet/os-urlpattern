from util import pattern_path_hashcode, pattern_path_string

class PatternPath(object):
    def __init__(self, pattern_path, url_struct):
        self._pattern_path = pattern_path
        self._url_struct = url_struct

    def __len__(self):
        return len(self._pattern_path)
        
    @property
    def count(self):
        return self._pattern_path[-1].count
    
    @property
    def percent(self):    
        return float(self._pattern_path[-1].count) / self._pattern_path[0].count
    
    @property
    def pattern_path_hashcode(self):
        return pattern_path_hashcode([p.pattern for p in self._pattern_path[1:]], self._url_struct)
    
    def __str__(self):
        return pattern_path_string([p.pattern for p in self._pattern_path[1:]], self._url_struct)
    
    __repr__ = __str__
    
class PatternNode(object):
    def __init__(self, pattern):#, base_pattern):
        self._pattern = pattern
        self._children = {}
        self._parrent = None
#         self._base_pattern = base_pattern
        self._count = 0
    
    @property
    def pattern(self):
        return self._pattern
        
#     @property
#     def base_pattern(self):
#         return self._base_pattern
    
    @property
    def count(self):
        return self._count
        
    def __str__(self):
        return str(self._pattern)
    
    __repr__ = __str__
    
    def incr_count(self, count=1):
        self._count += count
        
    def set_parrent(self, parrent):
        self._parrent = parrent
        
    def add_child_from_pattern(self, part_pattern, count=1):
        pattern = part_pattern.pattern
        if pattern not in self._children:
            child = PatternNode(pattern)#, part_pattern.base_pattern)
            child.set_parrent(self)
            self._children[pattern] = child
            
        self._children[pattern].incr_count(count)
        return self._children[pattern]
    
    def _dump_paths(self, p_list):
        p_list.append(self)
        if not self._children:
            yield p_list 
            return
        for c_part in self._children:
            for path in self._children[c_part]._dump_paths(p_list):
                yield path
            p_list.pop(-1)

    def dump_paths(self, url_struct):
        p_list = []
        for path in self._dump_paths(p_list):
            if path:
                yield PatternPath(path, url_struct)

from pattern_util import BasePattern
class PatternTree(object):
    def __init__(self, config, url_struct):
        self._root = PatternNode(BasePattern.EMPTY)#, BasePattern.EMPTY)
        self._config = config
        self._url_struct = url_struct
        
    @property
    def config(self):
        return self._config
    
    @property
    def count(self):
        return self._root.count
    
    def load_path(self, part_pattern_path):
        if not self.config.keep_all_match_pattern and True in set([p.all_match_pattern for p in part_pattern_path]):
            return
        node = self._root
        count = part_pattern_path[-1].count
        node.incr_count(count)
        for part_pattern in part_pattern_path:
            node = node.add_child_from_pattern(part_pattern, count)
    
    def dump_paths(self):
        for path in self._root.dump_paths(self._url_struct):
            if  len(path) == 1:
                continue
            yield path
    
