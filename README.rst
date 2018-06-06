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
* Install with pip

  ``$ pip install os-urlpattern``

* Install extra packages

  .. list-table::
      :header-rows: 1
        
      * - subpackage 
        - install command
        - enables
      * - memory
        - ``pip install os-urlpattern[memroy]``
        - Show memory useage
      * - ete-tree
        - ``pip install os-urlpattern[ete_tree]``
        - Enable ete3 pattern tree formatter

Usage
------

* Command line:

::
  
  $ pattern-make -h
  sage: pattern-make [-h] [-f FILE [FILE ...]]
                    [-L {NOTSET,DEBUG,INFO,WARN,ERROR,FATAL}]
                    [-c CONFIG [CONFIG ...]] [-F {JSON,ETE}]

  optional arguments:
    -h, --help            show this help message and exit
    -f FILE [FILE ...], --file FILE [FILE ...]
                          file to be processed (default: stdin)
    -L {NOTSET,DEBUG,INFO,WARN,ERROR,FATAL}, --loglevel {NOTSET,DEBUG,INFO,WARN,ERROR,FATAL}
                          log level (default: NOTSET)
    -c CONFIG [CONFIG ...], --config CONFIG [CONFIG ...]
                          config file
    -F {JSON,ETE}, --formatter {JSON,ETE}
                          output formatter (default: JSON)  

Unit Tests
----------

``$ tox``

License
--------

MIT licensed.
