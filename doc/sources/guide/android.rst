.. _Kivy Launcher: https://play.google.com/store/apps/details?id=org.kivy.pygame&hl=en
.. _android:

Kivy on Android
===============

Kivy runs on Android, but you need a phone with:

* SD Card
* OpenGL ES 2.0 (Android 2.2 minimum)

Requirements for an Android application
---------------------------------------

To create an application for the Android platform, you must have a
file named `main.py` in the root directory of your application.

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
- HTC HD2 with NexusHD2-ICS-CM9-HWA Rom (CyanogenMod 9.1.0 -stable-leo) Android 4.0.4
- HTC Desire
- HTC Desire Z
- HTC Desire HD (works with no issues when upgraded to 4.x roms, has random bugs with 2.3)
- HTC Desire SV (Kivy apps run, but there are issues running some apps via the
  Kivy Launcher)
- LG (Google) Nexus 4
- LG Optimus S
- LG Optimus V
- Motorola Droid 1
- Motorola Droid 2
- Micromax Canvas 2
- Samsung Galaxy S (mostly works, seems to have some weird OpenGL behaviour,
  most notably the kivy splash screen doesn't work)
- Samsumg Galaxy Pocket S5300
- Samsung Galaxy SII (I9100)
- Samsung Galaxy SIII (I9300)
- Samsung Galaxy S4 (I9500)
- Samsung Galaxy Note GT-N7000
- Samsung Galaxy Note (N7000)
- Samsung Galaxy Note II (N7100)
- Xperia 10 (custom ROM 2.1 + GLES 2.0 support)


Tablets
~~~~~~~
- Asus EeePad Transformer
- Asus (Google) Nexus 7 2013
- Motorola Xoom
- Samsung Galaxy Note 8.0” (N5100)
- Samsung Galaxy Note 10.1 (N8000) (Kivy Launcher does not install)
- Samsung Galaxy Tab (P1000)
- Samsung Galaxy Tab 7.0 Plus (P6200)
- Samsung Galaxy Tab 2 7.0 (P3100)
- Samsung Galaxy Tab 10.1” (P7500)

