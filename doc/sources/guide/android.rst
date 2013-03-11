.. _android:
.. _Kivy Launcher: https://play.google.com/store/apps/details?id=org.kivy.pygame&hl=en

Kivy on Android
===============

Kivy runs on Android, but you need a phone with:

* SD Card
* OpenGL ES 2.0 (Android 2.2 minimum)

Requirements for an Android application
---------------------------------------

To create an application for the Android platform, you must have a
file named `main.py` in the root directory of your application.

If you want your application to run inside the `Kivy launcher`_, then you 
must handle the `__name__` as::

    if __name__ in ('__main__', '__android__'):
        YourApp().run()

Create an APK
-------------

The whole process is described in the :ref:`packaging_android` documentation.


Debugging your application on the Android platform
--------------------------------------------------

The `Android SDK <http://developer.android.com/sdk/index.html>`_ includes a tool named adb.
Connect your device, and run::

    adb logcat

You'll see all the logs including your stdout/stderr, Kivy logger. 

You can also run and debug your application using the `Kivy Launcher`_.
If you run your application this way, you will find log files inside the 
"/.kivy/logs" sub-folder within your application folder.

Status of the Project
---------------------

The project is now stable, using `Python for Android
<http://github.com/kivy/python-for-android/>`_.

We made that project to be able to:

- create custom Python versions including only wanted modules
- handle multitouch events in Kivy
- create a python module for accessing features specific to Android
- handle sleep/wakeup properly

Tested Devices
--------------

These Android devices have been confirmed to work with Kivy. If your
device is not on the list, that does not mean that it is not supported.
If that is the case, please try running Kivy and if it succeeds, let us
know so that we can update this list. Note, however, that your device has
to support at least OpenGL 2.0 ES.

Phones
~~~~~~

- Motorola Droid 1
- Motorola Droid 2
- HTC Desire
- HTC Desire Z
- Xperia 10 (custom ROM 2.1 + GLES 2.0 support)
- LG Optimus S
- LG Optimus V
- Samsung Galaxy S (mostly works, seems to have some weird OpenGL behaviour, most notably the kivy splash screen doesn't work)
- Samsung Galaxy Note GT-N7000

Tablets
~~~~~~~

- Samsung Galaxy Tab
- Motorola Xoom
- Asus EeePad Transformer

