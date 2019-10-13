.. _installation_windows:

Installation on Windows
=======================

Using Conda
-----------

If you use Anaconda, you can simply install kivy using::

   $ conda install kivy -c conda-forge

Otherwise, continue below to install Kivy in a native Python installation.

Prerequisites
-------------

Kivy is written in
`Python <https://en.wikipedia.org/wiki/Python_%28programming_language%29>`_
and as such, to use Kivy, you need an existing
installation of `Python <https://www.python.org/downloads/windows/>`_.
Multiple versions of Python can be installed side by side, but Kivy needs to
be installed in each Python version that you want to use Kivy in.

Beginning with 1.9.1 we provide binary
`wheels <https://wheel.readthedocs.org/en/latest/>`_
for Kivy and all its dependencies to be used with an existing Python
installation. See :ref:`install-win-dist`.

We also provide nightly wheels generated using Kivy
`master <https://github.com/kivy/kivy>`_. See :ref:`install-nightly-win-dist`.
If installing kivy to an **alternate
location** and not to site-packages, please see :ref:`alternate-win`.

.. note::

    For Python < 3.5 we use the MinGW compiler. However, for Python 3.5+ on
    Windows we currently only support the MSVC compiler
    because of the following Python
    `issue 4709 <http://bugs.python.org/issue4709>`_ about MinGW.
    Generally this should make no difference when using precompiled wheels.

.. _install-win-dist-upgrade:

Updating Kivy from a previous release
-------------------------------------

When updating from a previous Kivy release, all the Kivy dependencies must be
updated first. Typically, just adding `--upgrade` to the `pip install ...` commands below
is sufficient for pip to update them.

.. warning::

    When updating from Kivy 1.10.1 or lower to 1.11.0 or higher, one **must** manually
    uninstall all kivy dependencies before upgrading because won't update them properly.
    This is done with::

        python -m pip uninstall -y kivy.deps.glew kivy.deps.gstreamer kivy.deps.sdl2 kivy.deps.angle

    assuming all the dependencies were previously installed. See :ref:`kivy-dependencies` for more details.

    After uninstalling, continue with the installation below.

.. _install-win-dist:

Installing the kivy stable release
-----------------------------------

.. warning::

    Kivy 1.11.1 is the last release that supports Python 2.

Now that python is installed, open the :ref:`windows-run-app` and make sure
python is available by typing ``python --version``. Then, do the following to
create a new `virtual environment <https://virtualenv.pypa.io/en/latest/>`_
(optionally) and install the most recent stable
kivy release (`1.11.1`) and its dependencies.

#. Ensure you have the latest pip, wheel, and virtualenv::

     python -m pip install --upgrade pip wheel setuptools virtualenv

   Optionally create a new `virtual environment <https://virtualenv.pypa.io/en/latest/>`_
   for your Kivy project. Highly recommended:

   #. First create the environment named `kivy_venv` in your current directory::

        python -m virtualenv kivy_venv

   #. Activate the virtual environment. You'll have to do this step from the current directory
      **every time** you start a new terminal. On windows CMD do::

        kivy_venv\Scripts\activate

      If you're in a bash terminal, instead do::

        source kivy_venv/Scripts/activate

   Your terminal should now preface the path with something like `(kivy_venv)`, indicating that
   the `kivy_venv` environment is active. If it doesn't say that, the virtual environment is not active.

#. Install the dependencies (skip gstreamer (~120MB) if not needed, see
   :ref:`kivy-dependencies`). If you are upgrading Kivy, see :ref:`install-win-dist-upgrade`::

     python -m pip install docutils pygments pypiwin32 kivy_deps.sdl2==0.1.22 kivy_deps.glew==0.1.12
     python -m pip install kivy_deps.gstreamer==0.1.17

   .. note::

       If you encounter a `MemoryError` while installing, add after
       `pip install` the `--no-cache-dir` option.

   For Python 3.5+, you can also use the angle backend instead of glew. This
   can be installed with::

     python -m pip install kivy_deps.angle==0.1.9

   .. warning::

       When installing, pin kivy's dependencies to the specific version that was released on pypi
       when your kivy version was released, like above. Otherwise you may get an incompatible dependency
       when it is updated in the future.

