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

* Cluster similar URLs:

  * **Similar URLs**
  
    URLs with the same **URL structure** and in the same character space.

  * **URL structure** 

    Typically, URL can be parsed into 6 components:

    ``<scheme>://<netloc>/<path>;<params>?<query>#<fragment>``

    We choose path, query, fragment to define URL structure.

    If the URLs have the same path levels, same query keys and with the same fragment existence, their URL structure should be the same.

    ::
      
      http://example.com/p1/p2?k1=v1&k2=v2#top

      URL Structure:
      path levels: 2
      query keys: k1, k2
      have fragment: True

  * **Character space**

    Consider `RFC 3986 (Section 2: Characters) <https://tools.ietf.org/html/rfc3986#section-2>`_, URL with the following characters would be legal:

    ``ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~:/?#[]@!$&'()*+,;=``

* Pattern definition:

  * **Regular expression compatible**




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
  usage: pattern-make [-h] [-f FILE [FILE ...]]
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

::
  
  $ pattern-match -h
  usage: pattern-match [-h] [-f FILE [FILE ...]]
                     [-L {NOTSET,DEBUG,INFO,WARN,ERROR,FATAL}] -p PATTERN_FILE
                     [PATTERN_FILE ...]

  optional arguments:
    -h, --help            show this help message and exit
    -f FILE [FILE ...], --file FILE [FILE ...]
                          file to be processed (default: stdin)
    -L {NOTSET,DEBUG,INFO,WARN,ERROR,FATAL}, --loglevel {NOTSET,DEBUG,INFO,WARN,ERROR,FATAL}
                          log level (default: NOTSET)
    -p PATTERN_FILE [PATTERN_FILE ...], --pattern-file PATTERN_FILE [PATTERN_FILE ...]
                          pattern file to be loaded


Unit Tests
----------

``$ tox``

License
--------

MIT licensed.
