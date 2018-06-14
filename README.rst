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

Aknowledgement
***************

* Cluster similar URLs:

  * **Similar URLs**
  
    - URLs with the same **URL structure**.

    - Components of the parsed URLs at the same position are in the same **character space**.

    - Corresponding components of the different URLs have the same **character space order**.


  * **URL structure** 

    Typically, URL can be parsed into 6 components:

    ``<scheme>://<netloc>/<path>;<params>?<query>#<fragment>``

    We choose path, query, fragment to define URL structure.

    If the URLs have the same path levels, same query keys(also keys order) and with the same 
    fragment existence, their URL structure should be the same. 

    ::
      
      http://example.com/p1/p2?k1=v1&k2=v2#pos

      URL structure:
      path levels: 2
      query keys: k1, k2
      have fragment: True

  * **Character space**

    - Consider `RFC 3986 (Section 2: Characters) <https://tools.ietf.org/html/rfc3986#section-2>`_,
      URL with the following characters would be legal:

      ``ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~:/?#[]@!$&'()*+,;=``

    - There are three major character space: lower-case letters, upper-case letters, number letters.
      Other symbols are in their own character space.
      
    ::

      HeLlOwoRd233!

      character space: a-z A-Z 0-9 !
      
  * **Character space order**

    - Split a string by character, consecutive character space can be joined. 

    ::

      HELLOword233!

      split into: HELLO word 233 !

      character space order: A-Z a-z 0-9 !

    - Complex consecutive major character space can be joined.

    ::

      HellWorld233!

      split into: H ell W orld 233 !

      major join: HellWorld233 !

      character space order: A-Za-z0-9 !

    - Because of URL quote, '%' can be joined with major character space.

    ::

      %E4%BD%A0%E5%A5%BD!

      split into: % E 4 % BD % A 0 % E 5 % A 5 % BD !

      major join: %E4%BD%A0%E5%A5%BD !

      character space order: A-Z0-9% !


* Pattern definition:

  * **Regular expression compatible**


Install
*******

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
*****

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
***********

``$ tox``

License
********

MIT licensed.
