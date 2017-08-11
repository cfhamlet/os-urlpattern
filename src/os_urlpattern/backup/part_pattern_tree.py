import math
from pattern_util import EMPTY_PART_PATTERN, BasePattern
from pattern_util import get_part_pattern_from_raw_string
from pattern_util import Pattern

class PartPatternNode(object):
    __slots__ = ['_parrent', '_children', '_count', '_pattern', '_base_part_pattern']
    def __init__(self, base_part_pattern, pattern=None):
        self._parrent = None
        self._children = None
        self._count = 0
        self._base_part_pattern = base_part_pattern
        self._pattern = Pattern(self.part) if pattern is None else pattern
    
    def part_as_pattern(self):
        return True if self.part == self._pattern.pattern_str else False
    
    def set_pattern(self, pattern):
        change = not (self._pattern == pattern)
        if change:
            self._pattern = pattern
#         self._pattern = pattern
        return change
    
    @property
    def all_match_pattern(self):
        return True if self._pattern == BasePattern.ALL_MATCH else False

    @property
    def base_pattern(self):
        return self._base_part_pattern.pattern

    @property
    def pattern(self):
        return self._pattern

    @property
    def part(self):
        return self._base_part_pattern.part

    @property
    def base_part_pattern(self):
        return self._base_part_pattern
    
    @property
    def count(self):
        return self._count

    def incr_count(self, count=1):
        self._count += count
        
    def add_child_node_from_part_pattern(self, part_pattern, count=1, pattern=None):
        if self._children is None:
            self._children = {} 
        part = part_pattern.part
        is_new = False
        if part not in self._children:
            child = PartPatternNode(part_pattern, pattern)
            child.set_parrent(self)
            self._children[part] = child
            is_new = True
        child = self._children[part]
        child.incr_count(count)
        return child, is_new
    
    @property
    def children(self):
        return self._children
    
    def add_child_node_from_part(self, part, config, last_dot_split=False, count=1):
        part_pattern = get_part_pattern_from_raw_string(part, config, last_dot_split)
        return self.add_child_node_from_part_pattern(part_pattern, count)

    def __str__(self):
        return ' '.join((self.part, str(self.base_pattern), self.pattern.pattern_str))

    __repr__ = __str__

    def set_parrent(self, parrent):
        self._parrent = parrent

    def _dump_paths(self, p_list):
        p_list.append(self)
        if not self._children:
            yield p_list 
            return
        for c_part in self._children:
            for path in self._children[c_part]._dump_paths(p_list):
                yield path
            p_list.pop(-1)
    
    def dump_paths(self):
        p_list = []
        for path in self._dump_paths(p_list):
            yield path
    
    def _entropy(self, all_count):
        if not self._children:
            p = float(self._count) / all_count
            return 0 - p * math.log(p, 2)
        entropy = 0
        for node in self._children.values():
            entropy += node._entropy(all_count)
        return entropy
    
    def entropy(self, all_count=-1):
        if all_count > 0:
            if all_count < self._count:
                return None
            return self._entropy(all_count)
        if self._count <= 0:
            return None
        return self._entropy(self._count)
    
    @property
    def parrent(self):
        return self._parrent
    
class PartPatternTree(object):
    def __init__(self, config, url_struct, all_dump=False, level_combiner_class=None, pre_process_config=None):
        self._config = config
        self._pre_process_config = pre_process_config
        self._root = PartPatternNode(EMPTY_PART_PATTERN)
        self._url_struct = url_struct
        level_combiner_class = StepLevelCombiner if level_combiner_class is None else level_combiner_class
        self._level_combiners = [level_combiner_class(self, i) for i in range(self._url_struct.all_depth + 1)]
        self._all_dump = all_dump

    @property
    def url_struct(self):
        return self._url_struct
    
    def pattern_entropy(self, all_count=-1):
        if all_count < self._root.count:
            all_count = self._root.count
        return sum([p.entropy(all_count) for p in self._level_combiners])
    
    def entropy(self, all_count=-1):
        if all_count < self._root.count:
            all_count = self._root.count
        return self._root.entropy(all_count)
    
    @property
    def level_combiners(self):
        return self._level_combiners
    
    @property
    def count(self):
        return self._root.count
    
    @property
    def depth(self):  
        return self._url_struct.all_depth
    
    @property    
    def config(self):
        return self._config
    
    def load_part_pattern_path(self, part_pattern_path):
        node = self._root
        count = part_pattern_path[-1].count
        node.incr_count(count)
        self._level_combiners[0].add_node(node, None, count)
        for idx, part_pattern_node in enumerate(part_pattern_path):
            node, is_new = node.add_child_node_from_part_pattern(part_pattern_node.base_part_pattern, count, part_pattern_node.pattern)
            self._level_combiners[idx + 1].add_node(node, is_new, count)
    
    def add_part_patterns(self, part_patterns, count=1):
        node = self._root
        node.incr_count(count)
        self._level_combiners[0].add_node(node, None, count)
        for idx, part_pattern in enumerate(part_patterns):
            node, is_new = node.add_child_node_from_part_pattern(part_pattern, count)
            self._level_combiners[idx + 1].add_node(node, is_new, count)
            
    def add_parts(self, parts, count=1):
        node = self._root
        node.incr_count(count)
        self._level_combiners[0].add_node(node, None, count)
        for idx, part in enumerate(parts):
            last_dot_split = True if idx == self._url_struct.path_depth - 1 else False 
            node, is_new = node.add_child_node_from_part(part, self._pre_process_config, last_dot_split, count)
            self._level_combiners[idx + 1].add_node(node, is_new, count)

    def _part_as_pattern_path(self, path):
        return False if False in set([p.part_as_pattern() for p in path]) else True

    def dump_paths(self):
        for path in self._root.dump_paths():
            if not self.config.keep_part_as_pattern and not self._all_dump and self._part_as_pattern_path(path):
                continue
            yield path

    def combine(self):
        change = False
        for level_combiner in self._level_combiners[::self.config.level_combine_order]:
            c = level_combiner.combine()
            if not change and c:
                change = c
        return change

from combiner import StepLevelCombiner
