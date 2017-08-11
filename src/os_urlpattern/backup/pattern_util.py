import StringIO
import re
import string

class BasePatternRule(object):
    DIGIT = '0-9'
    CHAR = 'a-z'
    CHAR_LOW = 'a-z'
    CHAR_UPPER = 'A-Z'
    CHAR_ALL = 'A-Za-z'
    DIGIT_AND_CHAR = '0-9a-z'
    DIGIT_AND_CHAR_UPPER = '0-9A-Z'
    DIGIT_AND_CHAR_ALL = '0-9A-Za-z'
    SINGLE_DIGIT = '[0-9]'
    SINGLE_CHAR = '[a-z]'
    ALL_DIGIT = '[0-9]+'
    ALL_CHAR = '[a-z]+'
    ALL_CAHR_UPPER = '[A-Z]+'
    ALL_CAHR_ALL = '[A-Za-z]+'
    DIGIT_CHAR_MIX = '[0-9a-z]+'
    DOT = '\\.'
    ALL_MATCH = '.*?'
    EMPTY = ''

_CHAR_RULE_LIST = []
_CHAR_RULE_LIST.extend([(i, BasePatternRule.DIGIT) for i in string.digits])
_CHAR_RULE_LIST.extend([(i, BasePatternRule.CHAR) for i in string.ascii_lowercase])
_CHAR_RULE_LIST.extend([(i, BasePatternRule.CHAR) for i in string.ascii_uppercase])

_DIGIT_SET = set(string.digits)
_CHAR_SET_LOW = set(string.ascii_lowercase)
_CHAR_SET_UPPER = set(string.ascii_uppercase)

CHAR_DIGIT_SET = set([c[0] for c in _CHAR_RULE_LIST])
_SYMBOL = '%&_@#;:,=<>~/'
_SYMBOL_SET = set([i for i in _SYMBOL])
_SYMBOL_LIST = [(i, i) for i in _SYMBOL_SET]
_ESCAPE = '.+\\"\'()[]{}*$^?|!-'
_ESCAPE_SET = set([i for i in _ESCAPE]) 
_ESCAPE_LIST = [(i, '\\%s' % i) for i in _ESCAPE_SET]

_CHAR_RULE_LIST.extend(_SYMBOL_LIST)
_CHAR_RULE_LIST.extend(_ESCAPE_LIST)
CHAR_RULE = dict(_CHAR_RULE_LIST)

_ALL_SIGN_RULE_SET = set([v for _, v in _SYMBOL_LIST + _ESCAPE_LIST])
_ALL_SIGN_RULE_DICT = dict([(v, k) for k, v in _SYMBOL_LIST + _ESCAPE_LIST])
_DIGIT_AND_CHAR_LIST = [BasePatternRule.DIGIT, BasePatternRule.CHAR]
_DIGIT_AND_CHAR_UPPER_LIST = [BasePatternRule.DIGIT, BasePatternRule.CHAR_UPPER]
_DIGIT_AND_CHAR_SET = set(_DIGIT_AND_CHAR_LIST)
_DIGIT_AND_CHAR_UPPER_SET = set(_DIGIT_AND_CHAR_UPPER_LIST)
_DIGIT_AND_CHAR_ALL_SET = _DIGIT_AND_CHAR_SET.union(_DIGIT_AND_CHAR_UPPER_SET)
_CHAR_ALL_SET = set([BasePatternRule.CHAR_LOW, BasePatternRule.CHAR_UPPER])

CHAR_PATTERN_SET = set([BasePatternRule.ALL_CAHR_ALL, BasePatternRule.ALL_CHAR, BasePatternRule.ALL_CAHR_UPPER])
CHAR_PATTERN_RULE = dict([(BasePatternRule.ALL_CAHR_ALL,BasePatternRule.CHAR_ALL)
                          , (BasePatternRule.ALL_CHAR, BasePatternRule.CHAR)
                          , (BasePatternRule.ALL_CAHR_UPPER, BasePatternRule.CHAR_UPPER)])

SPLIT_CHAR = {}  # '-', '_', '.'}

