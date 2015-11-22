Creating packages for OS X
==========================

.. note::
    - Packaging your application for the OS X platform can only be done inside OS X.

.. _osx_kivy-sdk-packager:

Using kivy-sdk-packager
-----------------------
.. note::
    - This is currently the preferred way to package an app.
    - The package will only work for the 64 bit OS X.

Since Kivy 1.9 Kivy package on OS X is a self contained portable distribution.
It is now possible to package Kivy apps using the method described below to make
it easier to include frameworks like SDL 2 and GStreamer.

1. Make sure you have the unmodified Kivy.app from the download page.

2. Run the following commands::

    > mkdir packaging
    > cd packaging
    packaging> git clone https://github.com/kivy/kivy-sdk-packager
    packaging> cd kivy-sdk-packager/osx
    osx> cp -a /Applications/Kivy.app ./Kivy.App

  .. note::
    - This step above is important, you have to make sure to preserve the paths and permissions.
      A command like ``cp -rf`` will copy but make the app unusable and lead to error later on.

3. Now all you need to do is to include your compiled app into the Kivy.app. Simply run the following command::

    osx> ./package-app.sh /path/to/your/<app_folder_name>/

  Where <app_folder_name> is the name of your app.

  This copies Kivy.app to `<app_folder_name>.app` and includes a compiled copy of the demo app into this package.

4. That's it, your first self contained package is ready to be deployed!
   You can now further customize your app as described bellow.


Shrink the app size
^^^^^^^^^^^^^^^^^^^
This is a pretty big sized app right now however you can simply remove the unneeded parts from this package.

For example if you don't use GStreamer, simply remove it from YourApp.app/Contents/Frameworks.
Similarly you can remove the examples dir from /Applications/Kivy.app/Contents/Resources/kivy/examples/
or kivyt/tools,  kivy/docs...

This way the whole app can be made to only include the parts that you use inside your app.

Adjust settings
^^^^^^^^^^^^^^^
You can edit the icons and other settings of your app by editing the YourApp/Contents/info.plist to suit your
needs, simply double click this file and make your changes.

Create a DMG
^^^^^^^^^^^^
To make a DMG of your app use the following command::

    osx> ./create-osx-dmg.sh YourApp.app

This should give you a compressed dmg that will even further minimize the size of your distributed app.


.. _osx_pyinstaller:

Using PyInstaller and Homebrew
------------------------------
.. note::
    - Package your app on the oldest OS X version you want to support.

Complete guide
^^^^^^^^^^^^^^
#. Install `Homebrew <http://brew.sh>`_
#. Install Python::

    $ brew install python

   .. note::
     - To use Python 3, ``brew install python3`` and replace ``pip`` with ``pip3``
       in the guide below.

#. Install Cython and Kivy::

    $ pip install -I Cython==0.21.2
    $ USE_OSX_FRAMEWORKS=0 pip install git+https://github.com/kivy/kivy.git@1.9.0

#. (Re)install your dependencies with ``--build-bottle`` to make sure they can be
   used on other machines::

    $ brew reinstall --build-bottle bsdl2 sdl2_image sdl2_ttf sdl2_mixer

   .. note::
     - If your projects depends on GStreamer or additional libraries (re)install them with
       ``--build-bottle`` at this point as described below.

#. Install Kivy via pip::

    $ pip install -I Cython==0.21.2
    $ USE_OSX_FRAMEWORKS=0 pip install git+https://github.com/kivy/kivy.git@1.9.0

#. Install the PyInstaller develop version which includes fixes to GStreamer hooks::

    $ pip install git+https://github.com/pyinstaller/pyinstaller.git@develop


#. Package your app using the path to your main.py::

    $ pyinstaller -y --clean --windowed --name touchtracer /usr/local/share/kivy-examples/demo/touchtracer/main.py

   .. note::
     - Depending on your system you might want to add "``--exclude-module _tkinter``"
       to the PyInstaller command.
     - This will not yet copy additional image or sound files. You would need to adapt the
       created ``.spec`` file for that.


The specs file is named `touchtracer/touchtracer.spec` and located inside the
pyinstaller directory. Now we need to edit the spec file to add kivy hooks
to correctly build the executable.
Open the spec file with your favorite editor and put theses lines at the
start of the spec::

  from kivy.tools.packaging.pyinstaller_hooks import get_hooks

In the `Analysis()` function, remove the `hookspath=None` parameter and
the `runtime_hooks` parameter if present. `get_hooks` will return the required
values for both parameters, so at the end of `Analysis()` add `**get_hooks()`.
E.g.::

    a = Analysis(['/usr/local/share/kivy-examples/demo/touchtracer/main.py'],
             pathex=['/Users/kivy-dev/Projects/kivy-packaging'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             excludes=None,
             win_no_prefer_redirects=None,
             win_private_assemblies=None,
             cipher=block_cipher,
             **get_hooks())

This will add the required hooks so that pyinstaller gets the required kivy files.

Then, you need to change the `COLLECT()` call to add the data of touchtracer
(`touchtracer.kv`, `particle.png`, ...). Change the line to add a Tree()
object. This Tree will search and add every file found in the touchtracer
directory to your final package.

You will need to specify to PyInstaller where to look for the frameworks
included with Kivy too, your COLLECT section should look something like this::

    coll = COLLECT( exe, Tree('../kivy/examples/demo/touchtracer/'),

We are done. Your spec is ready to be executed!


Additional Libraries
^^^^^^^^^^^^^^^^^^^^
GStreamer
"""""""""
If your project depends on GStreamer::

    $ brew reinstall --build-bottle gstreamer gst-plugins-{base,good,bad,ugly}

.. note::
    - If your Project needs Ogg Vorbis support be sure to add the ``--with-libvorbis``
      option to the command above.

If you are using Python from Homebrew you currently also need the following step::

    $ brew reinstall --build-bottle https://github.com/cbenhagen/homebrew/raw/patch-3/Library/Formula/gst-python.rb


SDL 2 HEAD for ``Window.on_dropfile`` support
"""""""""""""""""""""""""""""""""""""""""""""

You can install the newest SDL 2 library which supports ``on_dropfile`` with::

    $ brew reinstall --build-bottle --HEAD sdl2

Or you build 2.0.3 with the following patches (untested):

- https://hg.libsdl.org/SDL/rev/2cc90bb31777
- https://hg.libsdl.org/SDL/rev/63c4d6f1f85f


Build the spec and create a DMG
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Open a console.
#. Go to the PyInstaller directory, and build the spec::

    cd pyinstaller-3.0
    kivy pyinstaller.py touchtracer/touchtracer.spec

#. The package will be the `touchtracer/dist/touchtracer` directory. Rename it to .app::

    pushd touchtracer/dist
    mv touchtracer touchtracer.app
    hdiutil create ./Touchtracer.dmg -srcfolder touchtracer.app -ov
    popd

#. You will now have a Touchtracer.dmg available in the `touchtracer/dist` directory.


