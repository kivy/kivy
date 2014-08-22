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

__all__ = ('EventDispatcher', )


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
        self.bind(**{name: f})

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
            self.unbind(**{name: f})

    property proxy_ref:
        def __get__(self):
            return self


cdef class EventDispatcher(Observable):
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
            self.__event_stack[event] = []


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
            self.bind(**{func[3:]: getattr(self, func)})

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
            self.__event_stack[event_type] = []

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
        cdef Property prop
        cdef tuple handler
        for key, value in kwargs.iteritems():
            if key[:3] == 'on_':
                if key not in self.__event_stack:
                    continue
                # convert the handler to a weak method
                handler = (WeakMethod(value), )
                self.__event_stack[key].append(handler)
            else:
                prop = self.__properties[key]
                prop.bind(self, value)

    def unbind(self, **kwargs):
        '''Unbind properties from callback functions.

        Same usage as :meth:`bind`.
        '''
        cdef Property prop
        cdef tuple handler
        for key, value in kwargs.iteritems():
            if key[:3] == 'on_':
                if key not in self.__event_stack:
                    continue

                # we need to execute weak method to be able to compare
                for handler in self.__event_stack[key]:
                    # we only unbind here if bound with normal bind
                    if len(handler) != 1 or handler[0]() != value:
                        continue
                    self.__event_stack[key].remove(handler)
                    break
            else:
                prop = self.__properties[key]
                prop.unbind(self, value)

    def fast_bind(self, name, func, *largs):
        '''A method for faster binding. This method is meant to only be used
        internally and it performs less error checking. It can be used
        externally, as long as the following warnings are heeded.

        Compared to :meth:`bind`, it does not check that the name is valid,
        or that this function and args has not been bound before to this
        name. It is assumed that the combination of function + positional args
        has not been bound to this name before.

        In addition, although :meth:`bind` creates a :class:`WeakMethod` for
        the callback function, this method stores the function directly,
        without any proxying.

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
        cdef PropertyStorage ps
        cdef tuple handler = (func, largs)

        if name[:3] == 'on_':
            self.__event_stack[name].append(handler)
        else:
            ps = self.__storage[name]
            ps.observers.append(handler)

    def fast_unbind(self, name, func, *largs):
        '''Similar to :meth:`fast_bind`.

        Compared to :meth:`unbind`, it doesn't check that `name` is valid.
        Similarly, when unbinding from a property :meth:`unbind` will unbind
        all callback that match the callback, while this method will only
        unbind the first (as it is assumed that the combination of func and
        args are uniquely bound).

        To unbind, the same positional arguments passed to :meth:`fast_bind`
        must be passed on to unbind.

        .. versionadded:: 1.8.2
        '''
        cdef PropertyStorage ps
        cdef list observers
        cdef tuple item, src_item = (func, largs)
        cdef int i

        if name[:3] == 'on_':
            self.__event_stack[name].remove(src_item)
        else:
            ps = self.__storage[name]
            observers = ps.observers
            for i, item in enumerate(observers):
                if item == src_item:
                    del observers[i]
                    break

    def get_property_observers(self, name):
        ''' Returns a list of methods that are bound to the property/event
        passed as the *name* argument::

            widget_instance.get_property_observers('on_release')

        .. versionadded:: 1.8.0

        .. versionchanged:: 1.8.2
            To keep compatibility, callbacks bound with :meth:`fast_bind` will
            also only return the callback function and not their provided args.

        '''
        if name[:3] == 'on_':
            return [item[0] for item in self.__event_stack[name]]
        cdef PropertyStorage ps = self.__storage[name]
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
        cdef list event_stack = self.__event_stack[event_type]
        cdef tuple item, args_list, args
        cdef object handler, remove = event_stack.remove

        for item in reversed(event_stack[:]):
            # dispatch callback from a normal bind
            if len(item) == 1:
                handler = item[0]()
                if handler is None:
                    # handler has gone, must be removed
                    remove(item)
                    continue
                if handler(self, *largs, **kwargs):
                    return True

            # dispatch callback from a fast bind
            else:
                args = item[1]
                args_list = args + largs  # largs goes at the end
                if item[0](*args_list, **kwargs):
                    return True

        handler = getattr(self, event_type)
        return handler(*largs, **kwargs)

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

    def property(self, name):
        '''Get a property instance from the name.

        .. versionadded:: 1.0.9

        :return:

            A :class:`~kivy.properties.Property` derived instance
            corresponding to the name.
        '''
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
