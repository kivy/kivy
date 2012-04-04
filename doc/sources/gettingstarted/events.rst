Touch events
------------

Kivy is event oriented, this mean your widgets will get events and you will be able to respond to them. The most basic events you will work with are touch events, there are three of them:

on_touch_down: which is dispatched at the begining of a touch
on_touch_move: which is dispatched every time a touch is moving
on_touch_up: which is dispatched when the end of the touch

An important note is that all widgets get all of these events whatever there position, it's useful as this allow for widget to react to any event, but most of the time you want to check the position of the event when you get it.

    def on_touch_down(self, touch, \*args):
        # test if the event is on us
        if self.collide_point(\*touch.pos):
            print "I got touched!"

Another thing to understand is that if you handle an event, you become responsible of its dispatching, the easiest way to do that is to use the Widget on_touch_ method, thanks to super(), which propagate to all children until one of them return a non-false value.

    def on_touch_down(self, touch, \*args):
        # test if the event is on us
        if self.collide_point(\*touch.pos):
            print "I got touched!"
            return True # propagatior will stop
        else:
            return super(OurClass, self).on_touch_down(touch, \*args)

Note that the touch object passed to all these callbacks is the same for all events associated with one touch, so you can keep information in it, the best place to do so is in the `ud` member, of the touch.

    def on_touch_down(self, touch, \*args):
        touch.ud['moves'] = 0
        return super(OurClass. self).on_touch_down(touch, \*args)

    def on_touch_move(self, touch, \*args):
        touch['moves'] += 1
        return super(OurClass. self).on_touch_move(touch, \*args)

    def on_touch_up(self, touch, \*args):
        print "this event got %s moves" % touch.ud['moves']
        return super(OurClass. self).on_touch_up(touch, \*args)


If you want to be sure the following events of a touch will be dispatched to you no matter what (for example it moves out of your parent zone, which stops dispatching it, but you need to react to the end of the touch), you can grab it, that doesn't mean you'll be the only one to get it, that means you'll get _at least_ on time each event associated to this touch.

    class OurWidget(Widget):
        def on_touch_down(self, touch, \*args):
            touch.grab(self)
            return super(OurClass, self).on_touch_down(touch, \*args)

    def on_touch_up(self, touch, \*args):
        if touch.current_grab == self:
            print "got this dipatch because of the grab"
        else:
            print "got this dispatch throught parent dispatching"
            return super(OurClass, self).on_touch_down(touch, \*args)

Lastly touch events have a lot of information bundled inside them, about time, position (as seen earlier), about the device that produce them and so on, it's useful to look at the %
`touch_event` documentation.

