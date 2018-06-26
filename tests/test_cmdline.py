import hashlib
import os
import shlex
import subprocess
import sys

import pytest

from os_urlpattern.cmdline import make, match


def call(cmdline, env=None, **kwargs):
    if env is None:
        env = os.environ.copy()
    if env.get('COVERAGE', None) is not None:
        env['COVERAGE_PROCESS_START'] = os.path.abspath('.coveragerc')

    cmd = 'python -u %s %s' % (os.path.abspath(__file__), cmdline)
    proc = subprocess.Popen(shlex.split(cmd),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            cwd=os.getcwd(),
                            env=env,
                            **kwargs)
    stdout, stderr = proc.communicate()
    return stdout, stderr


def test_make(tmpdir):
    num = 9
    urls = ['http://example.com/abc%02d?id=%02d#abc' %
            (i, i) for i in range(0, num)]
    data = "\n".join(urls)
    f = tmpdir.join('urls.txt')
    f.write(data)
    cmdline = 'make -f %s' % f.strpath
    stdout, _ = call(cmdline)
    assert b'/abc[0-9]{2}' in stdout
    assert urls[0].encode() in stdout

    cmdline = 'make -f %s -F pattern' % f.strpath
    stdout, _ = call(cmdline)
    assert b'/abc[0-9]{2}' in stdout
    assert urls[0].encode() not in stdout

    cmdline = 'make -f %s -F ete' % f.strpath
    stdout, _ = call(cmdline)
    assert b' abc[0-9]{2}(%d) ' % num
    assert b' [\\?]id=[0-9]{2}(%d) ' % num
    assert b' - #abc(%d)' % num


def test_make_digest_type_urls(tmpdir):
    urls = ['http://example.com/%s.html' % j for j in
            [hashlib.md5(str(i).encode()).hexdigest() for i in range(0, 9)]]

    data = "\n".join(urls)
    f = tmpdir.join('urls.txt')
    f.write(data)
    cmdline = 'make -f %s -F pattern ' % f.strpath
    stdout, _ = call(cmdline)
    assert b'[0-9a-z]{32}[\\.]html' in stdout


def test_make_noise(tmpdir):
    urls = ['http://example.com/abc%02d?id=%02d#abc' %
            (i, i) for i in range(0, 8)]
    urls.append('http://example.com/abc009?id=09#abc')

    data = "\n".join(urls)
    f = tmpdir.join('urls.txt')
    f.write(data)
    cmdline = 'make -f %s -F pattern ' % f.strpath
    stdout, _ = call(cmdline)
    assert b'/abc[0-9]{2}' in stdout
    assert b'/abc009' in stdout


def test_make_fuzzy(tmpdir):
    urls = [
        'sdjfpewiefh',
        'dfsdksd',
        'dffalldsfisslkfdksd',
        'didif',
        'dif',
    ]
    urls = ['http://example.com/abc/' + i for i in urls]
    data = "\n".join(urls)
    f = tmpdir.join('urls01.txt')
    f.write(data)
    cmdline = 'make -f %s -F pattern ' % f.strpath
    stdout, _ = call(cmdline)
    assert b'/abc/[a-z]+' in stdout

    urls = [i + '.html' for i in urls]
    data = "\n".join(urls)
    f = tmpdir.join('urls02.txt')
    f.write(data)
    cmdline = 'make -f %s -F pattern ' % f.strpath
    stdout, _ = call(cmdline)
    assert b'/abc/[a-z]+[\\.]html' in stdout


def test_match(tmpdir):
    pattern = b'/abc[0-9]{2}'
    fp = tmpdir.join('patterns.txt')
    fp.write(pattern)

    urls = ['http://example.com/abc%02d' % i for i in range(1, 10)]
    data = "\n".join(urls)
    fu = tmpdir.join('urls.txt')
    fu.write(data)

    cmdline = 'match -f %s -p %s' % (fu.strpath, fp.strpath)
    stdout, _ = call(cmdline)

    assert pattern in stdout


if __name__ == "__main__":
    sys.path.insert(0, os.getcwd())
    if os.getenv('COVERAGE_PROCESS_START'):
        import coverage
        coverage.process_startup()
    cmds = {'make': make, 'match': match}
    cmds[sys.argv.pop(1)]()
