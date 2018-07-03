"""Compatible import.
"""

from __future__ import unicode_literals
import operator
import string
import sys

_PY3 = sys.version_info[0] >= 3

if _PY3:
    from io import StringIO
    iteritems = operator.methodcaller("items")
    itervalues = operator.methodcaller("values")
    from urllib.parse import urlparse, ParseResult
    from configparser import ConfigParser
    binary_stdin = sys.stdin.buffer
    binary_stdout = sys.stdout.buffer
else:
    try:
        from cStringIO import StringIO  # trick, only process ascii
    except ImportError:
        from StringIO import StringIO
    iteritems = operator.methodcaller("iteritems")
    itervalues = operator.methodcaller("itervalues")
    from urlparse import urlparse, ParseResult
    from ConfigParser import ConfigParser
    binary_stdin = sys.stdin
    binary_stdout = sys.stdout
