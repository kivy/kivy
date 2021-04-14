.. _installation_osx:

Installation on OS X
====================

To install Kivy on OS X using ``pip``, please follow the main
:ref:`installation guide<installation-canonical>`.
Otherwise, continue to the :ref:`Kivy.app instructions below<osx-app>`.

Installation components
-----------------------

Following, are additional information linked to from some of the steps in the
main :ref:`installation guide<installation-canonical>`, specific to OS X.

.. _install-python-osx:

Installing Python
^^^^^^^^^^^^^^^^^

Homebrew
~~~~~~~~

If you're using `Homebrew <http://brew.sh>`_, you can install Python with::

    brew install python3

MacPorts
~~~~~~~~

If you're using `Macports <https://www.macports.org>`_, you can install Python with::

    # Install and set e.g. Python 3.8 as the default
    port install python38
    port select --set python python38

    # Install and set pip as the default::
    port install py38-pip
    port select --set pip py38-pip

Frameworks
~~~~~~~~~~

To install frameworks Python on OSX, download it from the main
`Python website <https://www.python.org/downloads/mac-osx/>`_ and follow the
installation steps. You can read more about the installation in the
`Python guide <https://docs.python.org/3/using/mac.html>`_.

.. _install-source-osx:

Source installation Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install Kivy from source, please follow the installation guide until you reach the
:ref:`Kivy install step<kivy-source-install>` and then install the additional dependencies
below before continuing.

Homebrew
~~~~~~~~

If you're using Homebrew, you can install the dependencies with::

    brew install pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer

MacPorts
~~~~~~~~

.. note::

    You will have to manually install gstreamer support if you wish to
    support video playback in your Kivy App. The latest port documents show the
    following `py-gst-python port <https://trac.macports.org/ticket/44813>`_.

If you're using MacPorts, you can install the dependencies with::

    port install libsdl2 libsdl2_image libsdl2_ttf libsdl2_mixer

Frameworks
~~~~~~~~~~

If you're installing Python from a framework, you will need to install Kivy's dependencies
from frameworks as well. You can do that with the following commands (customize as needed)::

    # configure kivy
    export CC=clang
    export CXX=clang
    export FFLAGS='-ff2c'
    export USE_SDL2=1
    export USE_GSTREAMER=1

    # get the dependencies
    export SDL2=2.0.12
    export SDL2_IMAGE=2.0.5
    export SDL2_MIXER=2.0.4
    export SDL2_TTF=2.0.15
    export GSTREAMER=1.16.2

    curl -O -L "https://www.libsdl.org/release/SDL2-$SDL2.dmg"
    curl -O -L "https://www.libsdl.org/projects/SDL_image/release/SDL2_image-$SDL2_IMAGE.dmg"
    curl -O -L "https://www.libsdl.org/projects/SDL_mixer/release/SDL2_mixer-$SDL2_MIXER.dmg"
    curl -O -L "https://www.libsdl.org/projects/SDL_ttf/release/SDL2_ttf-$SDL2_TTF.dmg"
    curl -O -L "https://gstreamer.freedesktop.org/data/pkg/osx/$GSTREAMER/gstreamer-1.0-$GSTREAMER-x86_64.pkg"
    curl -O -L "https://gstreamer.freedesktop.org/data/pkg/osx/$GSTREAMER/gstreamer-1.0-devel-$GSTREAMER-x86_64.pkg"

    hdiutil attach SDL2-$SDL2.dmg
    sudo cp -a /Volumes/SDL2/SDL2.framework /Library/Frameworks/
    hdiutil attach SDL2_image-$SDL2_IMAGE.dmg
    sudo cp -a /Volumes/SDL2_image/SDL2_image.framework /Library/Frameworks/
    hdiutil attach SDL2_ttf-$SDL2_TTF.dmg
    sudo cp -a /Volumes/SDL2_ttf/SDL2_ttf.framework /Library/Frameworks/
    hdiutil attach SDL2_mixer-$SDL2_MIXER.dmg
    sudo cp -a /Volumes/SDL2_mixer/SDL2_mixer.framework /Library/Frameworks/

    sudo installer -package gstreamer-1.0-$GSTREAMER-x86_64.pkg -target /
    sudo installer -package gstreamer-1.0-devel-$GSTREAMER-x86_64.pkg -target /

Now that you have all the dependencies for kivy, you need to make sure
you have the command line tools installed::

    xcode-select --install

.. _osx-app:

Using The Kivy.app
------------------

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^

You can run any Kivy application by simply dragging the application's main file
onto the Kivy.app icon.
