from part_pattern_tree import PartPatternTree
from util import pattern_path_hashcode

class PatternSpliter(object):
    def __init__(self, config, url_stuct):
        self._config = config
        self._pattern_spliter_tree = {}
        self._no_change_pattern_spliter_tree = {}
        self._url_struct = url_stuct
        
    def no_change(self):
        return True if len(self._pattern_spliter_tree) == 0 else False
    
    def no_change_pattern_spliter_tree(self):
        return self._no_change_pattern_spliter_tree
    
    def self_update(self):
        self._pattern_spliter_tree.update(self._no_change_pattern_spliter_tree)
        self._no_change_pattern_spliter_tree.clear()
    
    def update_no_change_pattern_spliter_tree(self, no_change_pattern_spliter_tree):
        self._no_change_pattern_spliter_tree.update(no_change_pattern_spliter_tree)
    
    def pattern_entropy(self, all_count=-1):
        if all_count < self.count:
            all_count = self.count
        return sum([p.pattern_entropy(all_count) for p in self._pattern_spliter_tree.values()]) + sum([p.pattern_entropy(all_count) for p in self._no_change_pattern_spliter_tree.values()])
    
    @property
    def split_num(self):
        return len(self._pattern_spliter_tree) + len(self._no_change_pattern_spliter_tree)
    
    @property
    def count(self):
        return sum([t.count for t in self._pattern_spliter_tree.values()]) + sum([t.count for t in self._no_change_pattern_spliter_tree.values()]) 

    @property
    def config(self):
        return self._config
        
    def load_path(self, part_pattern_path):
        ph = pattern_path_hashcode([p.pattern for p in part_pattern_path], self._url_struct)
        if ph not in self._pattern_spliter_tree:
            self._pattern_spliter_tree[ph] = PartPatternTree(self.config, self._url_struct)  # , level_combiner_class=LevelCombiner)
        node_tree = self._pattern_spliter_tree[ph]
        node_tree.load_part_pattern_path(part_pattern_path)
    
    def combine(self):
        self.config.runtime_conf.tune_all(0.9)
        for ph, ntree in self._pattern_spliter_tree.items():
            change = ntree.combine()
            if not change:
                self._no_change_pattern_spliter_tree[ph] = ntree
        self.config.runtime_conf.reset()
        for ph in self._no_change_pattern_spliter_tree:
            if ph in self._pattern_spliter_tree:
                del self._pattern_spliter_tree[ph]
    
    def dump_paths(self):
        for ph, tree in self._pattern_spliter_tree.items():
            if tree.count == 0:
                continue
            if ph in self._no_change_pattern_spliter_tree:
                continue
            for path in tree.dump_paths():
                yield path
        self._pattern_spliter_tree.clear()
