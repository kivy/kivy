Events
------------
.. container:: title

    Events in Kivy

Kivy is **event oriented**. The most basic events you will work with are. ::

    1. Clock events:
        - Repetitive events : X times per second using schedule_interval()
        - One-time event : schedule_once
        - Trigger events: called only once for the next frame
    2. Widget events :
        - Property events: if your widget changes its position or size, an event is fired
        - Widget defined events: A Widget can define custom events
          Eg. on_press() and on_release() events in Button Widget
    3. Input events:
        - Touch events: There are three of them:
            - on_touch_down: which is dispatched at the begining of a touch
            - on_touch_move: which is dispatched every time a touch is moving
            - on_touch_up: which is dispatched when the end of the touch
          Note** that, all widgets get all of these events whatever there position,
          allowing for widget to react to any event
        -  Keyboard events

Another thing to **Note** is that if you override an event, you now become
responsible of implementing all it's behavoiur handled by the base class,
the easiest way to do that is to call **super** ::

    def on_touch_down(self, touch):
        if super(OurClaseName, self).on_touch_down(touch):
            return True
        if not self.collide_point(touch.x, touch.y):
            return False
        print 'you touched me!'

Get more familiar with events by reading the following `event <http://kivy.org/docs/guide/events.html#events>`_ documentation.

