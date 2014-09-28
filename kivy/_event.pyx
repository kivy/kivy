'''
Event dispatcher
================

All objects that produce events in Kivy implement the :class:`EventDispatcher`
which provides a consistent interface for registering and manipulating event
handlers.

.. versionchanged:: 1.0.9
    Property discovery and methods have been moved from the
    :class:`~kivy.uix.widget.Widget` to the :class:`EventDispatcher`.

.. versionchanged:: 1.8.2
    :class:`EventDispatcher` now inherits from :class:`Observable`, which
    defines the methods required to create a bindable object.
'''

__all__ = ('EventDispatcher', 'ObjectWithUid', 'Observable')


cdef extern from "Python.h":
    void Py_INCREF(PyObject *)
    void Py_DECREF(PyObject *)

from libc.stdlib cimport malloc, free
from libc.string cimport memset

from functools import partial
from collections import defaultdict
from kivy.weakmethod import WeakMethod
from kivy.compat import string_types
from kivy.properties cimport (Property, PropertyStorage, ObjectProperty,
    NumericProperty, StringProperty, ListProperty, DictProperty,
    BooleanProperty)

cdef int widget_uid = 0
cdef dict cache_properties = {}
cdef dict cache_events = {}
cdef dict cache_events_handlers = {}

def _get_bases(cls):
    for base in cls.__bases__:
        if base.__name__ == 'object':
            break
        yield base
        for cbase in _get_bases(base):
            yield cbase


cdef class ObjectWithUid(object):
    '''
    (internal) This class assists in providing unique identifiers for class
    instances. It it not intended for direct usage.
    '''
    def __cinit__(self):
        global widget_uid

        # XXX for the moment, we need to create a unique id for properties.
        # Properties need a identifier to the class instance. hash() and id()
        # are longer than using a custom __uid. I hope we can figure out a way
        # of doing that without using any python code. :)
        widget_uid += 1
        self.uid = widget_uid


cdef class Observable(ObjectWithUid):
    ''':class:`Observable` is a stub class defining the methods required
    for binding. :class:`EventDispatcher` is (the) one example of a class that
    implements the binding interface. See :class:`EventDispatcher` for details.

    .. versionadded:: 1.8.2
    '''

    def __cinit__(self, *largs, **kwargs):
        self.__fast_bind_mapping = defaultdict(list)

    def bind(self, **kwargs):
        pass

    def unbind(self, **kwargs):
        pass

    def fast_bind(self, name, func, *largs):
        '''See :meth:`EventDispatcher.fast_bind`.

        .. note::

            To keep backward compatibility with derived classes which may have
            inherited from :class:`Observable` before
            :meth:`fast_bind` was added, the default implementation
            of :meth:`fast_bind` and :meth:`fast_unbind` is to create a partial
            function that it passes to bind. However, :meth:`fast_unbind`
            is fairly inefficient since we have to lookup this partial function
            before we can call :meth:`unbind`. It is recommended to overwrite
            these methods in derived classes to directly do binding for
            better performance.
        '''
        f = partial(func, *largs)
        self.__fast_bind_mapping[name].append(((func, largs), f))
        try:
            self.bind(**{name: f})
            return True
        except KeyError:
            return False

    def fast_unbind(self, name, func, *largs):
        '''See :meth:`fast_bind`.
        '''
        cdef object f = None
        cdef tuple item, val = (func, largs)
        cdef list bound = self.__fast_bind_mapping[name]

        for i, item in enumerate(bound):
            if item[0] == val:
                f = item[1]
                del bound[i]
                break

        if f is not None:
            try:
                self.unbind(**{name: f})
            except KeyError:
                pass

    property proxy_ref:
        def __get__(self):
            return self


