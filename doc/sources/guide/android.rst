.. _android:

Kivy on Android
===============

Requirements for android application
------------------------------------

As soon as you want to do an application for android platform, you must have a
file named `main.py` in for root directory of your application, and handling
the android platform in the `__name__` test::

    if __name__ in ('__main__', '__android__'):
        YourApp().run()


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


Debugging your application on android platform
----------------------------------------------

Android SDK ship a tool named adb. Connect your device, and run::

    adb logcat

You'll see all the log, but also your stdout/stderr, Kivy logger.


Status of the Project
---------------------

This project is a derivated work of Pygame Subset for Android, made by Tom
Rothamel. His work is available at::

	https://code.launchpad.net/~pgs4a-developer/pgs4a/mainline

This project code is available at::

	https://code.launchpad.net/~tito-bankiz/pgs4a/kivy

We made that branch to be able to:

	- integrate Kivy android-support branch in the build
	- create opengl es 2 surface with stencil buffer
	- enable multitouch event
	- custom start.pyx to launch kivy application
	- default activation of WRITE_EXTERNAL_STORAGE permission

Currently, Kivy is not fully supported on Android. We are missing:

    - Video providers
    - Camera providers
    - Audio (can use RenPySound) providers
    - Keyboard mapping for main button
    - Ability to hook app on sleep/wakeup
    - Ability for an application to have a settings screen

Tested Devices
--------------

These Android devices have been confirmed working with Kivy. If your
device is not on the list, that does not mean that it is not supported.
If that is the case, please try running Kivy and if it succeeds let us
know so that we can update this list. Note, however, that your device has
to support at least OpenGL 2.0 ES.

Phones
~~~~~~

- Motorola Droid 1
- Motorola Droid 2
- HTC Desire
- HTC Desire Z
- Xperia 10 (custom ROM 2.1 + GLES 2.0 support)

Tablets
~~~~~~~

- Samsung Galaxy Tab
- Motorola Xoom

