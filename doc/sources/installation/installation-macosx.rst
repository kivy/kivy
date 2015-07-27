.. _installation_macosx:

Installation on MacOSX
======================

.. note::

    This method has only been tested on Mac OSX 10.7 Lion 64-bit.
    For versions prior to 10.7 or 10.7 32-bit, you have to install the
    components yourself. We suggest using
    `homebrew <http://mxcl.github.com/homebrew/>`_ to do that.

    There can be a limitation on some OS X with more than one monitor.
    The application will crash when you try to start it on the second monitor.

For Mac OS X 10.7 and later, we provide a Kivy.app with all dependencies
bundled. Download it from our `Download Page <http://kivy.org/#download>`_.
It comes as a .dmg 
file that contains:

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
-------------------

Kivy package on osx uses its own virtual env that is activated when you run your app using `kivy` command.
To install any module you need to install the module like so::

    kivy -m pip install <modulename>

Installing the dev version
--------------------------
Follow these steps:

    1. Follow the procedure mentioned above to install kivy stable.
    2. Install the requirements like (sdl2, sdl2_ttf, sdl2_mixerm, gstreamer) as frameworks on your system.
    3. You need to link these frameworks to /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.10.sdk/System/Library/Frameworks.Make file will check /Library/Frameworks but Xcode will use its own folder, the second one.
    4. Open a terminal and type the following commands into it::

        kivy -m pip install cython
        cd /Applications/Kivy.app/Contents/Resources/
        mv kivy kivy_stable
        git clone http://github.com/kivy/kivy
        cd kivy
        kivy setup.py build_ext --inplace

That's it. You now have the latest kivy from github.

Start any Kivy Application
----------------------------

You can run any Kivy application by simply dragging the application's main file
onto the Kivy.app icon. Just try this with any python file in the examples folder.

.. _macosx-run-app:

Start from the Command Line
---------------------------

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
