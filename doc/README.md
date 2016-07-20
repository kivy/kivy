Kivy - Documentation
====================

You can access the latest documentation on the web:
  * http://kivy.org/docs


How to build the documentation
------------------------------

You need to install:

  * Python Sphinx
    - With pip:
    ```
	pip install sphinx
	```

    - With apt-get:
    ```
    apt-get install python-sphinx
    ```

    - With MacPorts:
    ```
	port install py34-sphinx
	```

    - On Windows (or from inside your virtualenv):

          Get pip (https://pypi.python.org/pypi/pip). You'll use it to install the dependencies.

          To install pip, run python setup.py install in the pip directory. Now run:
          ```
          pip install sphinxcontrib-blockdiag sphinxcontrib-seqdiag
          pip install sphinxcontrib-actdiag sphinxcontrib-nwdiag
          ```
          Or just use the provided `doc-requirements.txt`:
          ```
          pip install -r doc-requirements.txt
          ```

  * Latest kivy

Generate documentation using make: `make html`.

Documentation will be accessible in `build/html/`.

