Events
------

Kivy is mostly event-based, that's mean the flow of the program is determined
by events.

**Clock events**

.. image:: ../images/gs-events-clock.png
    :class: gs-eleft

The :doc:`/api-kivy.clock` allows you to schedule a function call in the
future, as a one-time event with :meth:`~kivy.clock.ClockBase.schedule_once`,
or as a repetitive event with :meth:`~kivy.clock.ClockBase.schedule_interval`.

You can also create Triggered events with
:meth:`~kivy.clock.ClockBase.create_trigger`, multiple call to a trigger will
schedule a function call only once.

**Input events**

.. image:: ../images/gs-events-input.png
    :class: gs-eleft

All the mouses click, touchs, scroll wheel are part of the
:class:`~kivy.input.motionevent.MotionEvent`, extended by
:doc:`/api-kivy.input.postproc`, dispatched through the `on_motion` in
:class:`~kivy.core.window.Window`, then in the
:meth:`~kivy.uix.widget.Widget.on_touch_down`,
:meth:`~kivy.uix.widget.Widget.on_touch_move`,
:meth:`~kivy.uix.widget.Widget.on_touch_up` in :class:`~kivy.uix.widget.Widget`

For an in-depth explaination, have a look at :doc:`/api-kivy.input`.

**Class events**

.. image:: ../images/gs-events-class.png
    :class: gs-eleft

Our base class :class:`~kivy.event.EventDispatcher`, used by
:class:`~kivy.uix.widget.Widget`, use the power of ours
:doc:`/api-kivy.properties` for dispatching changes. IE, when a widget changes
its position or size, an event is fired.

In addition, you have the possibility to create your own event using
:meth:`~kivy.event.EventDispatcher.register_event_type`, as the
`on_press`/`on_release` in :class:`~kivy.uix.button.Button`.

Another thing to note is that if you override an event, you become responsible
for implementing all its behaviour previously handled by the base class. The
easiest way to do this is to call `super()`::

    def on_touch_down(self, touch):
        if super(OurClassName, self).on_touch_down(touch):
            return True
        if not self.collide_point(touch.x, touch.y):
            return False
        print 'you touched me!'
        return True

Get more familiar with events by reading the :doc:`/guide/events` documentation.

