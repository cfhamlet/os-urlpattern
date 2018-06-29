import json

import pytest

from os_urlpattern.formatter import pformat
from os_urlpattern.pattern_maker import PatternMaker


@pytest.fixture(scope='function')
def p_maker():
    p_maker = PatternMaker()
    for url in ['http://www.example.com/abc/%02d.html' % i for i in range(0, 10)]:
        p_maker.load(url, meta=url)

    return p_maker


def test_inline(p_maker):
    for url_meta, clustered in p_maker.make():
        for o in pformat('inline', url_meta, clustered):
            assert u'/abc/[0-9]{2}[\\.]html\thttp' in o


def test_json(p_maker):
    for url_meta, clustered in p_maker.make():
        for o in pformat('json', url_meta, clustered):
            d = json.loads(o)
            assert d['ptn'] == u'/abc/[0-9]{2}[\\.]html'
            assert d['cnt'] == 10
