from keep_part_method import RuntimeDefinedKeepPartMethod
from deep_pattern import DeepPatternGenerator
from deep_pattern import DigitLengthSplitRuntimeDeepPatternGenerator
from deep_pattern import MultiPartDeepPatternGenerator
from deep_pattern import CharLengthSplitRuntimeDeepPatternGenerator

class Strategy(object):
    def __init__(self):
        self.keep_part_method_class = RuntimeDefinedKeepPartMethod

        self.digit_deep_pattern_generator_class = DigitLengthSplitRuntimeDeepPatternGenerator
        self.char_deep_pattern_generator_class = CharLengthSplitRuntimeDeepPatternGenerator
        self.multi_part_deep_pattern_generator_class = MultiPartDeepPatternGenerator
        self.default_deep_pattern_generator_class = DeepPatternGenerator
    
base_strategy = Strategy()