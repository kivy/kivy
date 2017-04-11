.. _installation_windows:

Installation on Windows
=======================

Beginning with 1.9.1 we provide binary
`wheels <https://wheel.readthedocs.org/en/latest/>`_
for Kivy and all its dependencies to be used with an existing Python
installation. See :ref:`install-win-dist`.

We also provide nightly wheels generated using Kivy
`master <https://github.com/kivy/kivy>`_. See :ref:`install-nightly-win-dist`.
See also :ref:`upgrade-win-dist`. If installing kivy to an **alternate
location** and not to site-packages, please see :ref:`alternate-win`.

.. note::

    For Python < 3.5 we use the MinGW compiler. However, for Python 3.5 on
    Windows we currently only support the microsoft MSVC compiler
    because of the following MinGW
    `issue <http://bugs.python.org/issue4709>`_. Generally this should make
    no difference when using precompiled wheels.

.. warning::

    Support for Python 3.5 and higher isn't available with the current
    stable version (``1.9.1``). Compile the master branch or use the
    nightly wheels.

To use Kivy you need `Python <https://www.python.org/downloads/windows/>`_.
Multiple versions of Python can be installed side by side, but Kivy needs to
be installed for each Python version that you want to use Kivy.

.. _install-win-dist:

Installation
------------

Now that python is installed, open the :ref:`windows-run-app` and make sure
python is available by typing ``python --version``. Then, do the following to
install.

#. Ensure you have the latest pip and wheel::

     python -m pip install --upgrade pip wheel setuptools

#. Install the dependencies (skip gstreamer (~120MB) if not needed, see
   :ref:`kivy-dependencies`)::

     python -m pip install docutils pygments pypiwin32 kivy.deps.sdl2 kivy.deps.glew
     python -m pip install kivy.deps.gstreamer

   For Python 3.5 only we additionally offer angle which can be used instead of glew
   and can be installed with::

    python -m pip install kivy.deps.angle

#. Install kivy::

     python -m pip install kivy

That's it. You should now be able to ``import kivy`` in python or run a basic
example::

    python share\kivy-examples\demo\showcase\main.py

.. note::

    If you encounter any **permission denied** errors, try opening the
    `Command prompt as administrator
    <https://technet.microsoft.com/en-us/library/cc947813%28v=ws.10%29.aspx>`_
    and trying again.

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

.. |cp27_win32| replace:: Python 2.7, 32bit
.. _cp27_win32: https://kivy.org/downloads/appveyor/kivy/Kivy-1.9.2.dev0-cp27-cp27m-win32.whl
.. |cp34_win32| replace:: Python 3.4, 32bit
.. _cp34_win32: https://kivy.org/downloads/appveyor/kivy/Kivy-1.9.2.dev0-cp34-cp34m-win32.whl
.. |cp27_amd64| replace:: Python 2.7, 64bit
.. _cp27_amd64: https://kivy.org/downloads/appveyor/kivy/Kivy-1.9.2.dev0-cp27-cp27m-win_amd64.whl
.. |cp34_amd64| replace:: Python 3.4, 64bit
.. _cp34_amd64: https://kivy.org/downloads/appveyor/kivy/Kivy-1.9.2.dev0-cp34-cp34m-win_amd64.whl
.. |cp35_win32| replace:: Python 3.5, 32bit
.. _cp35_win32: https://kivy.org/downloads/appveyor/kivy/Kivy-1.9.2.dev0-cp35-cp35m-win32.whl
.. |cp35_amd64| replace:: Python 3.5, 64bit
.. _cp35_amd64: https://kivy.org/downloads/appveyor/kivy/Kivy-1.9.2.dev0-cp35-cp35m-win_amd64.whl
.. |cp36_win32| replace:: Python 3.6, 32bit
.. _cp36_win32: https://kivy.org/downloads/appveyor/kivy/Kivy-1.9.2.dev0-cp36-cp36m-win32.whl
.. |cp36_amd64| replace:: Python 3.6, 64bit
.. _cp36_amd64: https://kivy.org/downloads/appveyor/kivy/Kivy-1.9.2.dev0-cp36-cp36m-win_amd64.whl
.. |examples_whl| replace:: Kivy examples
.. _examples_whl: https://kivy.org/downloads/appveyor/kivy/Kivy_examples-1.9.2.dev0-py2.py3-none-any.whl

.. warning::

    Using the latest development version can be risky and you might encounter
    issues during development. If you encounter any bugs, please report them.

Snapshot wheels of current Kivy master are created on every commit to the
`master` branch of kivy repository. They can be found
`here <https://kivy.org/downloads/appveyor/kivy>`_. To use them, instead of
doing ``python -m pip install kivy`` we'll install one of these wheels as
follows.

+ |cp27_win32|_
+ |cp34_win32|_
+ |cp35_win32|_
+ |cp36_win32|_

