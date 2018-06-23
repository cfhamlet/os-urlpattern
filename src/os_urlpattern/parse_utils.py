import copy
import hashlib
from collections import namedtuple

from .compat import ParseResult, StringIO, urlparse
from .definition import (ASCII_DIGIT_SET, BLANK_LIST, CHAR_RULE_DICT,
                         DEFAULT_ENCODING, DIGIT_AND_ASCII_RULE_SET,
                         EMPTY_LIST, EMPTY_TUPLE, LITERAL_RULES_PRIFIX,
                         QUERY_PART_RESERVED_CHARS, SIGN_RULE_SET,
                         BasePatternRule, Symbols)
from .exceptions import (InvalidCharException, InvalidPatternException,
                         IrregularURLException)

MIXED_RULE_SET = copy.copy(DIGIT_AND_ASCII_RULE_SET)
MIXED_RULE_SET.add(Symbols.PERCENT)


class URLMeta(namedtuple('URLMeta', 'path_depth query_keys has_fragment')):
    """The URL structure meta.

    Attributes:
        path_depth (int): The num of URL path levels.
        querys_keys (:obj:`list` of :obj:`str`): A list contains all of the query keys.
        has_fragment (bool): Whether the URL have fragmemt component.

    """
    __slots__ = ()

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        s = StringIO()
        s.write(str(self.path_depth))
        if self.query_keys:
            s.write(Symbols.QUESTION)
            s.write(Symbols.AMPERSAND.join(self.query_keys))
        if self.has_fragment:
            s.write(Symbols.NUMBER)
        s.seek(0)
        return s.read()

    @property
    def depth(self):
        return self.path_depth + len(self.query_keys) + (1 if self.has_fragment else 0)

    def __eq__(self, o):
        if not isinstance(o, URLMeta):
            return False
        return hash(o) == hash(self)


def specify_rule(rule, num):
    """Specify the format of the rule.

    num == 1 will return [rule], single
    num > 1  will return [rule]{num}, with number
    num < 0  will return [rule]+, wildcard
    num == 0 will raise ValueError

    Args:
        rule (str): The raw rule string to be secified.
        num (int): The num of the rule. Can't be 0. 

    Raises:
        ValueError: If the num == 0.

    Returns:
        str: The specified format of the rule.

    Examples:

        >>> from os_urlpattern.parse_utils import specify_rule
        >>> specify_rule('a-z', 1)
        [a-z]
        >>> specify_rule('a-z', 2)
        [a-z]{2}
        >>> specify_rule('a-z', -1)
        [a-z]+

    """

    if num == 1:
        return u'[%s]' % rule
    elif num < 0:
        return u'[%s]+' % rule
    elif num > 1:
        return u'[%s]{%d}' % (rule, num)
    else:
        raise ValueError('Invalid num %s' % str(num))


def wildcard_rule(rule):
    """Specify the wildcard format of the rule.

    Shotcut of specify_rule(rule, -1).

    Args:
        rule (str): The raw rule string to be secified.

    Returns:
        str: The wildcard format of the rule.
    """
    return specify_rule(rule, -1)


def normalize_str_list(str_list, reserved_chars):
    return [normalize_str(i, reserved_chars) for i in str_list]


