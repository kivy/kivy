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
               <debug|install|release>

The last argument stand for:

- debug: build debug version and save to bin directory
- install: same as debug + upload on connected device
- release: build release version and save to bin directory

For example, if we imagine that touchtracer demo of Kivy is in the directory
~/kivy/examples/demo/touchtracer, you can do::

    python build.py --dir ~/kivy/examples/demo/touchtracer \
    --package org.demo.touchtracer \
	--name "Kivy Touchtracer" --version 1.0.6 debug

The debug binary will be generated in bin/KivyTouchtracer-1.0.6-debug.apk.

Then in later time, you can install directly to your android device by doing::

    adb install -r bin/KivyTouchtracer-1.0.6-debug.apk

Or you can use the `install` method instead of `debug`.

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


