Architectural Overview
======================

From a software engineering point of view, Kivy is a pretty well-designed product.
If you just look at the code, chances are you will get a rough idea already, but
since this approach certainly is daunting for most users, this section explains
the basic ideas of the implementation.


Core Providers and Input Providers
----------------------------------

One idea that is key to understanding Kivy's internals is that of modularity and
abstraction. We try to abstract from basic tasks such as opening a window,
displaying images and text, playing audio, getting images from a camera,
spelling correction and so on. We call these *core* tasks.
This makes the API both easy to use and easy to extend. Most importantly, it
allows us to use -- what we call -- specific providers for the respective
scenario in which your app is being run.
For example, on OSX, Linux and Windows, there are different native APIs for the
different core tasks. A piece of code that uses one of these specific APIs to
talk to the operating system on one side and to Kivy on the other (acting as an
intermediate communication layer) is what we call a *core provider*.
The advantage of using specialized core providers for each platform is that we
can fully leverage the functionality exposed by the operating system and act as
efficiently as possible. It also gives users a choice. Furthermore, by using
libraries that are shipped with any one platform, we effectively reduce the size
of the Kivy distribution and make packaging easier. It's also easier to port
Kivy to other platforms. The Android port did greatly benefit from this.

We follow the same concept with input handling. *An input provider* is a piece
of code that adds support for a specific input device, such as Apple's
trackpads, TUIO or a mouse emulator.
If you need to add support for a new input device, you can simply provide a new
class that reads your input data from your device and transforms them into Kivy
basic events.


Input Events (Touches)
----------------------

Kivy abstracts from different input types and sources such as touches, mice,
TUIO or similar. What all of these input types have in common is that you
can associate a 2D onscreen-position with any individual input event. (There are
other input devices such as accelerometers where you cannot easily find a
2D position for e.g. a tilt of your device. This kind of input is handled
separately. In the following we describe the former types.)

All of these input types are represented by instances of the Touch()
class. (Note that this does not only refer to finger touches, but all the other
input types as well. We just called it *Touch* for the sake of simplicity.
Think of it of something that *touches* the user interface or your screen.)
A touch instance, or object, can be in one of three states. When a touch
enters one of these states, your program is informed that the event
occurred.
The three states a touch can be in are:

    Down
        A touch is down only once, at the very moment where it first
        appears.
    Move
        A touch can be in this state for a potentially unlimited time.
        A touch does not have to be in this state during its lifetime.
        A 'Move' happens whenever the 2D position of a touch changes.
    Up
        A touch goes up at most once, or never.
        In practice you will almost always receive an up event because
        nobody is going to hold a finger on the screen for all eternity,
        but it is not guaranteed. If you know the input sources your users
        will be using, you will know whether or not you can rely on this
        state being entered.


Widgets and Event Dispatching
-----------------------------

The term *widget* is often used in GUI programming contexts to describe
some part of the program that the user interacts with.
For Kivy, a widget is an object that receives input events. It does not
necessarily have to have a visible representation on the screen.
All widgets are arranged in a *widget tree* (which is a tree data structure
as known from computer science classes): One widget can have any number of
child widgets or none. There is exactly one *root widget* at the top of the
tree that has no parent widget, and all other widgets are directly or
indirectly children of this widget (which is why it's called the root).

When new input data is available, Kivy sends out one event per touch.
The root widget of the widget tree first receives the event.
Depending on the state of the touch, the on_touch_down,
on_touch_move or on_touch_up event is dispatched (with the touch as the
argument) to the root widget, which results in the root widget's
corresponding on_touch_down, on_touch_move or on_touch_up event handler
being called.

Each widget (this includes the root widget) in the tree can choose to
either digest or pass the event further. If an event handler returns True
it means that the event has been digested and handled properly. No further
processing will happen with that event. Otherwise, the event handler
passes the widget on to its own children by calling its superclass's
implementation of the respective event handler. This goes all the way up
to the base Widget class, which -- in its touch event handlers -- does
nothing but pass the touches to its children::

    def on_touch_down(self, touch): # This is the same for move/up
        for child in reversed(self.children[:]):
            if child.dispatch('on_touch_down', touch):
                return True

This really is much easier than it first seems. Let's take a look at a
simple example. If you want to implement a line drawing program, you will
want to know when a touch starts, moves and ends. You keep track of the
touch's positions and draw a line through those points::

    TODO PAINTER WIDGET

As you can see, this widget does not really care where the touch occurred.
Often times you will want to restrict the *area* on the screen that a
widget watches for touches. You can use a widget's collide_point() method
to achieve this. You simply pass it the touches position and it returns
True if the touch is within the 'watched area' or False otherwise. By
default, this checks the rectangular region on the screen that's described
by the widget's pos (for position; x & y) and size (width & height), but
you can override this behaviour in your own class.

