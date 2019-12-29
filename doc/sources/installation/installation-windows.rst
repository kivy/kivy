.. _installation_windows:

Installation on Windows
=======================

.. warning::

    These instructions apply only to install Kivy 2.0+.
    For previous versions, please select the appropriate
    documentation on the top-left.

Using Conda
-----------

If you use Anaconda, you can simply install Kivy using::

   conda install kivy -c conda-forge

.. _install-win-dist:

Native Windows Python
---------------------

For a more detailed introduction, see the next section. Start a new :ref:`windows-run-app`
terminal that has Python available.

#. Ensure you have the latest pip, wheel, and virtualenv::

     python -m pip install --upgrade pip wheel setuptools virtualenv

   Optionally create a new `virtual environment <https://virtualenv.pypa.io/en/latest/>`_
   for your Kivy project. **Strongly recommended**:

   #. Create the virtual environment named `kivy_venv` in your current directory::

        python -m virtualenv kivy_venv

   #. Activate the virtual environment. You'll have to do this step from the current directory
      **every time** you start a new terminal. On windows CMD do::

        kivy_venv\Scripts\activate

      If you're in a bash terminal, instead do::

        source kivy_venv/Scripts/activate

   Your terminal should now preface the path with something like `(kivy_venv)`, indicating that
   the `kivy_venv` environment is active. If it doesn't say that, the virtual environment is not active.

#. Install kivy and kivy_examples (optional)::

     python -m pip install kivy[base] kivy_examples

   To install kivy with **audio/video** support, replace ``base`` with ``full``. See :ref:`kivy-dependencies`.

   To install a **pre-release** of kivy, add ``--pre`` to the pip command. E.g.
   ``python -m pip install --pre kivy[base] kivy_examples``.

   :ref:`nightly-win-wheels` can be installed from the Kivy server with::

     pip install kivy kivy_examples --pre --extra-index-url https://kivy.org/downloads/simple/

That's it. You should now be able to ``import kivy`` in python or run a basic
example if you installed the kivy examples::

    python kivy_venv\share\kivy-examples\demo\showcase\main.py

The exact path to the kivy examples directory is in ``kivy.kivy_examples_dir``.

Introduction
------------

Kivy is written in
`Python <https://en.wikipedia.org/wiki/Python_%28programming_language%29>`_
and as such, to use Kivy, you need an existing
installation of `Python <https://www.python.org/downloads/windows/>`_.
Multiple versions of Python can be installed side by side, but Kivy needs to
be installed in each Python version that you want to use Kivy in.

Once Python is installed, open the :ref:`windows-run-app` and make sure
python is available by typing ``python --version``.

What are wheels, pip and wheel
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In Python, packages such as Kivy can be installed with the python package
manager, `pip <https://pip.pypa.io/en/stable/>`_. Some packages such as Kivy
require additional steps, such as compilation, when installing using the Kivy
source code with pip. Wheels (with a ``.whl`` extension) are pre-built
distributions of a package that has already been compiled and do not require
additional steps to install.

When hosted on `pypi <https://pypi.python.org/pypi>`_ one installs a wheel
using ``pip``, e.g. ``python -m pip install kivy``, which automatically finds it on PyPI.
When downloading and installing a wheel file directly,
``python -m pip install wheel_file_name`` is used, such as::

    python -m pip install C:\Kivy-1.9.1.dev-cp27-none-win_amd64.whl

.. _windows-run-app:

Command line
^^^^^^^^^^^^

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
python version installed, permanently add the python directory to the path
by selecting the option during Python installation, or manually for
`cmd <http://www.computerhope.com/issues/ch000549.htm>`_ or
`bash <http://stackoverflow.com/q/14637979>`_.

.. _nightly-win-wheels:

Nightly wheels
^^^^^^^^^^^^^^

Snapshot wheels of current Kivy master are created daily on the `master` branch
of kivy repository. As opposed to the last stable release on PyPI, nightly wheels
contain all the latest changes to Kivy, including any experimental fixes.
For installation instructions, see :ref:`install-win-dist`. See also :ref:`dev-install-win`.

