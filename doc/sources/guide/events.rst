Events
======

You have 2 types of events living in Kivy:

- Clock events: if you want to call a function X times per seconds, or if you
  want to call a function later.
- Widget events: if you want to call a function where something change in the
  widget, or attach a function to a widget specific event.


Clock events
------------

Before starting the event part, Kivy have a main loop, and must avoid to break
it. The main loop is responsible to read all the inputs, load images
asynchronously, draw the frame etc. If you are looping yourself or sleeping
somewhere, you'll break the main loop. For example, here is the biggest mistake
done::

    while True:
        animate_something()
        time.sleep(.10)

This is wrong. Because you'll never go out of your loop, and you'll see a black
window, no more interaction. You need to "schedule" the call of your function
over the time. You can schedule it in 2 way: repetitive call or one-time call.

Scheduling an repetitive event
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can call a function or a method every X times per seconds using
:meth:`~kivy.clock.Clock.schedule_interval`. Here is an example of calling a
function named my_callback 30 times per seconds::

    def my_callback(dt):
        print 'My callback is called', dt
    Clock.schedule_interval(my_callback, 1 / 30.)

You have 2 ways of unschedule a previously scheduled event. The first would be
to use :meth:`~kivy.clock.Clock.unschedule`::

    Clock.unschedule(my_callback)

Or, you can return False in your callback, and your event will be automatically
unschedule::

    count = 0
    def my_callback(dt):
        global count
        count += 1
        if count == 10:
            print 'Last call of my callback, bye bye !'
            return False
        print 'My callback is called'
    Clock.schedule_interval(my_callback, 1 / 30.)


Scheduling an one-time call event
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometime, you can to call a function "later", like in the next frame, or in X
seconds. Use :meth:`~kivy.clock.Clock.schedule_once`::

    def my_callback(dt):
        print 'My callback is called !'
    Clock.schedule_once(my_callback, 1)

This will call the callback one second after. The second argument is the time
to call the function, but you have achieve tiny tricks here :

- If it's more than 0, the callback will be called in the X seconds
- If it's 0, the callback will be called in the next frame, before the drawing
- If it's -1, the callback will be called before the drawing, if the clock is
  not overflooded

The -1 is mostly used when you are already is a scheduled event, and if you
want to schedule a call BEFORE the next frame is happening.


Trigger events
~~~~~~~~~~~~~~

If you want to have schedule a call only "one time" for the next frame, the
trigger events is for you. Before, triggering can be achieve with::

    Clock.unschedule(my_callback)
    Clock.schedule_once(my_callback, 0)

That way of doing trigger is expensive, because you'll always call unschedule
whatever if the event is already scheduled or not. In addition, it need to
iterate into the weakref list of the Clock to found your callback, and remove
it. Don't do that. Use trigger::

    trigger = Clock.create_trigger(my_callback)
    # later
    trigger()

Each time you'll call trigger, it will schedule a call of your callback, only
one. If the schedule was already done, it will be ignored.




Widget events
-------------

A widget have 2 types of events:

- Property event: if your widget change of pos or size, you'll have an event
  fired
- Widget defined event: a Button will have even fired when it's pressed or
  released.


Property event
~~~~~~~~~~~~~~

A widget have many property. You'll find in the doc that every property have a
type like :class:`~kivy.properties.NumericProperty`,
:class:`~kivy.properties.StringProperty`,
:class:`~kivy.properties.ListProperty`.

Usualy, when you want to create a Python class with properties, you'll do something like this::

    class MyClass(object):
        def __init__(self):
            super(MyClass, self).__init__()
            self.prop1 = 'bleh'

By doing that, you have not a good way to know when the prop1 is changed,
except by rewriting the class and hook the __getattribute__. But we'll not get
into details here. The Kivy way is that::

    class MyClass(Widget):
        prop1 = StringProperty('bleh')

You can connect a function to that property if you willing to be called when
the value of the property change::

    def my_callback(instance, value):
        print 'the widget', instance, 'prop1 changed to', value

    # create an instance of MyClass
    obj = MyClass()
    # and connect my_callback to prop1
    obj.bind(prop1=my_callback)
    # now change prop1 => it will call your callback !
    obj.prop1 = 'hello world'

If you want to resign of receiving event from prop1 property, call unbind::

    obj.unbind(prop1=my_callback)


Widget defined event
~~~~~~~~~~~~~~~~~~~~

Sometime, the properties event is not enought to hook on it. For example, a
Button can have a state property that will indicate if the Button is currently
pressed or not ("down " or "normal" actually). We make the choice to add
additionnals event for that: :meth:`~kivy.uix.button.Button.on_press` and
:meth:`~kivy.uix.button.Button.on_release` event::

    def my_callback_press(instance):
        print 'The button', instance, 'is pressed'
    button = Button(text='Hello world')
    button.bind(on_press=my_callback_press)

Every widget defined event are in the documentation, at the start of the widget
class. You can find a list of widget defined event that the widget support.

If are designing your own widget, you can create your own widget event by using the :meth:`~kivy.event.register_event_type`::

    class MyClass(Widget):

        def __init__(self, **kwargs):
            self.register_event_type('on_custom_event')
            super(MyClass, self).__init__(**kwargs)

        def on_custom_event(self):
            # empty handler needed
            pass

Then, the user can hook on it, same as the Button.on_press event. But the event
is never dispatched here. Let's just add a function for demonstrating how to
dispatch a widget defined event::

    class MyClass(Widget):

        # ... __init__ + on_custom_event

        def do_something(self):
            self.dispatch('on_custom_event')

Now, everytime you'll call do_something() method, it will dispatch
on_custom_event, and call every function attached to this event.
