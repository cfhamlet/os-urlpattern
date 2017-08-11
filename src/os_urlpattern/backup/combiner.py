import math

class _NodesCounter(object):
    def __init__(self, pattern_combiner):
        self.count = 0
        self.nodes = []
        self._pattern_combiner = pattern_combiner
    
    def set_pattern(self, pattern):
        change = False
        for node in self.nodes:
            c = node.set_pattern(pattern)
            if c:
                change = c
        return change
            
    @property
    def part(self):
        if not self.nodes:
            return None
        return self.nodes[0].part
    
    @property
    def pattern(self):
        if not self.nodes:
            return None
        return self.nodes[0].pattern
        
class PatternCombiner(object):
    def __init__(self, level_combiner, base_part_pattern):
        self._level_combiner = level_combiner
        self._base_part_pattern = base_part_pattern
        self._part_nodes = {}
        self._count = 0
        self._deep_pattern_generator = get_deep_pattern_generator(self)
        self._use_base_pattern = False
    
    @property
    def url_struct(self):
        return self._level_combiner.url_struct
    
    @property
    def parts_num(self):
        return len(self._part_nodes)
    
    @property
    def level_combiner(self):
        return self._level_combiner
    
    @property
    def level_combiner_count(self):
        return self._level_combiner.count
    
    @property
    def has_multi_part(self):
        return self._base_part_pattern.has_multi_part()
    
    @property
    def part_num(self):
        return self._base_part_pattern.part_num
    
    @property
    def base_pattern(self):
        return self._base_part_pattern.pattern
    
    @property
    def base_part_pattern(self):
        return self._base_part_pattern
        
    def add_node(self, node, is_new, count=1):
        self._deep_pattern_generator.add_node(node, is_new, count)
        self._count += count
        part = node.part
        if part not in self._part_nodes:
            self._part_nodes[part] = _NodesCounter(self)
        nc = self._part_nodes[part]
        nc.count += count
        if is_new:
            nc.nodes.append(node) 
    
    @property
    def count(self):
        return self._count

    def keep_part(self, nc):
        return self._level_combiner.keep_part(self, nc)
    
    def use_base_pattern(self):
        self._use_base_pattern = True
    
    def _after_pattern_define(self, nc):
        pass
    
    def combine(self):
        change = False
        if not self._use_base_pattern:
            self._deep_pattern_generator.combine()
        for part, nc in self._part_nodes.items():
            if self._level_combiner.current_level == 1 and nc.part == 'nuccore':
                print nc.count, nc.part, self._level_combiner.count
            bp = None
            if self._use_base_pattern:
                bp = self.base_pattern
            elif not self._base_part_pattern.has_multi_part() and self.keep_part(nc):
                from pattern_util import get_pattern_from_cache
                bp = get_pattern_from_cache(part)
            else:
                bp = self._deep_pattern_generator.get_pattern(part)
            c = nc.set_pattern(bp)
            if not change and c:
                change = c
            self._after_pattern_define(nc)
        return change
    
    @property
    def config(self):
        return self._level_combiner.config

class LevelCombiner(object):
    def __init__(self, part_pattern_tree, current_level):
        self._part_pattern_tree = part_pattern_tree
        self._current_level = current_level
        self._depth = self._part_pattern_tree.depth
        self._pattern_combiners = {}
        self._keep_part_method = self.config.strategy.keep_part_method_class(self)
        
    @property
    def url_struct(self):
        return self._part_pattern_tree.url_struct
    
    @property
    def current_level(self):
        return self._current_level
    
    @property
    def last_level(self):
        return self._current_level >= self._depth
    
    @property
    def pattern_combiners(self):
        return self._pattern_combiners
    
    @property
    def next_level_combiner(self):
        return self._part_pattern_tree.level_combiners[self._current_level + 1]
    
    @property
    def config(self):
        return self._part_pattern_tree.config
    
    @property
    def part_pattern_tree(self):
        return self._part_pattern_tree
    
    def keep_part(self, pattern_combiner, nc):
        return self._keep_part_method.keep_part(pattern_combiner, nc)

    @property
    def count(self):
        return self._part_pattern_tree.count
        
    def add_node(self, node, is_new, count=1):
        base_pattern = node.base_pattern
        if base_pattern not in self._pattern_combiners:
            self._pattern_combiners[base_pattern] = PatternCombiner(self, node.base_part_pattern)
        self._pattern_combiners[base_pattern].add_node(node, is_new, count)

    def combine(self):
        change = False
        for _, pattern_combiner in self._pattern_combiners.items():
            if self.config.use_base_pattern or pattern_combiner.count <= 1 and pattern_combiner.count < self.count * self.config.rare_pattern_threshold:
                pattern_combiner.use_base_pattern()
            c = pattern_combiner.combine()
            if not change and c:
                change = c
        return change

class StepPatternCombiner(PatternCombiner):
    def __init__(self, level_combiner, base_part_pattern):
        super(StepPatternCombiner, self).__init__(level_combiner, base_part_pattern)
        self._next_level_combiners = {}
        self._pattern_count = {}
    
    def prob(self, all_count):
        return float(self.count) / all_count
    
    def add_node(self, node, is_new, count=1):
        super(StepPatternCombiner, self).add_node(node, is_new, count)
        if is_new is None:
            nc = self._part_nodes[node.part]
            if not nc.nodes:
                nc.nodes.append(node)
                
    def entropy(self, all_count=-1):
        if all_count <= 0:
            return 0
        return 0 - sum([float(p) / all_count * math.log(float(p) / all_count, 2) for p in self._pattern_count.values()])
    
    def _after_pattern_define(self, nc):
        if self.level_combiner.last_level:
            pattern = nc.pattern
            hp = hash(pattern)
            if hp not in self._pattern_count:
                self._pattern_count[hp] = 0
            self._pattern_count[hp] += nc.count
            return
        pattern = nc.pattern
        if pattern not in self._next_level_combiners:
            self._next_level_combiners[pattern] = {}
        nlc = self._next_level_combiners[pattern]
        for node in nc.nodes:
            for c_node in node.children.values():
                if c_node.base_pattern not in nlc:
                    spc = StepPatternCombiner(self.level_combiner.next_level_combiner, c_node.base_part_pattern)
                    nlc[c_node.base_pattern] = spc
                    self.level_combiner.next_level_combiner.pattern_combiners[hash(spc)] = spc
                spc = nlc[c_node.base_pattern]
                spc.add_node(c_node, True, c_node.count)
                    
class StepLevelCombiner(LevelCombiner):
    
    def complexity(self, all_count):
        if not self.last_level:
            return 0
        return 0
    
    def entropy(self, all_count=-1):
        if not self.last_level:
            return 0
        if all_count < self.count:
            all_count = self.count
        return sum([p.entropy(all_count) for p in self._pattern_combiners.values()])
        
    def add_node(self, node, is_new, count=1):
        if is_new is not None:  # None is root node, only process root node
            return
        if  not self._pattern_combiners:
            pc = StepPatternCombiner(self, node.base_part_pattern)
            self._pattern_combiners[hash(pc)] = pc
        for pc in self._pattern_combiners.values():
            pc.add_node(node, is_new, count)
        
from deep_pattern import get_deep_pattern_generator            
