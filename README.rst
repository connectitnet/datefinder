datefinder - extract dates from text
====================================

.. image:: https://travis-ci.com/connectitnet/datefinder.svg?branch=master
    :target: https://travis-ci.com/connectitnet/datefinder
    :alt: travis build status

.. image:: https://api.codeclimate.com/v1/badges/b77a662901c82e0dcc73/test_coverage
   :target: https://codeclimate.com/github/connectitnet/datefinder/test_coverage
   :alt: Test Coverage

.. image:: https://api.codeclimate.com/v1/badges/b77a662901c82e0dcc73/maintainability
   :target: https://codeclimate.com/github/connectitnet/datefinder/maintainability
   :alt: Maintainability

.. image:: https://img.shields.io/gitter/room/nwjs/nw.js.svg
    :target: https://gitter.im/datefinder/Lobby
    :alt: gitter chat


A python module for locating dates inside text. Use this package to extract all sorts 
of date like strings from a document and turn them into datetime objects.

This module finds the likely datetime strings and then uses the  
`dateparser <https://github.com/scrapinghub/dateparser>`_ package to convert 
to the datetime object.


Installation
------------

.. code-block:: sh

    git pull https://github.com/connectitnet/datefinder.git
    cd datefinder
    pip install -e .

How to Use
----------

.. code-block:: text

    In [1]: string_with_dates = """
       ...: ...
       ...: entries are due by January 4th, 2017 at 8:00pm
       ...: ...
       ...: created 01/15/2005 by ACME Inc. and associates.
       ...: ...
       ...: """

    In [2]: import datefinder

    In [3]: matches = datefinder.find_dates(string_with_dates)

    In [4]: for match in matches:
       ...:     print match
       ...:
    2017-01-04 20:00:00
    2005-01-15 00:00:00


Support
-------

You can talk to us on `Gitter <https://gitter.im/datefinder/Lobby>`_ or just submit an issue on `github <https://github.com/connectitnet/datefinder/issues/>`_. 

