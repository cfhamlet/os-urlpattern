import pytest

from os_urlpattern.exceptions import (InvalidCharException,
                                      InvalidPatternException,
                                      IrregularURLException)
from os_urlpattern.parse_utils import (PieceParser, URLMeta, analyze_url,
                                       digest, filter_useless,
                                       normalize_str, pack,
                                       parse_pattern_path_string,
                                       parse_pattern_string,
                                       parse_pattern_unit_string,
                                       parse_query_string, parse_url)
from os_urlpattern.pattern import Pattern


def test_normalize_str():
    data = [
        ('a', 'a'),
        ('ab=', 'ab[=]'),
        ('ab1=a', 'ab1[=]a'),
        ('ab==a', 'ab[=]{2}a'),
        ('ab=={a', 'ab[=]{2}[\\{]a'),
        ('=', '[=]'),
        ('==', '[=]{2}'),
        ('==+a', '[=]{2}[\\+]a'),
        ('\\', '[\\\\]'),
    ]
    for i, j in data:
        assert normalize_str(i) == j


def test_parse_url():
    data = [
        ('http://www.test.com/', [''], [('query_depth', 0)]),
        ('http://www.test.com/?', ['', ''], [('query_depth', 1)]),
        ('http://www.test.com/abc/def?k=v#xxx', ['abc', 'def', 'v', 'xxx'], [
         ('query_depth', 1), ('has_fragment', True), ('depths', (2, 1, 1))]),
    ]
    for url, p, m in data:
        url_meta, parts = analyze_url(url)
        assert parts == p
        for k, v in m:
            assert getattr(url_meta, k) == v
    with pytest.raises(IrregularURLException):
        analyze_url('http://www.g.com')


def test_parse_query_string():
    data = [
        ('a', [''], ['a']),
        ('a=', ['a='], ['']),
        ('a&b', ['a', 'b'], ['', '']),
        ('a=1', ['a='], ['1']),
        ('a=1&b=2', ['a=', 'b='], ['1', '2']),
    ]
    for q, k, v in data:
        assert parse_query_string(q) == (k, v)

    data = ['a&', 'a&&b', 'a=1&']

    for i in data:
        with pytest.raises(IrregularURLException):
            parse_query_string(i)


def test_analyze_url():
    data = [
        ['http://www.g.com/test', ('path', '/test'),
         ('query', None), ('fragment', None)],
        ['http://www.g.com/test?',
            ('query', ''), ('fragment', None)],
        ['http://www.g.com/test?#',
            ('query', ''), ('fragment', '')],
        ['http://www.g.com/test?#abc',
            ('query', ''), ('fragment', 'abc')],
        ['http://www.g.com/test#abc',
            ('query', None), ('fragment', 'abc')],
        ['http://www.g.com/test?a#',
            ('query', 'a'), ('fragment', '')],
        ['http://www.g.com/test?a##',
            ('query', 'a'), ('fragment', '#')],
        ['http://www.g.com/test#?',
            ('query', None), ('fragment', '?')],
    ]
    for check in data:
        url = check[0]
        r = parse_url(url)
        for attr, expect in check[1:]:
            assert getattr(r, attr) == expect


def test_filter_useless_part():
    data = [
        ('/', ['']),
        ('//', ['']),
        ('', ['']),
        ('/a/b', ['a', 'b']),
        ('/a/b/', ['a', 'b', '']),
        ('/a/b//', ['a', 'b', '']),
        ('/a/b///c', ['a', 'b', 'c']),
        ('a/b///c', ['a', 'b', 'c']),
    ]
    for s, expect in data:
        assert filter_useless(s.split('/')) == expect


def test_piece_parser():
    parser = PieceParser()
    data = [
        ('abc', ['abc', ], ['a-z', ]),
        ('abc.exe', ['abc', '[\\.]', 'exe'], ['a-z', '\\.', 'a-z']),
        ('%' * 10, ['[%]{10}', ], ['%', ]),
        ('abc1D..exe',  ['abc', '1', 'D',
                         '[\\.]{2}', 'exe'], ['a-z', '0-9', 'A-Z', '\\.', 'a-z']),
        ('@<>..', ['[@]', '[<]', '[>]', '[\\.]{2}'], ['@', '<', '>', '\\.']),
    ]
    for piece, expected_pieces, expected_rules in data:
        parsed = parser.parse(piece)
        assert parsed.rules == expected_rules
        assert parsed.pieces == expected_pieces
        assert parsed.piece_length == len(piece)
    with pytest.raises(InvalidCharException):
        parser.parse(' a')