def normalize_str(raw_string, reserved_chars=None):
    """Normalize a string.

    Transfor the continuous same signs in the string to the format of
    [sign_rule]{num}, if the sign is not in zhe reserved_chars.

    Args:
        raw_string (str): The string to be normalized.
        reserved_chars ([type], optional): Defaults to None. Reserved chars
            which are not to be normalized.

    Returns:
        str: The normalized string.

    Examples:

        >>> from os_urlpattern.parse_utils import normalize_str
        >>> normalize_str('abc==123---')
        u'abc[=]{2}123[\\-]{3}'

    """
    normalized_str = StringIO()
    frag = StringIO()
    last_c = None
    for c in raw_string:
        if c in ASCII_DIGIT_SET:
            if last_c and last_c not in ASCII_DIGIT_SET:
                frag.seek(0)
                w = frag.read()
                l = len(w)
                if l > 0:
                    if not reserved_chars or w[0] not in reserved_chars:
                        r = CHAR_RULE_DICT.get(w[0])
                        w = specify_rule(r, l)
                    normalized_str.write(w)
                    frag = StringIO()
        else:
            if last_c != c:
                frag.seek(0)
                w = frag.read()
                l = len(w)
                if l > 0 and w[0] not in ASCII_DIGIT_SET and \
                        (not reserved_chars or w[0] not in reserved_chars):
                    r = CHAR_RULE_DICT.get(w[0])
                    w = specify_rule(r, l)
                normalized_str.write(w)
                frag = StringIO()
        frag.write(c)
        last_c = c

    frag.seek(0)
    w = frag.read()
    l = len(w)
    if last_c and last_c not in ASCII_DIGIT_SET and \
            (not reserved_chars or w[0] not in reserved_chars):
        r = CHAR_RULE_DICT.get(w[0])
        w = specify_rule(r, l)
    normalized_str.write(w)
    normalized_str.seek(0)
    return normalized_str.read()


def parse_url(url):
    """Parse a URL into 6 components.

    <scheme>://<netloc>/<path>;<params>?<query>#<fragment>

    Like the built-in urlparse method, but handle some unusual situation.

    Args:
        url (unicode): The URL to be parsed.

    Returns:
        ParseResult: A 6-tuple, (scheme, netloc, path, params, query, fragment).
    """
    scheme, netloc, path, params, query, fragment = urlparse(url)
    if not fragment:
        if url[-1] != Symbols.NUMBER:
            fragment = None
            if not query and url[-1] != Symbols.QUESTION:
                query = None
        elif not query and url[-2] != Symbols.QUESTION:
            query = None
    elif not query:
        if url[len(url) - len(fragment) - 2] != Symbols.QUESTION:
            query = None
    return ParseResult(scheme, netloc, path, params, query, fragment)


def filter_useless(objs):
    """Filter the useless objects in the list.

    If bool(object) == False, the object is useless except the last one.

    Args:
        objs (list): The object list will be filtered.

    Returns:
        list: The filterd list

    Examples:

        >>> from os_urlpattern.parse_utils import filter_useless
        >>> filter_useless([0,1,0,0])
        [1, 0]

    """
    keep = {'c': 0, 'l': len(objs)}

    def _filterd(x):
        keep['c'] += 1
        if not x:
            if keep['c'] == keep['l']:
                return True
            return False
        else:
            return True

    return list(filter(_filterd, objs))


def parse_query_string(query_string):
    if query_string is None:
        return EMPTY_LIST, EMPTY_LIST
    elif query_string == Symbols.EMPTY:
        return BLANK_LIST, BLANK_LIST
    elif query_string.endswith(Symbols.AMPERSAND):
        raise IrregularURLException('Invalid url query')
    kv_type = True  # qkey True, qvalue False
    last_c = None
    kv_buf = {True: StringIO(), False: StringIO()}
    kv_list = {True: [], False: []}
    for i in query_string:
        if i == Symbols.EQUALS and kv_type:
            s = kv_buf[kv_type]
            s.write(i)
            s.seek(0)
            kv_list[kv_type].append(s.read())
            kv_buf[kv_type] = StringIO()
            kv_type = not kv_type
        elif i == Symbols.AMPERSAND:
            if last_c is None or last_c == Symbols.AMPERSAND:
                raise IrregularURLException('Invalid url query')
            s = kv_buf[kv_type]
            s.seek(0)
            kv_list[kv_type].append(s.read())
            kv_buf[kv_type] = StringIO()
            if kv_type:
                kv_list[False].append(Symbols.EMPTY)  # treat as value-less
            else:
                kv_type = not kv_type
        else:
            s = kv_buf[kv_type]
            s.write(i)
        last_c = i

    s = kv_buf[kv_type]
    s.seek(0)
    kv_list[kv_type].append(s.read())
    if kv_type:  # treat as value-less
        kv_list[False].append(Symbols.EMPTY)

    # only one query without value, treat as key-less
    if len(kv_list[True]) == 1 and not kv_list[True][0].endswith(Symbols.EQUALS):
        kv_list[False][0], kv_list[True][0] = kv_list[True][0], kv_list[False][0]
    return kv_list[True], kv_list[False]


