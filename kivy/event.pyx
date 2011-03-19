'''
Event dispatcher
================

All objects that produce events in Kivy implement :class:`EventDispatcher`,
providing a consistent interface for registering and manipulating event
handlers.
'''
__all__ = ('EventDispatcher', )

from kivy.weakmethod import WeakMethod

cdef class EventDispatcher(object):
    '''Generic event dispatcher interface

    See the module docstring for usage.
    '''

    cdef dict event_stack

    def __cinit__(self):
        self.event_stack = {}

    def __init__(self):
        super(EventDispatcher, self).__init__()

    cpdef register_event_type(self, str event_type):
        '''Register an event type with the dispatcher.

        Registering event types allows the dispatcher to validate event handler
        names as they are attached, and to search attached objects for suitable
        handlers. Each event type declaration must :

            1. start with the prefix `on_`
            2. have a default handler in the class

        Example of creating custom event::

            class MyWidget(Widget):
                def __init__(self, **kwargs):
                    super(MyWidget, self).__init__(**kwargs)
                    self.register_event_type('on_swipe')

                def on_swipe(self):
                    pass

            def on_swipe_callback(*largs):
                print 'my swipe is called', largs
            w = MyWidget()
            w.dispatch_event('on_swipe')
        '''

        if not event_type.startswith('on_'):
            raise Exception('A new event must start with "on_"')

        # Ensure the user have at least declare the default handler
        if not hasattr(self, event_type):
            raise Exception(
                'Missing default handler <%s> in <%s>' % (
                event_type, self.__class__.__name__))

        # Add the event type to the stack
        if not event_type in self.event_stack:
            self.event_stack[event_type] = []

    cpdef unregister_event_types(self, str event_type):
        '''Unregister an event type in the dispatcher
        '''
        if event_type in self.event_stack:
            del self.event_stack[event_type]

    def bind(self, **kwargs):
        '''Bind an event type or a property to a callback

        Usage::

            # With properties
            def my_x_callback(obj, value):
                print 'on object', obj, 'x changed to', value
            def my_width_callback(obj, value):
                print 'on object', obj, 'width changed to', value
            self.bind(x=my_x_callback, width=my_width_callback)

            # With event
            self.bind(on_press=self.my_press_callback)
        '''
        for key, value in kwargs.iteritems():
            if key not in self.event_stack:
                continue
            # convert the handler to a weak method
            handler = WeakMethod(value)
            self.event_stack[key].append(handler)

    def unbind(self, **kwargs):
        '''Unbind properties from callback functions.

        Same usage as bind().
        '''
        for key, value in kwargs.iteritems():
            if key not in self.event_stack:
                continue
            # we need to execute weak method to be able to compare
            for handler in self.event_stack[key]:
                if handler() != value:
                    continue
                self.event_stack[key].remove(handler)
                break

    def dispatch(self, str event_type, *largs):
        '''Dispatch an event across all the handler added in bind().
        As soon as a handler return True, the dispatching stop
        '''
        for value in self.event_stack[event_type]:
            handler = value()
            if handler is None:
                # handler have gone, must be removed
                # XXX FIXME event stack change while iterating
                self.event_stack[event_type].remove(value)
                continue
            if handler(self, *largs):
                return True

        handler = getattr(self, event_type)
        return handler(*largs)

