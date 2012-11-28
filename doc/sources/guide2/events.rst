.. _events:
.. _properties:

Events and Properties
=====================

Events are a big part of kivy programming, that may not be surprising to those
having done GUI development before, but it's an important concept to get for
newcomers, and the specifics of how to use these in kivy. Once you understand
how events and ways to bind to them, are everywhere in kivy, it becomes easy to
build about whatever you want with kivy.

Introduction to Event Dispatcher
--------------------------------

One of the most important base classes of the framework is the
:class:`kivy.event.EventDispatcher` class, this class allows to register event
types, and to dispatch them to interested parties (usually other event
dispatchers). :class:`kivy.uix.widget.Widget`,
:class:`kivy.animation.Animation` and :obj:`kivy.clock.Clock` for example are
event dispatchers.

Creating custom events
----------------------

To create an event dispatcher with custom events, you need to register the name
of the event in the class, and to create a method of the same name.

See the following example::

    class MyEventDispatcher(EventDispatcher):
        def __init__(self, **kwargs):
            self.register_event_type('on_test')
            super(MyEventDispatcher, self).__init__(**kwargs)

        def do_something(self, value):
            # when test is called, the 'on_test' event will be
            # dispatched with the value
            self.dispatch('on_test', value)

        def on_test(self):
            pass


Attaching callbacks
-------------------

To use events, you have to bind callbacks to them, when the event is
dispatched, your callbacks will be called with the various data the event has
to pass around.

A callback can be any python callable, but you need to be sure it can accept
the arguments the event will use, for this, it's usually safer to accept the
`*args` argument, that will catch any remaining arguments in the `args` list.

Example::

    def my_callback(value, *args):
        print "Hello, I got an event!", value


    ev = MyEventDispatcher()
    ev.bind(on_test=my_callback)
    ev.test('test')


Introduction to properties
--------------------------

Properties are an awesome way to define events and bind to them, it basically
produce events when the attributes to your object changes, so you can bind
actions to the change of these values.

There are different kind of properties to describe the type of data you want to
describe.

- :class:`kivy.properties.StringProperty`
- :class:`kivy.properties.NumericProperty`
- :class:`kivy.properties.ObjectProperty`
- :class:`kivy.properties.ListProperty`
- :class:`kivy.properties.ObjectProperty`
- :class:`kivy.properties.AliasProperty`

Declaration of a Property
-------------------------

To declare a property, you must create it at class level, the class will do the
work to instantiate the real attributes when the object will be created, the
properties is not the attribute, it's a mechanism to create events for your
attributes::

    class MyWidget(Widget):
        text = StringProperty('')


If you override `__init__`, *always* accept `**kwargs` and use super() to call
parent's `__init__` with it::

        def __init__(self, **kwargs):
            super(MyWidget, self).__init__(**kwargs)


Dispatching a Property event
----------------------------