def mix(pieces, rules):
    """Combine the sub-pieces and sub-rules.

    If the sub pieces have continuous letter num and percent sign fragments
    will be combine into one piece as well as the rules.

    Args:
        pieces (list): List of the raw pieces.
        rules (list): List of the rules.

    Returns:
        tuple: Mixed pieces and mixed rules.
    """
    mixed_pieces = []
    mixed_rules = []

    t_pieces = []
    t_rules = []
    t_mix = False
    for piece, rule in zip(pieces, rules):
        if rule in MIXED_RULE_SET:
            if t_rules and not t_mix:
                mixed_pieces.extend(t_pieces)
                mixed_rules.extend(t_rules)
                t_pieces = []
                t_rules = []
            t_mix = True
        else:
            if t_rules and t_mix:
                mixed_pieces.append(u''.join(t_pieces))
                mixed_rules.append(u''.join(sorted(set(t_rules))))
                t_pieces = []
                t_rules = []
            t_mix = False
        t_pieces.append(piece)
        t_rules.append(rule)
    if t_mix:
        mixed_pieces.append(u''.join(t_pieces))
        mixed_rules.append(u''.join(sorted(set(t_rules))))
    else:
        mixed_pieces.extend(t_pieces)
        mixed_rules.extend(t_rules)
    return mixed_pieces, mixed_rules


def unpack(result, norm_query_key=True):
    pieces = filter_useless(result.path.split(Symbols.SLASH)[1:])
    path_depth = len(pieces)
    if path_depth <= 0:
        raise IrregularURLException('Invalid url depth')

    keys, values = parse_query_string(result.query)
    if norm_query_key:
        keys = normalize_str_list(keys, QUERY_PART_RESERVED_CHARS)
    has_fragment = False if result.fragment is None else True

    url_meta = URLMeta(path_depth, keys, has_fragment)
    pieces.extend(values)
    if has_fragment:
        pieces.append(result.fragment)
    return url_meta, pieces


def pack(url_meta, paths):
    s = StringIO()
    s.write(Symbols.SLASH)
    query_depth = len(url_meta.query_keys)
    idx = url_meta.path_depth + query_depth
    p = Symbols.SLASH.join([str(p) for p in paths[0:url_meta.path_depth]])
    s.write(p)
    if query_depth > 0:
        s.write(BasePatternRule.SINGLE_QUESTION)
        kv = zip(url_meta.query_keys,
                 [str(p) for p in paths[url_meta.path_depth:idx]])
        s.write(Symbols.AMPERSAND.join(
            [u''.join((str(k), str(v))) for k, v in kv]))

    if url_meta.has_fragment:
        s.write(Symbols.NUMBER)
        s.write(u''.join([str(p) for p in paths[idx:]]))
    s.seek(0)
    return s.read()


def analyze_url(url):
    """Parse a URL to URLMeta object and a list of raw pieces.

    Args:
        url (unicode): The URL to be parsed.

    Returns:
        tuple: URLMeta object, list of raw pieces.
    """

    result = parse_url(url)
    return unpack(result, True)


