Events
======

There are two types of events in Kivy:

- Clock events: if you want to call a function X times per second, or if you
  want to call a function later.
- Widget events: if you want to call a function when something changes in the
  widget, or attach a function to a widget specific event.


Clock events
------------

Before we discuss events, you need to know that Kivy has a main loop, and that
it's important that you avoid breaking it. The main loop is responsible for
reading from inputs, loading images asynchronously, drawing to the frame, etc.
If you are looping or sleeping, you'll break the main loop. As an example, the
following code does both::

    while True:
        animate_something()
        time.sleep(.10)

When you run this, the program will never exit your loop, preventing Kivy from
doing all of the other things that need doing. As a result, all you'll see is a
black window which you won't be able to interact with. You need to "schedule"
your ``animate_something()`` function call over time. You can do this in 2 ways:
a repetitive call or one-time call.

Scheduling a repetitive event
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can call a function or a method every X times per second using
:meth:`~kivy.clock.Clock.schedule_interval`. Here is an example of calling a
function named my_callback 30 times per second::

    def my_callback(dt):
        print 'My callback is called', dt
    Clock.schedule_interval(my_callback, 1 / 30.)

You have two ways of unscheduling a previously scheduled event. The first would be
to use :meth:`~kivy.clock.Clock.unschedule`::

    Clock.unschedule(my_callback)

Or, you can return False in your callback, and your event will be automatically
unscheduled::

    count = 0
    def my_callback(dt):
        global count
        count += 1
        if count == 10:
            print 'Last call of my callback, bye bye !'
            return False
        print 'My callback is called'
    Clock.schedule_interval(my_callback, 1 / 30.)


Scheduling a one-time event
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using :meth:`~kivy.clock.Clock.schedule_once`, you can call a function "later",
like in the next frame, or in X seconds::

    def my_callback(dt):
        print 'My callback is called !'
    Clock.schedule_once(my_callback, 1)

This will call ``my_calback`` in one second. The second argument is the amount
of time to wait before calling the function, in seconds. However, you can
achieve some other results with special values for the second argument:

- If X is greater than 0, the callback will be called in X seconds
- If X is 0, the callback will be called after the next frame
- If X is -1, the callback will be called before the next frame

The -1 is mostly used when you are already in a scheduled event, and if you
want to schedule a call BEFORE the next frame is happening.


Trigger events
~~~~~~~~~~~~~~

If you want to schedule a function to be called only once for the next frame,
like a trigger, you can achieve that like so::

    Clock.unschedule(my_callback)
    Clock.schedule_once(my_callback, 0)

This way of programming a trigger is expensive, since you'll always call
unschedule, whether or not you've even scheduled it. In addition, unschedule
needs to iterate the weakref list of the Clock in order to find your callback
and remove it. Use a trigger instead::

    trigger = Clock.create_trigger(my_callback)
    # later
    trigger()

Each time you call trigger, it will schedule a single call of your callback. If
it was already scheduled, it will not be rescheduled.




Widget events
-------------

A widget has 2 types of events:

- Property event: if your widget changes its position or size, an event is fired.
- Widget-defined event: an event will be fired for a Button when it's pressed or
  released.


Property event
~~~~~~~~~~~~~~

A widget has many properties. You'll find in the documentation that every property has a
type like :class:`~kivy.properties.NumericProperty`,
:class:`~kivy.properties.StringProperty`,
:class:`~kivy.properties.ListProperty`.

Usually, when you want to create a Python class with properties, you do something like this::

    class MyClass(object):
        def __init__(self):
            super(MyClass, self).__init__()
            self.prop1 = 'bleh'

Using this code though, you do not have a good way to know when ``prop1`` is
changed, except by rewriting the class and adding a hook in
``__getattribute__``. The Kivy way to do this is::

    class MyClass(Widget):
        prop1 = StringProperty('bleh')

You can connect a function to this property if you want to be called when the
value of the property changes::

    def my_callback(instance, value):
        print 'the widget', instance, 'prop1 changed to', value

    # create an instance of MyClass
    obj = MyClass()
    # and connect my_callback to prop1
    obj.bind(prop1=my_callback)
    # now change prop1 => it will call your callback !
    obj.prop1 = 'hello world'

If you want to stop receiving events from the ``prop1`` property, call unbind::

    obj.unbind(prop1=my_callback)


Widget-defined event
~~~~~~~~~~~~~~~~~~~~

Sometimes the property event is not enough to hook onto. For example, a Button
could have a state property that indicates whether the Button is currently
pressed or not. We made the choice to add additional events for this: the
:meth:`~kivy.uix.button.Button.on_press` and
:meth:`~kivy.uix.button.Button.on_release` events::

    def my_callback_press(instance):
        print 'The button', instance, 'is pressed'
    button = Button(text='Hello world')
    button.bind(on_press=my_callback_press)

Every event defined by a widget is in the documentation, at the start of the
class. You can find a list of widget-defined events that the widget supports.

If you are designing your own widget, you can create a widget event by using
:meth:`~kivy.event.register_event_type`::

    class MyClass(Widget):

        def __init__(self, **kwargs):
            self.register_event_type('on_custom_event')
            super(MyClass, self).__init__(**kwargs)

        def on_custom_event(self):
            # empty handler needed
            pass

Then, the user can hook to it, the same as to the Button.on_press event. In this
example,  the event is never dispatched. Let's just add a function demonstrating
how to dispatch a widget-defined event::

    class MyClass(Widget):

        # ... __init__ + on_custom_event

        def do_something(self):
            self.dispatch('on_custom_event')

Now, every time you call the ``do_something()`` method, it will dispatch
``on_custom_event``, and call every function attached to this event.