class Pattern(object):
    def __init__(self, pattern_str):
        self._pattern_str = pattern_str
        self._pattern_regex = None
    
    def __str__(self):
        return self.pattern_str
    
    __repr__ = __str__
    
    @property
    def pattern_str(self):
        return self._pattern_str
    
    def __hash__(self):
        return hash(self.pattern_str)
    
    def __eq__(self, o):
        if not isinstance(o, Pattern):
            return False
        return self.pattern_str == o.pattern_str
    
    def match(self, part):
        if not self._pattern_regex:
            self._pattern_regex = re.compile("".join(('^', self._pattern_str, '$')), re.I)
        return True if re.match(self._pattern_regex, part) else False
               
class BasePattern(object):
    SINGLE_DIGIT = Pattern(BasePatternRule.SINGLE_DIGIT)
    SINGLE_CHAR = Pattern(BasePatternRule.SINGLE_CHAR)
    ALL_DIGIT = Pattern(BasePatternRule.ALL_DIGIT)
    ALL_CHAR = Pattern(BasePatternRule.ALL_CHAR)  
    DIGIT_CHAR_MIX = Pattern(BasePatternRule.DIGIT_CHAR_MIX)
    DOT = Pattern(BasePatternRule.DOT)
    ALL_MATCH = Pattern(BasePatternRule.ALL_MATCH)
    EMPTY = Pattern(BasePatternRule.EMPTY)

_PATTERN_CACHE = {}
for obj_str in [obj_str for obj_str in dir(BasePattern) if not obj_str.startswith('__')]:
    obj = getattr(BasePattern, obj_str)
    _PATTERN_CACHE[obj.pattern_str] = obj

def get_pattern_from_cache(pattern_str):
    if pattern_str not in _PATTERN_CACHE:
        _PATTERN_CACHE[pattern_str] = Pattern(pattern_str)
    return _PATTERN_CACHE[pattern_str]

class PartAndPattern(object):
    def __init__(self, part, pattern):
        self._part = part
        self._pattern = pattern
        
    @property
    def part(self):
        return self._part
    
    def __str__(self):
        return ' '.join((self.part, self.pattern_str))
    
    __repr__ = __str__
    
    @property
    def pattern(self):
        return self._pattern
    
    @property
    def pattern_str(self):
        return self._pattern.pattern_str
    
    def has_multi_part(self):
        return False
    
    @property
    def part_num(self):
        return 1
    
    def __hash__(self):
        return hash(self.pattern_str)
    
    def __eq__(self, o):
        if not isinstance(o, PartAndPattern):
            return False
        return self.pattern_str == o.pattern_str

EMPTY_PART_PATTERN = PartAndPattern(BasePatternRule.EMPTY, BasePattern.EMPTY)

class GroupPartAndPattern(PartAndPattern):
    def __init__(self, part_pattern_list):
        self._part = ''.join([pp.part for pp in part_pattern_list])
        self._pattern = get_pattern_from_cache(''.join([pp.pattern_str for pp in part_pattern_list]))
        self._part_pattern_list = part_pattern_list
    
    def has_multi_part(self):
        return True if self.part_num > 1 else False
    
    @property
    def part_num(self):
        return sum([p.part_num for p in self._part_pattern_list])
    
    @property
    def part_pattern_list(self):
        return self._part_pattern_list
    
_NORM_STR_CACHE = {}

def char_normlize(raw_string, keep_chars=set()):
    if raw_string in _NORM_STR_CACHE:
        return _NORM_STR_CACHE[raw_string]
    s = StringIO.StringIO()
    t = StringIO.StringIO()
    last_c = None
    for c in raw_string:
        if c in CHAR_DIGIT_SET:
            if last_c not in CHAR_DIGIT_SET:
                t.seek(0)
                w = t.read()
                l = len(w)
                if l > 0:
                    if w[0] not in keep_chars:
                        r = CHAR_RULE.get(w[0])
                        w = _exact_num(r, l)
                    s.write(w)
                    t = StringIO.StringIO()
        else:
            if last_c != c:
                t.seek(0)
                w = t.read()
                l = len(w)
                if l > 0 and w[0] not in CHAR_DIGIT_SET and w[0] not in keep_chars:
                    r = CHAR_RULE.get(w[0])
                    w = _exact_num(r, l)
                s.write(w)
                t = StringIO.StringIO()
        t.write(c)
        last_c = c
            
    t.seek(0)
    w = t.read()
    l = len(w)
    if last_c and last_c not in CHAR_DIGIT_SET and w[0] not in keep_chars:
        r = CHAR_RULE.get(w[0])
        w = _exact_num(r, l)
    s.write(w)
    s.seek(0)
    n = s.read()
    _NORM_STR_CACHE[raw_string] = n 
    return n

