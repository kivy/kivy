Kivy - Documentation
====================

You can access the latest documentation on the web:

* http://kivy.org/docs

Contributing
------------

If you intend on editing and contributing documentation, assure the kivy source
code is up to date before proceeding. If your documentation is outdated, it
could result in merge conflicts.

Install Sphinx
--------------

- With pip:
  

  ``pip install sphinx``

- With apt-get:
    

  ``apt-get install python-sphinx``

- With MacPorts:
  

  ``port install py34-sphinx``

- On Windows (or from inside your virtualenv):

  Get pip (https://pypi.python.org/pypi/pip). You'll use it to install the dependencies.

  To install pip, run ``python setup.py install`` in the pip directory. Now run:
    

  ``pip install sphinxcontrib-blockdiag sphinxcontrib-seqdiag``
  

  ``pip install sphinxcontrib-actdiag sphinxcontrib-nwdiag``
    

  Or just use the provided *doc-requirements.txt*:
    

  ``pip install -r doc-requirements.txt``
  

Building the documentation
--------------------------

Generate documentation using make: ``make html``.

Documentation will be accessible in ``build/html/``.

