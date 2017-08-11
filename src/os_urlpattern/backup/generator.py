import StringIO
import copy
import logging
import time

from config import default_pattern_gen_config, default_preprocess_config
from part_pattern_tree import PartPatternTree
from pattern_spliter import PatternSpliter
from pattern_tree import PatternTree
from util import path_dump_and_load, get_memory_used, parse_url

_logger = logging.getLogger('Process')

class Processor(object):
    def __init__(self, config, url_struct):
        self._config = config
        self._url_struct = url_struct
        self._s_hash = url_struct.hashcode[0:8]
        self._path_depth = url_struct.path_depth
    
    def log_debug(self, msg):
        m = get_memory_used()
        if m:
            _logger.debug('[%s] [%d] [%s] %s' % (m, self._path_depth , self._s_hash, msg))
        else:
            _logger.debug('[%d] [%s] %s' % (self._path_depth, self._s_hash, msg))
        
    def generate_pattern_tree(self, part_pattern_tree):
        all_count = part_pattern_tree.count
        p_tree = part_pattern_tree
        self.log_debug('[OVERALL] [BASE ENTROPY] %d %f' % (p_tree.count, p_tree.entropy()))
        p_tree.combine()
        self.log_debug('[OVERALL] [COMBINE] FINISH %d' % p_tree.count)
        self.log_debug('[OVERALL] [PATTERN ENTROPY] %f' % p_tree.pattern_entropy())
        
        n = self._config.max_iteration_num
        if self._config.use_base_pattern:
            n = 0
        for i in range(n):
            t = '%d/%d' % (i + 1, n)
            p_tree = self._g_pattern_spilter(p_tree)
            self.log_debug('[SPLIT] [%s] [LOAD] FINISH %d %d' % (t, p_tree.count, p_tree.split_num))
            if p_tree.count == 0:
                self.log_debug('[SPLIT] [%s] NO PATTERN' % t)
                return None
            p_tree.combine()
            if p_tree.no_change():
                self.log_debug('[SPLIT] [%s] NO CHANGE' % t)
                self.log_debug('[SPLIT] [PATTERN ENTROPY] %f' % p_tree.pattern_entropy())
                break
            self.log_debug('[SPLIT] [%s] [COMBINE] FINISH' % t)
            self.log_debug('[SPLIT] [PATTERN ENTROPY] %f' % p_tree.pattern_entropy())
        
        if n > 0:
            p_tree.self_update()
            self.log_debug('[SPLIT] FINISH')
        
        pattern_tree = self._g_pattern_tree(p_tree)
        lost = (all_count - pattern_tree.count) / float(all_count) * 100
        self.log_debug('[GEN] FINISH %d/%d, LOST:%.2f%%' % (pattern_tree.count, all_count, lost))
        return pattern_tree
    
    def _g_pattern_spilter(self, p_tree):
        pattern_spliter = PatternSpliter(self._config, self._url_struct)
        if isinstance(p_tree, PatternSpliter):
            pattern_spliter.update_no_change_pattern_spliter_tree(p_tree.no_change_pattern_spliter_tree())
        path_dump_and_load(p_tree, pattern_spliter, 1)
        return pattern_spliter
    
    def _g_pattern_tree(self, p_tree):
        pattern_tree = PatternTree(self._config, self._url_struct)
        path_dump_and_load(p_tree, pattern_tree, 1)
        return pattern_tree
    
    def process_and_dump(self, part_pattern_tree):
        pattern_tree = self.generate_pattern_tree(part_pattern_tree)
        if not part_pattern_tree:
            return
        for path in pattern_tree.dump_paths():
            yield path

