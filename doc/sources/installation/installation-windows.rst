.. _installation_windows:

Installation on Windows
=======================

.. warning::

    These instructions apply only to the installation of Kivy 2.0+.
    For previous versions, please select the appropriate
    documentation on the top-left.

Installation using Conda
------------------------

If you use `Anaconda <https://en.wikipedia.org/wiki/Anaconda_(Python_distribution)>`_, you can install Kivy with its package manager `Conda <https://en.wikipedia.org/wiki/Conda_(package_manager)>`_::

   conda install kivy -c conda-forge

.. _install-win-dist:

Installation of the precompiled binaries
----------------------------------------

Here we explain how to install Kivy using precompiled wheels. This is the simplest way to install it.

*If you have problems understanding this section, please read the next section first. There we explain Python package installation, wheels, and how to use the command line.*

Start a new :ref:`console window <windows-run-app>` that has Python available.

#. Ensure you have the latest `pip <https://pypi.org/project/pip/>`_, `wheel <https://pypi.org/project/wheel/>`_, `setuptools <https://pypi.org/project/setuptools/>`_, and `virtualenv <https://pypi.org/project/virtualenv/>`_::

     python -m pip install --upgrade pip wheel setuptools virtualenv

   Optional **(but strongly recommended)**: Create a new `virtual environment <https://virtualenv.pypa.io/en/latest/>`_
   for your Kivy project. A virtual environment will prevent possible installation conflicts with other Python versions and with other packages.
   
   #. Create the virtual environment named `kivy_venv` in your current directory::

        python -m virtualenv kivy_venv

   #. Activate the virtual environment. You will have to do this step from the current directory
      **every time** you start a new terminal. In the command line do::

        kivy_venv\Scripts\activate

      If you are in a bash terminal, instead do::

        source kivy_venv/Scripts/activate

   Your terminal should now preface the path with something like ``(kivy_venv)``, indicating that
   the `kivy_venv` environment is active. If it doesn't say that, the virtual environment is not active.

#. Install ``kivy`` and optionally ``kivy_examples``::

     python -m pip install kivy[base] kivy_examples

   To install Kivy with **audio/video** support, replace ``base`` with ``full``. See :ref:`kivy-dependencies`.

   To install a **pre-release** of Kivy, add ``--pre`` to the pip command. E.g.
   ``python -m pip install --pre kivy[base] kivy_examples``.

   :ref:`Nightly wheels <nightly-win-wheels>` can be installed from the Kivy server with::

     pip install kivy[base] kivy_examples --pre --extra-index-url https://kivy.org/downloads/simple/

That's it. You should now be able to ``import kivy`` in Python or, if you installed the Kivy examples, to run a basic
example::

    python kivy_venv\share\kivy-examples\demo\showcase\main.py

The exact path to the Kivy examples directory is ``kivy.kivy_examples_dir``.

Python package installation
---------------------------

Here we explain how to install Python packages, how to use the command line and what wheels are.

Installing Python
^^^^^^^^^^^^^^^^^

Kivy is written in
`Python <https://en.wikipedia.org/wiki/Python_%28programming_language%29>`_
and as such, to use Kivy, you need an existing
installation of `Python <https://www.python.org/downloads/windows/>`_.
Multiple versions of Python can be installed side by side, but Kivy needs to
be installed as package under each Python version that you want to use Kivy in.

Once Python is installed, open the :ref:`console <windows-run-app>` and make sure
Python is available by typing ``python --version``.

.. _windows-run-app:

How to use the command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To execute any of the ``pip`` or ``wheel`` commands given here, you need a *command line* (here also called *console*, *terminal*, `shell <https://en.wikipedia.org/wiki/Unix_shell>`_ or `bash <https://en.wikipedia.org/wiki/Bash_(Unix_shell)>`_, where the last two refer to Linux style command lines) and Python must be on the `PATH <https://en.wikipedia.org/wiki/PATH_(variable)>`_.

The default command line on Windows is the
`command prompt <http://www.computerhope.com/issues/chusedos.htm>`_, short *cmd*. The
quickest way to open it is to press `Win+R` on your keyboard.
In the window that opens, type ``cmd`` and then press enter.

Alternative Linux style command lines that we recommend are
`Git for Windows <https://git-for-windows.github.io/>`_ which offers a bash, `as well <http://rogerdudler.github.io/git-guide/>`_ as
`git <https://try.github.io>`_. Further there is `Mysys <http://www.mingw.org/wiki/MSYS>`_.

