=============
os-urlpattern
=============

.. image:: https://travis-ci.org/cfhamlet/os-urlpattern.svg?branch=master
   :target: https://travis-ci.org/cfhamlet/os-urlpattern

.. image:: https://codecov.io/gh/cfhamlet/os-urlpattern/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/cfhamlet/os-urlpattern

.. image:: https://img.shields.io/pypi/pyversions/os-urlpattern.svg
   :alt: PyPI - Python Version
   :target: https://pypi.python.org/pypi/os-urlpattern
  
.. image:: https://img.shields.io/pypi/v/os-urlpattern.svg
   :alt: PyPI
   :target: https://pypi.python.org/pypi/os-urlpattern


Automatically generate URL pattern.



Install
-------

``$ pip install os-urlpattern``

Usage
------

* Command line:

::
  
  $ pattern-make -h
  usage: pattern-make [-h] [-c CONFIG] [-f FILE]
                      [-L {NOTSET,DEBUG,INFO,WARN,ERROR,FATAL}] [-F {JSON,ETE}]

  optional arguments:
    -h, --help            show this help message and exit
    -c CONFIG, --config CONFIG
                          config file
    -f FILE, --file FILE  file to be processed (default: stdin)
    -L {NOTSET,DEBUG,INFO,WARN,ERROR,FATAL}, --loglevel {NOTSET,DEBUG,INFO,WARN,ERROR,FATAL}
                          log level (default: NOTSET)
    -F {JSON}, --formatter {JSON}
                          output formatter (default: JSON)


Unit Tests
----------

``$ tox``

License
--------

MIT licensed.
