import operator
import sys

_PY3 = sys.version_info[0] >= 3

if _PY3:
    from io import StringIO
    iteritems = operator.methodcaller("items")
    itervalues = operator.methodcaller("values")
    from urllib.parse import urlparse, ParseResult
    from configparser import RawConfigParser
else:
    from StringIO import StringIO
    iteritems = operator.methodcaller("iteritems")
    itervalues = operator.methodcaller("itervalues")
    from urlparse import urlparse, ParseResult
    from ConfigParser import RawConfigParser
