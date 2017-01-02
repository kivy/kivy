.. _installation_osx:

Installation on OS X
====================

.. note::

    This guide describes multiple ways for setting up Kivy. Installing
    with Homebrew and pip is recommended for general use.

Using Homebrew with pip
-----------------------

You can install Kivy with Homebrew and pip using the following steps:

    1. Install the requirements using `homebrew <http://brew.sh>`_::

        $ brew install sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer

    2. Install cython 0.23 and kivy using pip
       (make sure to set the env variable USE_OSX_FRAMEWORKS=0, command varies by shell)::

        $ pip install -I Cython==0.23
        $ USE_OSX_FRAMEWORKS=0 pip install kivy

    - To install the development version, use this in the second step::

        $ USE_OSX_FRAMEWORKS=0 pip install https://github.com/kivy/kivy/archive/master.zip

Using MacPorts with pip
-----------------------

.. note::

    You will have to manually install gstreamer support if you wish to
    support video playback in your Kivy App. The latest port documents show the
    following `py-gst-python port <https://trac.macports.org/ticket/44813>`_.

You can install Kivy with Macports and pip using the following steps:

    1. Install `Macports <https://www.macports.org>`_

    2. Install and set Python 3.4 as the default::

        $ port install python34
        $ port select --set python python34

    3. Install and set pip as the default::

        $ port install pip-34
        $ port select --set pip pip-34

    4. Install the requirements using `Macports <https://www.macports.org>`_::

        $ port install libsdl2 libsdl2_image libsdl2_ttf libsdl2_mixer

    5. Install cython 0.23 and kivy using pip
       (make sure to set the env variable USE_OSX_FRAMEWORKS=0, command varies by shell)::

        $ pip install -I Cython==0.23
        $ USE_OSX_FRAMEWORKS=0 pip install kivy

    - To install the development version, use this in the second step::

        $ USE_OSX_FRAMEWORKS=0 pip install https://github.com/kivy/kivy/archive/master.zip

Using The Kivy.app
------------------

.. note::

    This method has only been tested on OS X 10.7 and above (64-bit).
    For versions prior to 10.7 or 10.7 32-bit, you have to install the
    components yourself. We suggest using
    `homebrew <http://brew.sh>`_ to do that.

For OS X 10.7 and later, we provide packages with all dependencies
bundled in a virtual environment, including a Python interpreter for
Kivy3.app. These bundles are primarily used for rapid prototyping,
and currently serve as containers for packaging Kivy apps with Buildozer.
Download them from our `Download Page <http://kivy.org/#download>`_.
They come as .7z files which contain:

    * Kivy.app

To install Kivy, you must:

    1. Download the latest version from http://kivy.org/#download
       Kivy2.7z is using using Python 2 (System Python), Kivy3.7z (Python 3)
    2. Extract it using an archive program like `Keka <http://www.kekaosx.com/>`_.
    3. Copy the Kivy2.app or Kivy3.app as Kivy.app to /Applications.
       Paste the following line in the terminal::

        $ sudo mv Kivy2.app /Applications/Kivy.app

    4. Create a symlink named `kivy` to easily launch apps with kivy venv::

        $ ln -s /Applications/Kivy.app/Contents/Resources/script /usr/local/bin/kivy

    5. Examples and all the normal kivy tools are present in the Kivy.app/Contents/Resources/kivy directory.

You should now have a `kivy` script that you can use to launch your kivy app from the terminal.

You can just drag and drop your main.py to run your app too.


Installing modules
~~~~~~~~~~~~~~~~~~

The Kivy SDK on OS X uses its own virtual env that is activated when you run your app using the `kivy` command.
To install any module you need to install the module like so::

    $ kivy -m pip install <modulename>

Where are the modules/files installed?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Inside the portable venv within the app at::

    Kivy.app/Contents/Resources/venv/

If you install a module that installs a binary for example like kivy-garden.
That binary will be only available from the venv above, as in after you do::

    kivy -m pip install kivy-garden

The garden lib will be only available when you activate this env::

    source /Applications/Kivy.app/Contents/Resources/venv/bin/activate
    garden install mapview
    deactivate

To install binary files
~~~~~~~~~~~~~~~~~~~~~~~

Just copy the binary to the /Applications/Kivy.app/Contents/Resources/venv/bin/ directory.

To include other frameworks
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Kivy.app comes with SDL2 and Gstreamer frameworks provided.
To include frameworks other than the ones provided do the following::

    git clone http://github.com/tito/osxrelocator
    export PYTHONPATH=~/path/to/osxrelocator
    cd /Applications/Kivy.app
    python -m osxrelocator -r . /Library/Frameworks/<Framework_name>.framework/ \
    @executable_path/../Frameworks/<Framework_name>.framework/

Do not forget to replace <Framework_name> with your framework.
This tool `osxrelocator` essentially changes the path for the
libs in the framework such that they are relative to the executable
within the .app, making the Framework portable with the .app.

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
