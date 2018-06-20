import pytest

from os_urlpattern.config import Config, get_default_config


@pytest.fixture(scope='function')
def config():
    return Config()


def _config_getboolean(config):
    config.add_section('test')
    config.set('test', 'test1', 'true')
    assert config.getboolean('test', 'test1') == True


def test_config_getlist(config):
    config.add_section('test')
    config.set('test', 'test1', 'a,b')
    assert config.getlist('test', 'test1') == ['a', 'b']
    config.set('test', 'test1', '1,2')
    assert config.getlist('test', 'test1', conv=int) == [1, 2]
    config.set('test', 'test1', '1;2')
    assert config.getlist('test', 'test1', sep=';', conv=int) == [1, 2]


def test_config_set(config):
    config.add_section('test')
    config.set('test', 'test1', 'a')
    assert config.get('test', 'test1') == 'a'


def test_config_read(config, tmpdir):
    fn = 'test.cfg'
    with tmpdir.as_cwd():
        f = tmpdir.join(fn)
        f.write("[make]\ntest1 = 1\n")
        config.read(fn)
        assert config.get('make', 'test1') == '1'


def test_config_freeze(config):
    config.add_section('test')
    config.freeze()
    with pytest.raises(TypeError):
        config.set('test', 'tesst')


def test_get_default_config():
    config = get_default_config()
    assert config.getint('make', 'min_cluster_num') == 3
