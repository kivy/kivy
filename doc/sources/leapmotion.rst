LeapHand vs. LeapFinger Providers
---------------------------------

The :mod:`~kivy.input.providers.leapfinger` provider generates fine-grained
input based on each of thefingers tracked by the LeapMotion. Whilst powerful,
this provider requires the programmer to explicitly capture these events an
interpret them.

The :mod:`~kivy.input.providers.leaphand` provider, however, simulates a more
traditional pointing device in order to generate the standard
:meth:`~kivy.core.window.WindowBase.on_touch_down`,
:meth:`~kivy.core.window.WindowBase.on_touch_move` and
:meth:`~kivy.core.window.WindowBase.on_touch_up` events. It can therefore be
used as a drop-in alternative for touch screen and mouse input.

.. note::

    The LeapMotion input providers currently rely on V2 of the LeapMotion
    software drivers. We hope to update this soon to use newer bindings.
