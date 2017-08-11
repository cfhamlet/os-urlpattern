from os_urlpattern.url_meta import URLMeta


def test_url_meta():
    url_meta1 = URLMeta(1, ['key1', 'key2'], False)
    assert url_meta1.depth == 3
    url_meta2 = URLMeta(1, ['key1', 'key2'], True)
    assert url_meta2.depth == 4
    assert hash(url_meta1) != hash(url_meta2)
    url_meta3 = URLMeta(1, ['key1', 'key2'], False)
    assert hash(url_meta1) == hash(url_meta3)