class UrlPatternGenerator(object):
    def __init__(self, config=None, pre_process_config=None):
        self._depth_node_tree = {}
        if config is None:
            self._config = default_pattern_gen_config()
        else:
            self._config = copy.deepcopy(config)
        self._config.global_stats.clear()
        if pre_process_config is None:
            self._pre_process_config = default_preprocess_config()
        else:
            self._pre_process_config = copy.deepcopy(pre_process_config)
        self._count = 0
        self._skip_count = 0
        self._valid_count = 0
        self._depth_pattern_tree = {}
    
    def _process(self, path_depth):
        if path_depth in self._depth_pattern_tree:
            self.log_warn("[GEN] PROCESSED", path_depth)
            return True
        if path_depth not in self._depth_node_tree:
            self.log_warn("[GEN] NO DEPATH", path_depth)
            return False
        ptrees = {}
        for s_hash, tree in self._depth_node_tree[path_depth].items():
            processor = Processor(self.config, tree.url_struct)
            pattern_tree = processor.generate_pattern_tree(tree)
            if not pattern_tree:
                continue
            ptrees[s_hash] = pattern_tree
        if len(ptrees) <= 0:
            self._depth_pattern_tree[path_depth] = None
            return False
        self._depth_pattern_tree[path_depth] = ptrees
        return True
    
    def log_debug(self, msg, depth=-1):
        self._log(logging.DEBUG, msg, depth)
        
    def log_warn(self, msg, depth=-1):
        self._log(logging.WARN, msg, depth)
    
    def _log(self, level, msg, depth=-1):
        o = StringIO.StringIO()
        m = get_memory_used()
        
        if m:
            o.write('[%s]' % m)
            
        if depth > 0:
            if m:
                o.write(' ')
            o.write('[%d]' % depth)            
            
        o.seek(0)
        s = o.read()
        if len(s) > 0:
            _logger.log(level, '%s %s' % (s, msg))
        else:
            _logger.log(level, msg)
            
    def _dump(self, path_depth):
        if path_depth not in self._depth_pattern_tree:
            self.log_warn('[DUMP] NOT PROCESSED', path_depth)
            return
        ptree = self._depth_pattern_tree[path_depth]
        if ptree is None:
            self.log_warn('[DUMP] NO PATTERN TREE', path_depth)
            return
        count = 0
        for _, pattern_tree in ptree.items():
            for path in pattern_tree.dump_paths():
                count += 1
                yield path
        self.log_debug("[DUMP] FINISH %d" % count, path_depth)
        if not self.config.part_pattern_tree_reuseable and path_depth in self._depth_node_tree:
            del self._depth_node_tree[path_depth]
        
    def _process_and_dump(self, path_depth):
        if self._process(path_depth):
            for path in self._dump(path_depth):
                yield path
                
    def process(self, handle_depths=[]):
        if not handle_depths:
            handle_depths = self._depth_node_tree.keys()
        for path_depth in sorted(list(set(handle_depths))):
            self._process(path_depth)
    
    def dump(self, handle_depths=[]):
        if not handle_depths:
            handle_depths = self._depth_node_tree.keys()
        for depth in sorted(list(set(handle_depths))):
            for path in self._dump(depth):
                yield path
    
    def process_and_dump(self, handle_depths=[]):
        if not handle_depths:
            handle_depths = self._depth_node_tree.keys()
        for path_depth in sorted(list(set(handle_depths))):
            for path in self._process_and_dump(path_depth):
                yield path
    
    def load(self, f, allowed_depths=[]):
        self._load_start_time = time.time()
        self.log_debug('[LOAD] START')
        allowed_depths = set(allowed_depths) 
        for line in f:
            self._load(line.strip(), allowed_depths)
        self.config.global_stats['all_count'] = self._valid_count
        now = time.time()
        self.log_debug('[LOAD] FINISH ALL:%d SKIP:%d VALID:%d %.1f/s' % (self._count, self._skip_count, self._valid_count, self._count / (now - self._load_start_time)))
    
    def _load(self, url, allowed_depths=set()):
        if self._count % 5000 == 0:
            now = time.time()
            self.log_debug('[LOADING] %d %.1f/s' % (self._count, self._count / (now - self._load_start_time)))
        self._count += 1
        ret = self.load_url(url, allowed_depths)
        if not ret:
            self._skip_count += 1
            self.log_warn('[INVALID] %s' % url)
            return False
        self._valid_count += 1
        return True
    
    def load_url(self, url, allowed_depths):
        p = parse_url(url)
        if p is None:
            return False
        url_struct, parts = p
        path_depth = url_struct.path_depth
        
        if not allowed_depths:
            if path_depth > self._config.max_depth:
                return False
        else:
            if path_depth not in allowed_depths:
                return False
            
        s_hash = url_struct.hashcode
        
        if path_depth not in self._depth_node_tree:
            self._depth_node_tree[path_depth] = {}
        t = self._depth_node_tree[path_depth]
        if s_hash not in t:
            t[s_hash] = PartPatternTree(self._config
                                        , url_struct
                                        , pre_process_config=self._pre_process_config)

        tree = t[s_hash]
        tree.add_parts(parts)
        return True        
    
    @property
    def config(self):
        return self._config
