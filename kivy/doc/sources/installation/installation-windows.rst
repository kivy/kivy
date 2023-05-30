.. _installation_windows:

Installation on Windows
=======================

To install Kivy on Windows via ``pip``, please follow the main :ref:`installation guide<installation-canonical>`.

Installation components
-----------------------

Following, are additional information linked to from some of the steps in the
main :ref:`installation guide<installation-canonical>`, specific to Windows.

.. _install-python-win:

Installing Python
^^^^^^^^^^^^^^^^^

To install Python on Windows, download it from the main
`Python website <https://www.python.org/downloads/windows/>`_ and follow the
installation steps. You can read about the individual installation options in the
`Python guide <https://docs.python.org/3/using/windows.html#the-full-installer>`_.

If you installed the
`Python launcher <https://docs.python.org/3/using/windows.html#launcher>`_,
you will be more easily able to install multiple Python versions side by side
and select, which to run, at each invocation.

.. _install-source-win:

Source installation Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install Kivy from source, please follow the :ref:`installation guide<kivy-wheel-install>` until you reach the
:ref:`Kivy install step<kivy-source-install>` and then install the compiler below before continuing.

To install kivy from source, you need a compiler. On Windows, the *Visual Studio Build Tools* are
required, and they are available for free. You can either:

* Download and install the complete *Visual Studio IDE*, which contains the build tools.
  This is the easiest approach and the IDE can be downloaded from `here <https://www.visualstudio.com/downloads/>`_.
* The IDE is very big, so you can also download just the smaller build tools, which are used from the command line.
  The current download (2019) can be found on `this page <https://visualstudio.microsoft.com/downloads/?q=build+tools>`_
  under "Tools for Visual Studio 2019". More info about this topic can be found
  `in the Kivy wiki <https://github.com/kivy/kivy/wiki/Using-Visual-C---Build-Tools-instead-of-Visual-Studio-on-Windows>`_.

Now that the compiler is installed, continue to :ref:`install Kivy<kivy-source-install>`.

Making Python available anywhere
--------------------------------

There are two methods for launching Python when double clicking on your ``*.py`` files.

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
   'shell:sendto'. You should get the special Windows directory `SendTo`.
#. Paste the previously copied ``python.exe`` file **as a shortcut**.
#. Rename it to python <python-version>. E.g. ``python39``.

You can now execute your application by right clicking on the `.py` file ->
"Send To" -> "python <python-version>".
