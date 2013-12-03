.. _installation_windows:

Installation on Windows
=======================

For Windows, we provide what we call a 'portable package'. You don't have
to install anything "system" wide. Just unzip & run:

#. Download the latest version from http://kivy.org/#download

    .. image:: images/win-step1.png
        :scale: 75%

#. Unzip the package

    .. image:: images/win-step3.png
        :scale: 75%

#. In the folder where you unzipped the package, you have a script called `kivy.bat`.
   Use this file for launching any kivy application as described below


.. _windows-run-app:

Start a Kivy Application
------------------------

Send-to method
~~~~~~~~~~~~~~

You can launch a .py file with our Python using the Send-to menu:

#. Copy the kivy.bat file to the Clipboard

    .. image:: images/win-step4.png
        :scale: 75%

#. Open Windows explorer (File explorer in Windows 8), and to go the address 'shell:sendto'

    .. image:: images/win-step5.png
        :scale: 75%

#. You should get the special Windows directory `SendTo`

    .. image:: images/win-step6.png
        :scale: 75%

#. Paste the previously copied kivy.bat file **as a shortcut**

    .. image:: images/win-step7.png
        :scale: 75%

#. Rename it to Kivy <kivy-version>

    .. image:: images/win-step8.png
        :scale: 75%

You can now execute your application by right clicking on the .py file ->
"Send To" -> "Kivy <version>".

    .. image:: images/win-step9.png
        :scale: 75%

Double-click method
~~~~~~~~~~~~~~~~~~~

There are some simple steps that you need to complete in order to be able
to launch Kivy applications by just double-clicking them:

    #. Right click on the main Python file (.py file extention) of the application you want to launch
    #. From the context menu that appears, select *Open With*
    #. Browse your hard disk drive and find the file ``kivy.bat`` from the portable package. Select it.
    #. Select "Always open the file with..." if you don't want to repeat this procedure every time you
       double click a .py file.
    #. You are done. Open the file.

The next time you double click a .py file, it will be executed with the version
of Python that Kivy ships with.

.. note::
   On Windows we have to ship our own version of Python since it's not
   installed by default on Windows (unlike Mac OS X and Linux). By
   following the steps above, you will set Kivy's version of Python as the
   default for opening .py files for your user.
   Normally this should not be harmful as it's just a normal version of
   Python with the :ref:`necessary third party libraries <winpackagecontents>`
   added to the module search path.
   If you do encounter unexpected problems, please :ref:`contact`.


Start from the Command-line (using bash)
----------------------------------------

If you just want to use or develop with the latest stable Kivy version, this can
be achieved using the console. You will need a minimalist GNU system installed.
We recommend `msysGit <http://code.google.com/p/msysgit/>`_.

When you install msysGit, you must select these options:

    * Don't replace windows shell
    * Checkout as-is, commit as-is (no CLRF replacement!)

You'll have an icon "Git bash" on your desktop. This is the console we want:

    #. Start "Git bash"
    #. ``cd <directory of portable kivy>``
    #. ``source kivyenv.sh <full directory path of portable kivy>`` # (don't use .)

You are now ready to launch Python/Kivy from the command-line! Just do::

    python <filename.py>

Also, all other scripts and binaries are available, such as:

    * cython
    * gcc / make...
    * easy_install
    * gst-inspect-0.10

Start from the Command-line or Double-click (using Python launcher for Windows)
-------------------------------------------------------------------------------

The Python launcher for Windows is available as a separate download
from `pylauncher <https://bitbucket.org/vinay.sajip/pylauncher>`_,
but is most conveniently installed by simply installing Python 3.3 (or later).
Don't worry, this installation is designed to cause minimum disruption, it will run your latest Python 2 by default.

The launcher defines a ``PY`` command which can launch scripts for any version of Python installed on the workstation.
It also connects itself as the default processor for all files with a .py extension.
It scans the Python file to see if the first line starts with the string "#!" and, if it does, uses that string to
select the appropriate version of Python to run. We will define a customized command so that we can tell it to
start the correct version of python for Kivy.

Create a file named ``py.ini`` and place it either in your users ``application data`` directory, or in ``C:\Windows``.
It will contain the path used to start Kivy.  I put my Kivy installation at ``C:\utils\kivy`` so my copy says::

    [commands]
    kivy="c:\utils\kivy\kivy.bat"