cdef class EventDispatcher(ObjectWithUid):
    '''Generic event dispatcher interface.

    See the module docstring for usage.
    '''

    def __cinit__(self, *largs, **kwargs):
        global cache_properties
        cdef dict cp = cache_properties
        cdef dict attrs_found
        cdef list attrs
        cdef Property attr
        cdef str k

        self.__event_stack = {}
        self.__storage = {}

        __cls__ = self.__class__

        if __cls__ not in cp:
            attrs_found = cp[__cls__] = {}
            attrs = dir(__cls__)
            for k in attrs:
                uattr = getattr(__cls__, k, None)
                if not isinstance(uattr, Property):
                    continue
                if k == 'touch_down' or k == 'touch_move' or k == 'touch_up':
                    raise Exception('The property <%s> has a forbidden name' % k)
                attrs_found[k] = uattr
        else:
            attrs_found = cp[__cls__]

        # First loop, link all the properties storage to our instance
        for k in attrs_found:
            attr = attrs_found[k]
            attr.link(self, k)

        # Second loop, resolve all the references
        for k in attrs_found:
            attr = attrs_found[k]
            attr.link_deps(self, k)

        self.__properties = attrs_found

        # Automatic registration of event types (instead of calling
        # self.register_event_type)

        # If not done yet, discover __events__ on all the baseclasses
        cdef dict ce = cache_events
        cdef list events
        cdef str event
        if __cls__ not in ce:
            classes = [__cls__] + list(_get_bases(self.__class__))
            events = []
            for cls in classes:
                if not hasattr(cls, '__events__'):
                    continue
                for event in cls.__events__:
                    if event in events:
                        continue

                    if event[:3] != 'on_':
                        raise Exception('{} is not an event name in {}'.format(
                            event, __cls__.__name__))

                    # Ensure that the user has at least declared the default handler
                    if not hasattr(self, event):
                        raise Exception(
                            'Missing default handler <%s> in <%s>' % (
                            event, __cls__.__name__))

                    events.append(event)
            ce[__cls__] = events
        else:
            events = ce[__cls__]

        # then auto register
        for event in events:
            self.__event_stack[event] = EventObservers(1, 0)

    def __init__(self, **kwargs):
        cdef str func, name, key
        cdef dict properties
        # object.__init__ takes no parameters as of 2.6; passing kwargs
        # triggers a DeprecationWarning or worse
        super(EventDispatcher, self).__init__()

        # Auto bind on own handler if exist
        properties = self.properties()
        __cls__ = self.__class__
        if __cls__ not in cache_events_handlers:
            event_handlers = []
            for func in dir(self):
                if func[:3] != 'on_':
                    continue
                name = func[3:]
                if name in properties:
                    event_handlers.append(func)
            cache_events_handlers[__cls__] = event_handlers
        else:
            event_handlers = cache_events_handlers[__cls__]
        for func in event_handlers:
            self.fast_bind(func[3:], getattr(self, func))

        # Apply the existing arguments to our widget
        for key, value in kwargs.iteritems():
            if key in properties:
                setattr(self, key, value)

    def register_event_type(self, str event_type):
        '''Register an event type with the dispatcher.

        Registering event types allows the dispatcher to validate event handler
        names as they are attached and to search attached objects for suitable
        handlers. Each event type declaration must:

            1. start with the prefix `on_`.
            2. have a default handler in the class.

        Example of creating a custom event::

            class MyWidget(Widget):
                def __init__(self, **kwargs):
                    super(MyWidget, self).__init__(**kwargs)
                    self.register_event_type('on_swipe')

                def on_swipe(self):
                    pass

            def on_swipe_callback(*largs):
                print('my swipe is called', largs)
            w = MyWidget()
            w.dispatch('on_swipe')
        '''

        if event_type[:3] != 'on_':
            raise Exception('A new event must start with "on_"')

        # Ensure that the user has at least declared the default handler
        if not hasattr(self, event_type):
            raise Exception(
                'Missing default handler <%s> in <%s>' % (
                event_type, self.__class__.__name__))

        # Add the event type to the stack
        if event_type not in self.__event_stack:
            self.__event_stack[event_type] = EventObservers(1, 0)

    def unregister_event_types(self, str event_type):
        '''Unregister an event type in the dispatcher.
        '''
        if event_type in self.__event_stack:
            del self.__event_stack[event_type]

    def is_event_type(self, str event_type):
        '''Return True if the event_type is already registered.

        .. versionadded:: 1.0.4
        '''
        return event_type in self.__event_stack

    def bind(self, **kwargs):
        '''Bind an event type or a property to a callback.

        Usage::

            # With properties
            def my_x_callback(obj, value):
                print('on object', obj, 'x changed to', value)
            def my_width_callback(obj, value):
                print('on object', obj, 'width changed to', value)
            self.bind(x=my_x_callback, width=my_width_callback)

            # With event
            def my_press_callback(obj):
                print('event on object', obj)
            self.bind(on_press=my_press_callback)

        In general, property callbacks are called with 2 arguments (the
        object and the property's new value) and event callbacks with
        one argument (the object). The example above illustrates this.

        The following example demonstates various ways of using the bind
        function in a complete application::

            from kivy.uix.boxlayout import BoxLayout
            from kivy.app import App
            from kivy.uix.button import Button
            from functools import partial


            class DemoBox(BoxLayout):
                """
                This class demonstrates various techniques that can be used for binding to
                events. Although parts could me made more optimal, advanced Python concepts
                are avoided for the sake of readability and clarity.
                """
                def __init__(self, **kwargs):
                    super(DemoBox, self).__init__(**kwargs)
                    self.orientation = "vertical"

                    # We start with binding to a normal event. The only argument
                    # passed to the callback is the object which we have bound to.
                    btn = Button(text="Normal binding to event")
                    btn.bind(on_press=self.on_event)

                    # Next, we bind to a standard property change event. This typically
                    # passes 2 arguments: the object and the value
                    btn2 = Button(text="Normal binding to a property change")
                    btn2.bind(state=self.on_property)

                    # Here we use anonymous functions (a.k.a lambdas) to perform binding.
                    # Their advantage is that you can avoid declaring new functions i.e.
                    # they offer a concise way to "redirect" callbacks.
                    btn3 = Button(text="Using anonymous functions.")
                    btn3.bind(on_press=lambda x: self.on_event(None))

                    # You can also declare a function that accepts a variable number of
                    # positional and keyword arguments and use introspection to determine
                    # what is being passed in. This is very handy for debugging as well
                    # as function re-use. Here, we use standard event binding to a function
                    # that accepts optional positional and keyword arguments.
                    btn4 = Button(text="Use a flexible function")
                    btn4.bind(on_press=self.on_anything)

                    # Lastly, we show how to use partial functions. They are sometimes
                    # difficult to grasp, but provide a very flexible and powerful way to
                    # reuse functions.
                    btn5 = Button(text="Using partial functions. For hardcores.")
                    btn5.bind(on_press=partial(self.on_anything, "1", "2", monthy="python"))

                    for but in [btn, btn2, btn3, btn4, btn5]:
                        self.add_widget(but)

                def on_event(self, obj):
                    print("Typical event from", obj)

                def on_property(self, obj, value):
                    print("Typical property change from", obj, "to", value)

                def on_anything(self, *args, **kwargs):
                    print('The flexible function has *args of', str(args),
                        "and **kwargs of", str(kwargs))


            class DemoApp(App):
                def build(self):
                    return DemoBox()

            if __name__ == "__main__":
                DemoApp().run()
        '''
        cdef EventObservers observers
        cdef PropertyStorage ps

        for key, value in kwargs.iteritems():
            if key[:3] == 'on_':
                observers = self.__event_stack.get(key)
                if observers is None:
                    continue
                # convert the handler to a weak method
                observers.fast_bind(WeakMethod(value), None, None, 1)
            else:
                ps = self.__storage[key]
                ps.observers.bind(value)

    def unbind(self, **kwargs):
        '''Unbind properties from callback functions.

        Same usage as :meth:`bind`.
        '''
        cdef EventObservers observers
        cdef PropertyStorage ps

        for key, value in kwargs.iteritems():
            if key[:3] == 'on_':
                observers = self.__event_stack.get(key)
                if observers is None:
                    continue
                # it's a ref, and stop on first match
                observers.unbind(value, 1, 1)
            else:
                ps = self.__storage[key]
                ps.observers.unbind(value, 0, 0)

    def fast_bind(self, name, func, *largs, **kwargs):
        '''A method for faster binding. This method is meant to only be used
        internally and it performs less error checking. It can be used
        externally, as long as the following warnings are heeded.

        As opposed to :meth:`bind`, it does not check that this function and
        args has not been bound before to this name. It is assumed that the
        combination of function + positional args has not been bound to this
        name before.

        In addition, although :meth:`bind` creates a :class:`WeakMethod` for
        the callback function, this method stores the function directly,
        without any proxying.

        Finally, this method returns True if `name` was found and bound, and
        `False`, otherwise. It does not raise an exception, like :meth:`bind`,
        if `name` is not found.

        Anything bound with this method, must be unbound with
        :meth:`fast_unbind`; :meth:`unbind` will not unbind it.

        The method passes on the caught positional arguments to the callback,
        removing the need to call partial. When calling back, the
        instance/value, or dispatched parameters are passed on after the
        positional arguments provided here.

        .. note::
            Since the kv lang uses this method to bind, one has to implement
            this method, instead of :meth:`bind` when creating a non
            :class:`EventDispatcher` based class (e.g. based on
            :class:`Observable`) used with the kv lang. A simple method is to
            make `fast_bind` call `bind` e.g.::

                def fast_bind(self, name, func, *largs):
                    self.bind(**{name: partial(func, *largs)})

            Then one can use this partial function with fast_unbind.

        .. versionadded:: 1.8.2
        '''
        cdef EventObservers observers
        cdef PropertyStorage ps

        if name[:3] == 'on_':
            observers = self.__event_stack.get(name)
            if observers is not None:
                observers.fast_bind(func, largs, kwargs, 0)
                return True
            return False
        else:
            ps = self.__storage.get(name)
            if ps is None:
                return False
            ps.observers.fast_bind(func, largs, kwargs, 0)
            return True

    def fast_unbind(self, name, func, *largs, **kwargs):
        '''Similar to :meth:`fast_bind`.

        When unbinding from a property :meth:`unbind` will unbind
        all callback that match the callback, while this method will only
        unbind the first (as it is assumed that the combination of func and
        args are uniquely bound).

        To unbind, the same positional arguments passed to :meth:`fast_bind`
        must be passed on to unbind.

        .. versionadded:: 1.8.2
        '''
        cdef EventObservers observers
        cdef PropertyStorage ps

        if name[:3] == 'on_':
            observers = self.__event_stack.get(name)
            if observers is not None:
                observers.fast_unbind(func, largs, kwargs)
        else:
            ps = self.__storage.get(name)
            if ps is not None:
                ps.observers.fast_unbind(func, largs, kwargs)

    def get_property_observers(self, name):
        ''' Returns a list of methods that are bound to the property/event
        passed as the *name* argument::

            widget_instance.get_property_observers('on_release')

        .. versionadded:: 1.8.0

        .. versionchanged:: 1.8.2
            To keep compatibility, callbacks bound with :meth:`fast_bind` will
            also only return the callback function and not their provided args.

        '''
        cdef PropertyStorage ps
        cdef EventObservers observers

        if name[:3] == 'on_':
            observers = self.__event_stack[name]
            return [item[0] for item in observers]
        ps = self.__storage[name]
        return [item[0] for item in ps.observers]

    def events(EventDispatcher self):
        '''Return all the events in the class. Can be used for introspection.

        .. versionadded:: 1.8.0

        '''
        return self.__event_stack.keys()

    def dispatch(self, str event_type, *largs, **kwargs):
        '''Dispatch an event across all the handlers added in bind().
        As soon as a handler returns True, the dispatching stops.

        The function collects all the positional and keyword arguments and
        passes them on to the handlers.

        .. note::
            The handlers are called in reverse order than they were registered
            with :meth:`bind`.

        :Parameters:
            `event_type`: str
                the event name to dispatch.

        .. versionchanged:: 1.8.1
            Keyword arguments collection and forwarding was added. Before, only
            positional arguments would be collected and forwarded.

        '''
        cdef EventObservers observers = self.__event_stack[event_type]
        if observers.dispatch(self, None, largs, kwargs, 1):
            return True

        handler = getattr(self, event_type)
        return handler(*largs, **kwargs)

    def dispatch_generic(self, str event_type, *largs, **kwargs):
        if event_type in self.__event_stack:
            return self.dispatch(event_type, *largs, **kwargs)
        return self.dispatch_children(event_type, *largs, **kwargs)

    def dispatch_children(self, str event_type, *largs, **kwargs):
        for child in self.children[:]:
            if child.dispatch_generic(event_type, *largs, **kwargs):
                return True

    #
    # Properties
    #
    def __proxy_setter(self, EventDispatcher dstinstance, name, instance, value):
        cdef Property prop = self.__properties[name]
        prop.set(dstinstance, value)

    def __proxy_getter(self, EventDispatcher dstinstance, name, instance):
        cdef Property prop = self.__properties[name]
        return prop.get(dstinstance)

    def setter(self, name):
        '''Return the setter of a property. Use: instance.setter('name').
        The setter is a convenient callback function useful if you want
        to directly bind one property to another.
        It returns a partial function that will accept
        (obj, value) args and results in the property 'name' of instance
        being set to value.

        .. versionadded:: 1.0.9

        For example, to bind number2 to number1 in python you would do::

            class ExampleWidget(Widget):
                number1 = NumericProperty(None)
                number2 = NumericProperty(None)

                def __init__(self, **kwargs):
                    super(ExampleWidget, self).__init__(**kwargs)
                    self.bind(number1=self.setter('number2'))

        This is equivalent to kv binding::

            <ExampleWidget>:
                number2: self.number1

        '''
        return partial(self.__proxy_setter, self, name)

    def getter(self, name):
        '''Return the getter of a property.

        .. versionadded:: 1.0.9
        '''
        return partial(self.__proxy_getter, self, name)

    def property(self, name, quiet=False):
        '''Get a property instance from the property name. If quiet is True,
        None is returned instead of raising an exception when `name` is not a
        property. Defaults to `False`.

        .. versionadded:: 1.0.9

        :return:

            A :class:`~kivy.properties.Property` derived instance
            corresponding to the name.

        .. versionchanged:: 1.8.1
            quiet was added.
        '''
        if quiet:
            return self.__properties.get(name, None)
        else:
            return self.__properties[name]

    cpdef dict properties(EventDispatcher self):
        '''Return all the properties in the class in a dictionary of
        key/property class. Can be used for introspection.

        .. versionadded:: 1.0.9
        '''
        # fast path, use the cache first
        __cls__ = self.__class__
        if __cls__ in cache_properties:
            return cache_properties[__cls__]

        cdef dict ret, p
        ret = {}
        p = self.__properties
        for x in self.__storage:
            ret[x] = p[x]
        return ret

    def create_property(self, name, value=None):
        '''Create a new property at runtime.

        .. versionadded:: 1.0.9

        .. versionchanged:: 1.8.0
            `value` parameter added, can be used to set the default value of the
            property. Also, the type of the value is used to specialize the
            created property.

        .. versionchanged:: 1.8.1
            In the past, if `value` was of type `bool`, a `NumericProperty`
            would be created, now a `BooleanProperty` is created.

        .. warning::

            This function is designed for the Kivy language, don't use it in
            your code. You should declare the property in your class instead of
            using this method.

        :Parameters:
            `name`: string
                Name of the property
            `value`: object, optional
                Default value of the property. Type is also used for creating
                more appropriate property types. Defaults to None.

        >>> mywidget = Widget()
        >>> mywidget.create_property('custom')
        >>> mywidget.custom = True
        >>> print(mywidget.custom)
        True
        '''
        if isinstance(value, bool):
            prop = BooleanProperty(value)
        elif isinstance(value, (int, float)):
            prop = NumericProperty(value)
        elif isinstance(value, string_types):
            prop = StringProperty(value)
        elif isinstance(value, (list, tuple)):
            prop = ListProperty(value)
        elif isinstance(value, dict):
            prop = DictProperty(value)
        else:
            prop = ObjectProperty(value)
        prop.link(self, name)
        prop.link_deps(self, name)
        self.__properties[name] = prop
        setattr(self.__class__, name, prop)

    property proxy_ref:
        '''Default implementation of proxy_ref, returns self.
        ..versionadded:: 1.8.1
        '''
        def __get__(self):
            return self


