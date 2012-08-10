.. _installation_windows:

Installation on Windows
=======================

For Windows, we provide what we call a 'portable package'. You don't have
to install anything "system" wide. Just unzip & run:

#. Download the latest version from http://kivy.org/#download

    .. image:: images/win-step1.png
        :scale: 50%

#. Unzip the package

    .. image:: images/win-step3.png
        :scale: 50%

#. Then, in the unzipped package, you have a script called `kivy.bat`,
   use it for launching any kivy application as described below


.. _windows-run-app:

Start a Kivy Application
------------------------

Send-to method
~~~~~~~~~~~~~~

You can launch a .py file with our Python using the Send-to menu:

#. Copy the kivy.bat in the Clipboard

    .. image:: images/win-step4.png

#. Open the explorer, and to go the address 'shell:sendto'

    .. image:: images/win-step5.png

#. You should get the special windows directory SendTo

    .. image:: images/win-step6.png

#. Paste the previously copied kivy.bat **as a shortcut**

    .. image:: images/win-step7.png

#. Rename it to Kivy <kivy-version>

    .. image:: images/win-step8.png

Then, you can execute application by doing a right click on the .py file ->
"Send To" -> "Kivy <version>".

    .. image:: images/win-step9.png

Double-click method
~~~~~~~~~~~~~~~~~~~

There are some simple steps that you need to do once in order to be able
to launch any kivy application by just double-clicking it:

    #. Right click on the main python file (.py ending) of the application you want to launch
    #. From the context menu that appears, select *Open With*
    #. Browse your hard disk drive and find the file ``kivy.bat`` from the portable package. Select it.
    #. Select "Always open the file with..." if you don't want to repeat this procedure every time you double click a .py file.
    #. You are done. Open the file.

The next time you double click a .py file, it will be executed with the version
of python that Kivy ships with.

.. note::
   On Windows we have to ship our own version of Python since it's not
   installed by default on Windows (unlike Mac OS X and Linux). By
   following the steps above, you will set Kivy's version of Python as the
   default for opening .py files for your user.
   Normally this should not be harmful as it's just a normal version of
   Python with the :ref:`necessary third party libraries <winpackagecontents>`
   added to the module search path.
   If you do encounter unexpected problems, please :ref:`contact`.


Start from Command-Line
-----------------------

If you just want to use or develop with the latest stable kivy version, we offer
an alternative way with a console. You need a minimalist GNU system installed on
your system. Use `msysGit <http://code.google.com/p/msysgit/>`_.

When you install msysGit, you must select theses options:

    * Don't replace windows shell
    * Checkout as-is, commit as-is (no CLRF replacement!)

You'll have an icon "Git bash" on your desktop, this is the console we want:

    #. Start "Git bash"
    #. ``cd <directory of portable kivy>``
    #. ``source kivyenv.sh <full directory path of portable kivy>`` # (don't use .)

You are now ready to launch python/kivy from the command-line! Just do::

    python <filename.py>

Also, all other scripts and binaries are available, such as:

    * cython
    * gcc / make...
    * easy_install
    * gst-inspect-0.10


Use development Kivy
--------------------

.. warning::

    Using the latest development version can be risky. You might encounter
    issue during the development. If you hit any bug, please report it.

If you want to use the latest development version of Kivy, you can follow theses step:

#. Download and install Kivy for windows as the explained before
#. Go into the portable Kivy directory, where is located Python, Mingw, kivy.bat etc.
#. Rename the kivy directory to kivy.stable
#. Go on github, and download the `latest development version of Kivy <https://github.com/kivy/kivy/zipball/master>`_
#. Extract the zip into the Kivy portable directory
#. Rename the directory named "kivy-<some hash>" to just "kivy"
#. Launch kivy.bat
#. Go to the Kivy portable directory/kivy
#. Type::

    make force

#. That's all, you have a latest development version!


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

