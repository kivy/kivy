'''
Interactive launcher
====================

.. versionadded:: 1.3.0

.. deprecated:: 1.10.0
    The interactive launcher has been deprecated.

The :class:`InteractiveLauncher` provides a user-friendly python shell
interface to an :class:`App` so that it can be prototyped and debugged
interactively.

.. note::

    The Kivy API intends for some functions to only be run once or before the
    main EventLoop has started. Methods that can normally be called during the
    course of an application will work as intended, but specifically overriding
    methods such as :meth:`on_touch` dynamically leads to trouble.

Creating an InteractiveLauncher
-------------------------------

Take your existing subclass of :class:`App` (this can be production code) and
pass an instance to the :class:`InteractiveLauncher` constructor. ::

    from kivy.interactive import InteractiveLauncher
    from kivy.app import App
    from kivy.uix.button import Button

    class MyApp(App):
        def build(self):
            return Button(text='Hello Shell')

    launcher = InteractiveLauncher(MyApp())
    launcher.run()

After pressing *enter*, the script will return. This allows the interpreter to
continue running. Inspection or modification of the :class:`App` can be done
safely through the InteractiveLauncher instance or the provided
:class:`SafeMembrane` class instances.

.. note::

    If you want to test this example, start Python without any file to have
    already an interpreter, and copy/paste all the lines. You'll still have the
    interpreter at the end + the kivy application running.

Interactive Development
-----------------------

IPython provides a fast way to learn the Kivy API. The :class:`App` instance
and all of it's attributes, including methods and the entire widget tree,
can be quickly listed by using the '.' operator and pressing 'tab'. Try this
code in an Ipython shell. ::

    from kivy.interactive import InteractiveLauncher
    from kivy.app import App
    from kivy.uix.widget import Widget
    from kivy.graphics import Color, Ellipse

    class MyPaintWidget(Widget):
        def on_touch_down(self, touch):
            with self.canvas:
                Color(1, 1, 0)
                d = 30.
                Ellipse(pos=(touch.x - d/2, touch.y - d/2), size=(d, d))


    class TestApp(App):
        def build(self):
            return Widget()


    i = InteractiveLauncher(TestApp())
    i.run()
    i.       # press 'tab' to list attributes of the app
    i.root.  # press 'tab' to list attributes of the root widget

    # App is boring. Attach a new widget!
    i.root.add_widget(MyPaintWidget())

    i.safeIn()
    # The application is now blocked.
    # Click on the screen several times.
    i.safeOut()
    # The clicks will show up now

    # Erase artwork and start over
    i.root.canvas.clear()

.. note::

    All of the proxies used in the module store their referent in the
    :attr:`_ref` attribute, which can be accessed directly if needed, such as
    for getting doc strings. :func:`help` and :func:`type` will access the
    proxy, not its referent.

Directly Pausing the Application
--------------------------------

Both the :class:`InteractiveLauncher` and :class:`SafeMembrane` hold internal
references to the :class:`EventLoop`'s 'safe' and 'confirmed'
:class:`threading.Event` objects. You can use their safing methods to control
the application manually.

:meth:`SafeMembrane.safeIn` will cause the application to pause and
:meth:`SafeMembrane.safeOut` will allow a paused application
to continue running. This is potentially useful for scripting actions into
functions that need the screen to update etc.

.. note::

    The pausing is implemented via the
    :class:`Clocks' <kivy.clock.Clock>`
    :meth:`~kivy.clock.ClockBase.schedule_once` method
    and occurs before the start of each frame.

Adding Attributes Dynamically
-----------------------------

.. note::

    This module uses threading and object proxies to encapsulate the running
    :class:`App`. Deadlocks and memory corruption can occur if making direct
    references inside the thread without going through the provided proxy(s).

The :class:`InteractiveLauncher` can have attributes added to it exactly like a
normal object and if these were created from outside the membrane, they will
not be threadsafe because the external references to them in the python
interpreter do not go through InteractiveLauncher's membrane behavior,
inherited from :class:`SafeMembrane`.

To threadsafe these external references, simply assign them to
:class:`SafeMembrane` instances of themselves like so::

    from kivy.interactive import SafeMembrane

    interactiveLauncher.attribute = myNewObject
    # myNewObject is unsafe
    myNewObject = SafeMembrane(myNewObject)
    # myNewObject is now safe. Call at will.
    myNewObject.method()

TODO
====

Unit tests, examples, and a better explanation of which methods are safe in a
running application would be nice. All three would be excellent.

Could be re-written with a context-manager style i.e. ::

    with safe:
        foo()

Any use cases besides compacting code?

'''

__all__ = ('SafeMembrane', 'InteractiveLauncher')

import inspect
from threading import Thread, Event

from kivy.app import App
from kivy.base import EventLoop
from kivy.clock import Clock
from kivy.utils import deprecated