(You could also add commands to start other script interpreters, such as jython or IronPython.)

Now add a new first line to your ``main.py`` specifying your Python of choice::

    #!/usr/bin/kivy

You can now launch your Kivy (or any other Python script) either by double-clicking or typing::

    py <filename.py>

Programs without a ``#!`` first line will continue to be run be the default Python version 2 interpreter.
Programs beginning with ``#!/usr/bin/python3`` will launch Python 3.

The ``/usr/bin`` part will be ignored by the Windows launcher, we add it so that Linux users will also be able to
pick a specific Python version. (On my Linux workstation, ``/usr/bin/kivy`` is soft-linked to a virtualenv.)
NOTE: In order to work correctly on Linux, your Python file must be saved with Unix-style (LF-only) line endings.

Full documentation can be found at:
`Python3.3 docs <http://docs.python.org/3.3/using/windows.html#launcher>`_ and
`PEP 397 <http://www.python.org/dev/peps/pep-0397/>`_.

Use development Kivy
--------------------

.. warning::

    Using the latest development version can be risky and you might encounter
    issues during development. If you encounter any bugs, please report them.

If you want to use the latest development version of Kivy, you can follow these steps:

#. Download and install Kivy for Windows as explained above
#. Go into the portable Kivy directory. This contains the `kivy.bat` file and the `Python`, `kivy`, `Mingw` folders etc.
#. Rename the kivy directory to kivy.stable
#. Go to github, and download the `latest development version of Kivy <https://github.com/kivy/kivy/zipball/master>`_
#. Extract the zip into the Kivy portable directory
#. Rename the directory named "kivy-<some hash>" to just "kivy"
#. Launch kivy.bat
#. Go to the Kivy portable directory/kivy
#. Type::

    make force

#. That's all, you have a latest development version!

.. note::

    If you get errors you may need to upgrade Cython:

    1.  Launch kivy.bat
    2. ``cd Python/Scripts``
    3. ``pip install --upgrade cython``

Using an existing Python installation (64/32 bit)
--------------------------------------------------

As an alternative to downloading the kivy distribution zip file, you can
install the kivy requirements into an existing 32 or 64 bit Python installation.
For this example we'll assume you have Python installed in ``C:\dev\python27``:

#.  You need a MinGW installation. You can use the MinGW directory included
    in the kivy distribution or download a fresh MinGW. If you're compiling for 64
    bit you'll need to the download the 64 bit MinGW (see below for how to setup a 64 bit mingw).
#.  If you want to use gstreamer, copy it from the kivy distribution directory.
#.  Get the kivy.bat file from the kivy distribution, or alternatively set the
    path and other environmental variables as in the kivy.bat file in order to have
    a permanent setup. You'll have to execute the following instructions from this environment.

    You'll need to edit the paths first to point to the correct python and MinGW
    locations. If you started with a clean MinGW installation you'll also have to
    add to the path the location of make.exe if you will be doing any kivy development.
#.  Download and install distutils and pip. You can install both using the
    ez_setup.py and get_pip.py files from http://www.pip-installer.org/en/latest/installing.html.
#.  In ``C:\dev\python27\Lib\distutils`` create a empty ``distutils.cfg`` file.
    In the file type::

        [build]
        compiler=mingw32

#.  Download and install cython by typing::

        pip install https://github.com/cython/cython/zipball/master

#.  Download Glew 1.5.7 from http://sourceforge.net/projects/glew/files/glew/.
    Install the Glew files into the following locations::

        glew32.dll -> C:\dev\python27
        glew32.dll -> MinGW\lib
        glew32.lib -> MinGW\lib
        glew32s.lib -> MinGW\lib
        glew.h -> MinGW\include\GL
        glxew.h -> MinGW\include\GL
        wglew.h -> MinGW\include\GL

If you get errors when installing kivy such as ``GL/glew.h: No such file or directory``,
which is likely to happen with the 64 bit mingw, you'll need to copy the GL directory
and its contents into ``python27/include`` and the *.dll and *.lib files from above into
``python27/libs``. If you still get errors then type the following to generate the .a file::

    cd C:\dev\Python27\libs
    rename glew32.lib old_glew32.lib
    rename glew32s.lib old_glew32s.lib
    gendef glew32.dll
    dlltool --dllname glew32.dll --def glew32.def --output-lib libglew32.a

