from os_urlpattern.pattern_matcher import PatternMatcher


def match(patterns, urls, num, most_match=None):
    pm = PatternMatcher()
    for pattern in patterns:
        pm.load(pattern)
    for url in urls:
        matched = pm.match(url)
        assert len(matched) > num
        if most_match:
            sorted(matched)
            matched[-1].meta == most_match


def test_match():
    urls = ['http://example.com/abc%02d' % i for i in range(1, 10)]
    patterns = [
        '/abc[0-9]{2}',
        '/abc[0-9]+',
        '/[a-z]+[0-9]{2}',
        '/[a-z]{3}[0-9]{2}',
        '/[0-9a-z]+',
        '/[0-9a-z]{5}',
    ]
    for pattern in patterns:
        match([pattern], urls, 0)
    match(patterns, urls, 3, '/abc[0-9]{2}')
