.. _installation-canonical:

Installing Kivy
===============

Installation for Kivy version |kivy_version_bold|. Read the :ref:`changelog here <changelog>`.
For other Kivy versions, select the documentation from the dropdown on the top left.

Kivy |kivy_version| officially supports Python versions |python_versions_bold|.

==========  ==================  ==================================================  =======================================================================
‎           Platform            Installation                                        Packaging
==========  ==================  ==================================================  =======================================================================
|w_logo|    Windows             :ref:`pip<install-pip>`                             :ref:`PyInstaller<packaging-win>`
|m_logo|    macOS               :ref:`pip<install-pip>`, :ref:`Kivy.app<osx-app>`   :ref:`Kivy.app<packaging-osx-sdk>`, :ref:`PyInstaller<osx_pyinstaller>`
|l_logo|    Linux               :ref:`pip<install-pip>`, :ref:`PPA<linux-ppa>`      ---
|b_logo|    *BSD (FreeBSD,..)   :ref:`pip<install-pip>`                             ---
|r_logo|    RPi                 :ref:`pip<install-pip>`                             ---
|a_logo|    Android             :ref:`python-for-android<packaging_android>`        :ref:`python-for-android<packaging_android>`
|i_logo|    iOS                 :ref:`kivy-ios<packaging_ios>`                      :ref:`kivy-ios<packaging_ios>`
|c_logo|    Anaconda            :ref:`conda<install-conda>`                         ---
==========  ==================  ==================================================  =======================================================================

.. |w_logo| image:: ../images/windows.png
   :height: 20pt
.. |m_logo| image:: ../images/macosx.png
   :height: 20pt
.. |l_logo| image:: ../images/linux.png
   :height: 20pt
.. |b_logo| image:: ../images/freebsd.png
   :height: 20pt
.. |r_logo| image:: ../images/raspberrypi.png
   :height: 20pt
.. |a_logo| image:: ../images/android.png
   :height: 20pt
.. |i_logo| image:: ../images/IOS_wordmark_(2017).svg
   :height: 20pt
.. |c_logo| image:: ../images/conda.png
   :height: 20pt

.. _install-pip:

Using pip
---------

The easiest way to install Kivy is with ``pip``, which installs Kivy using either a
:ref:`pre-compiled wheel<pip-wheel>`, if available, otherwise from source (see below).

Kivy provides :ref:`pre-compiled wheels<kivy-wheel-install>` for the supported Python
versions on Windows, macOS, Linux, and RPi.

If no wheels are available ``pip`` will build the package from sources (i.e. on *BSD).

Alternatively, installing :ref:`from source<kivy-source-install>` is required for newer Python versions not listed
above or if the wheels do not work or fail to run properly.

On RPi, when using a 32 bit OS, wheels are provided for Python 3.7 (Raspberry Pi OS Buster) and Python 3.9 (Raspberry Pi OS Bullseye),
via the `PiWheels <https://www.piwheels.org/>`_ project. For other Python versions, on 32 bit OSes, you will need to
install from source.


Setup terminal and pip
^^^^^^^^^^^^^^^^^^^^^^

Before Kivy can be installed, Python and pip needs to be :ref:`pre-installed<install-python>`.
Then, start a :ref:`new terminal<command-line>` that has
:ref:`Python available<install-python>`. In the terminal, update ``pip`` and other installation
dependencies so you have the latest version as follows (for linux users you may have to
substitute ``python3`` instead of ``python`` and also add a ``--user`` flag in the
subsequent commands outside the virtual environment)::

     python -m pip install --upgrade pip setuptools virtualenv

Create virtual environment
^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a new `virtual environment <https://virtualenv.pypa.io/en/latest/>`_
for your Kivy project. A virtual environment will prevent possible installation conflicts
with other Python versions and packages. It's optional **but strongly recommended**:

#. Create the virtual environment named ``kivy_venv`` in your current directory::

       python -m virtualenv kivy_venv

#. Activate the virtual environment. You will have to do this step from the current directory
   **every time** you start a new terminal. This sets up the environment so the new ``kivy_venv``
   Python is used.

   For **Windows default CMD**, in the command line do::

       kivy_venv\Scripts\activate

   If you are in a bash terminal on **Windows**, instead do::

       source kivy_venv/Scripts/activate

   If you are in **linux** or **macOS**, instead do::

       source kivy_venv/bin/activate

Your terminal should now preface the path with something like ``(kivy_venv)``, indicating that
the ``kivy_venv`` environment is active. If it doesn't say that, the virtual environment
is not active and the following won't work.

Install Kivy
^^^^^^^^^^^^

Finally, install Kivy using one of the following options:

.. _kivy-wheel-install:

Pre-compiled wheels
~~~~~~~~~~~~~~~~~~~

