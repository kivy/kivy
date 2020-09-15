.. _installation_osx:

Installation on OS X
====================

.. note::

    This guide describes multiple ways for setting up Kivy.

Using Wheels
------------

Wheels are precompiled binaries for the specific platform you are on.
All you need to do to install Kivy using wheels on osx is ::

    $ python -m pip install kivy

Gstreamer is not included, so if you would like to use media playback with kivy,
you should install `ffpyplayer` like so ::

    $ python -m pip install ffpyplayer

Make sure to set `KIVY_VIDEO=ffpyplayer` env variable before running the app.

Nightly wheel installation
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. warning::

    Using the latest development version can be risky and you might encounter
    issues during development. If you encounter any bugs, please report them.

Snapshot wheels of current Kivy master are created daily on the
``master`` branch of kivy repository. You can install wheels with::

    pip install kivy[base] kivy_examples --pre --extra-index-url https://kivy.org/downloads/simple/

Using Conda
-----------

If you use Anaconda, you can simply install kivy using::

   $ conda install kivy -c conda-forge

.. _osx-run-app:

Using The Kivy.app
------------------

.. note::

    These instructions apply only from Kivy v2.0.0 onwards.

.. note::

    Kivy.app is built on the `current GitHub Action macOS version
    <https://github.com/actions/virtual-environments#available-environments>`_ and will typically
    not work on older OS X versions. For older OS X versions, you need to build Kivy.app
    on the oldest machine you wish to support. See below.

For OS X 10.14.4+ and later, we provide a Kivy DMG with all dependencies
bundled in a **virtual environment**, including a Python interpreter. This is
primarily useful for packaging Kivy applications.

You can find complete instructions to build and package apps with Kivy.app in the readme
of the `kivy-sdk-packager repo <https://github.com/kivy/kivy-sdk-packager/tree/master/osx>`_.

To install the Kivy virtualenv, you must:

    1. Navigate to the latest Kivy release on Kivy's `website <https://kivy.org/downloads/>`_ or
       `GitHub <https://github.com/kivy/kivy/releases>`_ and download ``Kivy.dmg``.
       You can also download a nightly snapshot of
       `Kivy.app <https://kivy.org/downloads/ci/osx/app/Kivy.dmg>`_.
    2. Open the dmg
    3. In the GUI copy the Kivy.app to /Applications by dragging the folder icon to the right.
    4. Optionally create a symlink by running the following command::

           ``ln -s /Applications/Kivy.app/Contents/Resources/script /usr/local/bin/kivy``

       This creates the ``kivy`` binary that you can use instead of python to run scripts.
       I.e. instead of doing ``python my_script.py`` or ``python -m pip install <module name>``, write
       ``kivy my_script.py`` or ``kivy -m pip install <module name>`` to run it using the kivy
       bundled Python interpreter with the kivy environment.

       As opposed to activating the virtualenv below, running with ``kivy`` will use the virtualenv
       but also properly configure the script environment required to run a Kivy app (i.e. setting
       kivy's home path etc.).

Using the App Virtual environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The path to the underlying virtualenv is ``/Applications/Kivy.app/Contents/Resources/venv``.
To activate it so you can use python, like any normal virtualenv, do::

        pushd /Applications/Kivy.app/Contents/Resources/venv/bin
        source activate
        source kivy_activate
        popd

On the default mac (zsh) shell you **must** be in the bin directory containing ``activate`` to be
able to ``activate`` the virtualenv, hence why we changed the directory temporarily.

``kivy_activate`` sets up the environment to be able to run Kivy, by setting the kivy home,
gstreamer, and other variables.

Start any Kivy Application
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can run any Kivy application by simply dragging the application's main file
onto the Kivy.app icon.


Using Homebrew with pip
-----------------------

You can install Kivy with Homebrew and pip using the following steps:

    1. Install the requirements using `homebrew <http://brew.sh>`_::

        $ brew install pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer python3

    2. Install Kivy using pip::

           $ python3 -m pip install --no-binary kivy kivy[base]

       To install the development version, use this in the second step::

           $ python3 -m pip install "kivy[base] @ https://github.com/kivy/kivy/archive/master.zip"

Using MacPorts with pip
-----------------------

.. note::

    You will have to manually install gstreamer support if you wish to
    support video playback in your Kivy App. The latest port documents show the
    following `py-gst-python port <https://trac.macports.org/ticket/44813>`_.

You can install Kivy with Macports and pip using the following steps:

    1. Install `Macports <https://www.macports.org>`_

    2. Install and set Python 3.8 as the default::

        $ port install python38
        $ port select --set python python38

    3. Install and set pip as the default::

        $ port install py38-pip
        $ port select --set pip py38-pip

    4. Install the requirements using `Macports <https://www.macports.org>`_::

        $ port install libsdl2 libsdl2_image libsdl2_ttf libsdl2_mixer

    2. Install Kivy using pip::

           $ python3 -m pip install --no-binary kivy kivy[base]

       To install the development version, use this in the second step::

           $ python3 -m pip install "kivy[base] @ https://github.com/kivy/kivy/archive/master.zip"
