from os_urlpattern.parse_utils import specify_rule, wildcard_rule
from os_urlpattern.pattern import Pattern, PatternUnit


def test_equal():
    p1 = Pattern('[a-z]+')
    p2 = Pattern('[a-z]+')
    p3 = Pattern('[a-z]')
    assert p1 == p2
    assert p1 != p3


def test_fuzzy_rule():
    data = [
        ('123', '0-9'),
        ('abc', 'a-z'),
        ('a1b2c3', '0-9a-z'),
        ('a1b2c3D4', '0-9A-Za-z'),
        ('a1[\\-]b2[\\-]c3[_]D4', '0-9A-Z\-_a-z'),
        ('[a-z]+', 'a-z'),
    ]

    for s, r in data:
        p = Pattern(s)
        assert p.fuzzy_rule == r
        pw = Pattern(wildcard_rule(p.fuzzy_rule))
        assert pw.fuzzy_rule == r
        pn = Pattern(specify_rule(p.fuzzy_rule, 3))
        assert pn.fuzzy_rule == r


def test_pattern_unit():
    data = [
        ('[a-z]+', 'a-z', -1, False),
        ('[a-z]{3}', 'a-z', 3, False),
        ('abc', 'a-z', 3, True),
        ('[0-9a-z]', '0-9a-z', 1, False),
    ]

    for s, fuzzy_rule, num, literal in data:
        pu = PatternUnit(s)
        assert pu.fuzzy_rule == fuzzy_rule
        assert pu.num == num
        assert pu.is_literal() == literal