- |cp27_amd64|_
- |cp34_amd64|_
- |cp35_amd64|_
- |cp36_amd64|_

#. Perform steps 1 and 2 of the above Installation section.
#. Download the appropriate wheel for your system.
#. Install it with ``python -m pip install wheel-name`` where ``wheel-name``
   is the name of the renamed file and add deps to the `PATH`.

Kivy examples are separated from the core because of their size. The examples
can be installed separately on both Python 2 and 3 with this single wheel:

- |examples_whl|_

.. _kivy-dependencies:

Kivy's dependencies
-------------------

We offer wheels for Kivy and its dependencies separately so only desired
dependencies need be installed. The dependencies are offered as
optional sub-packages of kivy.deps, e.g. ``kivy.deps.sdl2``.

Currently on Windows, we provide the following dependency wheels:

* `gstreamer <https://gstreamer.freedesktop.org>`_ for audio and video
* `glew <http://glew.sourceforge.net/>`_ and/or
  `angle (3.5 only) <https://github.com/Microsoft/angle>`_ for OpenGL
* `sdl2 <https://libsdl.org>`_ for control and/or OpenGL.

One can select which of these to use for OpenGL use using the
`KIVY_GL_BACKEND` envrionment variable by setting it to `glew`
(the default), `angle`, or `sdl2`. `angle` is currently
in an experimental phase as a substitute for `glew` on Python
3.5 only.

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
and then us the ``cd`` command to change the current directory to where python
is installed, e.g. ``cd C:\Python27``. Alternatively if you only have one
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
   gstreamer and gstreamer_dev if you aren't going to use video/audio)::

     python -m pip install cython docutils pygments pypiwin32 kivy.deps.sdl2 \
     kivy.deps.glew kivy.deps.gstreamer kivy.deps.glew_dev kivy.deps.sdl2_dev \
     kivy.deps.gstreamer_dev

#. If you downloaded or cloned kivy to an alternate location and don't want to
   install it to site-packages read the next section.

#. Finally compile and install kivy with ``pip install filename``, where
   ``filename`` can be a url such as
   ``https://github.com/kivy/kivy/archive/master.zip`` for kivy master, or the
   full path to a local copy of a kivy.

Compile Kivy
^^^^^^^^^^^^

#. Start installation of Kivy cloned from GitHub::

    python -m pip install kivy\.

If the compilation succeeds without any error, Kivy should be good to go. You
can test it with running a basic example::

    python share\kivy-examples\demo\showcase\main.py

.. _alternate-win:

Installing Kivy to an alternate location
----------------------------------------

In development Kivy is often installed to an alternate location and then
installed with::

    python -m pip install -e location

That allows Kivy to remain in its original location while being available
to python, which is useful for tracking changes you make in Kivy for example
directly with Git.

To achieve using Kivy in an alternate location extra tweaking is required.
Due to this `issue <https://github.com/pypa/pip/issues/2677>`_ ``wheel`` and
``pip`` install the dependency wheels to ``python\Lib\site-packages\kivy``. So
they need to be moved to your actual kivy installation from site-packages.

After installing the kivy dependencies and downloading or cloning kivy to your
favorite location, do the following:

#. Move the contents of ``python\Lib\site-packages\kivy\deps`` to
   ``your-path\kivy\deps`` where ``your-path`` is the path where your kivy is
   located.
#. Remove the ``python\Lib\site-packages\kivy`` directory altogether.
#. From ``python\Lib\site-packages`` move **all** ``kivy.deps.*.dist-info``
   directories to ``your-path`` right next to ``kivy``.

Now you can safely compile kivy in its current location with one of these
commands::

> make
> mingw32-make
> python -m pip install -e .
> python setup.py build_ext --inplace

**If kivy fails to be imported,** you probably didn't delete all the
``*.dist-info`` folders and and the kivy or ``kivy.deps*`` folders from
site-packages.

Making Python available anywhere
--------------------------------

There are two methods for launching python on your ``*.py`` files.

Double-click method
~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~

You can launch a .py file with our Python using the Send-to menu:

#. Browse to the ``python.exe`` file you want to use. Right click on it and
   copy it.

#. Open Windows explorer (File explorer in Windows 8), and to go the address
   'shell:sendto'. You should get the special Windows directory `SendTo`

#. Paste the previously copied ``python.exe`` file **as a shortcut**.
#. Rename it to python <python-version>. E.g. ``python27-x64``

You can now execute your application by right clicking on the `.py` file ->
"Send To" -> "python <python-version>".

.. _upgrade-win-dist:

Upgrading from a previous Kivy dist
-----------------------------------

To install the new wheels to a previous Kivy distribution all the files and
folders, except for the python folder should be deleted from the distribution.
This python folder will then be treated as a normal system installed python and
all the steps described in :ref:`Installation` can then be continued.
