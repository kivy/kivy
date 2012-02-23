.. _android:

Kivy on Android
===============

Kivy is able to run on android, but you need a phone with:

* SD Card
* OpenGL ES 2.0 (Android 2.2 minimum)

Requirements for android application
------------------------------------

To create an application for Android platform, you must have a
file named `main.py` in the root directory of your application, handling
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

You'll see all the log including your stdout/stderr, Kivy logger.


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
    - custom python native launcher that run the main.py
    - default activation of WRITE_EXTERNAL_STORAGE permission
    - Video support (done in 1.0.8 version using ffmpeg-android)
    - Audio support

Currently, Kivy is not fully supported on Android. We are missing:

    - Camera providers
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