#. Install kivy::

     python -m pip install kivy==1.11.1

#. (Optionally) Install the kivy examples::

     python -m pip install kivy_examples==1.11.1

   The examples are installed in the share directory under the root directory where python is installed.

That's it. You should now be able to ``import kivy`` in python or run a basic
example if you installed the kivy examples::

    python kivy_venv\share\kivy-examples\demo\showcase\main.py

Replace `kivy_venv` with the path where python is installed if you didn't use a virtualenv.

.. note::

    If you encounter any **permission denied** errors, try opening the
    `Command prompt as administrator
    <https://technet.microsoft.com/en-us/library/cc947813%28v=ws.10%29.aspx>`_
    and trying again. The best solution for this is to use a virtual environment
    instead.

What are wheels, pip and wheel
------------------------------

In Python, packages such as Kivy can be installed with the python package
manager, `pip <https://pip.pypa.io/en/stable/>`_. Some packages such as Kivy
require additional steps, such as compilation, when installing using the Kivy
source code with pip. Wheels (with a ``.whl`` extension) are pre-built
distributions of a package that has already been compiled and do not require
additional steps to install.

When hosted on `pypi <https://pypi.python.org/pypi>`_ one installs a wheel
using ``pip``, e.g. ``python -m pip install kivy``. When downloading and
installing a wheel directly, ``python -m pip install wheel_file_name`` is used,
such as::

    python -m pip install C:\Kivy-1.9.1.dev-cp27-none-win_amd64.whl

.. _install-nightly-win-dist:

Nightly wheel installation
--------------------------

.. |cp35_win32| replace:: Python 3.5, 32bit
.. _cp35_win32: https://kivy.org/downloads/appveyor/kivy/Kivy-2.0.0.dev0-cp35-cp35m-win32.whl
.. |cp35_amd64| replace:: Python 3.5, 64bit
.. _cp35_amd64: https://kivy.org/downloads/appveyor/kivy/Kivy-2.0.0.dev0-cp35-cp35m-win_amd64.whl
.. |cp36_win32| replace:: Python 3.6, 32bit
.. _cp36_win32: https://kivy.org/downloads/appveyor/kivy/Kivy-2.0.0.dev0-cp36-cp36m-win32.whl
.. |cp36_amd64| replace:: Python 3.6, 64bit
.. _cp36_amd64: https://kivy.org/downloads/appveyor/kivy/Kivy-2.0.0.dev0-cp36-cp36m-win_amd64.whl
.. |cp37_win32| replace:: Python 3.7, 32bit
.. _cp37_win32: https://kivy.org/downloads/appveyor/kivy/Kivy-2.0.0.dev0-cp37-cp37m-win32.whl
.. |cp37_amd64| replace:: Python 3.7, 64bit
.. _cp37_amd64: https://kivy.org/downloads/appveyor/kivy/Kivy-2.0.0.dev0-cp37-cp37m-win_amd64.whl
.. |examples_whl| replace:: Kivy examples
.. _examples_whl: https://kivy.org/downloads/appveyor/kivy/Kivy_examples-2.0.0.dev0-py2.py3-none-any.whl

.. warning::

    Using the latest development version can be risky and you might encounter
    issues during development. If you encounter any bugs, please report them.

Snapshot wheels of current Kivy master are created daily on the
`master` branch of kivy repository. They can be found
`here <https://kivy.org/downloads/appveyor/kivy>`_. To use them, instead of
doing ``python -m pip install kivy`` we'll install one of these wheels as
follows.

+ |cp35_win32|_
+ |cp36_win32|_
+ |cp37_win32|_

- |cp35_amd64|_
- |cp36_amd64|_
- |cp37_amd64|_

