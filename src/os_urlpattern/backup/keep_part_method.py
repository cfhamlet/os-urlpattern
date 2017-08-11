import math

class KeepPartMethod(object):
    def __init__(self, level_combiner):
        self._level_combiner = level_combiner
    
    @property
    def config(self):
        return self._level_combiner.config
    
    def keep_part(self, pattern_combiner, nc):
        if nc.count >= math.sqrt(self._level_combiner.count):
            return True
        return False

class StrictKeepPartMethod(KeepPartMethod):
    def keep_part(self, pattern_combiner, nc):              
        if nc.count >= pattern_combiner.count:
            return True
        return False
    
class HighRatioKeepPartMethod(KeepPartMethod):
    def keep_part(self, pattern_combiner, nc):              
        if nc.count  >=  pattern_combiner.count * 0.99:
            return True
        return False

class RuntimeDefinedKeepPartMethod(KeepPartMethod):
    def keep_part(self, pattern_combiner, nc):
        if nc.count  >= pattern_combiner.count * self.config.runtime_conf.keep_part_ratio:
            return True
        return False 

class CustomDefinedKeepPartMethod(KeepPartMethod):
    def keep_part(self, pattern_combiner, nc):              
        if float(nc.count) / pattern_combiner.count >= self.config.custom_defined_keep_part_ratio:
            return True
        return False 
    
class DigitStrictKeepPartMethod(KeepPartMethod):
    def keep_part(self, pattern_combiner, nc):
        from pattern_util import BasePattern
        if pattern_combiner.base_pattern == BasePattern.ALL_DIGIT:
            if nc.count >= pattern_combiner.count:
                return True
            return False
        return super(DigitStrictKeepPartMethod, self).keep_part(pattern_combiner, nc)