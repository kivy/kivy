.. _deps_cython:

Cython
======

|cython_note|

Working versions
----------------

* Kivy 2.0.0 -> |cython_install|
* Kivy 1.11.1 -> Cython==0.29.9
* Kivy 1.11.0 -> Cython==0.29.9
* Kivy 1.10.1 -> Cython==0.28.2
* Kivy 1.10.0 -> Cython==0.25.2
* Kivy 1.9.1 -> Cython==0.23.1
* Kivy 1.9.0 -> Cython==0.21.2

To force a version of cython, use::

    $ sudo pip install -U --force-reinstall Cython==<version>

where <version> is the appropriate version number.

Known issues
------------

* 0.27 -> Kivy Cython declaration bug in 1.10.0 causes failing compilation

Unsupported
-----------

* 0.27 - 0.27.2 -> Kivy doesn't compile on Python 3.4 with `MinGWPy
  <http://mingwpy.github.io>`_ because of a used unexported symbol
  during the compilation. For more details see `this issue.
  <https://github.com/cython/cython/issues/1968>`_
