.. _installation:

Installation
============

We try not to reinvent the wheel but bring something innovative to the
market. As a consequence, we're focused on our own code and use already
existing, high-quality third-party libraries where possible.
For the rich set of features that Kivy offers, several other libraries are
required. If you do not use a specific feature (e.g. video playback) you
don't need the corresponding dependency, however.
That said, there is one dependency that Kivy **does** require:
`Cython <http://cython.org>`_.

In addition, you need a `Python <http://python.org/>`_ 2.x (**not**  3.x)
interpreter. If you want to enable features like windowing (i.e., open a Window),
audio/video playback or spelling correction, additional dependencies must
be available. For these, we recommend `Pygame <http://pygame.org>`_, `Gst-Python
<http://www.gstreamer.net/modules/gst-python.html>`_ and `Enchant
<http://www.rfk.id.au/software/pyenchant/>`_, respectively.

Other optional libraries (mutually interchangeable) are:

    * `OpenCV 2.0 <http://sourceforge.net/projects/opencvlibrary/>`_ -- Camera input.
    * `PIL <http://www.pythonware.com/products/pil/index.htm>`_ -- Image and text display.
    * `PyCairo <http://www.cairographics.org/pycairo/>`_ -- Text display.
    * `PyEnchant <http://www.rfk.id.au/software/pyenchant/>`_ -- Spelling correction.
    * `PyGST <http://gstreamer.freedesktop.org/ + http://pygstdocs.berlios.de/>`_ -- Audio/video playback and camera input.


That said, **DON'T PANIC**!

We don't ask you to install all those things on your own.
Instead, we created nice portable packages that you can use directly
since they already contain the necessary packages for your platform.
We just want you to know about the alternatives for the defaults and give
you an overview about the things Kivy uses internally.


Stable Version
--------------

The latest stable version can be found on Kivy's website at http://kivy.org/#download
Please refer to the installation instructions for your specific platform:

.. toctree::
    :maxdepth: 2

    installation-windows
    installation-macosx
    installation-linux
    installation-android


Development Version
-------------------

The development version is for developers and testers. Note that when
running a development version, you're running potentially broken code at
your own risk.
To use the development version, you will first need to install the
dependencies. Afterwards you have to set up Kivy on your computer in a way
that allows for easy development. For that, please see our
:ref:`contributing` document.

Installing Dependencies
~~~~~~~~~~~~~~~~~~~~~~~

To install Kivy's dependencies, follow the guide below for your platform.

Ubuntu
++++++

For Ubuntu, simply enter the following command that will install all
necessary packages:

::

    $ sudo apt-get install python-setuptools python-pygame python-opengl \
      python-gst0.10 python-enchant gstreamer0.10-plugins-good cython python-dev \
      build-essential libgl1-mesa-dev libgles2-mesa-dev

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

Or, if you don't want to make any changes to Kivy itself, you can also run
(as admin, e.g. with sudo)::

    $ python setup.py install

If you want to contribute code (patches, new features) to the Kivy
code base, please read :ref:`contributing`.

Uninstalling Kivy
~~~~~~~~~~~~~~~~~

If you are mixing multiple Kivy installation, you might be confused where is
located each Kivy version. Please note that you might need to do it multiple
time, if you have multiple kivy version installed into python libraries path.
To found your current installed version, you can write in command line::

    $ python -c 'import kivy; print kivy.__path__'

Then, remove that directory recursively.

If you have installed Kivy with easy_install on linux, the directory can
contain a "egg" directory. Remove it as well::

    $ python -c 'import kivy; print kivy.__path__'
    ['/usr/local/lib/python2.7/dist-packages/Kivy-1.0.7-py2.7-linux-x86_64.egg/kivy']
    $ sudo rm -rf /usr/local/lib/python2.7/dist-packages/Kivy-1.0.7-py2.7-linux-x86_64.egg

If you have installed with apt-get, do::

    $ sudo apt-get remove --purge python-kivy