def safeWait(dt):
    EventLoop.confirmed.set()
    EventLoop.safe.wait()
    EventLoop.confirmed.clear()


def unwrap(ob):
    while type(ob) == SafeMembrane:
        ob = ob._ref
    return ob


class SafeMembrane(object):
    '''
    This help is for a proxy object. Did you want help on the proxy's referent
    instead? Try using help(<instance>._ref)

    The SafeMembrane is a threadsafe proxy that also returns attributes as new
    thread-safe objects
    and makes thread-safe method calls, preventing thread-unsafe objects
    from leaking into the user's environment.
    '''

    __slots__ = ('_ref', 'safe', 'confirmed')

    def __init__(self, ob, *args, **kwargs):
        self.confirmed = EventLoop.confirmed
        self.safe = EventLoop.safe
        self._ref = ob

    def safeIn(self):
        """Provides a thread-safe entry point for interactive launching."""
        self.safe.clear()
        Clock.schedule_once(safeWait, -1)
        self.confirmed.wait()

    def safeOut(self):
        """Provides a thread-safe exit point for interactive launching."""
        self.safe.set()

    def isMethod(self, fn):
        return inspect.ismethod(fn)

    # Everything from this point on is just a series of thread-safing proxy
    # methods that make calls against _ref and threadsafe whenever data will be
    # written to or if a method will be called. SafeMembrane instances should
    # be unwrapped whenever passing them into the thread
    # use type() to determine if an object is a SafeMembrane while debugging
    def __repr__(self):
        return self._ref.__repr__()

    def __call__(self, *args, **kw):
        self.safeIn()
        args = list(map(unwrap, args))
        for k in list(kw.keys()):
            kw[k] = unwrap(kw[k])
        r = self._ref(*args, **kw)
        self.safeOut()
        if r is not None:
            return SafeMembrane(r)

    def __getattribute__(self, attr, oga=object.__getattribute__):
        if attr.startswith('__') or attr == '_ref':
            subject = oga(self, '_ref')
            if attr == '_ref':
                return subject
            return getattr(subject, attr)
        return oga(self, attr)

    def __getattr__(self, attr, oga=object.__getattribute__):
        r = getattr(oga(self, '_ref'), attr)
        return SafeMembrane(r)

    def __setattr__(self, attr, val, osa=object.__setattr__):
        if (attr == '_ref' or
                hasattr(type(self), attr) and not attr.startswith('__')):
            osa(self, attr, val)
        else:
            self.safeIn()
            val = unwrap(val)
            setattr(self._ref, attr, val)
            self.safeOut()

    def __delattr__(self, attr, oda=object.__delattr__):
        self.safeIn()
        delattr(self._ref, attr)
        self.safeOut()

    def __bool__(self):
        return bool(self._ref)

    def __getitem__(self, arg):
        return SafeMembrane(self._ref[arg])

    def __setitem__(self, arg, val):
        self.safeIn()
        val = unwrap(val)
        self._ref[arg] = val
        self.safeOut()

    def __delitem__(self, arg):
        self.safeIn()
        del self._ref[arg]
        self.safeOut()

    def __getslice__(self, i, j):
        return SafeMembrane(self._ref[i:j])

    def __setslice__(self, i, j, val):
        self.safeIn()
        val = unwrap(val)
        self._ref[i:j] = val
        self.safeOut()

    def __delslice__(self, i, j):
        self.safeIn()
        del self._ref[i:j]
        self.safeOut()

    def __enter__(self, *args, **kwargs):
        self.safeIn()
        self._ref.__enter__(*args, **kwargs)

    def __exit__(self, *args, **kwargs):
        self._ref.__exit__(*args, **kwargs)
        self.safeOut()


class InteractiveLauncher(SafeMembrane):
    '''
    Proxy to an application instance that launches it in a thread and
    then returns and acts as a proxy to the application in the thread.
    '''

    __slots__ = ('_ref', 'safe', 'confirmed', 'thread', 'app')

    @deprecated
    def __init__(self, app=None, *args, **kwargs):
        if app is None:
            app = App()
        EventLoop.safe = Event()
        self.safe = EventLoop.safe
        self.safe.set()
        EventLoop.confirmed = Event()
        self.confirmed = EventLoop.confirmed
        self.app = app

        def startApp(app=app, *args, **kwargs):
            app.run(*args, **kwargs)

        self.thread = Thread(target=startApp, *args, **kwargs)

    def run(self):
        self.thread.start()
        # Proxy behavior starts after this is set. Before this point, attaching
        # widgets etc can only be done through the Launcher's app attribute
        self._ref = self.app

    def stop(self):
        EventLoop.quit = True
        self.thread.join()

    # Act like the app instance even before _ref is set
    def __repr__(self):
        return self.app.__repr__()
