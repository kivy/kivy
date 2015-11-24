.. _installation_osx:

Installation on OS X
======================

Using The Kivy.app
------------------

.. note::

    This method has only been tested on OS X 10.7 Lion 64-bit.
    For versions prior to 10.7 or 10.7 32-bit, you have to install the
    components yourself. We suggest using
    `homebrew <http://brew.sh>`_ to do that.

For OS X 10.7 and later, we provide a Kivy.app with all dependencies
bundled. Download it from our `Download Page <http://kivy.org/#download>`_.
It comes as a .dmg file that contains:

    * Kivy.app
    * Readme.txt
    * An Examples folder
    * A script to install a `kivy` command for shell usage

To install Kivy, you must:

    1. Download the latest version from http://kivy.org/#download
    2. Double-click to open it
    3. Drag the Kivy.app into your Applications folder
    4. Double click the makesymlinks script.

You should now have a `kivy` script that you can use to launch your kivy app from terminal.

You can just drag and drop your main.py to run your app too.


Installing modules
~~~~~~~~~~~~~~~~~~

Kivy package on osx uses its own virtual env that is activated when you run your app using `kivy` command.
To install any module you need to install the module like so::

    $ kivy -m pip install <modulename>


Start any Kivy Application
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can run any Kivy application by simply dragging the application's main file
onto the Kivy.app icon. Just try this with any python file in the examples folder.

.. _osx-run-app:


Start from the Command Line
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to use Kivy from the command line, double-click the ``Make Symlinks`` script
after you have dragged the Kivy.app into the Applications folder. To test if it worked:

    #. Open Terminal.app and enter::

           $ kivy

       You should get a Python prompt.

    #. In there, type::

           >>> import kivy

       If it just goes to the next line without errors, it worked.

    #. Running any Kivy application from the command line is now simply a matter
       of executing a command like the following::

           $ kivy yourapplication.py


Using pip
---------

Alternatively you can install Kivy using the following steps:

    1. Install the requirements using `homebrew <http://brew.sh>`_::

        $ brew install sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer

    2. Install cython 0.21.2 and kivy using pip::

        $ pip install -I Cython==0.21.2
        $ USE_OSX_FRAMEWORKS=0 pip install git+https://github.com/kivy/kivy.git@1.9.0
