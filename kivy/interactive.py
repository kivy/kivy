'''
InteractiveLauncher
===========

The :class:`InteractiveLauncher` provides a user-friendly python shell interface
to an :class:`App` so that it can be prototyped and debugged interactively. 

Creating an InteractiveLauncher
-----------------------

Take you existing subclass of :class:`App` (this can be production code) and pass an
instance to the :class:`InteractiveLauncher` constructor.::

    from kivy.interactive import InteractiveLauncher
    from kivy.app import App
    from kivy.uix.button import Button
    
    class MyApp(App):
        def build(self):
            return Button(test='Hello Shell')

    interactiveLauncher = InteractiveLauncher(MyApp()).run()

The script will return, allowing an interpreter shell to continue running and
inspection or modification of the :class:`App` can be done safely through the
InteractiveLauncher instance or the provided SafeMembrane class instances.


Directly Pausing the Application
-------------------------

Both :class:`InteractiveLauncher and :class:`SafeMembrane` hold internal
references to :class:`EventLoop`'s 'safe' and 'confirmed'
:class:`threading.Event` objects.  You can use their safing methods to control the
application manually.

:meth:`InteractiveLauncher.safeIn()` will internally allow a paused application
to continue running.  :meth:`Interactive.safeOut()` will cause the applicaiton
to pause.  This is useful for scripting actions into functions that need the
screen to update etc.

Adding Attributes Dynamically
-------------------------

The :class:`InteractiveLauncher` can have attributes added to it exactly like a normal
object, and if these were created from outside the membrane, they will not be
threadsafe because the external references to them in the python interpreter do
not go through InteractiveLauncher's membrane behavior inherited from
SafeMembrane.

To threadsafe these external referencess, simply assign them to SafeMembrane
instances of themselves like so::

    interactiveLauncher.attribute = myNewObject
    # myNewObject is unsafe
    myNewObject = SafeMembrane(myNewObject)
    # myNewObject is now safe.  Call at will.
    myNewObject.method()

'''

from kivy.app import App
from kivy.base import EventLoop
from kivy.clock import Clock
from threading import Thread, Event

def safeWait(dt):
    EventLoop.confirmed.set()
    EventLoop.safe.wait()
    EventLoop.confirmed.clear()

class SafeMembrane(object):
    """Threadsafe proxy that also returns attributes as new thread-safe objects
    and makes thread-safe method calls, preventing thread-unsafe objects
    from leaking into the user's environment."""
    __slots__ = {'__subject__', 'safe', 'confirmed'}

    def __init__(self, ob, *args, **kwargs):
        self.confirmed = EventLoop.confirmed()
        self.safe = EventLoop.safe()
        self.__subject__ = ob
        
    def safeIn(self):
        self.safe.clear()
        Clock.schedule_once(safeWait, -1)
        self.confirmed.wait()

    def safeOut(self):
        self.safe.set()

    def enSafen(self, fn):
        """ returns a threadsafe version of the method """
        def safeFunction( *args, **kwargs):
                self.safeIn()
                r = fn(*args, **kwargs)
                self.safeOut()
                return r
        return safeFunction

    def isMethod(self, fn):
        return type(fn) is type(self.isMethod)
        
    # the interpreter will report that all attributes are objects of class
    # SafeProxy unless some effort is made.
    def __repr__(self):
        return self.__subject__.__repr__()

    #  just in case __subject__ is a non-method and callable
    def __call__(self,*args,**kw):
        self.safeIn()
        r = self.__subject__(*args,**kw)
        self.safeOut()
        return r

    def __getattribute__(self, attr, oga=object.__getattribute__):
        if attr.startswith('__'):
            subject = oga(self,'__subject__')
            if attr=='__subject__':
                return subject
            return getattr(subject,attr)
        return oga(self,attr)

    def __getattr__(self,attr, oga=object.__getattribute__):
        #print 'getting {} of type {}'.format(attr, type(getattr(oga(self, '__subject__'), attr)))
        r = getattr(oga(self,'__subject__'), attr)
        if self.isMethod(r):
            r = self.enSafen(r)
            return r
        return SafeMembrane(r, self.safe, self.confirmed)

    def __setattr__(self,attr,val, osa=object.__setattr__):
        if (
            attr=='__subject__'
            or hasattr(type(self),attr) and not attr.startswith('__')
        ):
            osa(self,attr,val)
        else:
            self.safeIn()
            setattr(self.__subject__,attr,val)
            self.safeOut()
    # TODO
    # add some dictionary and list methods to prevent other avenues
    # for non-threadsafe objects to leak into the user's shell
    # see peak.util.proxies.AbstractProxy for a guide


class InteractiveLauncher(SafeMembrane):
    """ Proxy to an application instance that launches it in a thread and
    then returns and acts as a proxy to the application in the thread"""
    __slots__ = {'__subject__', 'safe', 'confirmed', 'thread', 'app'}

    def __init__(self, app = App(), *args, **kwargs):
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
        #Proxy behavior starts after this is set.  Before this point, attaching
        #widgets etc can only be done through the Launcher's app attribute
        self.__subject__ = self.app()

    def stop(self):
        EventLoop.quit = True
        self.thread.join()
        
    #Act like the app instance before __subject__ is set
    def __repr__(self):
        return self.app.__repr__()


#Here's some testing code.  

"""from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse



class MyPaintWidget(Widget):
    def on_touch_down(self, touch):
        with self.canvas:
            Color(1, 1, 0)
            d = 30.
            Ellipse(pos=(touch.x - d/2, touch.y - d/2), size=(d, d))

class TestApp(App):
    def build(self):
        return MyPaintWidget()"""

#  Test that nothing was broken
#TestApp().run()

#i = InteractiveLauncher(TestApp())
#i.safe.set()
# The application is now blocked
# Click on the screen a bit
#i.safe.clear()
# The clicks will show up now
