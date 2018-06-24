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


This package is used for unsupervised URLs clustering. Furthermore, it generate URL Pattern(RegEx) 
from cluster for matching purpose. It is a pure python package tested under python2.7 python3.6, 
`pypy <http://pypy.org/>`_ can also be used for performance(4x-8x). Command line tools are provided 
for standalone clustering and matching, APIs are also convenient. Several extra packages can be 
installed for additional features. Under CPython 1cpu, 100 thousand URLs clustering cost almost 1min 
and 200M memory. Built-in matching strategy is efficient enough at most use case(3k/s, depend on 
patterns complexity).

.. code:: console

   $ pip install -U os-urlpattern
   $ wget -qO- 'https://git.io/vhXGq' | pattern-make
   /[0-9]{2}[\.]html
         http://example.com/01.html
         http://example.com/02.html
         http://example.com/03.html
   /[0-9]{3}/test[0-9]{2}[\.]html
         http://example.com/123/test01.html
         http://example.com/456/test02.html
         http://example.com/789/test03.html


==============
Aknowledgement
==============

Similar URLs
=============
  
* URLs with the same **URL structure**.

* Components of the parsed URLs at the same position are in the same **character space**.

* Corresponding components of the different URLs have the same **character space order**.


URL structure
==============

Typically, URL can be parsed into 6 components:

``<scheme>://<netloc>/<path>;<params>?<query>#<fragment>``

Because different sites may have similar URLs structure and <params> is rare, so <schema> 
<netloc> and <params> are ignored, <path> <query> <fragment> are used to define URL structure.

If the URLs have the same path levels, same query keys(also keys order) and with the same 
fragment existence, their URL structure should be the same. 

::
    
  http://example.com/p1/p2?k1=v1&k2=v2#pos

  URL structure:
  path levels: 2
  query keys: k1, k2
  have fragment: True

Character space
===============

Consider `RFC 3986 (Section 2: Characters) <https://tools.ietf.org/html/rfc3986#section-2>`_,
URL with the following characters would be legal:

``ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~:/?#[]@!$&'()*+,;=``

There are three major character space: lower-case letters(a-z), upper-case letters(A-Z), 
number letters(0-9). Other symbols are in their own character space.
  
::

  HeLlOwoRd233!

  character space: a-z A-Z 0-9 !
      
Character space order
=====================

Split a string by character, consecutive character space can be joined. 

::

  HELLOword233!

  split into: HELLO word 233 !

  character space order: A-Z a-z 0-9 !

Complex consecutive major character space can be joined.

::

  HellWorld233!

  split into: H ell W orld 233 !

  major join: HellWorld233 !

  character space order: A-Za-z0-9 !

Because of URL quote, '%' can be joined with major character space.

::

  %E4%BD%A0%E5%A5%BD!

  split into: % E 4 % BD % A 0 % E 5 % A 5 % BD !

  major join: %E4%BD%A0%E5%A5%BD !

  character space order: A-Z0-9% !


URL Pattern
============

URL Pattern is used to express each cluster. It is normal regex string. Each URL in 
the same cluster can be matched with the pattern.

::

  pattern examples:

  /news/[0-9]{8}/[a-z]+[\\.]html
  /newsShow[\\.]asp[\\?]dataID=[0-9]+
  /thread[\\-][0-9]+[\\-][0-9][\\-]1[\\.]html

The built-in matching strategy is strict, it can't tolerate incomplet matching.
  
::

  letter: helloword

  pattern01: [a-z0-9]+  # not match, because no number in the letter
  pattern02: [a-z]+ # match


========
Install
========

Install with pip

``$ pip install os-urlpattern``

Install extra packages

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
     - Enable `ete <https://github.com/etetoolkit/ete>`_ pattern tree formatter

========
Usage
========

Command line
=============

* **pattern-make**
    
  Load urls, cluster and dump patterns.

  .. code:: console
    
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
       -F {JSON,CLUSTER,PATTERN,ETE}, --formatter {PATTERN,CLUSTER,JSON,ETE}
                             output formatter (default: CLUSTER)
  
  Dump clustered URLs with patterns:

  .. code:: console
  
     $ cat urls.txt | pattern-make -L debug > clustered.txt

  Only generate URL Pattern:

  .. code:: console
  
     $ cat urls.txt | pattern-make -L debug -F pattern > patterns.txt
  
  Generate pattern tree from URLs(`ete <https://github.com/etetoolkit/ete>`_ installed):

  .. code:: console
    
     $ cat urls.txt | pattern-make -L debug -F ete

* **pattern-match**

  Load patterns, dump URLs match results.

  .. code:: console
    
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


  Match URLs:

  .. code:: console
  
     $ cat urls.txt | pattern-match -L debug -p patterns.txt

APIs
=====

Cluster and generate URL Pattern:

.. code:: python 
  
   from os_urlpattern.config import get_default_config
   from os_urlpattern.formatter import PatternFormatter
   from os_urlpattern.pattern_maker import PatternMaker

   conf = get_default_config()
   pattern_maker = PatternMaker(conf)

   # load URLs(unicode)
   for url in urls:
       pattern_maker.load(url)

   # cluster and dump patterns
   formatter = PatternFormatter()
   for url_meta, clustered in pattern_maker.make():
       for pattern in formatter.format(url_meta, clusterd)
           print(pattern)


Match URLs:

.. code:: python 
  
   from os_urlpattern.pattern_matcher import PatternMatcher

   pattern_matcher = PatternMatcher()

   # load pattern(unicode)
   for pattern in patterns:
       pattern_matcher.load(pattern, meta=pattern) # meta will bind to matched result

   # match URLs(unicode)
   for url in urls:
       matched_results = patterm_matcher.match(url)
       # the best matched result:
       # sorted(matched_results, reverse=True)[0]
       patterns = [n.meta for n in matched_results]

============
Unit Tests
============

``$ tox``

============
License
============

MIT licensed.
