.. _installation:

Installation
============

We try not to reinvent the wheel, but to bring something innovative to the
market. As a consequence, we're focused on our own code and use pre-existing,
high-quality third-party libraries where possible.
To support the full, rich set of features that Kivy offers, several other libraries are
required. If you do not use a specific feature (e.g. video playback), you
don't need the corresponding dependency.
That said, there is one dependency that Kivy **does** require:
`Cython <http://cython.org>`_.

In addition, you need a `Python <http://python.org/>`_ 2.x (2.6 <= x < 3.0)
interpreter. If you want to enable features like windowing (i.e. open a Window),
audio/video playback or spelling correction, additional dependencies must
be available. For these, we recommend `Pygame <http://pygame.org>`_, `Gst-Python
<http://www.gstreamer.net/modules/gst-python.html>`_ and `Enchant
<http://www.rfk.id.au/software/pyenchant/>`_, respectively.

Other optional libraries (mutually independent) are:

    * `OpenCV 2.0 <http://sourceforge.net/projects/opencvlibrary/>`_ -- Camera input.
    * `PIL <http://www.pythonware.com/products/pil/index.htm>`_ -- Image and text display.
    * `PyCairo <http://www.cairographics.org/pycairo/>`_ -- Text display.
    * `PyEnchant <http://www.rfk.id.au/software/pyenchant/>`_ -- Spelling correction.
    * `PyGST <http://gstreamer.freedesktop.org/ + http://pygstdocs.berlios.de/>`_ -- Audio/video playback and camera input.


That said, **DON'T PANIC**!

We don't expect you to install all those things on your own.
Instead, we have created nice portable packages that you can use directly,
and they already contain the necessary packages for your platform.
We just want you to know that there are alternatives to the defaults and give
you an overview of the things Kivy uses internally.


Stable Version
--------------

The latest stable version can be found on Kivy's website at http://kivy.org/#download.
Please refer to the installation instructions for your specific platform:

.. toctree::
    :maxdepth: 2

    installation-windows
    installation-macosx
    installation-linux
    installation-android
    troubleshooting-macosx


.. _installation_devel:

Development Version
-------------------

The development version is for developers and testers. Note that when
running a development version, you're running potentially broken code at
your own risk.
To use the development version, you will first need to install the
dependencies. Thereafter, you will need to set up Kivy on your computer
in a way that allows for easy development. For that, please see our
:ref:`contributing` document.

Installing Dependencies
~~~~~~~~~~~~~~~~~~~~~~~

To install Kivy's dependencies, follow the guide below for your platform.

Ubuntu
++++++

For Ubuntu 12.04, simply enter the following command that will install all
necessary packages::

    $ sudo apt-get install python-setuptools python-pygame python-opengl \
      python-gst0.10 python-enchant gstreamer0.10-plugins-good python-dev \
      build-essential libgl1-mesa-dev-lts-quantal libgles2-mesa-dev-lts-quantal\ 
      python-pip

For other versions of Ubuntu, this one should work::

    $ sudo apt-get install python-setuptools python-pygame python-opengl \
      python-gst0.10 python-enchant gstreamer0.10-plugins-good python-dev \
      build-essential libgl1-mesa-dev libgles2-mesa-dev python-pip

Kivy requires a recent version of Cython, so it's better to use the last
version published on pypi::

    $ sudo pip install --upgrade cython

Mac OS X
++++++++

You will need to install at least the following:

* PyGame - we recommend installing from a binary packaged for your version
  of Mac OS X. Download it from http://www.pygame.org/download.shtml

If you run into problems, please read :ref:`troubleshooting-macosx`.

.. _dev-install:

Installing Kivy for Development
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that you've installed all the required dependencies, it's time to
download and compile a development version of Kivy::

    $ # Download Kivy from GitHub
    $ git clone git://github.com/kivy/kivy.git
    $ cd kivy

    $ # Compile:
    $ python setup.py build_ext --inplace -f

If you have the ``make`` command available, you can also use the
following shortcut to compile (does the same as the last command)::

    $ make

If you want to modify the Kivy code itself, set up the `PYTHONPATH environment
variable
<http://docs.python.org/tutorial/modules.html#the-module-search-path>`_ to
point at your clone.
This way you don't have to install (``setup.py install``) after every tiny
modification. Python will instead import Kivy from your clone.

Alternatively, if you don't want to make any changes to Kivy itself, you can
also run (as admin, e.g. with sudo)::

    $ python setup.py install

If you want to contribute code (patches, new features) to the Kivy
code base, please read :ref:`contributing`.

Running the test suite
~~~~~~~~~~~~~~~~~~~~~~

To help detect issues and behaviour changes in Kivy, a set of unittests are
provided. A good thing to do is to run them just after your Kivy installation, and
every time you intend to push a change. If you think something was broken
in Kivy, perhaps a test will show this? If not, it might be a good time to write
one .)

Kivy tests are based on nosetest, which you can install from your package
manager or using pip :

  $ pip install nose

To run the test suite, do :

  $ make test

Uninstalling Kivy
~~~~~~~~~~~~~~~~~

If you are mixing multiple Kivy installations, you might be confused about where each Kivy version is
located.  Please note that you might need to follow these steps multiple times if you have multiple
Kivy versions installed in the Python library path.
To find your current installed version, you can use the command line::

    $ python -c 'import kivy; print(kivy.__path__)'

Then, remove that directory recursively.

If you have installed Kivy with easy_install on linux, the directory may
contain a "egg" directory. Remove that as well::

    $ python -c 'import kivy; print(kivy.__path__)'
    ['/usr/local/lib/python2.7/dist-packages/Kivy-1.0.7-py2.7-linux-x86_64.egg/kivy']
    $ sudo rm -rf /usr/local/lib/python2.7/dist-packages/Kivy-1.0.7-py2.7-linux-x86_64.egg

If you have installed with apt-get, do::

    $ sudo apt-get remove --purge python-kivy
