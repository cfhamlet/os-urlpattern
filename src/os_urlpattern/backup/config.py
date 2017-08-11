from strategy import base_strategy
import copy

def default_pattern_gen_config():
    return copy.deepcopy(_Config())

def default_preprocess_config():
    return copy.deepcopy(_PreProcessConfig())

class _RuntimeConfig(object):
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.digit_length_keep_ratio = 1
        self.char_length_keep_ratio = 1
        self.keep_part_ratio = 1
    
    def tune_all(self, ratio=1.0):
        self.digit_length_keep_ratio *= ratio
        self.char_length_keep_ratio *= ratio
        self.keep_part_ratio *= ratio

class _PreProcessConfig(object):
    def __init__(self):
        self.all_match_pat_num_threshold = 7
        self.merge_part_num_threshold = 7
        self.digit_char_merge_threshold = 4
        self.reserved_ext_names = set([
                                        'html', 'htm', 'shtml', 'shtm', 'xhtml', 'xml',
                                        'aspx', 'asp' , 'php' , 'php3', 'php4', 'php5', 'jsp',
                                        'doc', 'docx', 'pdf', 'ppt', 'pptx', 'xlsx', 'xls', 'rtf',
                                        'pl', 'py',
                                        'cig', 'exe',
                                        ])

class _Config(object):
    def __init__(self):
        self.global_stats = {}
        self.runtime_conf = _RuntimeConfig()
        self.strategy = base_strategy
        self.part_pattern_tree_reuseable = False
        self.use_base_pattern = False
        self.level_combine_order = 1
        self.rare_pattern_threshold = 0.1
        self.keep_part_as_pattern = False
        self.keep_all_match_pattern = False
        self.max_iteration_num = 10
        self.max_depth = 14
        
