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
regardless of the platform or operating system.

For instance, the following code would make your Android device
vibrate, or raise a NotImplementedError that you can handle
appropriately on other platforms such as desktops that don't have
appropriate hardware:::

    from plyer import vibrator
    vibrator.vibrate(10)  # vibrate for 10 seconds

Plyer's list of supported APIs is growing quite quickly, you can see
the full list in the Plyer `README <https://github.com/kivy/plyer>`_.

