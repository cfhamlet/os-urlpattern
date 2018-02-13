from os_urlpattern.pattern import PatternUnit


def test_pattern_unit():
    data = [
        ('[a-z]', set(['a-z']), 1),
        ('[a-z]+', set(['a-z']), '+'),
        ('', set(['']), 1),
        ('[%\\+]{12}', set(['%', '\\+']), 12),
    ]
    for p_str, e_rules, e_num in data:
        pu = PatternUnit(p_str)
        assert pu.num == e_num
        assert pu.rules == e_rules
