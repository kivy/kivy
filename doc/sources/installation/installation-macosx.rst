Installation on MacOSX
======================

.. note::

    This method has only been tested on Mac OSX 10.6 Snow Leopard 64-bit.
    For versions prior to 10.6 or 10.6 32-bit, you have to install the
    components yourself. We suggest using
    `homebrew <http://mxcl.github.com/homebrew/>`_ to do that.

For Mac OS X 10.6 and later, we provide a Kivy.app with all dependencies
bundled. Download it from our google code project page. It comes as a .dmg
file that contains:

    * Kivy.app
    * Readme.txt
    * An Examples folder
    * A script to install a `kivy` command for shell usage

To install Kivy, you must:

    1. Download the latest version from http://kivy.org/#downloads
    2. Double-click to open it
    3. Drag the Kivy.app into your Applications folder
    4. Make sure to read the Readme.txt

Start any Kivy Application
----------------------------

You can run any Kivy application by simply dragging the application's main file
onto the Kivy.app icon. Just try with any python file in the examples folder.

.. _macosx-run-app:

Start from Command Line
-----------------------

If you want to use Kivy from the command line, double-click the ``Make Symlinks`` script
after you dragged the Kivy.app into the Applications folder. To test if it worked:

    #. Open Terminal.app and run ``kivy``. You should get a Python prompt.
    #. In there, enter import kivy. If it just goes to the next line without errors, it worked.
    #. Running any Kivy application from the command line is now simply a matter
       of executing a command like the following: ``kivy yourapplication.py``