def test_unpack_pack():
    data = [
        ('http://www.g.com/', '/'),
        ('http://www.g.com/abc', '/abc'),
        ('http://www.g.com/abc?a=1#c', '/abc[\\?]a=1#c'),
        ('http://www.g.com/abc???a=1#c', '/abc[\\?][\\?]{2}a=1#c'),
        ('http://www.g.com/abc?=1#c', '/abc[\\?]=1#c'),
        ('http://www.g.com/abc?a=1#', '/abc[\\?]a=1#'),
        ('http://www.g.com/abc?a=1&b=2#', '/abc[\\?]a=1&b=2#'),
    ]
    for url, expected in data:
        assert pack(*analyze_url(url)) == expected


def test_url_meta():
    url_meta1 = URLMeta(1, ['key1', 'key2'], False)
    assert url_meta1.depth == 3
    url_meta2 = URLMeta(1, ['key1', 'key2'], True)
    assert url_meta2.depth == 4
    assert hash(url_meta1) != hash(url_meta2)
    url_meta3 = URLMeta(1, ['key1', 'key2'], False)
    assert hash(url_meta1) == hash(url_meta3)


def test_parse_url_pattern():
    data = [
        'http://www.g.com/',
        'http://www.g.com/abc',
        'http://www.g.com/abc?a=1#c',
        'http://www.g.com/abc???a=1#c',
        'http://www.g.com/abc?=1#c',
        'http://www.g.com/abc?a=1#',
        'http://www.g.com/abc?a=1&b=2#',
    ]
    for url in data:
        meta1, parts1 = analyze_url(url)
        pattern_string = pack(meta1, parts1)
        meta2, parts2 = parse_pattern_path_string(pattern_string)
        assert meta1 == meta2
        assert len(parts1) == len(parts2)


def test_parse_pattern():
    data = [
        ('abc', 1),
        ('[0-9]{2}abc', 2),
        ('abc[0-9]+', 2),
        ('abc[\\[\\?][a-z]', 3),
        ('', 1),
        ('abcAbc', 3),
    ]
    for p_str, num in data:
        ps = parse_pattern_string(p_str)
        assert ''.join([str(u) for u in ps]) == p_str
        assert len(ps) == num

    invalid_data = [
        '[a-z',
        'a-z]',
        '[a-z]{-}',
        '[a-z]{-2}',
    ]

    for data in invalid_data:
        with pytest.raises(InvalidPatternException):
            parse_pattern_string(data)


def test_parse_pattern_unit():
    data = [
        ('[a-z]', set(['a-z']), 1),
        ('[a-z]+', set(['a-z']), -1),
        ('', set(['']), 1),
        ('[%\\+]{12}', set(['%', '\\+']), 12),
    ]
    for p_str, e_rules, e_num in data:
        rules, num = parse_pattern_unit_string(p_str)
        assert num == e_num
        assert rules == e_rules


def test_parse_pattern_path_string():
    patterns = [
        ('/AaBb/123456.shtml', '/[A-Za-z]+/[0-9]{6}[\\.]shtml'),
        ('/abc/123/index.html', '/abc/123/index[\\.]html'),
        ('/12345678/index.asp?id=123',
         '/[0-9]{8}/[a-z]+[\\.]asp[\\?]id=[0-9]+'),
        ('/newsShow.asp?dataID=1', '/newsShow[\\.]asp[\\?]dataID=[0-9]+'),
    ]

    for url, pattern in patterns:
        url = 'http://example.com' + url
        um1, pieces = analyze_url(url)
        um2, pattern_strings = parse_pattern_path_string(pattern)
        assert um1 == um2
        for p, s in zip(pattern_strings, pieces):
            assert Pattern(p).match(s)


def test_digest():
    parser = PieceParser()
    data = [
        ('/abc/', '/abcdef/'),
        ('/abc/index.html?k1=v1&k2=v2', '/abc/html.htm?k1=c01&k2=2m'),
        ('/abc/index.html?k1=v1#abc', '/abc/html.htm?k1=c01#def'),
    ]

    for urls in data:
        urls = ['http://example.com' + u for u in urls]
        digests = set()
        for url in urls:
            url_meta, pieces = analyze_url(url)
            parsed_pieces = [parser.parse(piece) for piece in pieces]
            sid = digest(url_meta, [p.fuzzy_rule for p in parsed_pieces])
            digests.add(sid)
        assert len(digests) == 1
