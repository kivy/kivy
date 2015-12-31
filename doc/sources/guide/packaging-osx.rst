Creating packages for OS X
==========================

.. note::
    Packaging Kivy applications with the following methods must be done inside
    OS X, 32-bit platforms are no longer supported.

.. _osx_kivy-sdk-packager:

Using Buildozer
---------------

    pip install git+http://github.com/kivy/buildozer
    cd /to/where/I/Want/to/package
    buildozer init

Edit the buildozer.spec and add the details for your app.
Dependencies can be added to the `requirements=` section.

By default the kivy version specified in the requirements is ignored.

If you have a Kivy.app at /Applications/Kivy.app then that is used,
for packaging. Otherwise the latest build from kivy.org using Kivy
master will be downloaded and used.

If you want to package for python 3.x.x simply download the package
named Kivy3.7z from the download sectoin of Kivy.org and extract it
to Kivy.app in /Applications.

Then run.

    buildozer osx debug

Once the app is packaged, you might want to remove extra un needed
packages like gstreamer framework etc from it if you don't use video.
Same logic implies for other things you do not use, just reduce
the package to it's minimal state that is needed for the app to run.

As a example we are including the showcase example packaged using
this method for both python 2(9.xMB) and 3(15.xMB), you can find the
packages here 
https://drive.google.com/drive/folders/0B1WO07-OL50_alFzSXJUajBFdnc .

That's it. Enjoy!

buildozer right now uses the Kivy sdk method to package your app.
If you want to control more details about your app than buildozer
currently offers then you can use the following method `using Kivy SDK`
mentioned below.

Using Kivy SDK
--------------

Since version 1.9.0, Kivy is released for the OS X platform in a
self-contained, portable distribution.

Apps can be packaged and distributed with the Kivy SDK using the method
described below, making it easier to include frameworks like SDL2 and
GStreamer.

1. Make sure you have the unmodified Kivy SDK (Kivy.app) from the download page.

2. Run the following commands::

    > mkdir packaging
    > cd packaging
    packaging> git clone https://github.com/kivy/kivy-sdk-packager
    packaging> cd kivy-sdk-packager/osx
    osx> cp -a /Applications/Kivy.app ./Kivy.App

  .. note::
    This step above is important, you have to make sure to preserve the paths
    and permissions. A command like ``cp -rf`` will copy but make the app
    unusable and lead to error later on.

3. Now all you need to do is to include your compiled app in the Kivy.app
   by running the following command::

    osx> ./package-app.sh /path/to/your/<app_folder_name>/

  Where <app_folder_name> is the name of your app.

  This copies Kivy.app to `<app_folder_name>.app` and includes a compiled copy
  of your app into this package.

4. That's it, your self-contained package is ready to be deployed!
   You can now further customize your app as described bellow.

Installing modules
~~~~~~~~~~~~~~~~~~

Kivy package on osx uses its own virtual env that is activated when you run your app using `kivy` command.
To install any module you need to install the module like so::

    $ kivy -m pip install <modulename>

Where are the modules/files installed?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Inside the relocatable venv within the app at::

    Kivy.app/Contents/Resources/venv/

If you install a module that install's a binary for example like kivy-garden
That binary will be only available from the venv above, as in after you do::

    kivy -m pip install kivy-garden

The garden lib will be only available when you activate this env.

    source /Applications/Kivy.app/Contents/Resources/venv/bin/activate
    garden install mapview
    deactivate

To install binary files
~~~~~~~~~~~~~~~~~~~~~~

Just copy the binary to the Kivy.app/Contents/Resources/venv/bin/ directory.

To Include other frameworks
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Kivy.app comes with SDL2 and Gstreamer frameworks provided.
To Include frameworks other than the ones provided do the following::

    git clone http://github.com/tito/osxrelocator
    export PYTHONPATH=~/path/to/osxrelocator
    cd Kivy.app
    python -m osxrelocator -r . /Library/Frameworks/<Framework_name>.framework/ \
    @executable_path/../Frameworks/<Framework_name>.framework/

Do not forget to replace <Framework_name> with your framework.
This tool `osxrelocator` essentially changes the path for the
libs in the framework such that they are relative to the executable
within the .app. Making the Framework relocatable with the .app.


Shrinking the app size
^^^^^^^^^^^^^^^^^^^^^^
The app has of considerable size right now, however the unneeded parts can be
removed from the package.

For example if you don't use GStreamer, simply remove it from
YourApp.app/Contents/Frameworks.
Similarly you can remove the examples folder from
/Applications/Kivy.app/Contents/Resources/kivy/examples/ or kivy/tools,
kivy/docs etc.

This way the package can be made to only include the parts that are needed for
your app.

Adjust settings
^^^^^^^^^^^^^^^
Icons and other settings of your app can be changed by editing
YourApp/Contents/info.plist to suit your needs.

Create a DMG
^^^^^^^^^^^^
To make a DMG of your app use the following command::

    osx> ./create-osx-dmg.sh YourApp.app

Note the lack of `/` at the end.
This should give you a compressed dmg that will further shrink the size of your distributed app.


.. _osx_pyinstaller:


Using Pyinstaller without brew
------------------------------
First install Kivy and it's dependencies without using homebrew as mentioned here
http://kivy.org/docs/installation/installation.html#development-version

Once you have kivy and it's deps installed then you need to install pyinstaller

let's assume we use a folder like `testpackaging`::

    cd testpackaging
    git clone http://github.com/pyinstaller/pyinstaller
    
