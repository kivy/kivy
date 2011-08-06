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

Create an APK
-------------

The whole process is described in the :ref:`packaging_android` documentation.


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
- Asus EeePad Transformer

