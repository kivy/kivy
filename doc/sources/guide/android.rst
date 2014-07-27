.. _Kivy Launcher: https://play.google.com/store/apps/details?id=org.kivy.pygame&hl=en
.. _android:

Kivy on Android
===============

You can run Kivy applications on Android, on (more or less) any device
with OpenGL ES 2.0 (Android 2.2 minimum). This is standard on modern
devices; Google reports the requirement is met by `99.9% of devices
<https://developer.android.com/about/dashboards/index.html>`_.

Kivy APKs are normal Android apps that you can distribute like any
other, including on stores like the Play store.

Follow the instructions below to learn how to :ref:`package your app
for Android <package_for_android>`.

.. _package_for_android:

Package for Android
-------------------

The Kivy project provides all the necessary tools to package your app
on Android, including building your own standalone APK that may be
distributed on a market like the Play store. This is covered fully in
the :ref:`packaging_android` documentation.


.. _debug_android:

Debugging your application on the Android platform
--------------------------------------------------

You can view the normal output of your code (stdout, stderr), as well
as the normal Kivy logs, through the Android logcat stream. This is
accessed through adb, provided by the `Android SDK
<http://developer.android.com/sdk/index.html>`_. You may need to
enable adb in your device's developer options, then connect your device
to your computer and run::

    adb logcat

You'll see all the logs including your stdout/stderr and Kivy
logger.

If you packaged your app with Buildozer, the `adb` tool may not be in
your :code:`$PATH` and the above command may not work. You can instead run
:code:`buildozer logcat` to run the version installed by Buildozer, or
find the SDK tools at
:code:`$HOME/.buildozer/android/platform`.

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
- Kindle Fire 2nd generation
- Motorola Xoom
- Samsung Galaxy Note 8.0” (N5100)
- Samsung Galaxy Note 10.1 (N8000) (Kivy Launcher does not install)
- Samsung Galaxy Tab (P1000)
- Samsung Galaxy Tab 7.0 Plus (P6200)
- Samsung Galaxy Tab 2 7.0 (P3100)
- Samsung Galaxy Tab 10.1” (P7500)