#.  Download and install the precompiled Pygame 1.9.2 binaries from
    http://www.lfd.uci.edu/~gohlke/pythonlibs/#pygame.
#.  Finally, to install the latest kivy, type::

        pip install https://github.com/kivy/kivy/zipball/master

    Alternatively instead of the githup zipball you can point to a specific
    kivy zip file. Also, if you have a development version of kivy and want
    to continue working on it while still installing it you can use the pip
    --editable switch e.g.::

        pip install --editable C:\dev\kivy

    This will put a link in the site-packages directory pointing to your kivy
    source, so any changes in the source will be reflected in the install.
    See here for more details: http://pythonhosted.org/setuptools/setuptools.html#development-mode.

Creating a 64 bit development environment
-----------------------------------------

In order to use kivy in true 64 bit mode you'll first need to set up your environment
to be able to build 64 bit binaries. For this you'll need the 64 bit mingw. We'll
assume that you already installed a 64 bit Python into e.g. ``C:\dev-64\python27``::

#.  Download the mingw 64 binaries (e.g. x86_64-4.8.2-release-win32-sjlj-rt_v3-rev0.7z) from the personal builds
    at http://sourceforge.net/projects/mingw-w64/files/Toolchains%20targetting%20Win64/Personal%20Builds/mingw-builds/4.8.2/threads-win32/sjlj/.
    Now extract the zip file into ``C:\dev-64``. Rename the top level directory, if it's not already, to
    ``mingw64``. You should now have the following directory structure::

        C:\dev-64\mingw64\bin
        C:\dev-64\mingw64\include
        C:\dev-64\mingw64\mingw
        ...

    where ``C:\dev-64\mingw64\bin`` contains e.g. ``gcc.exe`` etc.
#.  You'll need gendef. Download and extract gendef.exe into ``mingw64/bin`` from
    http://sourceforge.net/projects/mingw/files/MinGW/Extension/gendef/gendef-1.0.1346/.
    Keep in mind that this is a 32 bit binary.
#.  At this point it's helpful to use the kivy.bat file and to edit the python paths to point
    to the proper Python27 location and to add the mingw64\bin directory to the system path.
    In any case, for the following to work you either have to provide the full path to gendef and dlltool
    or add mingw64\bin to the system path.
#.  From ``C:\windows\system32`` copy the file ``python27.dll`` into ``C:\dev-64\Python27\libs``.
    Now type the following as described here http://bugs.python.org/issue4709::

        cd C:\dev-64\Python27\libs
        rename python27.lib old_python27.lib
        gendef python27.dll
        dlltool --dllname python27.dll --def python27.def --output-lib libpython27.a

#.  Now we'll patch the ``C:\Python27\include\pyconfig.h`` file. In that file
    search for the text ``#ifdef _WIN64``, which in our copy of this file was at line 141,
    and cut out the following three lines::

        #ifdef _WIN64
        #define MS_WIN64
        #endif

    Search for the text ``#ifdef _MSC_VER``, which in our copy of this file was at line 107.
    Paste in the cut-out lines, ABOVE the ``#ifdef _MSC_VER``.
#.  Finally, we need to patch the cygwin compiler in distutils as described here http://bugs.python.org/issue16472.
    Open ``C:\dev-64\Python27\Lib\distutils\cygwinccompiler.py`` and comment out the line that
    says ``self.dll_libraries = get_msvcr()``. In our file it's line 343. Be carefull because there's
    another similar line that does not need to be commented out.

You should now have a working 64 bit mingw installation and are ready to continue at step 2
of `Using an existing Python installation (64/32 bit)`_. Just remember in step 3 to add
mingw64\bin to the path instead of MinGW\bin.

.. _winpackagecontents:

Package Contents
----------------

The latest Windows package contains:

    * Latest stable kivy version
    * Python 2.7.1
    * Glew 1.5.7
    * Pygame 1.9.2
    * Cython 0.14
    * MinGW
    * GStreamer
    * Setuptools