def get_part_pattern_from_raw_string(raw_string, config, last_dot_split=False):
    last_char = None
    char_rule_list = []
    char_buf_list = []
    part_pattern_list = []
    for c in raw_string:
        if c in SPLIT_CHAR:  # useless
            if c != last_char:
                part_pattern = _process_char_rule(char_rule_list, char_buf_list, config)
                del char_rule_list[:]
                del char_buf_list[:]
                if part_pattern.pattern_str:
                    part_pattern_list.append(part_pattern)
                part_pattern_list.append(PartAndPattern(c, get_pattern_from_cache(CHAR_RULE.get(c))))
        else:
            define_char_rule(c, char_rule_list, char_buf_list, config)
        last_char = c
    part_pattern = _process_char_rule(char_rule_list, char_buf_list, config, last_dot_split)
    if part_pattern.pattern_str:
        if len(part_pattern_list) <= 0:
            return part_pattern
        part_pattern_list.append(part_pattern)
    return GroupPartAndPattern(part_pattern_list)

def _merge_char_rule(rules):
    rules = sorted(rules)
    return _one_or_more(''.join(rules))

def _one_or_more(rule):
    return '[%s]+' % rule

def _exact_num(rule, num):
    if num == 1:
        return '[%s]' % rule
    return '[%s]{%d}' % (rule, num)

def _normalize(letter, rule):
    if rule in _ALL_SIGN_RULE_SET:
        l = len(letter)
        return _exact_num(rule, l)
    return letter

def _letter_type(letter):
    s = set()
    for c in letter:
        if len(s) == 2:
            return BasePatternRule.CHAR_ALL
        if c in _CHAR_SET_LOW:
            s.add(BasePatternRule.CHAR_LOW)
        elif c in _CHAR_SET_UPPER:
            s.add(BasePatternRule.CHAR_UPPER)
    if len(s) == 1:
        return list(s)[0]
    return BasePatternRule.CHAR_ALL

def _toggle_rule_case(letter, rule):
    if rule == BasePatternRule.CHAR_LOW:
        return _letter_type(letter)
    elif rule == BasePatternRule.DIGIT_AND_CHAR:
        t = _letter_type(letter)
        if t == BasePatternRule.CHAR_UPPER:
            return BasePatternRule.DIGIT_AND_CHAR_UPPER
        elif t == BasePatternRule.CHAR_ALL:
            return BasePatternRule.DIGIT_AND_CHAR_ALL
    return rule

def _process_char_rule(char_rule_list, char_buf_list, config, last_dot_split=False):
    if len(char_buf_list) <= 0:
        return EMPTY_PART_PATTERN
    char_list = []
    norm_char_rule_list = []
    rl = len(char_rule_list)
    last_dot_pos = -99
    for idx, s in enumerate(char_buf_list[::-1]):
        rule_idx = rl - idx - 1
        s.seek(0)
        letter = s.readline()
        char_list.append(_normalize(letter, char_rule_list[rule_idx]))
        norm_char_rule_list.append(_toggle_rule_case(letter, char_rule_list[rule_idx]))
        if last_dot_split and last_dot_pos < 0 and char_rule_list[rule_idx] == BasePatternRule.DOT:
            last_dot_pos = rule_idx
    char_list.reverse()
    norm_char_rule_list.reverse()
    char_rule_list = norm_char_rule_list
        
    if not (last_dot_split and last_dot_pos > rl - 3 and last_dot_pos < rl - 1):
        return _redefine_char_rule(char_rule_list, char_list, config)
    ext_part = False
    if last_dot_split and config.reserved_ext_names:
        ext_name = None
        if last_dot_pos == rl - 2:
            ext_name = char_list[-1]
            if ext_name in config.reserved_ext_names:
                char_rule_list[-1] = char_list[-1]
                ext_part = True
        else:
            ext_name = "".join(char_list[last_dot_pos + 1:])
            if ext_name in config.reserved_ext_names:
                del char_list[last_dot_pos + 1:]
                del char_rule_list[last_dot_pos + 1:]
                char_list.append(ext_name)
                char_rule_list.append(ext_name)
                ext_part = True
    
    part_pattern_before_dot = _redefine_char_rule(char_rule_list[0:last_dot_pos], char_list[0:last_dot_pos], config)
    part_pattern_after_dot = _redefine_char_rule(char_rule_list[last_dot_pos:], char_list[last_dot_pos:], config, ext_part)
    
    return GroupPartAndPattern([part_pattern_before_dot, part_pattern_after_dot])