The simplest is to install the current stable version of ``kivy`` and optionally ``kivy_examples``
from the kivy-team provided PyPi wheels. Simply do::

    python -m pip install "kivy[base]" kivy_examples

This also installs the minimum dependencies of Kivy. To additionally install Kivy with
**audio/video** support, install either ``kivy[base,media]`` or ``kivy[full]``.
See :ref:`Kivy's dependencies<kivy-dependencies>` for the list of selectors.

.. _kivy-source-install:

From source
~~~~~~~~~~~

If a wheel is not available or is not working, Kivy can be installed from source
with some additional steps. Installing from source means that Kivy will be installed
from source code and compiled directly on your system.

First install the additional system dependencies listed for each platform:
:ref:`Windows<install-source-win>`, :ref:`macOS<install-source-osx>`,
:ref:`Linux<install-source-linux>`, :ref:`*BSD<install-source-bsd>`,
:ref:`RPi<install-source-rpi>`

.. note::
    In past, for macOS, Linux and BSD Kivy required the installation of the SDL dependencies from package
    managers (e.g. ``apt`` or ``brew``). However, this is no longer officially supported as the version
    of SDL provided by the package managers is often outdated and may not work with Kivy as we
    try to keep up with the latest SDL versions in order to support the latest features and bugfixes.

    **You can still install the SDL dependencies from package managers if you wish, but we no longer
    offer support for this.**

    Instead, we recommend installing the SDL dependencies from source. This is the same process
    our CI uses to build the wheels. The SDL dependencies are built from source and installed into a 
    specific directory.

With all the build tools installed, you can now install the SDL dependencies from source for SDL support
(this is not needed on Windows as we provide pre-built SDL dependencies for Windows)

In order to do so, we provide a script that will download and build the SDL dependencies
from source. This script is located in the ``tools`` directory of the Kivy repository.

Create a directory to store the self-built dependencies and change into it::

    mkdir kivy-deps-build && cd kivy-deps-build

Then download the build tool script, according to your platform:

On **macOS**::

    curl -O https://raw.githubusercontent.com/kivy/kivy/master/tools/build_macos_dependencies.sh -o build_kivy_deps.sh

On **Linux**::

    curl -O https://raw.githubusercontent.com/kivy/kivy/master/tools/build_linux_dependencies.sh -o build_kivy_deps.sh

Make the script executable::

    chmod +x build_kivy_deps.sh

Finally, run the script::

    ./build_kivy_deps.sh

The script will download and build the SDL dependencies from source. It will also install
the dependencies into a directory named `kivy-dependencies`. This directory will be used
by Kivy to build and install Kivy from source with SDL support.

Kivy will need to know where the SDL dependencies are installed. To do so, you must set
the ``KIVY_DEPS_ROOT`` environment variable to the path of the ``kivy-dependencies`` directory.
For example, if you are in the ``kivy-deps-build`` directory, you can set the environment
variable with::

    export KIVY_DEPS_ROOT=$(pwd)/kivy-dependencies

With the dependencies installed, and `KIVY_DEPS_ROOT` set you can now install Kivy into the virtual environment.

To install the stable version of Kivy, from the terminal do::

    python -m pip install "kivy[base]" kivy_examples --no-binary kivy

To install the latest cutting-edge Kivy from **master**, instead do::

    python -m pip install "kivy[base] @ https://github.com/kivy/kivy/archive/master.zip"

