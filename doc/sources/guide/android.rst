.. _android:

Kivy on Android
===============

Kivy is able to run on android, but you need a phone with:

* SD Card
* OpenGL ES 2.0 (Android 2.2 minimum)

Requirements for android application
------------------------------------

To create an application for Android platform, you must have a
file named `main.py` in the root directory of your application.

If the application will run inside the Kivy launcher, then you must handle the
`__name__` as::

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

The project is now stable, using `Python for Android
<http://github.com/kivy/python-for-android/>`_.

We made that project to be able to:

- create custom Python version including only wanted modules
- handle multitouch events to Kivy
- create a python module for accessing to some intents
- handle sleep/wakeup properly

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

