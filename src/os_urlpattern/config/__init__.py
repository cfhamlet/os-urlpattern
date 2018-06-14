from ..compat import RawConfigParser
try:
    from collections import OrderedDict as _default_dict
except ImportError:
    # fallback for setup.py which hasn't yet built _collections
    _default_dict = dict


class Config(RawConfigParser):
    def __init__(self, defaults=None, dict_type=_default_dict,
                 allow_no_value=False):
        RawConfigParser.__init__(self, defaults=defaults,
                                 dict_type=dict_type, allow_no_value=allow_no_value)
        self._frozen = False

    def getlist(self, section, option, sep=',', conv=None):
        values = self.get(section, option).split(sep)
        if conv:
            return [conv(v.strip()) for v in values]
        return [v.strip() for v in values]

    def _assert_mutability(self):
        if self._frozen:
            raise TypeError("Trying to modify an immutable Config object")

    def freeze(self):
        self._frozen = True

    def set(self, section, option, value=None):
        self._assert_mutability()
        RawConfigParser.set(self, section, option, value)


def get_default_config():
    """Get default configure instance.

    Returns:
        Config -- default confiure instance
    """
    import os
    path = os.path.dirname(__file__)
    cfg = Config()
    cfg.read(os.path.join(path, 'default_config.cfg'))
    return cfg