cdef inline void release_callback(BoundCallabck *callback):
    Py_DECREF(callback.func)
    if callback.largs != NULL:
        Py_DECREF(callback.largs)
    if callback.kwargs != NULL:
        Py_DECREF(callback.kwargs)
    free(callback)


cdef class EventObservers:
    '''A class that stores observers to events as a forward linked list
    (doubly linked if dispatch_reverse is true, and then dispatching occurs
    in reverse order of binding).
    '''

    def __cinit__(self, int dispatch_reverse=0, dispatch_value=1):
        self.first_callback = self.last_callback = NULL
        self.dispatch_reverse = dispatch_reverse
        self.dispatch_value = dispatch_value

    def __dealloc__(self):
        cdef BoundCallabck *callback
        cdef BoundCallabck *last_c
        callback = self.first_callback
        while callback != NULL:
            last_c = callback
            callback = callback.next
            release_callback(last_c)

    cdef inline void bind(self, object observer):
        '''Bind the observer to the event. If this observer has already been
        bound, we don't add it again.
        '''
        cdef BoundCallabck *callback = self.first_callback

        # ensure observer is not bound already
        while callback != NULL:
            if (callback.largs == NULL and callback.kwargs == NULL and
                <object>(callback.func) == observer):
                return
            callback = callback.next

        callback = <BoundCallabck *>malloc(sizeof(BoundCallabck))
        memset(callback, 0, sizeof(BoundCallabck))
        callback.func = <PyObject *>observer
        Py_INCREF(callback.func)

        if self.first_callback == NULL:
            self.last_callback = self.first_callback = callback
        else:
            if self.dispatch_reverse:
                callback.previous = self.last_callback
            self.last_callback.next = callback
            self.last_callback = callback


    cdef inline int fast_bind(self, object observer, tuple largs, dict kwargs, int is_ref):
        '''Similar to bind, except it accepts largs, kwargs that is forwards.
        is_ref, if true, will mark the observer that it is a ref so that we
        can unref it before calling.
        '''
        cdef BoundCallabck *callback = <BoundCallabck *>malloc(sizeof(BoundCallabck))
        memset(callback, 0, sizeof(BoundCallabck))

        callback.func = <PyObject *>observer
        Py_INCREF(callback.func)
        callback.is_ref = is_ref
        if largs is not None and len(largs):
            callback.largs = <PyObject *>largs
            Py_INCREF(callback.largs)
        if kwargs is not None and len(kwargs):
            callback.kwargs = <PyObject *>kwargs
            Py_INCREF(callback.kwargs)

        if self.first_callback == NULL:
            self.last_callback = self.first_callback = callback
        else:
            if self.dispatch_reverse:
                callback.previous = self.last_callback
            self.last_callback.next = callback
            self.last_callback = callback

    cdef inline void unbind(self, object observer, int is_ref, int stop_on_first):
        '''Removes the observer. If is_ref, he observers will be derefed before
        comparing to observer, if they are refed. If stop_on_first, after the
        first match we return.
        '''
        cdef BoundCallabck *callback = self.first_callback
        cdef BoundCallabck *last_callback = NULL
        cdef BoundCallabck  *c
        cdef object f

        while callback != NULL:
            if callback.largs != NULL or callback.kwargs != NULL:
                last_callback = callback
                callback = callback.next
                continue

            f = <object>(callback.func)
            if is_ref and callback.is_ref:
                f = f()
            if f != observer and (not (is_ref and callback.is_ref) or f is not None):
                last_callback = callback
                callback = callback.next
                continue

            c = callback
            if callback == self.first_callback:
                callback = self.first_callback = callback.next
                if callback != NULL and self.dispatch_reverse:
                    callback.previous = NULL
            else:
                last_callback.next = callback = callback.next
                if callback != NULL and self.dispatch_reverse:
                    callback.previous = last_callback

            release_callback(c)
            if stop_on_first and f is not None:
                self.last_callback = last_callback
                return
        self.last_callback = last_callback

    cdef inline void fast_unbind(self, object observer, tuple largs, dict kwargs):
        '''Similar to unbind, except we only remove the first match, and
        we don't deref the observers before comparing to observer. The
        largs and kwargs must match the largs and kwargs from when binding.
        '''
        cdef BoundCallabck *callback = self.first_callback
        cdef BoundCallabck *last_callback = NULL
        cdef int il = len(largs) if largs is not None else 0, ikw = len(kwargs) if kwargs is not None else 0

        while callback != NULL:
            if ((callback.largs != NULL and il == 0 or
                 callback.largs == NULL and il != 0 or
                 <tuple>(callback.largs) != largs) or
                (callback.kwargs != NULL and ikw == 0 or
                 callback.kwargs == NULL and ikw != 0 or
                 <dict>(callback.kwargs) != kwargs) or
                <object>(callback.func) != observer):
                last_callback = callback
                callback = callback.next
                continue

            if callback == self.first_callback:
                self.first_callback = callback.next
                if self.first_callback != NULL and self.dispatch_reverse:
                    self.first_callback.previous = NULL
            else:
                last_callback.next = callback.next
                if callback.next != NULL and self.dispatch_reverse:
                    callback.next.previous = last_callback
            if callback == self.last_callback:
                self.last_callback = last_callback

            release_callback(callback)
            return

    cdef inline int dispatch(self, object obj, object value, tuple largs, dict kwargs, int stop_on_true):
        '''Dispatches obj, value to all bound observers. If largs and/or kwargs,
        they are forwarded after obj, value. if stop_on_true, if a observer returns
        true, the function stops and returns true.
        '''
        cdef BoundCallabck *callback = self.last_callback if self.dispatch_reverse else self.first_callback
        cdef BoundCallabck *last_callback = NULL
        cdef BoundCallabck *c
        cdef object result, f
        cdef dict d
        cdef tuple param = (obj, value) if self.dispatch_value else (obj, )
        cdef tuple fargs = None

        while callback != NULL:
            f = <object>(callback.func)

            # first make sure that if the callback is a ref and dead, we remove it
            if callback.is_ref:
                f = f()
                if f is None:  # remove invalid callback
                    c = callback
                    if self.dispatch_reverse:
                        if callback == self.last_callback:
                            self.last_callback = callback.previous
                            if self.last_callback != NULL:
                                self.last_callback.next = NULL
                        else:
                            last_callback.previous = callback.previous
                            if callback.previous != NULL:
                                callback.previous.next = last_callback
                        if callback == self.first_callback:
                            self.first_callback = last_callback
                        callback = callback.previous
                    else:
                        if callback == self.first_callback:
                            self.first_callback = callback.next
                        else:
                            last_callback.next = callback.next
                        if callback == self.last_callback:
                            self.last_callback = last_callback
                        callback = callback.next
                    release_callback(c)
                    continue

            # find the correct combo of largs, kwargs from binding and dispatching
            last_callback = callback
            if callback.largs != NULL and callback.kwargs != NULL:  # both kw and largs
                if largs is not None:
                    fargs = <tuple>(callback.largs) + param + largs
                else:
                    fargs = (<tuple>(callback.largs)) + param

                if kwargs is not None:
                    d = dict(<dict>(callback.kwargs))
                    d.update(kwargs)
                else:
                    d = <dict>(callback.kwargs)

                result = f(*fargs, **d)
            elif callback.largs != NULL:  # only largs
                if largs is not None:
                    fargs = <tuple>(callback.largs) + param + largs
                else:
                    fargs = (<tuple>(callback.largs)) + param

                if kwargs is None:
                    result = f(*fargs)
                else:
                    result = f(*fargs, **kwargs)
            elif callback.kwargs != NULL:  # only kwargs
                if kwargs is not None:
                    d = dict(<dict>(callback.kwargs))
                    d.update(kwargs)
                else:
                    d = <dict>(callback.kwargs)

                if largs is None:
                    if self.dispatch_value:
                        result = f(obj, value, **d)
                    else:
                        result = f(obj, **d)
                else:
                    if self.dispatch_value:
                        result = f(obj, value, *largs, **d)
                    else:
                        result = f(obj, *largs, **d)
            else:  # no args
                if largs is None:
                    if kwargs is None:
                        if self.dispatch_value:
                            result = f(obj, value)
                        else:
                            result = f(obj)
                    else:
                        if self.dispatch_value:
                            result = f(obj, value, **kwargs)
                        else:
                            result = f(obj, **kwargs)
                else:
                    if kwargs is None:
                        if self.dispatch_value:
                            result = f(obj, value, *largs)
                        else:
                            result = f(obj, *largs)
                    else:
                        if self.dispatch_value:
                            result = f(obj, value, *largs, **kwargs)
                        else:
                            result = f(obj, *largs, **kwargs)

            if stop_on_true and result:
                return 1
            if self.dispatch_reverse:
                callback = callback.previous
            else:
                callback = callback.next
        return 0

    def __iter__(self):
        cdef BoundCallabck *callback = self.first_callback

        while callback != NULL:
            if callback.largs != NULL and callback.kwargs != NULL:
                yield <object>(callback.func), <tuple>(callback.largs), <dict>(callback.kwargs), callback.is_ref
            elif callback.largs != NULL:
                yield <object>(callback.func), <tuple>(callback.largs), {}, callback.is_ref
            elif callback.kwargs != NULL:
                yield <object>(callback.func), (), <dict>(callback.kwargs), callback.is_ref
            else:
                yield <object>(callback.func), (), {}, callback.is_ref
            callback = callback.next
