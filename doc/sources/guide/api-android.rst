.. _api_android:

Using Android APIs
==================

Although Kivy is a Python framework, the Kivy project maintains tools
to easily use the normal java APIs, for everything from vibration to
sensors to sending messages through SMS or email.

For new users, we recommend using :ref:`Plyer`. For more advanced
access or for APIs not currently wrapped, you can use :ref:`Pyjnius`
directly.

.. _plyer:

Plyer
-----

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
-------

Pyjnius is a Python module that lets you access java classes directly
from Python, automatically converting arguments to the right type, and
letting you easily convert the java results to Python.

Pyjnius can be obtained from `github
<https://github.com/kivy/pyjnius>`_, and has its `own documentation
<http://pyjnius.readthedocs.org/en/latest/>`__.

Here is a simple example showing pyjnius' ability to access
the normal Android vibration API, the same result of the plyer code
above::

    from jnius import PythonJavaClass, java_method, autoclass, cast

    # 'autoclass' takes a java class and gives it a Python wrapper
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
vibrator, with pyjnius automatically translating the api to Python
code and our calls back to the equivalent java. It is much more
verbose and java-like than Plyer's version, for no benefit in this
case, though Plyer does not wrap every API available to pyjnius.

Pyjnius also has powerful abilities to implement java interfaces,
which is important for wrapping some APIs, but these are not
documented here - you can see pyjnius' `own documentation
<<http://pyjnius.readthedocs.org/en/latest/>`__.
