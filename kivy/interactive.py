from kivy.app import App
from kivy.base import EventLoop

from threading import Thread, Event

class InteractiveLauncher(Thread):
    """ Allows an App to be run in a thread and for thread-safe membranes to
    objects in that thread to be created"""
    def __init__(self, App = App(), *args, **kwargs):
        self.app = App
        #
        # modify the EventLoop to make it cooperative
        EventLoop.safe = Event()
        EventLoop.safe.set()
        EventLoop.confirmed = Event()
        idle = EventLoop.idle
        def idle_interactive():
            '''EventLoopBase.idle is wrapped in threadsafing code to allow the
            interpreter to interject execution'''
            #print 'running in interactive mode'
            if  EventLoop.safe.is_set():
                idle()
            else:
                EventLoop.confirmed.set()
                EventLoop.safe.wait()
                EventLoop.confirmed.clear()
                idle()

        EventLoop.idle = idle_interactive
        self.safe = EventLoop.safe
        self.confirmed = EventLoop.confirmed
        
        # start the app in a thread
        super(InteractiveLauncher, self).__init__(target=self.startApp, *args, **kwargs)
        self.start()

    def startApp(self, *args, **kwargs):
        print 'Starting the application in a manager thread'
        self.app.run(*args, **kwargs)
        
    def join(self, *args, **kwargs):
        # joining a non-returning thread is annoying
        self.app.eventLoop.quit = True
        super(InteractiveLauncher, self).join()

    def membrane(self, ob=None):
        """ returns a threadsafe membrane to any object it's passed.  use when
        you already have references to non-threadsafe objects to thread-safe them.
        by default, a membrane to App is returned."""
        if ob is None:
            ob = self.app
        return SafeMembrane(ob, self.safe, self.confirmed)


class SafeMembrane(object):
    """Returns attributes as new thread-safe objects and makes thread-safe
    method calls, preventing thread-unsafe objects from leaking into the user's
    environment.  Create these with InteractiveLauncher.membrane to be sure
    EventLoop has been made cooperative."""
    __slots__ = {'__subject__', 'safe', 'confirmed'}

    def __init__(self, ob, safe, confirmed):
        self.__subject__ = ob
        self.safe = safe
        self.confirmed = confirmed
        
    def safeIn(self):
        self.safe.clear()
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

            

#Here's some testing code.  

#from kivy.uix.widget import Widget
#from kivy.graphics import Color, Ellipse



#class MyPaintWidget(Widget):
#    def on_touch_down(self, touch):
#        with self.canvas:
#            Color(1, 1, 0)
#            d = 30.
#            Ellipse(pos=(touch.x - d/2, touch.y - d/2), size=(d, d))

#class TestApp(App):
#    def build(self):
#        return MyPaintWidget()

#  Test that nothing was broken
#TestApp().run()

# Test the interactive overrides
#i = InteractiveLauncher(TestApp())

# Test that the safing bahavior works
#m = i.membrane()
# m is now a membrane to the App instance
#m.safe.set()
# The application is now blocked
# Click on the screen a bit
#m.safe.clear()
# The clicks will show up now
