import math
from pattern_util import BasePattern, BasePatternRule, Pattern, get_pattern_from_cache, CHAR_PATTERN_RULE
from util import UrlStructMeta

def get_deep_pattern_generator(pattern_combiner):
    config = pattern_combiner.config
    if pattern_combiner.has_multi_part:
        return config.strategy.multi_part_deep_pattern_generator_class(pattern_combiner)
    else:
        if pattern_combiner.base_pattern == BasePattern.ALL_DIGIT:
            return config.strategy.digit_deep_pattern_generator_class(pattern_combiner)
        elif pattern_combiner.base_pattern in CHAR_PATTERN_RULE:
            return config.strategy.char_deep_pattern_generator_class(pattern_combiner)
    
    return config.strategy.default_deep_pattern_generator_class(pattern_combiner)

class DeepPatternGenerator(object):
    def __init__(self, pattern_combiner):
        self._pattern_combiner = pattern_combiner
        self._count = 0
        
    @property
    def url_struct(self):
        return self._pattern_combiner.url_struct
    
    def add_node(self, node, is_new, count):
        self._count += count
    
    @property
    def count(self):
        return self._count
        
    def combine(self):
        pass
    
    def get_pattern(self, part):
        return self._pattern_combiner.base_pattern
    
    @property
    def config(self):
        return self._pattern_combiner.config

class CharDeepPatternGenerator(DeepPatternGenerator):
    def __init__(self, pattern_combiner):
        super(CharDeepPatternGenerator, self).__init__(pattern_combiner)
        self._length_stats = {}
        self._length_pattern = {}
        
    def add_node(self, node, is_new, count):
        super(CharDeepPatternGenerator, self).add_node(node, is_new, count)
        l = len(node.part)
        if l not in self._length_stats:
            self._length_stats[l] = 0
        self._length_stats[l] += count
        
    def combine(self):
        kpt = self._pattern_combiner.level_combiner_count * 0.8
        for l, count in self._length_stats.items():
            if count >= kpt or len(self._length_stats) == 1:
                if l == 1:
                    self._length_pattern[l] = BasePattern.SINGLE_CHAR
                else:
                    self._length_pattern[l] = get_pattern_from_cache('%s{%d}' % (BasePatternRule.SINGLE_CHAR, l))
                    
    def get_pattern(self, part):
        return self._length_pattern.get(len(part), self._pattern_combiner.base_pattern)

class SingleCharCominbeDeepPatternGenerator(CharDeepPatternGenerator):
    def __init__(self, pattern_combiner):
        super(SingleCharCominbeDeepPatternGenerator, self).__init__(pattern_combiner)
        self._single_chars = set()
        
    def add_node(self, node, is_new, count):
        super(SingleCharCominbeDeepPatternGenerator, self).add_node(node, is_new, count)
        l = len(node.part)
        if l != 1:
            return
        self._single_chars.add(node.part)
        
    def get_pattern(self, part):
        l = len(part)
        if l == 1 and len(self._single_chars) >= 2:
            return BasePattern.SINGLE_CHAR
        return super(SingleCharCominbeDeepPatternGenerator, self).get_pattern(part)

class CharDeepPatternNotExactGenerator(CharDeepPatternGenerator):
    def get_pattern(self, part):
        if len(self._length_stats) >= self.config.exact_char_length_keep_threshold:
            return self._pattern_combiner.base_pattern
        return super(CharDeepPatternNotExactGenerator, self).get_pattern(part)

class DigitDeepPatternGenerator(DeepPatternGenerator): 
    def __init__(self, pattern_combiner):
        super(DigitDeepPatternGenerator, self).__init__(pattern_combiner)
        self._digit_stats = {}
        self._length_pattern = {}

    def add_node(self, node, is_new, count):
        super(DigitDeepPatternGenerator, self).add_node(node, is_new, count)
        l = len(node.part)
        if l not in self._digit_stats:
            self._digit_stats[l] = 0
        self._digit_stats[l] += count
        
    def combine(self):
        if len(self._digit_stats) >= 2:
            return
        kpt = math.sqrt(self._pattern_combiner.level_combiner_count)
        for l, count in self._digit_stats.items():
            if count >= kpt or len(self._digit_stats) == 1:
                if l == 1:
                    self._length_pattern[l] = BasePattern.SINGLE_DIGIT
                else:
                    self._length_pattern[l] = get_pattern_from_cache('%s{%d}' % (BasePatternRule.SINGLE_DIGIT, l))

    def get_pattern(self, part):
        return self._length_pattern.get(len(part), self._pattern_combiner.base_pattern)

class DigitLengthSplitRuntimeDeepPatternGenerator(DigitDeepPatternGenerator): 
    def combine(self):
        kpt = self.count * self.config.runtime_conf.digit_length_keep_ratio
        for l, count in self._digit_stats.items():
            if count >= kpt or len(self._digit_stats) == 1:
                if l == 1:
                    self._length_pattern[l] = BasePattern.SINGLE_DIGIT
                else:
                    self._length_pattern[l] = get_pattern_from_cache('%s{%d}' % (BasePatternRule.SINGLE_DIGIT, l))
    
class CharLengthSplitRuntimeDeepPatternGenerator(CharDeepPatternGenerator):
    
    def combine(self):
        kpt = self.count * self.config.runtime_conf.char_length_keep_ratio
        for l, count in self._length_stats.items():
            if count >= kpt or len(self._length_stats) == 1 or (l == 1 and count > self._count * 0.3):
                c = CHAR_PATTERN_RULE[self._pattern_combiner.base_pattern]
                if l == 1:
                    self._length_pattern[l] = c
                else:
                    self._length_pattern[l] = get_pattern_from_cache('%s{%d}' % (c, l))

from combiner import LevelCombiner
class MultiPartDeepPatternGenerator(DeepPatternGenerator):
    def __init__(self, pattern_combiner):
        super(MultiPartDeepPatternGenerator, self).__init__(pattern_combiner)
        url_struct = UrlStructMeta(len(pattern_combiner.base_part_pattern.part_pattern_list), [], False)
        self._node_tree = PartPatternTree(pattern_combiner.config, url_struct, True, LevelCombiner)
        self._part_pattern = {}
         
    def add_node(self, node, is_new, count):
        super(MultiPartDeepPatternGenerator, self).add_node(node, is_new, count)
        self._node_tree.add_part_patterns(node.base_part_pattern.part_pattern_list, count)        
         
    def combine(self):
        self._node_tree.combine()
        for path in self._node_tree.dump_paths():
            part = ''.join([p.part for p in path])
            pattern = Pattern(''.join([p.pattern.pattern_str for p in path]))
            self._part_pattern[part] = pattern
             
    def get_pattern(self, part):
        return self._part_pattern.get(part, self._pattern_combiner.base_pattern)
    
from part_pattern_tree import PartPatternTree
