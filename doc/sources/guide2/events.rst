.. _events:
.. _properties:

Events and Properties
=====================

Events are a big part of kivy programming, that may not be surprising to those
having done GUI development before, but it's an important contept to get to
newcomers, and the specificies of how to use these in kivy. Once you understand
how events and ways to bind to these, are everywhere in kivy, it becomes easy
to build about whatever you want with kivy.

Introduction to Event Dispatcher
--------------------------------

One of the most important base class of the framework is the
`:cls:kivy.event.EventDispatcher` class, this class allows to register event
types, and to dispatch them to interrested parties (usually other event
dispatchers). `:cls:kivy.uix.widget.Widget`, `:cls:kivy.animation.Animation`
and `:obj:kivy.clock.Clock` for example are event dispatchers.

Creating custom events
----------------------

To create an event dispatcher with custom events, you need to register
the name of the event in the class, and to create a method of the same
name.

See the following example::

    class MyEventDispatcher(EventDispatcher):
        def __init__(self, **kwargs):
            super(MyEventDispatcher, self).__init__(**kwargs)
            self.register_event_type('on_test')

        def test(self, value):
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

example::

    def my_callback(value, *args):
        print "Hello, I got an event!", value


    ev = MyEventDispatcher()
    ev.bind(on_test=my_callback)
    ev.test('test')


Introduction to properties
--------------------------

Declaration of a Property
-------------------------

Dispatching a Property event
----------------------------