class ParsedPiece(object):
    """The parsed piece object.

    It contains the sub-pieces of a piece and the corresponding sub-rules.
    With it, you can get fuzzy rule and the length of the entire piece.
    It is hashable

    """
    __slots__ = ('_pieces', '_rules', '_piece', '_piece_length', '_fuzzy_rule')

    def __init__(self, pieces, rules):
        """Init the ParsedPiece object.

        Args:
            pieces (list): The list of parsed pieces.
            rules (list): The list of the rules of each parsed pieces.
        """
        self._pieces = pieces
        self._rules = rules
        self._piece_length = -1
        self._piece = pieces[0] if len(pieces) == 1 else None
        self._fuzzy_rule = rules[0] if len(rules) == 1 else None

    @property
    def fuzzy_rule(self):
        if not self._fuzzy_rule:
            self._fuzzy_rule = u''.join(sorted(set(self.rules)))
        return self._fuzzy_rule

    @property
    def rules(self):
        return self._rules

    @property
    def pieces(self):
        return self._pieces

    @property
    def piece_length(self):
        if self._piece_length < 0:
            piece = self.piece
            length_base = length = len(piece)
            idx = 0
            while idx < length_base:
                c = piece[idx]
                if c == Symbols.BRACKETS_L or c == Symbols.BRACKETS_R:
                    if idx == 0 or piece[idx - 1] != Symbols.BACKSLASH:
                        length += -1
                elif c == Symbols.BACKSLASH:
                    if piece[idx + 1] != Symbols.BACKSLASH:
                        length += -1
                elif c == Symbols.BRACES_L:
                    if piece[idx - 1] == Symbols.BRACKETS_R:
                        e = piece.index(Symbols.BRACES_R, idx)
                        length += int(piece[idx + 1:e]) - 1 - (e - idx + 1)
                        idx = e
                idx += 1

            self._piece_length = length
        return self._piece_length

    def __eq__(self, o):
        if not isinstance(o, ParsedPiece):
            return False
        return self.piece == o.piece

    def __hash__(self):
        return hash(self.piece)

    @property
    def piece(self):
        if self._piece is None:
            self._piece = u''.join(self._pieces)
        return self._piece

    def __str__(self):
        return str(zip(self.pieces, self.rules))

    __repr__ = __str__


EMPTY_PARSED_PIECE = ParsedPiece(EMPTY_TUPLE, EMPTY_TUPLE)


class PieceParser(object):
    """Parser to parse the piece of the URL.

    Used it to generate ParsedPiece object from the piece of URL.
    """

    def __init__(self):
        self._reset()

    def _reset(self):
        self._rule_list = []
        self._piece_list = []

    def parse(self, piece):
        self._reset()
        self._preprocess(piece)
        return self._create_parsed_piece()

    def _preprocess(self, piece):
        for c in piece:
            self._define(c)
        for idx, buf in enumerate(self._piece_list):
            buf.seek(0)
            letter = buf.read()
            self._piece_list[idx] = self._normalize(
                letter, self._rule_list[idx])

    def _define(self, char):
        last_rule = self._rule_list[-1] if self._rule_list else None
        try:
            rule = CHAR_RULE_DICT[char]
        except KeyError as e:
            raise InvalidCharException('Invalid char %s' % e)

        if last_rule != rule:
            self._piece_list.append(StringIO())
            self._rule_list.append(rule)
        self._piece_list[-1].write(char)

    def _normalize(self, letter, rule):
        if rule in SIGN_RULE_SET:
            return specify_rule(rule, len(letter))
        return letter

    def _create_parsed_piece(self):
        return ParsedPiece(tuple(self._piece_list), tuple(self._rule_list))


def digest(url_meta, parts):
    """Get hex digest string from the given URLMeta and strings.

    Args:
        url_meta (URLMeta): The URLMeta object.
        parts (list): A list of strings.

    Returns:
        str: Digest value as a string of hexadecimal digits.
    """
    return hashlib.md5(pack(url_meta, parts).encode(DEFAULT_ENCODING)).hexdigest()


