Kivy - Documentation
====================

You can access the latest documentation on the web:

* http://kivy.org/docs

Contributing
------------

If you intend on editing and contributing documentation, assure the kivy source
code is up to date before proceeding. If your documentation is outdated, it
could result in merge conflicts.

Building the documentation
--------------------------

Install the documentation dependencies (Sphinx requires Python 3.12+)::

  ``pip install -e ".[full,docs]"``

Generate documentation using make: ``make html``.

Documentation will be accessible in ``build/html/``.

Testing locally the docs: ``cd build/html/`` and then ``python -m http.server 8000``
