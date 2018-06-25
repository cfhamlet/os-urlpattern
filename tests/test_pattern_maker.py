import pytest

from os_urlpattern.config import Config, get_default_config
from os_urlpattern.parse_utils import pack
from os_urlpattern.pattern_maker import PatternMaker
from os_urlpattern.utils import dump_tree


@pytest.fixture(scope='function')
def config():
    return get_default_config()


@pytest.fixture(scope='function')
def pattern_maker(config):
    return PatternMaker(config)


def test_load(config):
    pm = PatternMaker(config)
    urls = ['http://example.com' + u for u in ['/a', '/a/b', '/a/b/c']]
    for url in urls:
        pm.load(url)
    assert len(list(pm.makers)) == len(urls)
    for _, clustered in pm.make():
        for nodes in dump_tree(clustered):
            assert len(nodes[-1].meta) == 1

    config.set('make', 'drop_url', 'true')
    pm = PatternMaker(config)
    urls = ['http://example.com' + u for u in ['/a', '/b', '/c']]
    for url in urls:
        pm.load(url)
    assert len(list(pm.makers)) == 1
    for _, clusterd in pm.make():
        for nodes in dump_tree(clusterd):
            assert nodes[-1].meta is None


def cluster_and_test(urls, pattern_string):
    pm = PatternMaker(get_default_config())
    for url in urls:
        pm.load(url)

    for url_meta, clusterd in pm.make(combine=True):
        for nodes in dump_tree(clusterd):
            assert pack(
                url_meta, [n.value for n in nodes[1:]]) == pattern_string


def test_make():
    urls = ['http://example.com' + u for u in ['/a01', '/b02', '/c03']]
    cluster_and_test(urls, '/[a-z][0-9]{2}')
    urls = ['http://example.com' + u for u in ['/3h4hd9s9w9d9',
                                               '/9s2m1m3j2d10', '/i2i2g4g23j0m']]
    cluster_and_test(urls, '/[0-9a-z]{12}')
    urls = [u + '.html' for u in urls]
    cluster_and_test(urls, '/[0-9a-z]{12}[\\.]html')
    urls = [u + '?id=%02d' % i for i, u in enumerate(urls, 1)]
    cluster_and_test(urls, '/[0-9a-z]{12}[\\.]html[\\?]id=[0-9]{2}')

    urls = ['http://example.com' + u for u in ['/3h4hd9s9w9ddsadf9',

                                               '/9s2m1m3j2d10', '/i2i2g4g23j0dsdm']]
    cluster_and_test(urls, '/[0-9a-z]+')