def analyze_pattern_path_string(pattern_path_string):
    idx_p = 0
    idx_q = pattern_path_string.find(BasePatternRule.SINGLE_QUESTION)
    idx_f = pattern_path_string.find(Symbols.NUMBER)
    path = query = fragment = None
    if idx_q < 0 and idx_f < 0:
        path = pattern_path_string[idx_p:]
    elif idx_q > 0 and idx_f > 0:
        if idx_f > idx_q:
            path = pattern_path_string[idx_p:idx_q]
            query = pattern_path_string[idx_q + 4:idx_f]
        else:
            path = pattern_path_string[idx_p:idx_f]
        fragment = pattern_path_string[idx_f + 1:]
    elif idx_q < 0 and idx_f > 0:
        path = pattern_path_string[idx_p:idx_f]
        fragment = pattern_path_string[idx_f + 1:]
    elif idx_q > 0 and idx_f < 0:
        path = pattern_path_string[idx_p:idx_q]
        query = pattern_path_string[idx_q + 4:]

    scheme = netloc = params = u''
    return ParseResult(scheme, netloc, path, params, query, fragment)


def parse_pattern_path_string(pattern_path_string):
    result = analyze_pattern_path_string(pattern_path_string)
    return unpack(result, False)


def parse_pattern_string(pattern_string):
    if pattern_string == Symbols.EMPTY:
        return BLANK_LIST
    pattern_units = []
    l = len(pattern_string)
    s = StringIO()
    idx = 0
    last_rule = None
    while idx < l:
        c = pattern_string[idx]
        if c == Symbols.BRACKETS_L:
            if last_rule is not None:
                s.seek(0)
                pattern_units.append(s.read())
                s = StringIO()
                last_rule = None

            idx_s = idx
            while True:
                idx = pattern_string.find(Symbols.BRACKETS_R, idx + 1)
                if idx < 0:
                    raise InvalidPatternException(
                        'Missing \'%s\'' % Symbols.BRACKETS_R)
                elif pattern_string[idx - 1] == Symbols.BACKSLASH:
                    continue
                break
            if idx + 1 < l:
                if pattern_string[idx + 1] == Symbols.BRACES_L:
                    old_idx = idx + 2
                    idx = pattern_string.find(Symbols.BRACES_R, idx + 1)
                    if idx < 0:
                        raise InvalidPatternException(
                            'Missing \'%s\'' % Symbols.BRACES_R)
                    num_str = pattern_string[old_idx:idx]
                    if not num_str.isdigit():
                        raise InvalidPatternException('Not digit %s' % num_str)

                elif pattern_string[idx + 1] == Symbols.PLUS:
                    idx += 1
            idx += 1
            pattern_units.append(pattern_string[idx_s:idx])
        else:
            rule = CHAR_RULE_DICT[c]
            if rule not in DIGIT_AND_ASCII_RULE_SET:
                raise InvalidPatternException(
                    'Invalid pattern %s' % pattern_string)
            if last_rule is None:
                s.write(c)
            else:
                if rule == last_rule:
                    s.write(c)
                else:
                    s.seek(0)
                    pattern_units.append(s.read())
                    s = StringIO()
                    s.write(c)
            last_rule = rule
            idx += 1
    if last_rule is not None:
        s.seek(0)
        pattern_units.append(s.read())

    return pattern_units


def parse_pattern_unit_string(pattern_unit_string):
    rules = set()
    num = 1
    if pattern_unit_string == Symbols.EMPTY:
        rules.add(Symbols.EMPTY)
    elif pattern_unit_string[0] != Symbols.BRACKETS_L:
        rules.add(CHAR_RULE_DICT[pattern_unit_string[0]])
        num = len(pattern_unit_string)
    else:
        if pattern_unit_string[-1] == Symbols.BRACKETS_R:
            num = 1
        elif pattern_unit_string[-1] == Symbols.BRACES_R:
            t = pattern_unit_string.rfind(Symbols.BRACES_L)
            num = int(pattern_unit_string[t + 1:-1])
        elif pattern_unit_string[-1] == Symbols.PLUS:
            num = -1
        t = pattern_unit_string.rfind(Symbols.BRACKETS_R)
        p_str = pattern_unit_string[1:t]
        l = len(p_str)
        idx = 0
        while idx < l:
            c = p_str[idx]
            n = 3
            if c in LITERAL_RULES_PRIFIX:
                pass
            elif c == Symbols.BACKSLASH:
                n = 2
            else:
                n = 1
            rules.add(p_str[idx:idx + n])
            idx += n
    return rules, num
