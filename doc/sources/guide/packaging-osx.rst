.. _packaging-osx:

Creating packages for macOS
==========================

.. note::

    This guide describes multiple ways for packaging Kivy applications.
    Packaging using the Kivy SDK is recommended for general use.

.. _packaging-osx-sdk:

Using the Kivy SDK
------------------

.. note::

    These instructions apply only from Kivy v2.0.0 onwards.

.. note::

    Kivy.app is built with ``MACOSX_DEPLOYMENT_TARGET=10.9``.

We provide a Kivy DMG with all dependencies bundled in a **virtual environment**,
including a Python interpreter that can be used as a base to package kivy apps.

This is the safest approach because it packages the binaries without references to
any binaries on the system on which the app is packaged. Because all references are
to frameworks included in the dmg or to binaries with the dmg. As opposed to
e.g. pyinstaller which copies binaries from your local python installation.

You can find complete instructions to build and package apps with Kivy.app, starting either
with Kivy.app or building from scratch, in the readme
of the `kivy-sdk-packager repo <https://github.com/kivy/kivy-sdk-packager/tree/master/osx>`_.


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

When you're ready to package your macOS app just run::

    buildozer osx debug

Once the app is packaged, you might want to remove unneeded
packages, just reduce the package to its minimal state that
is needed for the app to run.

That's it. Enjoy!

Buildozer right now uses the Kivy SDK to package your app.
If you want to control more details about your app than buildozer
currently offers then you can use the SDK directly, as detailed in the
section below.

.. _osx_pyinstaller:

Using PyInstaller and Homebrew
------------------------------
.. note::

    Package your app on the oldest macOS version you want to support.

Complete guide
~~~~~~~~~~~~~~
#. Install `Homebrew <http://brew.sh>`_
#. Install Python::

    $ brew install python

   .. note::
     To use Python 3, ``brew install python3`` and replace ``pip`` with
     ``pip3`` in the guide below.

#. (Re)install your dependencies with ``--build-from-source`` to make sure they can
   be used on other machines::

    $ brew reinstall --build-from-source sdl2 sdl2_image sdl2_ttf sdl2_mixer

   .. note::
       If your project depends on GStreamer or other additional libraries
       (re)install them with ``--build-from-source`` as described
       `below <additional libraries_>`_.

#. Install Cython and Kivy:

    .. parsed-literal::

        $ pip install |cython_install|
        $ pip install -U kivy

#. Install PyInstaller::

    $ pip install -U pyinstaller

#. Package your app using the path to your main.py::

    $ pyinstaller -y --clean --windowed --name touchtracer \
      --exclude-module _tkinter \
      --exclude-module Tkinter \
      --exclude-module enchant \
      --exclude-module twisted \
      /usr/local/share/kivy-examples/demo/touchtracer/main.py

   .. note::
     This will not yet copy additional image or sound files. You would need to
     adapt the created ``.spec`` file for that.


Editing the spec file
~~~~~~~~~~~~~~~~~~~~~
The specs file is named `touchtracer.spec` and is located in the directory
where you ran the pyinstaller command.

You need to change the `COLLECT()` call to add the data of touchtracer
(`touchtracer.kv`, `particle.png`, ...). Change the line to add a Tree()
object. This Tree will search and add every file found in the touchtracer
directory to your final package. Your COLLECT section should look something
like this::


    coll = COLLECT(exe, Tree('/usr/local/share/kivy-examples/demo/touchtracer/'),
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=None,
                   upx=True,
                   name='touchtracer')

This will add the required hooks so that PyInstaller gets the required Kivy
files. We are done. Your spec is ready to be executed.

Build the spec and create a DMG
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Open a console.
#. Go to the PyInstaller directory, and build the spec::

    $ pyinstaller -y --clean --windowed touchtracer.spec

#. Run::

    $ pushd dist
    $ hdiutil create ./Touchtracer.dmg -srcfolder touchtracer.app -ov
    $ popd

#. You will now have a Touchtracer.dmg available in the `dist` directory.


Additional Libraries
~~~~~~~~~~~~~~~~~~~~
GStreamer
^^^^^^^^^
If your project depends on GStreamer::

    $ brew reinstall --build-from-source gstreamer gst-plugins-{base,good,bad,ugly}

.. note::
    If your Project needs Ogg Vorbis support be sure to add the
    ``--with-libvorbis`` option to the command above.

If you are using Python from Homebrew you will also need the following step
until `this pull request <https://github.com/Homebrew/homebrew/pull/46097>`_
gets merged::

    $ brew reinstall --with-python --build-from-source https://github.com/cbenhagen/homebrew/raw/patch-3/Library/Formula/gst-python.rb


Using PyInstaller without Homebrew
----------------------------------
First install Kivy and its dependencies without using Homebrew as mentioned here
http://kivy.org/docs/installation/installation.html#development-version.

Once you have kivy and its deps installed, you need to install PyInstaller.

Let's assume we use a folder like `testpackaging`::

    cd testpackaging
    git clone http://github.com/pyinstaller/pyinstaller

Create a file named touchtracer.spec in this directory and add the following
code to it::

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

Change the paths with your relevant paths::

    a = Analysis(['/path/to/yout/folder/containing/examples/demo/touchtracer/main.py'],
                pathex=['/path/to/yout/folder/containing/testpackaging'],
    ...
    ...
    coll = COLLECT(exe, Tree('../kivy/examples/demo/touchtracer/'),

Then run the following command::

    pyinstaller/pyinstaller.py touchtracer.spec

Replace `touchtracer` with your app where appropriate.
This will give you a <yourapp>.app in the dist/ folder.