#. Perform steps 1 and 2 of the above Installation section.
#. Download the appropriate wheel for your system.
#. Install it with ``python -m pip install wheel-name`` where ``wheel-name``
   is the name of the file.

Kivy examples are separated from the core because of their size. The examples
can be installed separately on both Python 2 and 3 with this single wheel:

- |examples_whl|_

.. _kivy-dependencies:

Kivy's dependencies
-------------------

We offer wheels for Kivy and its dependencies separately so only desired
dependencies need be installed. The dependencies are offered as
optional sub-packages of kivy_deps, e.g. ``kivy_deps.sdl2``.

.. note::

    In Kivy 1.11.0 we transitioned the kivy Windows dependencies from the
    `kivy.deps.xxx` namespace stored under `kivy/deps/xxx` to the
    `kivy_deps.xxx` namespace stored under `kivy_deps/xxx`. Pip is
    sometimes not able to distinguish between these two formats, so follow the
    instructions at :ref:`install-win-dist-upgrade` when upgrading from a older Kivy.
    See `here <https://github.com/kivy/kivy/wiki/Moving-kivy.garden.xxx-to-kivy_garden.xxx-and-kivy.deps.xxx-to-kivy_deps.xxx#kivy-deps>`_
    for more details.

Currently on Windows, we provide the following dependency wheels:

* `gstreamer <https://gstreamer.freedesktop.org>`_ for audio and video
* `glew <http://glew.sourceforge.net/>`_ and/or
  `angle (3.5 only) <https://github.com/Microsoft/angle>`_ for OpenGL
* `sdl2 <https://libsdl.org>`_ for control and/or OpenGL.

One can select which of these to use for OpenGL using the
`KIVY_GL_BACKEND` envrionment variable by setting it to `glew`
(the default), `angle`, or `sdl2`. `angle` is currently
in an experimental phase as a substitute for `glew` on Python
3.5+ only.

`gstreamer` is an optional dependency which only needs to be
installed if video display or audio is desired. `ffpyplayer`
is an alternate dependency for audio or video.

.. _windows-run-app:

Command line
------------

Know your command line. To execute any of the ``pip``
or ``wheel`` commands, one needs a command line tool with python on the path.
The default command line on Windows is
`Command Prompt <http://www.computerhope.com/issues/chusedos.htm>`_, and the
quickest way to open it is to press `Win+R` on your keyboard, type ``cmd``
in the window that opens, and then press enter.

Alternate linux style command shells that we recommend is
`Git for Windows <https://git-for-windows.github.io/>`_ which offers a bash
command line as `well <http://rogerdudler.github.io/git-guide/>`_ as
`git <https://try.github.io>`_. Note, CMD can still be used even if bash is
installed.

Walking the path! To add your python to the path, simply open your command line
and then use the ``cd`` command to change the current directory to where python
is installed, e.g. ``cd C:\Python37``. Alternatively if you only have one
python version installed, permanently add the python directory to the path for
`cmd <http://www.computerhope.com/issues/ch000549.htm>`_ or
`bash <http://stackoverflow.com/q/14637979>`_.

.. _dev-install-win:

Use development Kivy
--------------------

.. warning::

    Using the latest development version can be risky and you might encounter
    issues during development. If you encounter any bugs, please report them.

To compile and install kivy using the kivy
`source code <https://github.com/kivy/kivy/archive/master.zip>`_  or to use
kivy with git rather than a wheel there are some additional steps:

#. Both the ``python`` and the ``Python\Scripts`` directories **must** be on
   the path. They must be on the path every time you recompile kivy.

#. Ensure you have the latest pip and wheel with::

     python -m pip install --upgrade pip wheel setuptools