def _redefine_char_rule(char_rule_list, char_list, config, ext_part=False):
    if ext_part:
        def _ext_pattern(part, pattern_str):
            if pattern_str != BasePatternRule.DOT:
                pass
            else:
                if part.endswith('}'):
                    pattern_str = _one_or_more(pattern_str)
                else:
                    pattern_str = _exact_num(pattern_str, 1)
            return get_pattern_from_cache(pattern_str)
        return GroupPartAndPattern([PartAndPattern(part, _ext_pattern(part, pattern_str)) for part, pattern_str in zip(char_list, char_rule_list)]) 
    char_rule_set = set(char_rule_list)
    if BasePatternRule.CHAR_ALL in char_rule_set:
        char_rule_set.discard(BasePatternRule.CHAR_ALL)
        char_rule_set.update(_CHAR_ALL_SET)
    if BasePatternRule.DIGIT_AND_CHAR in char_rule_set:
        char_rule_set.discard(BasePatternRule.DIGIT_AND_CHAR)
        char_rule_set.update(_DIGIT_AND_CHAR_SET)
    if BasePatternRule.DIGIT_AND_CHAR_UPPER in char_rule_set:
        char_rule_set.discard(BasePatternRule.DIGIT_AND_CHAR_UPPER)
        char_rule_set.update(_DIGIT_AND_CHAR_UPPER_SET)
    if BasePatternRule.DIGIT_AND_CHAR_ALL in char_rule_set:
        char_rule_set.discard(BasePatternRule.DIGIT_AND_CHAR_ALL)
        char_rule_set.update(_DIGIT_AND_CHAR_ALL_SET)
        
    rule_num = len(char_rule_set)
    if BasePatternRule.ALL_MATCH in char_rule_set or rule_num > config.all_match_pat_num_threshold:
        return PartAndPattern(''.join(char_list), BasePattern.ALL_MATCH)
    
    cl = len(char_list)
    if cl == 1:
        return PartAndPattern(char_list[0], get_pattern_from_cache(_one_or_more(char_rule_list[0])))
    if cl > config.merge_part_num_threshold:
        return PartAndPattern(''.join(char_list), get_pattern_from_cache(_merge_char_rule(char_rule_set)))
    
    if not char_rule_set.intersection(_DIGIT_AND_CHAR_ALL_SET):
        return PartAndPattern(''.join(char_list), get_pattern_from_cache(_merge_char_rule(char_rule_set)))
    
    return GroupPartAndPattern([PartAndPattern(part, get_pattern_from_cache(_one_or_more(pattern_str))) for part, pattern_str in zip(char_list, char_rule_list)])    

