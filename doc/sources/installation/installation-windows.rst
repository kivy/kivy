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