#. Get the compiler.
   For Python < 3.5 we use mingwpy as follows.

   #. Create the
      ``python\Lib\distutils\distutils.cfg`` file and add the two lines::

        [build]
        compiler = mingw32

   #. Install MinGW with::

        python -m pip install -i https://pypi.anaconda.org/carlkl/simple mingwpy

   For Python 3.5 we use the MSVC compiler. For 3.5,
   `Visual Studio 2015 <https://www.visualstudio.com/downloads/>`_ is
   required, which is availible for free. Just download and install it and
   you'll be good to go.

   Visual Studio is very big so you can also use the smaller,
   `Visual C Build Tools instead
   <https://github.com/kivy/kivy/wiki/Using-Visual-C---Build-Tools-instead-of-Visual-Studio-on-Windows>`_.

#. Set the environment variables. On windows do::

     set USE_SDL2=1
     set USE_GSTREAMER=1

   In bash do::

     export USE_SDL2=1
     export USE_GSTREAMER=1

   These variables must be set everytime you recompile kivy.

#. Install the other dependencies as well as their dev versions (you can skip
   gstreamer and gstreamer_dev if you aren't going to use video/audio). we don't pin
   the versions of the dependencies like for the stable kivy because we want the
   latest:

   .. parsed-literal::

     python -m pip install |cython_install| docutils pygments pypiwin32 kivy_deps.sdl2 \
     kivy_deps.glew kivy_deps.gstreamer kivy_deps.glew_dev kivy_deps.sdl2_dev \
     kivy_deps.gstreamer_dev

#. If you downloaded or cloned kivy to an alternate location and don't want to
   install it to site-packages read the next section.

#. Finally compile and install kivy with ``pip install filename``, where
   ``filename`` can be a url such as
   ``https://github.com/kivy/kivy/archive/master.zip`` for kivy master, or the
   full path to a local copy of a kivy.

Compile Kivy
^^^^^^^^^^^^

#. Start installation of Kivy cloned or downloaded and extracted from GitHub.
   You should be in the root directory where kivy is extracted containing the
   `setup.py` file::

    python -m pip install .

If the compilation succeeds without any error, Kivy should be good to go. You
can test it with running a basic example::

    python share\kivy-examples\demo\showcase\main.py

.. _alternate-win:

Installing Kivy and editing it in place
----------------------------------------

In development, Kivy is often cloned or downloaded to a location and then
installed with::

    python -m pip install -e kivy_path

Now you can safely compile kivy in its current location with one of these
commands::

    make
    python setup.py build_ext --inplace

But kivy would be fully installed and available from Python. remember to re-run the above command
whenever any of the cython files are changed (e.g. if you pulled from GitHub) to recompile.

Making Python available anywhere
--------------------------------

There are two methods for launching python on your ``*.py`` files.

Double-click method
^^^^^^^^^^^^^^^^^^^

If you only have one Python installed, you can associate all ``*.py`` files
with your python, if it isn't already, and then run it by double clicking. Or
you can only do it once if you want to be able to choose each time:

#. Right click on the Python file (.py file extension) of the application you
   want to launch

#. From the context menu that appears, select *Open With*
#. Browse your hard disk drive and find the file ``python.exe`` that you want
   to use. Select it.

#. Select "Always open the file with..." if you don't want to repeat this
   procedure every time you double click a .py file.

#. You are done. Open the file.

Send-to method
^^^^^^^^^^^^^^

You can launch a .py file with our Python using the Send-to menu:

#. Browse to the ``python.exe`` file you want to use. Right click on it and
   copy it.

#. Open Windows explorer (File explorer in Windows 8), and to go the address
   'shell:sendto'. You should get the special Windows directory `SendTo`

#. Paste the previously copied ``python.exe`` file **as a shortcut**.
#. Rename it to python <python-version>. E.g. ``python27-x64``

You can now execute your application by right clicking on the `.py` file ->
"Send To" -> "python <python-version>".

Uninstalling Kivy
^^^^^^^^^^^^^^^^^^

To uninstall Kivy, remove the installed packages with pip. E.g. if you isnatlled kivy following the instructions above, do::

     python -m pip uninstall kivy_deps.sdl2 kivy_deps.glew kivy_deps.gstreamer
     python -m pip uninstall kivy
