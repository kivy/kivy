.. _packaging_android:

Create a package for Android
============================

Packaging your application into APK
-----------------------------------

To be able to package your Kivy application into an APK, you must have some
tools available in your PATH:

    * Java
    * Python 2.7 (not 2.6.)
    * Jinja2 (python module)
    * Apache ant
    * Android SDK

You must download the tool named Kivy-XXX-android.zip, available at
http://code.google.com/p/kivy/downloads/list, and unzip it.

Build in debug mode
~~~~~~~~~~~~~~~~~~~

Inside the package, you have a tool named build.py. This is the script that will create APK for you::

    ./build.py --dir <path to your app>
               --name "<title>"
               --package <org.of.your.app>
               --version <human version>
               --icon <path to an icon to use>
               --orientation <landscape|portrait>
               --permission <android permission like VIBRATE> (multiple allowed)
               --with-ffmpeg
               <debug|release> <installd|installr|...>

Starting 1.0.9, build.py have been updated to use Android SDK rev14, but is
still compatible with previous version:

- if you pass 2 last argument, it will use Android SDK rev14 (new build system)
- if you pass only one argument, it will use older Android SDK build system

.. note::

    The Android SDK rev14 usage is available starting Kivy 1.0.9. If you have SDK
    rev14 installed on your system, you must upgrade Kivy for android as well.

For example, if we imagine that touchtracer demo of Kivy is in the directory
~/kivy/examples/demo/touchtracer, you can do::

    python build.py --dir ~/kivy/examples/demo/touchtracer \
    --package org.demo.touchtracer \
	--name "Kivy Touchtracer" --version 1.0.6 debug installd

The debug binary will be generated in bin/KivyTouchtracer-1.0.6-debug.apk.

Then in later time, you can install directly to your android device by doing::

    adb install -r bin/KivyTouchtracer-1.0.6-debug.apk

Or you can use the `install` method instead of `debug`.

Video support
~~~~~~~~~~~~~

.. versionadded:: 1.0.8

By default, the produced APK don't contain any libraries for video support. You
can add ffmpeg library on your build to activate it. The default ffmpeg
compiled is the "minimal support", and will increase the APK size of ~8MB.

The option to add on the build.py command line is `--with-ffmpeg`::

    python build.py --with-ffmpeg --dir ....

Release on the market
~~~~~~~~~~~~~~~~~~~~~

Launch the build.py script again, with the `release` command, then, you must
sign and zipalign the apk.  Read the android documentation at:

http://developer.android.com/guide/publishing/app-signing.html

The release binary will be generated in bin/KivyTouchtracer-1.0.6-unsigned.apk
(for previous touchtracer example.)


Packaging your application for Kivy Launcher
--------------------------------------------

The Kivy launcher is an application to run any Kivy examples stored on your
SD Card from android. See :ref:`androidinstall`.

Your application must be saved into::

    /sdcard/kivy/<yourapplication>

Your application directory must contain::

    # Your main application file:
    main.py
    # Some infos Kivy requires about your app on android:
    android.txt

The file `android.txt` must contain::

    title=<Application Title>
    author=<Your Name>
    orientation=<portrait|landscape>


