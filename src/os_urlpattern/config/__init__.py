"""Configure.
"""
from  ..compat import ConfigParser

def get_default_config():
    """Get default configure instance.

    Returns:
        Config -- default confiure instance
    """
    import os
    path = os.path.dirname(__file__)
    cfg = ConfigParser()
    cfg.read(os.path.join(path, 'default_config.cfg'))
    return cfg
