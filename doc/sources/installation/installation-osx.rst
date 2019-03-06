.. _installation_osx:

Installation on OS X
====================

.. note::

    This guide describes multiple ways for setting up Kivy.

Using Wheels
------------

Wheels are precompiled binaries for the specific platform you are on.
All you need to do to install kivy using wheels on osx is ::

    $ python -m pip install kivy

If you would like to use media playback with kivy, you should install `ffpyplayer` like so ::

    $ python -m pip install ffpyplayer

Make sure to set `KIVY_VIDEO=ffpyplayer` env variable before running the app.

Gstreamer Wheels would be uploaded to pypi shortly.

Using Conda
-----------

If you use Anaconda; you first need to activate conda-forger like so ::

   $ conda config --add channels conda-forge

Then you can install kivy using ::

   $ conda install kivy

Using The Kivy.app
------------------

.. note::

    This method has only been tested on OS X 10.7 and above (64-bit).
    For versions prior to 10.7 or 10.7 32-bit, you have to install the
    components yourself.

For OS X > 10.13.5 and later, we provide packages with all dependencies
bundled in a virtual environment, including a Python interpreter for
python3 version. These bundles are primarily used for rapid prototyping,
and currently serve as containers for packaging Kivy apps with Buildozer.

To install Kivy, you must:

    1. Navigate to the latest Kivy release at
       https://kivy.org/downloads/ and download `Kivy-*-osx-python*.dmg`.
    2. Open the dmg
    3. Copy the Kivy.app to /Applications.
    4. Create a symlink by running the `makesymlinks` in the window that opens when you open the dmg
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


Using Homebrew with pip
-----------------------

You can install Kivy with Homebrew and pip using the following steps:

    1. Install the requirements using `homebrew <http://brew.sh>`_::

        $ brew install pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer

    2. Install Cython and Kivy using pip:
    
        .. parsed-literal::

            $ pip install |cython_install|
            $ pip install kivy

    - To install the development version, use this in the second step::

        $ pip install https://github.com/kivy/kivy/archive/master.zip

Using MacPorts with pip
-----------------------

.. note::

    You will have to manually install gstreamer support if you wish to
    support video playback in your Kivy App. The latest port documents show the
    following `py-gst-python port <https://trac.macports.org/ticket/44813>`_.

You can install Kivy with macports only:

    1. Install `Macports <https://www.macports.org>`_

    2. Choose python versions for Kivy, available version 2.7, 3.5, 3.6

        $ port install py35-kivy  # for python 3.5
        $ port install py36-kivy  # for python 3.6

    3. Check if kivy is available

        $ python3.5
        $ >>> import kivy

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

    5. Install Cython and Kivy using pip:

        .. parsed-literal::

            $ pip install |cython_install|
            $ pip install kivy

    - To install the development version, use this in the second step::

        $ pip install https://github.com/kivy/kivy/archive/master.zip
