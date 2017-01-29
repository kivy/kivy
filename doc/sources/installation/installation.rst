.. _installation:

Installation
============

We try not to reinvent the wheel, but to bring something innovative to the
market. As a consequence, we're focused on our own code and use pre-existing,
high quality third-party libraries where possible.
To support the full, rich set of features that Kivy offers, several other libraries are
required. If you do not use a specific feature (e.g. video playback), you
don't need the corresponding dependency.
That said, there is one dependency that Kivy **does** require:
`Cython <http://cython.org>`_.

|cython_note|

In addition, you need a `Python <http://python.org/>`_ 2.x (2.7 <= x < 3.0)
or 3.x (3.3 <= x)
interpreter. If you want to enable features like windowing (i.e. open a Window),
audio/video playback or spelling correction, additional dependencies must
be available. For these, we recommend `SDL2 <https://www.libsdl.org/download-2.0.php>`_, `Gstreamer 1.x
<http://www.gstreamer.net/>`_ and `PyEnchant
<https://pythonhosted.org/pyenchant/>`_, respectively.


Other optional libraries (mutually independent) are:

    * `OpenCV 2.0 <http://sourceforge.net/projects/opencvlibrary/>`_ -- Camera input.
    * `Pillow <https://python-pillow.github.io/>`_ -- Image and text display.
    * `PyEnchant <https://pythonhosted.org/pyenchant/>`_ -- Spelling correction.


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
    installation-osx
    installation-linux
    installation-android
    installation-rpi


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

To install Kivy's dependencies, follow the guide below for your platform. You
might also need these packages for the RST and lexing components::

    $ sudo pip install pygments docutils

Ubuntu
++++++

For Ubuntu 12.04 and above (tested to 14.04), simply enter the following command
that will install all necessary packages::

    $ sudo apt-get install python-setuptools python-pygame python-opengl \
      python-gst0.10 python-enchant gstreamer0.10-plugins-good python-dev \
      build-essential libgl1-mesa-dev-lts-quantal libgles2-mesa-dev-lts-quantal\
      python-pip

For Ubuntu 15.04 and versions older than 12.04, this one should work::

    $ sudo apt-get install python-setuptools python-pygame python-opengl \
      python-gst0.10 python-enchant gstreamer0.10-plugins-good python-dev \
      build-essential libgl1-mesa-dev libgles2-mesa-dev zlib1g-dev python-pip

Kivy requires a recent version of Cython, so it's better to use the latest
supported version from pypi:

.. parsed-literal::

    $ sudo pip install --upgrade |cython_install|

OS X
++++

Without using brew you can install the dependencies for kivy by
manually pasting the following commands in a terminal::

    curl -O -L https://www.libsdl.org/release/SDL2-2.0.4.dmg
    curl -O -L https://www.libsdl.org/projects/SDL_image/release/SDL2_image-2.0.1.dmg
    curl -O -L https://www.libsdl.org/projects/SDL_mixer/release/SDL2_mixer-2.0.1.dmg
    curl -O -L https://www.libsdl.org/projects/SDL_ttf/release/SDL2_ttf-2.0.13.dmg
    curl -O -L http://gstreamer.freedesktop.org/data/pkg/osx/1.7.1/gstreamer-1.0-1.7.1-x86_64.pkg
    curl -O -L http://gstreamer.freedesktop.org/data/pkg/osx/1.7.1/gstreamer-1.0-devel-1.7.1-x86_64.pkg
    hdiutil attach SDL2-2.0.4.dmg
    sudo cp -a /Volumes/SDL2/SDL2.framework /Library/Frameworks/

This should ask you for your root password, provide it and then paste
the following lines in your terminal::

    hdiutil attach SDL2_image-2.0.1.dmg
    sudo cp -a /Volumes/SDL2_image/SDL2_image.framework /Library/Frameworks/
    hdiutil attach SDL2_ttf-2.0.13.dmg
    sudo cp -a /Volumes/SDL2_ttf/SDL2_ttf.framework /Library/Frameworks/
    hdiutil attach SDL2_mixer-2.0.1.dmg
    sudo cp -a /Volumes/SDL2_mixer/SDL2_mixer.framework /Library/Frameworks/
    sudo installer -package gstreamer-1.0-1.7.1-x86_64.pkg -target /
    sudo installer -package gstreamer-1.0-devel-1.7.1-x86_64.pkg -target /
    pip install --upgrade --user cython pillow

Now that you have all the dependencies for kivy, you need to make sure
you have the command line tools installed::

    xcode-select --install

Go to an appropriate dir like::

    mkdir ~/code
    cd ~/code

You can now install kivy itself::

    git clone http://github.com/kivy/kivy
    cd kivy
    make

This should compile kivy, to make it accessible in your python env
just point your PYTHONPATH to this dir::

    export PYTHONPATH=~/code/kivy:$PYTHONPATH

To check if kivy is installed, type the following command in your
terminal::

    python -c "import kivy"

It should give you an output similar to the following::

    $ python -c "import kivy"
    [INFO   ] [Logger      ] Record log in /Users/quanon/.kivy/logs/kivy_15-12-31_21.txt
    [INFO   ] [Screen      ] Apply screen settings for Motorola Droid 2
    [INFO   ] [Screen      ] size=480x854 dpi=240 density=1.5 orientation=portrait
    [INFO   ] [Kivy        ] v1.9.1-stable
    [INFO   ] [Python      ] v2.7.10 (default, Oct 23 2015, 18:05:06)
    [GCC 4.2.1 Compatible Apple LLVM 7.0.0 (clang-700.0.59.5)]

OSX HomeBrew
++++++++++++
If you prefer to use homebrew:
install the requirements using `homebrew <http://brew.sh>`_::

     $ brew install sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer

Windows
+++++++

See :ref:`dev-install-win`.

.. _dev-install:

Installing Kivy for Development
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that you've installed all the required dependencies, it's time to
download and compile a development version of Kivy:

Download Kivy from GitHub::

    $ git clone git://github.com/kivy/kivy.git
    $ cd kivy

Compile::

    $ python setup.py build_ext --inplace -f

If you have the ``make`` command available, you can also use the
following shortcut to compile (does the same as the last command)::

    $ make

.. warning::

  By default, versions 2.7 to 2.7.2 of Python use the gcc compiler which ships
  with earlier versions of XCode. As of version 4.2, only the clang compiler
  is shipped with XCode by default. This means that if you build using XCode
  4.2 or above, you need to ensure you have at least Python 2.7.3 installed,
  but preferably the latest version (2.7.5 at the time of writing).

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
codebase, please read :ref:`contributing`.

Running the test suite
~~~~~~~~~~~~~~~~~~~~~~

To help detect issues and behaviour changes in Kivy, a set of unittests are
provided. A good thing to do is to run them just after your Kivy installation, and
every time you intend to push a change. If you think something was broken
in Kivy, perhaps a test will show this. (If not, it might be a good time to write
one.)

Kivy tests are based on nosetest, which you can install from your package
manager or using pip::

  $ pip install nose

To run the test suite, do::

  $ make test

Uninstalling Kivy
~~~~~~~~~~~~~~~~~

If you are mixing multiple Kivy installations, you might be confused about where each Kivy version is
located. Please note that you might need to follow these steps multiple times if you have multiple
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