def define_char_rule(char, char_rule_list, char_buf_list, config):
    last_rule = char_rule_list[-1] if char_rule_list else None
    if last_rule == BasePatternRule.ALL_MATCH:
        char_buf_list[-1].write(char)
        return
    
    rule = CHAR_RULE.get(char, BasePatternRule.ALL_MATCH)
    if last_rule == BasePatternRule.DIGIT_AND_CHAR and rule in _DIGIT_AND_CHAR_SET:
        char_buf_list[-1].write(char)
        return
    
    if last_rule == rule:
        char_buf_list[-1].write(char)
        return
    
    crl = len(char_rule_list)
    append = True
    if rule in _DIGIT_AND_CHAR_SET and crl >= config.digit_char_merge_threshold:
        merge_start_idx = crl - config.digit_char_merge_threshold
        s = set(char_rule_list[merge_start_idx:crl])
        if len(s) == 2 and BasePatternRule.CHAR in s and BasePatternRule.DIGIT in s:
            append = False
            del char_rule_list[merge_start_idx:]
            rule = BasePatternRule.DIGIT_AND_CHAR
            new_io = StringIO.StringIO()
            for sio in char_buf_list[merge_start_idx:]:
                sio.seek(0)
                new_io.write(sio.readline())
            del char_buf_list[merge_start_idx:]
            char_buf_list.append(new_io)
    char_rule_list.append(rule)
    if append:
        char_buf_list.append(StringIO.StringIO())
    char_buf_list[-1].write(char)

def pattern_degree_stats(pattern_str, all_match_pat_num_threshold):
    nex_degree = mst_degree = 0
    idx = 0
    l = len(pattern_str)
    
    while idx >= 0 and idx < l:
        if pattern_str[idx] == '[':
            idx_s = idx_e = idx
            while True:
                idx_e = pattern_str.find(']', idx_e + 1)
                if idx_e < 0:
                    raise Exception('Error Pattern')
                if pattern_str[idx_e - 1] == '\\':
                    continue
                break
            part = pattern_str[idx_s + 1:idx_e]
            if idx_e == l - 1:
                if part not in _ALL_SIGN_RULE_SET:
                    nex_degree += 1
            else:
                if pattern_str[idx_e + 1] == '+':
                    mst_degree += 1
                else:
                    if part not in _ALL_SIGN_RULE_SET:
                        nex_degree += 1
            idx = idx_e + 1
        elif pattern_str[idx] == '.':
            if idx + 3 > l:
                raise Exception('Error Pattern')
            if pattern_str[idx:idx + 3] == '.*?':
                mst_degree += all_match_pat_num_threshold
                idx += 3
                continue
            else:
                raise Exception('Error Pattern')
        else:
            idx += 1
    return nex_degree, mst_degree

def _split_pattern(part):
    parts = []
    l = len(part)
    idx = 0
    while idx >= 0 and idx < l:
        c = part[idx]
        if c in set('0aA'):
            e = idx + 3
        elif c == '\\':
            e = idx + 2
        else:
            e = idx + 1
        p = part[idx:e]
        parts.append(_ALL_SIGN_RULE_DICT.get(p, p))
        idx = e
    return parts

def _concrete_c(c):
    import random
    if c == BasePatternRule.CHAR_LOW:
        return random.choice(string.ascii_lowercase)
    elif c == BasePatternRule.CHAR_UPPER:
        return random.choice(string.ascii_uppercase)
    elif c == BasePatternRule.DIGIT:
        return random.choice(string.digits)
    elif c in _ALL_SIGN_RULE_DICT:
        return _ALL_SIGN_RULE_DICT[c]
    
    raise Exception('Invalid c')

def trans_to_base_patterns(patterns, config, url_struct):
    base_patterns = []
    for idx, pattern_str in enumerate(patterns):
        last_dot_split = True if idx == url_struct.path_depth - 1 else False
        base_patterns.append(get_base_pattern(pattern_str, config, last_dot_split))
    return base_patterns

