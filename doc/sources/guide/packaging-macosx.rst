Creating packages for MacOSX
============================

Packaging your application for the MacOSX 10.6 platform can only be done inside
MacOSX. The following method has only been tested inside VirtualBox and
MacOSX 10.6, using the portable package of Kivy.

The package will only work for the 64 bit MacOSX. We no longer support 32 bit
MacOSX platforms.

+---------------------------------------------------------------------------------------------------------------+
| NOTE: Currently, packages for OSX can only be generated with Python 2.7. Python 3.3+ support is on the way... |
+---------------------------------------------------------------------------------------------------------------+

.. _mac_osx_requirements:

New Method
----------

Since kivy 1.9 it is now possible to package kivy apps using a new method as described below to make it easier to include frameworks like sdl2 and gstreamer.

Step 1: Make sure you have the Kivy.app(unmodified) from the download page.
Step 2: run the following commands::

    > mkdir  packaging
    > cd packaging
    packaging> git clone https://github.com/kivy/kivy-sdk-packager
    packaging> cd kivy-sdk-packager/osx
    osx> rsync -a /Applications/Kivy.app ./Kivy.App

Instead of copying the kivy.app we could also just creat it from scratch using the following command::

    osx> ./create-osx-bundle.sh

You will need to install some dependencies like Platypus for that,  however ideally you don't need to worry about that and you can simply use the kivy.app provided.

Now all you need to do is to include your compiled app into the Kivy.app, simply run the following command::

    osx> ./package-app.sh path/to/your/app

This should compile your app and include all the compiled app into Kivy.app and copy it to `yourapp.app`.
when you double clickk this app you can see your app run.

This is pretty heavy app right now however you can simply remove the unneeded parts from this package.

For example if you don't use Gstreamer, simply remove it from YourApp.app/Contents/Frameworks.
Similarly you can remove the examples dir from /Applications/Kivy.app/Contents/Resources/kivy/examples/

This way the whole app can be made to only include the parts that you use inside your app.

You can edit the icons and other settings of your app by editing the YourApp/Contents/info.plist to suit your needs, simply double click this file and make your changes.

Last step is to make a dmg of your app using the following command::

    osx> create-osx-dmg.sh YourApp.app

This should give you a compressed dmg that will even further minimize the size of your distributed app.


Pyinstaller Method
------------------

Requirements
------------

    * Latest Kivy (the whole portable package, not only the github sourcecode)
    * `PyInstaller 2.0 <http://www.pyinstaller.org/#Downloads>`_

Please ensure that you have installed the Kivy DMG and installed the `make-symlink` script.
The `kivy` command must be accessible from the command line.

Thereafter, download and decompress the PyInstaller 2.0 package.

.. _mac_Create-the-spec-file:

Create the spec file
--------------------

As an example, we'll package the touchtracer demo, using a custom icon. The
touchtracer code is in the `../kivy/examples/demo/touchtracer/` directory, and the main
file is named `main.py`. Replace both path/filename according to your system.

#. Open a console.
#. Go to the pyinstaller directory, and create the initial specs::

    cd pyinstaller-2.0
    kivy pyinstaller.py --windowed --name touchtracer ../kivy/examples/demo/touchtracer/main.py

#. The specs file is named `touchtracer/touchtracer.spec` and located inside the
   pyinstaller directory. Now we need to edit the spec file to add kivy hooks
   to correctly build the executable.
   Open the spec file with your favorite editor and put theses lines at the
   start of the spec::

    from kivy.tools.packaging.pyinstaller_hooks import install_hooks
    install_hooks(globals())

   In the `Analysis()` method, remove the `hookspath=None` parameter.
   If you don't do this, the kivy package hook will not be used at all.

   Then, you need to change the `COLLECT()` call to add the data of touchtracer
   (`touchtracer.kv`, `particle.png`, ...). Change the line to add a Tree()
   object. This Tree will search and add every file found in the touchtracer
   directory to your final package.
   
   You will need to specify to pyinstaller where to look for the frameworks
   included with kivy too, your COLLECT section should look something like this::

    coll = COLLECT( exe, Tree('../kivy/examples/demo/touchtracer/'),
                   Tree("../../../../../../Applications/Kivy.app/Contents/Frameworks/"),
                   Tree("../../../../../Applications/Kivy.app/Contents/Frameworks/SDL2_ttf.framework/Versions/A/Frameworks/Freetype.Framework"),
                   a.binaries,
                   #...
                   )
                   
Make sure the path to the frameworks is relative to the current directory you are on.

#. We are done. Your spec is ready to be executed!

.. _Build the spec and create DMG:

Build the spec and create a DMG
-------------------------------

#. Open a console.
#. Go to the pyinstaller directory, and build the spec::

    cd pyinstaller-2.0
    kivy pyinstaller.py touchtracer/touchtracer.spec

#. The package will be the `touchtracer/dist/touchtracer` directory. Rename it to .app::

    pushd touchtracer/dist
    mv touchtracer touchtracer.app
    hdiutil create ./Touchtracer.dmg -srcfolder touchtracer.app -ov
    popd

#. You will now have a Touchtracer.dmg available in the `touchtracer/dist` directory.

Including Gstreamer
-------------------

If you want to read video files, audio, or camera, you will need to include
gstreamer. By default, only pygst/gst files are discovered, but all the gst plugins
and libraries are missing. You need to include them in your .spec file too, by
adding one more arguments to the `COLLECT()` method::

    import os
    gst_plugin_path = os.environ.get('GST_PLUGIN_PATH').split(':')[0]

    coll = COLLECT( exe, Tree('../kivy/examples/demo/touchtracer/'),
                   Tree(os.path.join(gst_plugin_path, '..')),
                   a.binaries,
                   #...
                   )

For Kivy.app < 1.4.1, you also need to update one script included in our
Kivy.app. Go to
`/Applications/Kivy.app/Contents/Resources/kivy/kivy/tools/packaging/pyinstaller_hooks/`,
and edit the file named `rt-hook-kivy.py`, and add this line at the end::

    environ['GST_PLUGIN_PATH'] = join(root, '..', 'gst-plugins')

