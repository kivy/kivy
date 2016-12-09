.. _installation_windows:

Installation on Windows
=======================

Beginning with 1.9.1 we provide binary `wheels <https://wheel.readthedocs.org/en/latest/>`_
for Kivy and all its dependencies to be used with an existing Python installation. See
:ref:`install-win-dist`.

We also provide nightly wheels generated using Kivy `master <https://github.com/kivy/kivy>`_.
See :ref:`install-nightly-win-dist`. See also :ref:`upgrade-win-dist`. If installing kivy
to an **alternate location** and not to site-packages, please see :ref:`alternate-win`.

.. warning::

    Python 3.5 is currently not supported on Windows due to issues with MinGW and
    Python 3.5. Support is not expected for some time. See
    `this issue <http://bugs.python.org/issue4709>`_ for details. If required,
    3.5 MSVC builds should be possible, but have not been attempted, please enquire
    or let us know if you've compiled with MSVC.

To use Kivy you need `Python <https://www.python.org/downloads/windows/>`_.
Multiple versions of Python can be installed side by side, but Kivy needs to
be installed for each Python version that you want to use Kivy.

.. _install-win-dist:

.. |nowinfound| replace:: issues
.. _nowinfound: https://github.com/kivy/kivy/issues/3957

Installation
------------

Now that python is installed, open the :ref:`windows-run-app` and make sure python
is available by typing ``python --version``. Then, do the following to install.

#. Ensure you have the latest pip and wheel::

     python -m pip install --upgrade pip wheel setuptools

#. Install the dependencies (skip gstreamer (~90MB) if not needed, see
   :ref:`kivy-dependencies`)::

     python -m pip install docutils pygments pypiwin32 kivy.deps.sdl2 kivy.deps.glew
     python -m pip install kivy.deps.gstreamer --extra-index-url https://kivy.org/downloads/packages/simple/

#. Install kivy::

     python -m pip install kivy

#. Add deps to PATH to avoid |nowinfound|_ (run in folder with `python.exe`)::

     set PATH=%PATH%;%cd%\share\sdl2\bin;%cd%\share\glew\bin
     
That's it. You should now be able to ``import kivy`` in python.

.. note::

    If you encounter any **permission denied** errors, try opening the
    `Command prompt as administrator
    <https://technet.microsoft.com/en-us/library/cc947813%28v=ws.10%29.aspx>`_
    and trying again.

.. _install-nightly-win-dist:

Nightly wheel installation
--------------------------

.. warning::

    Using the latest development version can be risky and you might encounter
    issues during development. If you encounter any bugs, please report them.

Snapshot wheels of current Kivy master are created every night. They can be found
`here <https://drive.google.com/folderview?id=0B1_HB9J8mZepOV81UHpDbmg5SWM&usp=sharing#list>`_.
To use them, instead of doing ``python -m pip install kivy`` we'll install one of
these wheels as follows.

.. |cp27_win32| replace:: Python 2.7, 32bit
.. _cp27_win32: https://kivy.org/downloads/appveyor/kivy/Kivy-1.9.2.dev0-cp27-cp27m-win32.whl
.. |cp34_win32| replace:: Python 3.4, 32bit
.. _cp34_win32: https://kivy.org/downloads/appveyor/kivy/Kivy-1.9.2.dev0-cp34-cp34m-win32.whl
.. |cp27_amd64| replace:: Python 2.7, 64bit
.. _cp27_amd64: https://kivy.org/downloads/appveyor/kivy/Kivy-1.9.2.dev0-cp27-cp27m-win_amd64.whl
.. |cp34_amd64| replace:: Python 3.4, 64bit
.. _cp34_amd64: https://kivy.org/downloads/appveyor/kivy/Kivy-1.9.2.dev0-cp34-cp34m-win_amd64.whl

- |cp27_win32|_
- |cp34_win32|_
- |cp27_amd64|_
- |cp34_amd64|_

#. Perform steps 1 and 2 of the above Installation section.
#. Download the appropriate wheel for your system.
#. Rename the wheel to remove the version tag, e.g.
   ``Kivy-1.9.1.dev0_30112015_gitc68b630-cp27-none-win32.whl``
   should be renamed to ``Kivy-1.9.1.dev0-cp27-none-win32.whl``.
#. Install it with ``python -m pip install wheel-name`` where ``wheel-name``
   is the name of the renamed file.

.. _kivy-dependencies:

Kivy's dependencies
-------------------

We offer wheels for Kivy and its dependencies separately so only desired
dependencies need be installed. The dependencies are offered as
`namespace <https://www.python.org/dev/peps/pep-0420/>`_
packages of Kivy.deps, e.g. ``kivy.deps.sdl2``.

Currently on Windows, we provide the following dependency
wheels: ``gstreamer`` for audio and video and `glew` and ``sdl2`` for graphics
and control. ``gstreamer`` is an optional dependency which only needs to be
installed if video display or audio is desired.

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
`source code <https://github.com/kivy/kivy/archive/master.zip>`_  or to use kivy
with git rather than a wheel there are some additional steps:

#. Both the ``python`` and the ``Python\Scripts`` directories **must** be on the path
   They must be on the path every time you recompile kivy.
#. Ensure you have the latest pip and wheel with::

     python -m pip install --upgrade pip wheel setuptools

#. Create the ``python\Lib\distutils\distutils.cfg`` file and add the two lines::

     [build]
     compiler = mingw32

#. Install MinGW with::

     python -m pip install -i https://pypi.anaconda.org/carlkl/simple mingwpy

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
     kivy.deps.gstreamer_dev --extra-index-url https://kivy.org/downloads/packages/simple/

#. If you downloaded or cloned kivy to an alternate location and don't want to
   install it to site-packages read the next section.
#. Finally compile and install kivy with ``pip install filename``, where ``filename``
   can be a url such as ``https://github.com/kivy/kivy/archive/master.zip`` for
   kivy master, or the full path to a local copy of a kivy zip.

.. _alternate-win:

Installing Kivy to an alternate location
----------------------------------------

In development Kivy is often installed to an alternate location and then
installed with ``python -m pip install -e location``, which allows it to remain
in its original location while being available to python.
In that case extra tweaking is required. Due to a
`issue <https://github.com/pypa/pip/issues/2677>`_ ``wheel`` and
``pip`` install the dependency wheels to ``python\Lib\site-packages\kivy``. So they
need to be moved to your actual kivy installation from site-packages.

After installing the kivy dependencies and downloading or cloning kivy to your
favorite location, do the following:

#. Move the contents of ``python\Lib\site-packages\kivy\deps`` to
   ``your-path\kivy\deps`` where ``your-path`` is the path where your kivy is
   located.
#. Remove the ``python\Lib\site-packages\kivy`` directory altogether.
#. From ``python\Lib\site-packages`` move **all** the ``kivy.deps.*.pth``
   files and **all** ``kivy.deps.*.dist-info` directories to ``your-path``
   right next to ``kivy``.

Now you can safely compile kivy in its current location with ``make`` or
``python -m pip install -e location`` or just ``python setup.py build_ext --inplace``.

**If kivy fails to be imported,** you probably didn't delete all the *.pth files
and and the kivy or kivy.deps* folders from site-packages.

Making Python available anywhere
--------------------------------

There are two methods for launching python on your ``*.py`` files.

Double-click method
~~~~~~~~~~~~~~~~~~~

If you only have one Python installed, you can associate all ``*.py`` files with
your python, if it isn't already, and then run it by double clicking. Or you can
only do it once if you want to be able to choose each time:

#. Right click on the Python file (.py file extension) of the application you want to launch
#. From the context menu that appears, select *Open With*
#. Browse your hard disk drive and find the file ``python.exe`` that you want to use. Select it.
#. Select "Always open the file with..." if you don't want to repeat this procedure every time you
   double click a .py file.
#. You are done. Open the file.

Send-to method
~~~~~~~~~~~~~~

You can launch a .py file with our Python using the Send-to menu:

#. Browse to the ``python.exe`` file you want to use. Right click on it and
   copy it.
#. Open Windows explorer (File explorer in Windows 8), and to go the address 'shell:sendto'.
   You should get the special Windows directory `SendTo`
#. Paste the previously copied ``python.exe`` file **as a shortcut**.
#. Rename it to python <python-version>. E.g. ``python27-x64``

You can now execute your application by right clicking on the .py file ->
"Send To" -> "python <python-version>".

.. _upgrade-win-dist:

Upgrading from a previous Kivy dist
-----------------------------------

To install the new wheels to a previous Kivy distribution all the files
and folders, except for the python folder should be deleted from the distribution.
This python folder will then be treated as a normal system installed python and all
the steps described in :ref:`Installation` can then be continued.