.. warning::

    Using the latest development version can be risky and you might encounter
    issues during development. If you encounter any bugs, please report them.

.. _kivy-dependencies:

Kivy's dependencies
-------------------

We offer wheels for Kivy and its dependencies, separately, so only desired
dependencies need be installed. The dependencies are offered as
optional sub-packages of kivy_deps, e.g. ``kivy_deps.sdl2``.

.. note::

    In Kivy 1.11.0 we transitioned the kivy Windows dependencies from the
    `kivy.deps.xxx` namespace stored under `kivy/deps/xxx` to the
    `kivy_deps.xxx` namespace stored under `kivy_deps/xxx`.
    See `here <https://github.com/kivy/kivy/wiki/Moving-kivy.garden.xxx-to-kivy_garden.xxx-and-kivy.deps.xxx-to-kivy_deps.xxx#kivy-deps>`_
    for more details.

On Windows, we provide the following dependency wheels:

* `gstreamer <https://gstreamer.freedesktop.org>`_ for audio and video.

  ``gstreamer`` is an optional dependency which is only needed for audio/video support.
  ``ffpyplayer`` is an alternate dependency for audio or video. It can be installed with
  ``pip install ffpyplayer``.
* `glew <http://glew.sourceforge.net/>`_ and/or
  `angle <https://github.com/Microsoft/angle>`_ for OpenGL.

  One can select which of these to use for OpenGL using the
  ``KIVY_GL_BACKEND`` environment variable by setting it to ``glew``
  (the default), ``angle``, or ``sdl2``. ``angle`` is a substitute for ``glew``.
* `sdl2 <https://libsdl.org>`_ for control and/or OpenGL.

.. _dev-install-win:

Use development Kivy
--------------------

.. warning::

    Using the latest development version can be risky and you might encounter
    issues during development. If you encounter any bugs, please report them.

Consider using a pre-compiled :ref:`nightly-win-wheels`.
However, to compile and install kivy using the kivy
`source code <https://github.com/kivy/kivy>`_ there are some additional steps:

#. Both the ``python`` and the ``python\Scripts`` directories **must** be on
   the path. They must be on the path every time you recompile kivy.

#. Ensure you have the latest pip and wheel with::

     python -m pip install --upgrade pip wheel setuptools

#. Get the compiler.
  `Visual Studio 20xx <https://www.visualstudio.com/downloads/>`_ is
   required, which is available for free. Just download and install it and
   you'll be good to go.

   Visual Studio is very big so you can also use the smaller,
   `Visual C Build Tools instead
   <https://github.com/kivy/kivy/wiki/Using-Visual-C---Build-Tools-instead-of-Visual-Studio-on-Windows>`_.

#. Install the other dependencies as well as their dev versions (you can skip
   gstreamer and gstreamer_dev if you aren't going to use video/audio). we don't pin
   the versions of the dependencies like for the stable kivy because we want the
   latest:

   .. parsed-literal::

     python -m pip install |cython_install| docutils pygments pypiwin32 kivy_deps.sdl2 \
     kivy_deps.glew kivy_deps.angle kivy_deps.gstreamer kivy_deps.glew_dev kivy_deps.sdl2_dev \
     kivy_deps.gstreamer_dev

#. Skip to :ref:`alternate-win` if you wish to be able to edit kivy after installing it.

   Otherwise, compile and install kivy with ``pip install filename``, where
   ``filename`` can be a url such as
   ``https://github.com/kivy/kivy/archive/master.zip`` for kivy master, or the
   full path to a local copy of a kivy directory or downloaded zip.

.. _alternate-win:

Installing Kivy and editing it in place
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
   to use (e.g. the virtual environment). Select it.

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

To uninstall Kivy, remove the installed packages with pip. E.g. if you installed kivy following the instructions above, do::

     python -m pip uninstall kivy_deps.sdl2 kivy_deps.glew kivy_deps.gstreamer kivy_deps.angle
     python -m pip uninstall kivy

If you installed into a virtual environment, simply delete the virtual environment directory and create a new one.
