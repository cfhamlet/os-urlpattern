import operator
import string
import sys

_PY3 = sys.version_info[0] >= 3

if _PY3:
    from io import StringIO
    iteritems = operator.methodcaller("items")
    itervalues = operator.methodcaller("values")
    from urllib.parse import urlparse, ParseResult
    from configparser import RawConfigParser
    binary_stdin = sys.stdin.buffer
    binary_stdout = sys.stdout.buffer
    ascii_lowercase_unicode = string.ascii_lowercase
    ascii_uppercase_unicode = string.ascii_uppercase
    digits_unicode = string.digits
else:
    from StringIO import StringIO
    iteritems = operator.methodcaller("iteritems")
    itervalues = operator.methodcaller("itervalues")
    from urlparse import urlparse, ParseResult
    from ConfigParser import RawConfigParser
    binary_stdin = sys.stdin
    binary_stdout = sys.stdout
    ascii_lowercase_unicode = unicode(string.ascii_lowercase)
    ascii_uppercase_unicode = unicode(string.ascii_uppercase)
    digits_unicode = unicode(string.digits)
