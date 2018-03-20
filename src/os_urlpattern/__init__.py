import sys
__all__ = ['__version__', 'version_info']

import pkgutil
__version__ = pkgutil.get_data(__package__, 'VERSION').decode('ascii').strip()
version_info = tuple(int(v) if v.isdigit() else v
                     for v in __version__.split('.'))

if sys.version_info < (2, 7):
    print("os-urlpattern %s requires Python 2.7" % __version__)
    sys.exit(1)

del pkgutil
del sys