If you want to install Kivy from a different branch, from your forked repository, or
from a specific commit (e.g. to test a fix from a user's PR) replace the corresponding
components of the url.

For example to install from the ``stable`` branch, the url becomes
``https://github.com/kivy/kivy/archive/stable.zip``. Or to try a specific commit hash, use e.g.
``https://github.com/kivy/kivy/archive/3d3e45dda146fef3f4758aea548da199e10eb382.zip``

.. _kivy-nightly-install:

Pre-release, pre-compiled wheels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install a pre-compiled wheel of the last **pre-release** version of Kivy, instead of the
current stable version, add the ``--pre`` flag to pip::

    python -m pip install --pre "kivy[base]" kivy_examples

This will only install a development version of Kivy if one was released to
`PyPi <https://pypi.org/project/Kivy/#history>`_. Instead, one can also install the
latest **cutting-edge** :ref:`Nightly wheels <nightly-win-wheels>` from the Kivy server with::

    python -m pip install kivy --pre --no-deps --index-url  https://kivy.org/downloads/simple/
    python -m pip install "kivy[base]" --pre --extra-index-url https://kivy.org/downloads/simple/

It is done in two steps, because otherwise ``pip`` may ignore the wheels on the server and install
an older pre-release version from PyPi.

.. _kivy-dev-install:

Development install
~~~~~~~~~~~~~~~~~~~

.. note::

    We suggest to select `master` or relevant branch/version of doc from top left,
    ensuring correct version/branch of kivy git repository you are working with.

If you want to edit Kivy before installing it, or if you want to try fixing some Kivy issue
and submit a pull request with the fix, you will need to first download the Kivy source code.
The following steps assumes git is pre-installed and available in the terminal.

The typical process is to clone Kivy locally with::

    git clone https://github.com/kivy/kivy.git

This creates a kivy named folder in your current path. Next, follow the same steps of the
:ref:`Installing from source <_kivy-source-install>` above, but instead of installing Kivy via a
distribution package or zip file, install it as an
`editable install <https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs>`_.

In order to do so, first change into the Kivy folder you just cloned::
and then install Kivy as an editable install::

    cd kivy
    python -m pip install -e ".[dev,full]"

Now, you can use git to change branches, edit the code and submit a PR.
Remember to compile Kivy each time you change cython files as follows::

    python setup.py build_ext --inplace

Or if using bash or on Linux, simply do::

    make

to recompile.

To run the test suite, simply run::

    pytest kivy/tests

or in bash or Linux::

    make test

On *BSD Unix remember to use ``gmake`` (GNU) in place of ``make`` (BSD).

Checking the demo
^^^^^^^^^^^^^^^^^

Kivy should now be installed. You should be able to ``import kivy`` in Python or,
if you installed the Kivy examples, run the demo.

on Windows::

    python kivy_venv\share\kivy-examples\demo\showcase\main.py

in bash, Linux and macOS::

    python kivy_venv/share/kivy-examples/demo/showcase/main.py

on *BSD Unix:

    python3 kivy_venv/share/kivy-examples/demo/showcase/main.py

The exact path to the Kivy examples directory is also stored in ``kivy.kivy_examples_dir``.

The 3d monkey demo under ``kivy-examples/3Drendering/main.py`` is also fun to see.

.. _install-conda:

Installation using Conda
------------------------

If you use `Anaconda <https://en.wikipedia.org/wiki/Anaconda_(Python_distribution)>`_, you can
install Kivy with its package manager `Conda <https://en.wikipedia.org/wiki/Conda_(package_manager)>`_ using::

   conda install kivy -c conda-forge

Do not use ``pip`` to install kivy if you're using Anaconda, unless you're installing from source.


.. _kivy-dependencies-win:

Installing Kivy's dependencies
------------------------------

Kivy supports one or more backends for its core providers. E.g. it supports glew, angle,
and sdl2 for the graphics backend on Windows. For each category (window, graphics, video,
audio, etc.), at least one backend must be installed to be able to use the category.

To facilitate easy installation, we provide ``extras_require``
`groups <https://setuptools.readthedocs.io/en/latest/userguide/dependency_management.html#optional-dependencies>`_
that will install selected backends to ensure a working Kivy installation. So one can install
Kivy more simply with e.g.``pip install "kivy[base,media,tuio]"``. The full list of selectors and
the packages they install is listed in
`setup.py <https://github.com/kivy/kivy/blob/master/setup.cfg>`_. The exact packages in each selector
may change in the future, but the overall goal of each selector will remain as described below.

We offer the following selectors:

    `base`: The minimum typical dependencies required for Kivy to run,
        not including video/audio.
    `media`: Only the video/audio dependencies required for Kivy to
        be able to play media.
    `full`: All the typical dependencies required for Kivy to run, including video/audio and
        most optional dependencies.
    `dev`: All the additional dependencies required to run Kivy in development mode
        (i.e. it doesn't include the base/media/full dependencies). E.g. any headers required for
        compilation, and all dependencies required to run the tests and creating the docs.
    `tuio`: The dependencies required to make TUIO work (primarily oscpy).

The following selectors install backends packaged as wheels by kivy under the ``Kivy_deps`` namespace.
They are typically released and versioned to match specific Kivy versions, so we provide selectors
to facilitate installation (i.e. instead of having to do ``pip install kivy kivy_deps.sdl2==x.y.z``,
you can now do ``pip install "kivy[sdl2]"`` to automatically install the correct sdl2 for the Kivy
version).

    `gstreamer`: The gstreamer video/audio backend, if it's available
        (currently only on Windows)
    `angle`: A alternate OpenGL backend, if it's available
        (currently only on Windows)
    `sdl2`: The window/image/audio backend, if it's available (currently only on Windows,
        on macOS, Linux and *BSD Unix is already included in the main Kivy wheel).
    `glew`: A alternate OpenGL backend, if it's available (currently only on Windows)

Following are the ``kivy_deps`` dependency wheels:

* `gstreamer <https://gstreamer.freedesktop.org>`_ (optional)

  ``kivy_deps.gstreamer`` is an optional dependency which is only needed for audio/video support.
  We only provide it on Windows, for other platforms it must be installed independently.
  Alternatively, use `ffpyplayer <https://pypi.org/project/ffpyplayer/>`_  instead.

* `glew <http://glew.sourceforge.net/>`_ and/or
  `angle <https://github.com/Microsoft/angle>`_

  ``kivy_deps.glew`` and ``kivy_deps.angle`` are for `OpenGL <https://en.wikipedia.org/wiki/OpenGL>`_.
  You can install both, that is no problem. It is only available on Windows. On other
  platforms it is not required externally.

  One can select which of these to use for OpenGL using the
  ``KIVY_GL_BACKEND`` environment variable: By setting it to ``glew``
  (the default), ``angle_sdl2``, or ``sdl2``. Here, ``angle_sdl2`` is a substitute for
  ``glew`` but requires ``kivy_deps.sdl2`` be installed as well.

* `sdl2 <https://libsdl.org>`_

  ``kivy_deps.sdl2`` is for window/images/audio and optionally OpenGL. It is only available on Windows
  and is included in the main Kivy wheel for other platforms.

Python glossary
---------------

Here we explain how to install Python packages, how to use the command line and what wheels are.

.. _install-python:

Installing Python
^^^^^^^^^^^^^^^^^

Kivy is written in
`Python <https://en.wikipedia.org/wiki/Python_%28programming_language%29>`_
and as such, to use Kivy, you need an existing
installation of `Python <https://www.python.org/downloads/windows/>`_.
Multiple versions of Python can be installed side by side, but Kivy needs to
be installed as package under each Python version that you want to use Kivy in.

To install Python, see the instructions for each platform:
:ref:`Windows<install-python-win>`, :ref:`macOS<install-python-osx>`,
:ref:`Linux<install-python-linux>`, :ref:`RPi<install-python-rpi>`,
:ref:`*BSD<install-python-bsd>`.

Once Python is installed, open the :ref:`console <command-line>` and make sure
Python is available by typing ``python --version``.

.. _command-line:

How to use the command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To execute any of the ``pip`` or ``wheel`` commands given here, you need a *command line* (here also called *console*, *terminal*, `shell <https://en.wikipedia.org/wiki/Unix_shell>`_ or `bash <https://en.wikipedia.org/wiki/Bash_(Unix_shell)>`_, where the last two refer to Linux / *BSD Unix style command lines) and Python must be on the `PATH <https://en.wikipedia.org/wiki/PATH_(variable)>`_.

The default command line on Windows is the
`command prompt <http://www.computerhope.com/issues/chusedos.htm>`_, short *cmd*. The
quickest way to open it is to press `Win+R` on your keyboard.
In the window that opens, type ``cmd`` and then press enter.

Alternative Linux style command lines on Windows that we recommend are
`Git for Windows <https://git-for-windows.github.io/>`_ or `Mysys <http://www.mingw.org/wiki/MSYS>`_.

Note, the default Windows command line can still be used, even if a bash terminal is installed.

To temporarily add your Python installation to the PATH, simply open your command line and then use the ``cd`` command to change the current directory to where python is installed, e.g. ``cd C:\Python37``.

If you have installed Python using the default options, then the path to Python will already be permanently on your PATH variable. There is an option in the installer which lets you do that, and it is enabled by default.

If however Python is not on your PATH, follow the these instructions to add it:

* Instructions for `the windows command line <http://www.computerhope.com/issues/ch000549.htm>`_
* Instructions for `bash command lines <http://stackoverflow.com/q/14637979>`_

.. _pip-wheel:

What is pip and what are wheels
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In Python, packages such as Kivy can be installed with the python package
manager, named `pip <https://pip.pypa.io/en/stable/>`_ ("python install package").

When installing from source, some packages, such as Kivy, require additional steps, like compilation.

Contrary, wheels (files with a ``.whl`` extension) are pre-built
distributions of a package that has already been compiled.
These wheels do not require additional steps when installing them.

When a wheel is available on `pypi.org <https://pypi.python.org/pypi>`_ ("Python Package Index") it can be installed with ``pip``. For example when you execute ``python -m pip install kivy`` in a command line, this will automatically find the appropriate wheel on PyPI.

When downloading and installing a wheel directly, use the command
``python -m pip install <wheel_file_name>``, for example::

    python -m pip install C:\Kivy-1.9.1.dev-cp27-none-win_amd64.whl

.. _nightly-wheels:

What are nightly wheels
^^^^^^^^^^^^^^^^^^^^^^^

Every day we create a snapshot wheel of the current development version of Kivy ('nightly wheel').
You can find the development version in the master branch of the
`Kivy Github repository <https://github.com/kivy/kivy>`_.

As opposed to the last *stable* release (which we discussed in the previous section), nightly
wheels contain all the latest changes to Kivy, including experimental fixes.
For installation instructions, see :ref:`kivy-nightly-install`.

.. warning::

    Using the latest development version can be risky and you might encounter
    issues during development. If you encounter any bugs, please report them.
