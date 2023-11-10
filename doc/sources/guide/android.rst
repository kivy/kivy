.. _android:

Kivy on Android
===============

You can run Kivy applications on Android, on (more or less) any device
with OpenGL ES 2.0 (Android 2.2 minimum). This is standard on modern
devices; Google reports the requirement is met by `99.9% of devices
<https://developer.android.com/about/dashboards/index.html>`_.

Kivy APKs are normal Android apps that you can distribute like any
other, including on stores like the Google Play Store. They behave
properly when paused or restarted, may utilise Android services and
have access to most of the normal java API as described below.

Follow the instructions below to learn how to :ref:`package your app
for Android <package_for_android>`, :ref:`debug your code on the
device <debug_android>`, and :ref:`use Android APIs
<using_android_apis>` such as for vibration and reading sensors.

.. _package_for_android:

Package for Android
-------------------

The Kivy project provides all the necessary tools to package your app
on Android, including building your own standalone APK or AAB that may be
distributed on a market like the Google Play Store.
This is covered fully in the :ref:`packaging_android` documentation.


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
your :code:`$PATH` and the above command may not work. You can instead run::

    buildozer android logcat

to run the version installed by Buildozer, or
find the SDK tools at
:code:`$HOME/.buildozer/android/platform`.

You can also run and debug your application using the Kivy Launcher.
If you run your application this way, you will find log files inside the
"/.kivy/logs" sub-folder within your application folder.


.. _using_android_apis:

Using Android APIs
------------------

Although Kivy is a Python framework, the Kivy project maintains tools
to easily use the normal java APIs, for everything from vibration to
sensors to sending messages through SMS or email.

For new users, we recommend using :ref:`Plyer`. For more advanced
access or for APIs not currently wrapped, you can use :ref:`Pyjnius`
directly. Kivy also supplies an :ref:`android module
<android_module>` for basic Android functionality.

User contributed Android code and examples are available on the
`Kivy wiki <https://github.com/kivy/kivy/wiki#mobiles>`_.

.. _plyer:

Plyer
~~~~~

`Plyer <https://github.com/kivy/plyer>`__ is a pythonic,
platform-independent API to use features commonly found on various
platforms, particularly mobile ones. The idea is that your app can
call simply call a Plyer function, such as to present a notification
to the user, and Plyer will take care of doing so in the right way
regardless of the platform or operating system. Internally, Plyer uses
Pyjnius (on Android), Pyobjus (on iOS) and some platform specific APIs
on desktop platforms.

For instance, the following code would make your Android device
vibrate, or raise a NotImplementedError that you can handle
appropriately on other platforms such as desktops that don't have
appropriate hardware:::

    from plyer import vibrator
    vibrator.vibrate(10)  # vibrate for 10 seconds

Plyer's list of supported APIs is growing quite quickly, you can see
the full list in the Plyer `README <https://github.com/kivy/plyer>`_.


.. _pyjnius:

Pyjnius
~~~~~~~

Pyjnius is a Python module that lets you access java classes directly
from Python, automatically converting arguments to the right type, and
letting you easily convert the java results to Python.

Pyjnius can be obtained from `github
<https://github.com/kivy/pyjnius>`_, and has its `own documentation
<http://pyjnius.readthedocs.org/en/latest/>`__.

Here is a simple example showing Pyjnius' ability to access
the normal Android vibration API, the same result of the plyer code
above::

    # 'autoclass' takes a java class and gives it a Python wrapper
    from jnius import autoclass

    # Context is a normal java class in the Android API
    Context = autoclass('android.content.Context')

    # PythonActivity is provided by the Kivy bootstrap app in python-for-android
    PythonActivity = autoclass('org.renpy.android.PythonActivity')

    # The PythonActivity stores a reference to the currently running activity
    # We need this to access the vibrator service
    activity = PythonActivity.mActivity

    # This is almost identical to the java code for the vibrator
    vibrator = activity.getSystemService(Context.VIBRATOR_SERVICE)

    vibrator.vibrate(10000)  # The value is in milliseconds - this is 10s

This code directly follows the java API functions to call the
vibrator, with Pyjnius automatically translating the api to Python
code and our calls back to the equivalent java. It is much more
verbose and java-like than Plyer's version, for no benefit in this
case, though Plyer does not wrap every API available to Pyjnius.

Pyjnius also has powerful abilities to implement java interfaces,
which is important for wrapping some APIs, but these are not
documented here - you can see Pyjnius' `own documentation
<http://pyjnius.readthedocs.org/en/latest/>`__.

.. _android_module:

Android module
~~~~~~~~~~~~~~

Python-for-android includes a python module (actually cython wrapping
java) to access a limited set of Android APIs. This has been largely
superseded by the more flexible Pyjnius and Plyer as above, but may
still occasionally be useful. The available functions are given in the
`python-for-android documentation
<http://python-for-android.readthedocs.org/en/latest/>`_.

This includes code for billing/IAP and creating/accessing Android
services, which is not yet available in the other tools above.

Status of the Project and Tested Devices
----------------------------------------

These sections previously described the existence of Kivy's Android
build tools, with their limitations and some devices that were known
to work.

The Android tools are now quite stable, and should work with
practically any device; our minimum requirements are OpenGL ES
2.0 and Android 2.2. These are very common now - Kivy has
even been run on an Android smartwatch!

As Kivy works fine on most devices, the list of supported
phones/tablets has been retired - all Android devices are likely to
work if they meet the conditions above.

