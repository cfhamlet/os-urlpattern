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


This package is used for unsupervised URLs clustering. Furthermore, it generate URL patterns(RegEx) 
from clusters for matching purpose. It is a pure python package tested under python2.7 python3.6, 
`pypy <http://pypy.org/>`_ can also be used for performance(4x-8x). Command line tools are provided 
for standalone clustering and matching, APIs are also convenient. Several extra packages can be 
installed for additional features. Under CPython 1cpu, 100 thousand URLs clustering cost almost 1min 
and 200M memory. Built-in matching strategy is efficient enough in most use cases(4k/s, depend on 
patterns complexity).

.. code:: console

  $ pip install -U os-urlpattern
  $ wget -qO- 'https://git.io/f4QlP' | pattern-make
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

* Different types of charactors may be in the same order in most cases.


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

  HeLlOwoRd666!

  character space: a-z A-Z 0-9 !
      
Order consideration
=====================

Split a string by character, consecutive character space can be joined. In most cases, order is a 
distinguished feature.

::

  HELLOword666!

  split into: HELLO word 666 !

  character space order: A-Z a-z 0-9 !


Mix
=====================
Complex consecutive major character space can be mixed, order is less important.

::

  HellWorld666!

  split into: H ell W orld 666 !

  major join: HellWorld666 !

  character space order: A-Za-z0-9 !

Because of URL quote, '%' can be mixed with major character space.

::

  %E4%BD%A0%E5%A5%BD!

  split into: % E 4 % BD % A 0 % E 5 % A 5 % BD !

  major join: %E4%BD%A0%E5%A5%BD !

  character space order: A-Z0-9% !


URL pattern
============

URL pattern is used to express each cluster. It is normal regex string. Each URL in 
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
    usage: pattern-make [-h] [-i INPUT [INPUT ...]]
                        [-l {NOTSET,DEBUG,INFO,WARN,ERROR,FATAL}]
                        [-c CONFIG [CONFIG ...]]
                        [-f {PATTERN,CLUSTER,JSON,ETE,INLINE,NULL}]

    optional arguments:
      -h, --help            show this help message and exit
      -i INPUT [INPUT ...], --input INPUT [INPUT ...]
                            input file to be processed (default: stdin)
      -l {NOTSET,DEBUG,INFO,WARN,ERROR,FATAL}, --loglevel {NOTSET,DEBUG,INFO,WARN,ERROR,FATAL}
                            log level (default: NOTSET)
      -c CONFIG [CONFIG ...], --config CONFIG [CONFIG ...]
                            config file
      -f {PATTERN,CLUSTER,JSON,ETE,INLINE,NULL}, --formatter {PATTERN,CLUSTER,JSON,ETE,INLINE,NULL}
                            output formatter (default: CLUSTER)
  
  Dump clustered URLs with patterns:

  .. code:: console
  
    $ cat urls.txt | pattern-make -L debug > clustered.txt

  Only generate URL patterns:

  .. code:: console
  
    $ cat urls.txt | pattern-make -L debug -F pattern > patterns.txt
  
  Generate pattern tree from URLs(`ete <https://github.com/etetoolkit/ete>`_ installed):

  .. code:: console
    
    $ cat urls.txt | pattern-make -L debug -F ete

* **pattern-match**

  Load patterns, dump URLs matched results.

  .. code:: console
    
    $ pattern-match -h
    usage: pattern-match [-h] [-i INPUT [INPUT ...]]
                      [-l {NOTSET,DEBUG,INFO,WARN,ERROR,FATAL}] -p PATTERN_FILE
                      [PATTERN_FILE ...] [-a]

    optional arguments:
      -h, --help            show this help message and exit
      -i INPUT [INPUT ...], --input INPUT [INPUT ...]
                            input file to be processed (default: stdin)
      -l {NOTSET,DEBUG,INFO,WARN,ERROR,FATAL}, --loglevel {NOTSET,DEBUG,INFO,WARN,ERROR,FATAL}
                            log level (default: NOTSET)
      -p PATTERN_FILE [PATTERN_FILE ...], --pattern-file PATTERN_FILE [PATTERN_FILE ...]
                            pattern file to be loaded
      -a, --all_matched     all matched patterns


  Match URLs:

  .. code:: console
  
    $ cat urls.txt | pattern-match -L debug -p patterns.txt

APIs
=====

* Cluster and generate URL patterns:

  .. code:: python 
  
    from os_urlpattern.formatter import pformat
    from os_urlpattern.pattern_maker import PatternMaker

    pattern_maker = PatternMaker()

    # load URLs(unicode)
    for url in urls:
        pattern_maker.load(url)

    # cluster and print pattern
    for url_meta, clustered in pattern_maker.make():
        for pattern in pformat('pattern', url_meta, clustered):
            print(pattern)


* Match URLs:

  .. code:: python 
  
    from os_urlpattern.pattern_matcher import PatternMatcher

    pattern_matcher = PatternMatcher()

    # load url_pattern(unicode)
    for url_pattern in url_patterns:
        # meta will bind to matched result
        pattern_matcher.load(url_pattern, meta=url_pattern)

    # match URL(unicode)
    for url in urls:
        matched_results = patterm_matcher.match(url)
        # the best matched result:
        # sorted(matched_results, reverse=True)[0]
        patterns = [n.meta for n in matched_results]


* Low-level APIs:

  It is necessary to use low-level APIs for customizing processing procdure,
  especially for parallel computing or working on an distributed cluster(hadoop).

  **Key points: same fuzzy-digest same maker and same matcher.**

  Use ``os_urlpattern.parser.fuzzy_digest`` to get fuzzy digest from URL,
  URL pattern or URLMeta and parsed pieces/patterns.

  A brief All-In-One example:

  .. code:: python 
  
    from __future__ import print_function, unicode_literals
    from os_urlpattern.formatter import pformat
    from os_urlpattern.parser import fuzzy_digest, parse
    from os_urlpattern.pattern_maker import Maker
    from os_urlpattern.pattern_matcher import Matcher

    urls = ['http://t.com/%02d.html' % i for i in xrange(0,10)]
    makers = {}
    matchers = {}

    # Init makers from URLs(unicode).
    for url in urls:
        url_meta, parsed_pieces = parse(url)
        
        # same digest same maker
        digest = fuzzy_digest(url_meta, parsed_pieces)
        if digest not in makers:
            makers[digest] = Maker(url_meta)
        makers[digest].load(parsed_pieces)

    # Iterate makers, do clustering, generate URL pattern and init matchers.
    for maker in makers.values():
        for clustered in maker.make():
            for pattern in pformat('pattern', maker.url_meta, clustered):
                # init matchers
                url_meta, parsed_patterns = parse(pattern)
                digest = fuzzy_digest(url_meta, parsed_patterns)
                if digest not in matchers:
                    matchers[digest] = Matcher(url_meta)
                matchers[digest].load(parsed_patterns, pattern)
    
    # Match URLs(unicode).
    for url in urls:
        url_meta, parsed_pieces = parse(url)

        # same digest same matcher
        digest = fuzzy_digest(url_meta, parsed_pieces)
        if digest in matchers:
            matched = [n.meta for n in matchers[digest].match(parsed_pieces)]
            print(url, *matched, sep="\t")        
        else: # no matched at all
            pass



============
Unit Tests
============

``$ tox``

============
License
============

MIT licensed.