create a file named as touchtracer.spec in this directory and paste the following
into it editing ::

    # -*- mode: python -*-
    
    block_cipher = None
    from kivy.tools.packaging.pyinstaller_hooks import get_deps_all, hookspath, runtime_hooks
    
    a = Analysis(['/path/to/yout/folder/containing/examples/demo/touchtracer/main.py'],
                 pathex=['/path/to/yout/folder/containing/testpackaging'],
                 binaries=None,
                 win_no_prefer_redirects=False,
                 win_private_assemblies=False,
                 cipher=block_cipher,
                 hookspath=hookspath(),
                 runtime_hooks=runtime_hooks(),
                 **get_deps_all())
    pyz = PYZ(a.pure, a.zipped_data,
                 cipher=block_cipher)
    exe = EXE(pyz,
              a.scripts,
              exclude_binaries=True,
              name='touchtracer',
              debug=False,
              strip=False,
              upx=True,
              console=False )
    coll = COLLECT(exe, Tree('../kivy/examples/demo/touchtracer/'),
                   Tree('/Library/Frameworks/SDL2_ttf.framework/Versions/A/Frameworks/FreeType.framework'),
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=True,
                   name='touchtracer')
    app = BUNDLE(coll,
                 name='touchtracer.app',
                 icon=None,
             bundle_identifier=None)

Change the paths ::

    a = Analysis(['/path/to/yout/folder/containing/examples/demo/touchtracer/main.py'],
                pathex=['/path/to/yout/folder/containing/testpackaging'],
    ...
    ...
    coll = COLLECT(exe, Tree('../kivy/examples/demo/touchtracer/'),

By your relevant paths, then run the following command::

    pyinstaller/pyinstaller.py touchtracer.spec

Replace `touchtracer` with your app where appropriate.
This will give you a <yourapp>.app in dist/ folder.
    
    
Using PyInstaller and Homebrew
------------------------------
.. note::
    Package your app on the oldest OS X version you want to support.

Complete guide
^^^^^^^^^^^^^^
#. Install `Homebrew <http://brew.sh>`_
#. Install Python::

    $ brew install python

   .. note::
     To use Python 3, ``brew install python3`` and replace ``pip`` with ``pip3``
     in the guide below.

#. (Re)install your dependencies with ``--build-bottle`` to make sure they can be
   used on other machines::

    $ brew reinstall --build-bottle sdl2 sdl2_image sdl2_ttf sdl2_mixer

   .. note::
       If your project depends on GStreamer or other additional libraries (re)install
       them with ``--build-bottle`` as described `below <additional libraries_>`_.

#. Install Cython and Kivy::

    $ pip install -I Cython==0.21.2
    $ USE_OSX_FRAMEWORKS=0 pip install git+https://github.com/kivy/kivy.git@1.9.0

#. Install the development version of PyInstaller which includes fixes for the
   GStreamer hooks::

    $ pip install git+https://github.com/pyinstaller/pyinstaller.git@develop

#. Export the ``HOOKSPATH`` environment variable::

    $ export HOOKSPATH=`python -c "
    import imp, os
    print(os.path.join(imp.find_module('kivy')[1], 'tools/packaging/pyinstaller_hooks'))"`

#. Package your app using the path to your main.py::

    $ pyinstaller -y --clean --windowed --name touchtracer \
      --additional-hooks-dir $HOOKSPATH \
      --runtime-hook $HOOKSPATH/rt-hook-kivy.py \
      --exclude-module _tkinter \
      --exclude-module Tkinter \
      --exclude-module enchant \
      --exclude-module twisted \
      /usr/local/share/kivy-examples/demo/touchtracer/main.py

   .. note::
     This will not yet copy additional image or sound files. You would need to adapt the
     created ``.spec`` file for that.


Editing the spec file
^^^^^^^^^^^^^^^^^^^^^
The specs file is named `touchtracer.spec` and is located in the directory where you ran
the pyinstaller command.

You need to change the `COLLECT()` call to add the data of touchtracer
(`touchtracer.kv`, `particle.png`, ...). Change the line to add a Tree()
object. This Tree will search and add every file found in the touchtracer
directory to your final package. Your COLLECT section should look something like this::


    coll = COLLECT(exe, Tree('/usr/local/share/kivy-examples/demo/touchtracer/'),
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=None,
                   upx=True,
                   name='touchtracer')

This will add the required hooks so that PyInstaller gets the required Kivy files.
We are done. Your spec is ready to be executed.

Build the spec and create a DMG
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Open a console.
#. Go to the PyInstaller directory, and build the spec::

    $ pyinstaller -y --clean --windowed touchtracer.spec

#. Run::

    $ pushd dist
    $ hdiutil create ./Touchtracer.dmg -srcfolder touchtracer.app -ov
    $ popd

#. You will now have a Touchtracer.dmg available in the `dist` directory.


Additional Libraries
^^^^^^^^^^^^^^^^^^^^
GStreamer
"""""""""
If your project depends on GStreamer::

    $ brew reinstall --build-bottle gstreamer gst-plugins-{base,good,bad,ugly}

.. note::
    If your Project needs Ogg Vorbis support be sure to add the ``--with-libvorbis``
    option to the command above.

If you are using Python from Homebrew you currently also need the following step until `this pull request <https://github.com/Homebrew/homebrew/pull/46097>`_ gets merged::

    $ brew reinstall --with-python --build-bottle https://github.com/cbenhagen/homebrew/raw/patch-3/Library/Formula/gst-python.rb


SDL 2 HEAD for ``Window.on_dropfile`` support
"""""""""""""""""""""""""""""""""""""""""""""

You can install the newest SDL 2 library which supports ``on_dropfile`` with::

    $ brew reinstall --build-bottle --HEAD sdl2

Or you build 2.0.3 with the following patches (untested):

- https://hg.libsdl.org/SDL/rev/2cc90bb31777
- https://hg.libsdl.org/SDL/rev/63c4d6f1f85f
