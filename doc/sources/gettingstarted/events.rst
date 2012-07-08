Events
------
.. container:: title

    Events in Kivy

Kivy is **event oriented**. The most basic events you will work with are: ::

    1. Clock events:
        - Repetitive events : X times per second using schedule_interval()
        - One-time event : schedule_once
        - Trigger events: called only once for the next frame
    2. Widget events :
        - Property events: if your widget changes its position or size, an event is fired
        - Widget-defined events: A Widget can define custom events
          Eg. on_press() and on_release() events in Button Widget
    3. Input events:
        - Touch events: There are three of these:
            - on_touch_down: which is dispatched at the beginning of a touch
            - on_touch_move: which is dispatched every time a touch is moving
            - on_touch_up: which is dispatched at the end of the touch
          Note** that all widgets get all of these events whatever their positions,
          allowing for the widgets to react to any event.
        - Keyboard events
            - system kayboard events (hard/soft keyboards)
            - virtual keyboard events (kivy provided virtual keyboard)

Another thing to **note** is that if you override an event, you become
responsible for implementing all its behaviour previously handled by the base class.
The easiest way to do this is to call *super*: ::

    def on_touch_down(self, touch):
        if super(OurClaseName, self).on_touch_down(touch):
            return True
        if not self.collide_point(touch.x, touch.y):
            return False
        print 'you touched me!'

Get more familiar with events by reading the `event <http://kivy.org/docs/guide/events.html#events>`_ documentation.

