Events
------

Kivy is mostly `event-based <http://en.wikipedia.org/wiki/Event-driven_programming>`_, meaning the flow of the program is determined
by events.

**Clock events**

.. image:: ../images/gs-events-clock.png
    :class: gs-eleft

The :doc:`/api-kivy.clock` allows you to schedule a function call in the
future, as a one-time event with :meth:`~kivy.clock.ClockBase.schedule_once`,
or as a repetitive event with :meth:`~kivy.clock.ClockBase.schedule_interval`.

You can also create Triggered events with
:meth:`~kivy.clock.ClockBase.create_trigger`. Triggers have the advantage of
being called only once per frame, even if you have scheduled multiple triggers
for the same callback.

**Input events**

.. image:: ../images/gs-events-input.png
    :class: gs-eleft

All the mouse click, touch and scroll wheel events are part of the
:class:`~kivy.input.motionevent.MotionEvent`, extended by
:doc:`/api-kivy.input.postproc` and dispatched through the `on_motion` event in
the :class:`~kivy.core.window.Window` class. This event then generates the
:meth:`~kivy.uix.widget.Widget.on_touch_down`,
:meth:`~kivy.uix.widget.Widget.on_touch_move` and
:meth:`~kivy.uix.widget.Widget.on_touch_up` events in the
:class:`~kivy.uix.widget.Widget`.

For an in-depth explanation, have a look at :doc:`/api-kivy.input`.

**Class events**

.. image:: ../images/gs-events-class.png
    :class: gs-eleft

Our base class :class:`~kivy.event.EventDispatcher`, used by
:class:`~kivy.uix.widget.Widget`, uses the power of our
:doc:`/api-kivy.properties` for dispatching changes. This means when a widget
changes its position or size, the corresponding event is automatically fired.

In addition, you have the ability to create your own events using
:meth:`~kivy.event.EventDispatcher.register_event_type`, as the
`on_press` and `on_release` events in the :class:`~kivy.uix.button.Button`
widget demonstrate.

Another thing to note is that if you override an event, you become responsible
for implementing all its behaviour previously handled by the base class. The
easiest way to do this is to call `super()`::

    def on_touch_down(self, touch):
        if super(OurClassName, self).on_touch_down(touch):
            return True
        if not self.collide_point(touch.x, touch.y):
            return False
        print('you touched me!')
        return True

Get more familiar with events by reading the :doc:`/guide/events` documentation.