Note, the default Windows command line can still be used, even if a bash is installed.

To temporarily add your Python installation to the PATH, simply open your command line and then use the ``cd`` command to change the current directory to where python is installed, e.g. ``cd C:\Python37``.

If you have installed Python using the default options, then the path to Python will already be permanently on your PATH variable. There is an option in the installer which lets you do that, and it is enabled by default.

If however Python is not on your PATH, follow the these instructions:

* Instructions for `the windows command line <http://www.computerhope.com/issues/ch000549.htm>`_
* Instructions for `bash command lines <http://stackoverflow.com/q/14637979>`_

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

.. _nightly-win-wheels:

What are nightly wheels
^^^^^^^^^^^^^^^^^^^^^^^

Every day we create a snapshot wheel of the current development version of Kivy ('nightly wheel'). You can find the development version in the master branch of the `Kivy Github repository <https://github.com/kivy/kivy>`_.

As opposed to the last *stable* release (which we discussed in the previous section), nightly wheels contain all the latest changes to Kivy, including experimental fixes.
For installation instructions, see :ref:`install-win-dist`. See also :ref:`dev-install-win`.

.. warning::

    Using the latest development version can be risky and you might encounter
    issues during development. If you encounter any bugs, please report them.

.. _kivy-dependencies:

Installing Kivy's dependencies
------------------------------

We offer the wheels for Kivy and the wheels for its dependencies separately, so that you can install only the dependencies you want. The dependencies are offered as sub-packages, starting with ``kivy_deps``, for example ``kivy_deps.sdl2``.

.. note::

    In Kivy 1.11.0 we replaced the dot in ``kivy.deps`` with an underscore. So, instead of ``kivy.deps.xxx``, stored under ``kivy/deps/xxx`` it is now ``kivy_deps.xxx``, stored under ``kivy_deps/xxx``.
    See `here <https://github.com/kivy/kivy/wiki/Moving-kivy.garden.xxx-to-kivy_garden.xxx-and-kivy.deps.xxx-to-kivy_deps.xxx#kivy-deps>`_
    for more details.

.. note::
    depending on the keyword you used in the installation of Kivy itself you may already have some of the below dependencies installed. For example the keyword *full* (``python -m pip install kivy[full]``) installs the dependencies ``sdl2``, ``glew``, ``angle`` and ``gstreamer``.
    
    The following table lists which keyword installs what:
    
    +---------------------+------+------+------+
    |                     | none | base | full |
    +=====================+======+======+======+
    | kivy_deps.sdl2      | n    | y    | y    |
    +---------------------+------+------+------+
    | kivy_deps.glew      | n    | y    | y    |
    +---------------------+------+------+------+
    | kivy_deps.angle     | n    | y    | y    |
    +---------------------+------+------+------+
    | kivy_deps.gstreamer | n    | n    | y    |
    +---------------------+------+------+------+

So, the following are the dependency wheels which we provide for Windows:

* `gstreamer <https://gstreamer.freedesktop.org>`_ (optional)

  `gstreamer` is an optional dependency which is only needed for audio/video support.
  It can be installed with  ``python -m pip install kivy_deps.gstreamer``.

* `ffpyplayer <https://pypi.org/project/ffpyplayer/>`_ (optional)

  `ffpyplayer` is an alternative optional dependency for audio or video.
  It can be installed with ``python -m pip install ffpyplayer``.

* `glew <http://glew.sourceforge.net/>`_ and/or
  `angle <https://github.com/Microsoft/angle>`_
  
  These are for `OpenGL <https://en.wikipedia.org/wiki/OpenGL>`_. They can be installed with ``python -m pip install kivy_deps.glew`` and/or ``python -m pip install kivy_deps.angle``. You can install both, that is no problem.

  One can select which of these to use for OpenGL using the
  ``KIVY_GL_BACKEND`` environment variable: By setting it to ``glew``
  (the default), ``angle``, or ``sdl2``. Here, ``angle`` is a substitute for ``glew``.

* `sdl2 <https://libsdl.org>`_

  For control and/or OpenGL. Install it with ``python -m pip install kivy_deps.sdl2``.

.. _dev-install-win:

Installation of the development version from source
---------------------------------------------------

.. warning::

    Using the latest development version can be risky and you might encounter
    issues during development. If you encounter any bugs, please report them.

It may be simpler to install a pre-compiled :ref:`nightly wheel <nightly-win-wheels>`.
However, to compile and install from `the kivy source code <https://github.com/kivy/kivy>`_ there are some additional steps:

#. Both the ``python`` and the ``python\Scripts`` directories **must** be on the PATH.
   They must be on the PATH every time you recompile kivy.
   Once again, if you have installed Python using the default options, then this will be the case.

#. Ensure you have the latest `pip <https://pypi.org/project/pip/>`_, `wheel <https://pypi.org/project/wheel/>`_ and `setuptools <https://pypi.org/project/setuptools/>`_ by doing::

     python -m pip install --upgrade pip wheel setuptools

#. Get the compiler.
   The *Visual Studio Build Tools* are required, they are available for free.
  
   You can either download and install the complete *Visual Studio IDE*, which contains the build tools, or alternatively just the build tools.
  
   The IDE can be downloaded from `here <https://www.visualstudio.com/downloads/>`_.

   The IDE is very big, so you can also download just the smaller build tools, which are used from the command line.
   The current download (2019) can be found on `this page <https://visualstudio.microsoft.com/downloads/?q=build+tools>`_ under "Tools for Visual Studio 2019". More infos about this topic can be found `in the Kivy wiki <https://github.com/kivy/kivy/wiki/Using-Visual-C---Build-Tools-instead-of-Visual-Studio-on-Windows>`_.

#. Install the other dependencies as well as their development versions (you can skip
   ``gstreamer`` and ``gstreamer_dev`` if you aren't going to use video/audio).

   .. parsed-literal::

     python -m pip install |cython_install| docutils pygments pypiwin32 kivy_deps.sdl2 \
     kivy_deps.glew kivy_deps.angle kivy_deps.gstreamer kivy_deps.glew_dev kivy_deps.sdl2_dev \
     kivy_deps.gstreamer_dev
   
   Notice, we don't pin the versions of the dependencies like we do for the stable Kivy, because we want the
   latest.

#. Skip to :ref:`alternate-win` if you wish to be able to edit Kivy after installing it.

   Otherwise, compile and install Kivy with ``pip install <filename>``, where
   ``<filename>`` can be a url such as
   ``https://github.com/kivy/kivy/archive/master.zip`` for Kivy master, or the
   full path to a local copy of a Kivy directory or downloaded zip.

.. _alternate-win:

Installing Kivy and editing it in place
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For development purposes, Kivy is often cloned or downloaded to a location and then
installed with::

    python -m pip install -e kivy_path

Now you can safely compile Kivy in its current location with one of these
commands::

    make
    python setup.py build_ext --inplace

This will fully install Kivy and make it and available from Python. To recompile, remember to rerun the above command
whenever any of the Cython files are changed (e.g. if you pulled from GitHub).

Aside: Making Python available anywhere
---------------------------------------

There are two methods for launching Python on your ``*.py`` files.

Double-click method
^^^^^^^^^^^^^^^^^^^

If you only have one Python installed, and if you installed it using the default options, then ``*.py`` files are already
associated with your Python. You can run them by double clicking them in the file manager, or by just executing their name in a console window (without having to prepend ``python``).

Alternatively, if they are not assigned, you can do it the following way:

#. Right click on the Python file (.py file extension) in the file manager.
#. From the context menu that appears, select *Open With*
#. Browse your hard disk drive and find the ``python.exe`` file that you want
   to use (e.g. in the the virtual environment). Select it.
#. Select "Always open the file with..." if you don't want to repeat this
   procedure every time you double click a .py file.
#. You are done. Open the file.

Send-to method
^^^^^^^^^^^^^^

You can launch a .py file with Python using the *Send to* menu:

#. Browse to the ``python.exe`` you want to use. Right click on it and
   copy it.
#. Open Windows Explorer (the file explorer in Windows 8), and to go the address
   'shell:sendto'. You should get the special Windows directory `SendTo`
#. Paste the previously copied ``python.exe`` file **as a shortcut**.
#. Rename it to python <python-version>. E.g. ``python27-x64``

You can now execute your application by right clicking on the `.py` file ->
"Send To" -> "python <python-version>".

Uninstalling Kivy
^^^^^^^^^^^^^^^^^

To uninstall Kivy, remove the installed packages with pip. E.g. if you installed kivy following the instructions above, do::

     python -m pip uninstall kivy_deps.sdl2 kivy_deps.glew kivy_deps.gstreamer kivy_deps.angle
     python -m pip uninstall kivy

If you installed into a virtual environment, simply delete the virtual environment directory and create a new one.