def get_base_pattern(pattern_str, config, last_dot_split=False):
    last_dot_pos = -1
    if last_dot_split:
        last_dot_pos = pattern_str.rfind('[\\.]')
    base_pattern_s = StringIO.StringIO()
    s = StringIO.StringIO()
    l = len(pattern_str)
    idx = 0
    while idx >= 0 and idx < l:
        c = pattern_str[idx]
        if c in CHAR_DIGIT_SET:
            s.write(c)
        elif c == '.':
            if pattern_str[idx:idx + 3] == BasePatternRule.ALL_MATCH:
                base_pattern_s.write(BasePatternRule.ALL_MATCH)
                idx += 2
        elif c == '[':
            idx_s = idx_e = idx
            while True:
                idx_e = pattern_str.find(']', idx_e + 1)
                if idx_e < 0:
                    raise Exception('Error Pattern')
                if pattern_str[idx_e - 1] == '\\':
                    continue
                break
            part = pattern_str[idx_s + 1:idx_e]
            num = 1
            if idx_e + 1 < l:
                if pattern_str[idx_e + 1] == '{':
                    e = pattern_str.find('}', idx_e + 1)
                    if e < 0:
                        raise Exception('Error Pattern')
                    num = int(pattern_str[idx_e + 2:e])    
                    idx = e
                elif pattern_str[idx_e + 1] == '+':
                    idx = idx_e + 1
                else:
                    idx = idx_e
            else:
                idx = idx_e
            sp = _split_pattern(part)
            if len(sp) > 1 or (part == BasePatternRule.DOT and last_dot_pos == idx_s):
                s.seek(0)
                ss = s.read()
                if ss:
                    bp = get_part_pattern_from_raw_string(ss, config)
                    base_pattern_s.write(bp.pattern_str)
                    s = StringIO.StringIO()
                if len(sp) > 1 or num > 1:
                    base_pattern_s.write(_one_or_more(part))
                else:
                    base_pattern_s.write('[%s]' % part)
                if last_dot_pos == idx_s and idx + 1 < l:
                    if pattern_str[idx + 1:] in config.reserved_ext_names:
                        base_pattern_s.write(pattern_str[idx + 1:])
                        idx = l - 1
                    else:
                        base_pattern_s.write('+')
            else:
                c = _concrete_c(part) * num
                s.write(c)
        else:
            raise Exception('Error Pattern')
        idx += 1
    s.seek(0)
    ss = s.read()
    if ss:
        bp = get_part_pattern_from_raw_string(ss, config)
        base_pattern_s.write(bp.pattern_str)
    base_pattern_s.seek(0)
    return base_pattern_s.read()

def parse_pattern_string(pattern_str):
    if pattern_str[0] != '/':
        return None
    idx_p = 0
    idx_q = pattern_str.find('[\\?]')
    idx_f = pattern_str.find('#')
    path_part = None
    query_part = None
    fragment_part = None
    if idx_q < 0 and idx_f < 0:
        path_part = pattern_str[idx_p:]
    elif idx_q > 0 and idx_f > 0:
        if idx_f > idx_q:
            path_part = pattern_str[idx_p:idx_q]
            query_part = pattern_str[idx_q + 4:idx_f]
        else:
            path_part = pattern_str[idx_p:idx_f]
        fragment_part = pattern_str[idx_f + 1:]
    elif idx_q < 0 and idx_f > 0:
        path_part = pattern_str[idx_p:idx_f]
        fragment_part = pattern_str[idx_f + 1:]
    elif idx_q > 0 and idx_f < 0:
        path_part = pattern_str[idx_p:idx_q]
        query_part = pattern_str[idx_q + 4:]
    
    from util import parse_url_part
    return parse_url_part(path_part, query_part, fragment_part, pattern_str[-1], False)

if __name__ == "__main__":
#     print parse_pattern_string('/[a-z]+[\\.]asp[\\?]i[_]d=[%0-9a-z]+#')[0].query_keys
    import config
    p = '[a-z]+[\\.]shtml'
    p = '[a-z]+[\\-][0-9]+[\\-][0-9]+[\\.]shtml'
    p = '[%0-9a-z]+'
    p = '[0-9]+[\\-][0-9]+[\\.]{1}html'
    p = '[A-Za-z]+[A-Z\\-]+'
    p = '[A-Za-z]+[\\-][A-Z]+'
    p = '[\-][a-z]+'
    p = '[A-Za-z]+[\\-][A-Z]+'
    p = 'clinical-outcomes-assessment-recommendations-'
#     print get_base_pattern(p, config.default_preprocess_config(), True)
#     p = 'a1b2c3.ccc'
#     p = 'n415455418.shtml'
    print get_part_pattern_from_raw_string(p, config.default_preprocess_config(),True)
