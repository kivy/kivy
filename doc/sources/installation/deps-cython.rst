.. _deps_cython:

Cython
======

|cython_note|

Known issues
------------

* 0.27 -> Kivy Cython declaration bug in 1.10.0 causes failing compilation

Unsupported
-----------

* 0.27 - 0.27.2 -> Kivy doesn't compile on Python 3.4 with `MinGWPy
  <http://mingwpy.github.io>`_ because of a used unexported symbol
  during the compilation. For more details see `this issue.
  <https://github.com/cython/cython/issues/1968>`_
