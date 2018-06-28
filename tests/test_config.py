import pytest

from os_urlpattern.config import get_default_config


def test_get_default_config():
    config = get_default_config()
    assert config.getint('make', 'min_cluster_num') == 3
