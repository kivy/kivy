.. _installation_osx:

Installation on OS X
======================

Using The Kivy.app
------------------

.. note::

    This method has only been tested on OS X 10.7 and above (64-bit).
    For versions prior to 10.7 or 10.7 32-bit, you have to install the
    components yourself. We suggest using
    `homebrew <http://brew.sh>`_ to do that.

For OS X 10.7 and later, we provide a Kivy.app with all dependencies
bundled. Download it from our `Download Page <http://kivy.org/#download>`_.
It comes as a .7z file that contains:

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
~~~~~~~~~~~~~~~~~~~~~~

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


Using pip
---------

Alternatively you can install Kivy using the following steps:

    1. Install the requirements using `homebrew <http://brew.sh>`_::

        $ brew install sdl2 sdl2_image sdl2_ttf sdl2_mixer gstreamer

    2. Install cython 0.23 and kivy using pip::

        $ pip install -I Cython==0.23
        $ USE_OSX_FRAMEWORKS=0 pip install kivy
