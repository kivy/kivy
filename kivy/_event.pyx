'''
Event dispatcher
================

All objects that produce events in Kivy implement the :class:`EventDispatcher`
which provides a consistent interface for registering and manipulating event
handlers.

.. versionchanged:: 1.0.9
    Property discovery and methods have been moved from the
    :class:`~kivy.uix.widget.Widget` to the :class:`EventDispatcher`.
'''

__all__ = ('EventDispatcher', 'ObjectWithUid', 'Observable')

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
    instances. It is not intended for direct usage.
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

    .. versionadded:: 1.9.0
    '''

    def __cinit__(self, *largs, **kwargs):
        self.__fbind_mapping = defaultdict(list)
        self.bound_uid = 1

    def bind(self, **kwargs):
        pass

    def unbind(self, **kwargs):
        pass

    def fbind(self, name, func, *largs, **kwargs):
        '''See :meth:`EventDispatcher.fbind`.

        .. note::

            To keep backward compatibility with derived classes which may have
            inherited from :class:`Observable` before, the
            :meth:`fbind` method was added. The default implementation
            of :meth:`fbind` is to create a partial
            function that it passes to bind while saving the uid and largs/kwargs.
            However, :meth:`funbind` (and :meth:`unbind_uid`) are fairly
            inefficient since we have to first lookup this partial function
            using the largs/kwargs or uid and then call :meth:`unbind` on
            the returned function. It is recommended to overwrite
            these methods in derived classes to bind directly for
            better performance.

            Similarly to :meth:`EventDispatcher.fbind`, this method returns
            0 on failure and a positive unique uid on success. This uid can be
            used with :meth:`unbind_uid`.

        '''
        uid = self.bound_uid
        self.bound_uid += 1
        f = partial(func, *largs, **kwargs)
        self.__fbind_mapping[name].append(((func, largs, kwargs), uid, f))
        try:
            self.bind(**{name: f})
            return uid
        except KeyError:
            return 0

    def funbind(self, name, func, *largs, **kwargs):
        '''See :meth:`fbind` and :meth:`EventDispatcher.funbind`.
        '''
        cdef object f = None
        cdef tuple item, val = (func, largs, kwargs)
        cdef list bound = self.__fbind_mapping[name]

        for i, item in enumerate(bound):
            if item[0] == val:
                f = item[2]
                del bound[i]
                break

        if f is not None:
            try:
                self.unbind(**{name: f})
            except KeyError:
                pass

    def unbind_uid(self, name, uid):
        '''See :meth:`fbind` and :meth:`EventDispatcher.unbind_uid`.
        '''
        cdef object f = None
        cdef tuple item
        cdef list bound = self.__fbind_mapping[name]
        if not uid:
            raise ValueError(
                'uid, {}, that evaluates to False is not valid'.format(uid))

        for i, item in enumerate(bound):
            if item[1] == uid:
                f = item[2]
                del bound[i]
                break

        if f is not None:
            try:
                self.unbind(**{name: f})
            except KeyError:
                pass

    @property
    def proxy_ref(self):
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
        cdef basestring k

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
        cdef basestring event
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
        cdef basestring func, name, key
        cdef dict properties
        cdef dict prop_args

        # Auto bind on own handler if exist
        properties = self.properties()
        prop_args = {
            k: kwargs.pop(k) for k in list(kwargs.keys()) if k in properties}
        self._kwargs_applied_init = set(prop_args.keys()) if prop_args else set()
        super(EventDispatcher, self).__init__(**kwargs)

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
            self.fbind(func[3:], getattr(self, func))

        # Apply the existing arguments to our widget
        for key, value in prop_args.items():
            setattr(self, key, value)

    def register_event_type(self, basestring event_type):
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

    def unregister_event_types(self, basestring event_type):
        '''Unregister an event type in the dispatcher.
        '''
        if event_type in self.__event_stack:
            del self.__event_stack[event_type]

    def is_event_type(self, basestring event_type):
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

        The following example demonstrates various ways of using the bind
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

        When binding a function to an event or property, a
        :class:`kivy.weakmethod.WeakMethod` of the callback is saved, and
        when dispatching the callback is removed if the callback reference
        becomes invalid.

        If a callback has already been bound to a given event or property,
        it won't be added again.
        '''
        cdef EventObservers observers
        cdef PropertyStorage ps

        for key, value in kwargs.iteritems():
            assert callable(value), '{!r} is not callable'.format(value)
            if key[:3] == 'on_':
                observers = self.__event_stack.get(key)
                if observers is None:
                    continue
                # convert the handler to a weak method
                observers.bind(WeakMethod(value), value, 1)
            else:
                ps = self.__storage[key]
                ps.observers.bind(WeakMethod(value), value, 1)

    def unbind(self, **kwargs):
        '''Unbind properties from callback functions with similar usage as
        :meth:`bind`.

        If a callback has been bound to a given event or property multiple
        times, only the first occurrence will be unbound.

        .. note::

            It is safe to use :meth:`unbind` on a function bound with :meth:`fbind`
            as long as that function was originally bound without any keyword and
            positional arguments. Otherwise, the function will fail to be unbound
            and you should use :meth:`funbind` instead.
        '''
        cdef EventObservers observers
        cdef PropertyStorage ps

        for key, value in kwargs.iteritems():
            if key[:3] == 'on_':
                observers = self.__event_stack.get(key)
                if observers is None:
                    continue
                # it's a ref, and stop on first match
                observers.unbind(value, 1)
            else:
                ps = self.__storage[key]
                ps.observers.unbind(value, 1)

    def fbind(self, name, func, *largs, **kwargs):
        '''A method for advanced, and typically faster binding. This method is
        different than :meth:`bind` and is meant for more advanced users and
        internal usage. It can be used as long as the following points are heeded.

        #. As opposed to :meth:`bind`, it does not check that this function and
           largs/kwargs has not been bound before to this name. So binding
           the same callback multiple times will just keep adding it.
        #. Although :meth:`bind` creates a :class:`WeakMethod` of the callback when
           binding to an event or property, this method stores the callback
           directly, unless a keyword argument `ref` with value True is provided
           and then a :class:`WeakMethod` is saved.
           This is useful when there's no risk of a memory leak by storing the
           callback directly.
        #. This method returns a unique positive number if `name` was found and
           bound, and `0`, otherwise. It does not raise an exception, like
           :meth:`bind` if the property `name` is not found. If not zero,
           the uid returned is unique to this `name` and callback and can be
           used with :meth:`unbind_uid` for unbinding.


        When binding a callback with largs and/or kwargs, :meth:`funbind`
        must be used for unbinding. If no largs and kwargs are provided,
        :meth:`unbind` may be used as well. :meth:`unbind_uid` can be used in
        either case.

        This method passes on any caught positional and/or keyword arguments to
        the callback, removing the need to call partial. When calling the
        callback the expended largs are passed on followed by instance/value
        (just instance for kwargs) followed by expended kwargs.

        Following is an example of usage similar to the example in
        :meth:`bind`::

            class DemoBox(BoxLayout):

                def __init__(self, **kwargs):
                    super(DemoBox, self).__init__(**kwargs)
                    self.orientation = "vertical"

                    btn = Button(text="Normal binding to event")
                    btn.fbind('on_press', self.on_event)

                    btn2 = Button(text="Normal binding to a property change")
                    btn2.fbind('state', self.on_property)

                    btn3 = Button(text="A: Using function with args.")
                    btn3.fbind('on_press', self.on_event_with_args, 'right',
                                   tree='birch', food='apple')

                    btn4 = Button(text="Unbind A.")
                    btn4.fbind('on_press', self.unbind_a, btn3)

                    btn5 = Button(text="Use a flexible function")
                    btn5.fbind('on_press', self.on_anything)

                    btn6 = Button(text="B: Using flexible functions with args. For hardcores.")
                    btn6.fbind('on_press', self.on_anything, "1", "2", monthy="python")

                    btn7 = Button(text="Force dispatch B with different params")
                    btn7.fbind('on_press', btn6.dispatch, 'on_press', 6, 7, monthy="other python")

                    for but in [btn, btn2, btn3, btn4, btn5, btn6, btn7]:
                        self.add_widget(but)

                def on_event(self, obj):
                    print("Typical event from", obj)

                def on_event_with_args(self, side, obj, tree=None, food=None):
                    print("Event with args", obj, side, tree, food)

                def on_property(self, obj, value):
                    print("Typical property change from", obj, "to", value)

                def on_anything(self, *args, **kwargs):
                    print('The flexible function has *args of', str(args),
                        "and **kwargs of", str(kwargs))
                    return True

                def unbind_a(self, btn, event):
                    btn.funbind('on_press', self.on_event_with_args, 'right',
                                    tree='birch', food='apple')

        .. note::

            Since the kv lang uses this method to bind, one has to implement
            this method, instead of :meth:`bind` when creating a non
            :class:`EventDispatcher` based class used with the kv lang. See
            :class:`Observable` for an example.

        .. versionadded:: 1.9.0

        .. versionchanged:: 1.9.1
            The `ref` keyword argument has been added.
        '''
        cdef EventObservers observers
        cdef PropertyStorage ps

        if name[:3] == 'on_':
            observers = self.__event_stack.get(name)
            if observers is not None:
                if kwargs.pop('ref', False):
                    return observers.fbind(WeakMethod(func), largs, kwargs, 1)
                else:
                    return observers.fbind(func, largs, kwargs, 0)
            return 0
        else:
            ps = self.__storage.get(name)
            if ps is None:
                return 0
            if kwargs.pop('ref', False):
                return ps.observers.fbind(WeakMethod(func), largs, kwargs, 1)
            else:
                return ps.observers.fbind(func, largs, kwargs, 0)

    def funbind(self, name, func, *largs, **kwargs):
        '''Similar to :meth:`fbind`.

        When unbinding, :meth:`unbind` will unbind all callbacks that match the
        callback, while this method will only unbind the first.

        To unbind, the same positional and keyword arguments passed to
        :meth:`fbind` must be passed on to funbind.

        .. note::

            It is safe to use :meth:`funbind` to unbind a function bound with
            :meth:`bind` as long as no keyword and positional arguments are
            provided to :meth:`funbind`.

        .. versionadded:: 1.9.0
        '''
        cdef EventObservers observers
        cdef PropertyStorage ps

        if name[:3] == 'on_':
            observers = self.__event_stack.get(name)
            if observers is not None:
                observers.funbind(func, largs, kwargs)
        else:
            ps = self.__storage.get(name)
            if ps is not None:
                ps.observers.funbind(func, largs, kwargs)

    def unbind_uid(self, name, uid):
        '''Uses the uid returned by :meth:`fbind` to unbind the callback.

        This method is much more efficient than :meth:`funbind`. If `uid`
        evaluates to False (e.g. 0) a `ValueError` is raised. Also, only
        callbacks bound with :meth:`fbind` can be unbound with this method.

        Since each call to :meth:`fbind` will generate a unique `uid`,
        only one callback will be removed. If `uid` is not found among the
        callbacks, no error is raised.

        E.g.::

            btn6 = Button(text="B: Using flexible functions with args. For hardcores.")
            uid = btn6.fbind('on_press', self.on_anything, "1", "2", monthy="python")
            if not uid:
                raise Exception('Binding failed').
            ...
            btn6.unbind_uid('on_press', uid)

        .. versionadded:: 1.9.0
        '''
        cdef EventObservers observers
        cdef PropertyStorage ps

        if name[:3] == 'on_':
            observers = self.__event_stack.get(name)
            if observers is not None:
                observers.unbind_uid(uid)
        else:
            ps = self.__storage.get(name)
            if ps is not None:
                ps.observers.unbind_uid(uid)

    def get_property_observers(self, name, args=False):
        ''' Returns a list of methods that are bound to the property/event
        passed as the *name* argument::

            widget_instance.get_property_observers('on_release')

        :Parameters:

            `name`: str
                The name of the event or property.
            `args`: bool
                Whether to return the bound args. To keep compatibility,
                only the callback functions and not their provided args will
                be returned in the list when `args` is False.

                If True, each element in the list is a 5-tuple of
                `(callback, largs, kwargs, is_ref, uid)`, where `is_ref` indicates
                whether `callback` is a weakref, and `uid` is the uid given by
                :meth:`fbind`, or None if :meth:`bind` was used. Defaults to `False`.

        :Returns:
            The list of bound callbacks. See `args` for details.

        .. versionadded:: 1.8.0

        .. versionchanged:: 1.9.0
            `args` has been added.
        '''
        cdef PropertyStorage ps
        cdef EventObservers observers

        if name[:3] == 'on_':
            observers = self.__event_stack[name]
        else:
            ps = self.__storage[name]
            observers = ps.observers
        return list(observers) if args else [item[0] for item in observers]

    def events(EventDispatcher self):
        '''Return all the events in the class. Can be used for introspection.

        .. versionadded:: 1.8.0

        '''
        return self.__event_stack.keys()

    def dispatch(self, basestring event_type, *largs, **kwargs):
        '''Dispatch an event across all the handlers added in bind/fbind().
        As soon as a handler returns True, the dispatching stops.

        The function collects all the positional and keyword arguments and
        passes them on to the handlers.

        .. note::
            The handlers are called in reverse order than they were registered
            with :meth:`bind`.

        :Parameters:
            `event_type`: basestring
                the event name to dispatch.

        .. versionchanged:: 1.9.0
            Keyword arguments collection and forwarding was added. Before, only
            positional arguments would be collected and forwarded.

        '''
        cdef EventObservers observers = self.__event_stack[event_type]
        if observers.dispatch(self, None, largs, kwargs, 1):
            return True

        handler = getattr(self, event_type)
        return handler(*largs, **kwargs)

    def dispatch_generic(self, basestring event_type, *largs, **kwargs):
        if event_type in self.__event_stack:
            return self.dispatch(event_type, *largs, **kwargs)
        return self.dispatch_children(event_type, *largs, **kwargs)

    def dispatch_children(self, basestring event_type, *largs, **kwargs):
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

        .. versionchanged:: 1.9.0
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

    def create_property(self, str name, value=None, *largs, **kwargs):
        '''Create a new property at runtime.

        .. versionadded:: 1.0.9

        .. versionchanged:: 1.8.0
            `value` parameter added, can be used to set the default value of the
            property. Also, the type of the value is used to specialize the
            created property.

        .. versionchanged:: 1.9.0
            In the past, if `value` was of type `bool`, a `NumericProperty`
            would be created, now a `BooleanProperty` is created.

            Also, now and positional and keyword arguments are passed to the
            property when created.

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


        ::

            >>> mywidget = Widget()
            >>> mywidget.create_property('custom')
            >>> mywidget.custom = True
            >>> print(mywidget.custom)
            True
        '''
        cdef Property prop
        if value is None:  # shortcut
            prop = ObjectProperty(None, *largs, **kwargs)
        if isinstance(value, bool):
            prop = BooleanProperty(value, *largs, **kwargs)
        elif isinstance(value, (int, float)):
            prop = NumericProperty(value, *largs, **kwargs)
        elif isinstance(value, string_types):
            prop = StringProperty(value, *largs, **kwargs)
        elif isinstance(value, (list, tuple)):
            prop = ListProperty(value, *largs, **kwargs)
        elif isinstance(value, dict):
            prop = DictProperty(value, *largs, **kwargs)
        else:
            prop = ObjectProperty(value, *largs, **kwargs)
        prop.link(self, name)
        prop.link_deps(self, name)
        self.__properties[name] = prop
        setattr(self.__class__, name, prop)

    def apply_property(self, **kwargs):
        '''Adds properties at runtime to the class. The function accepts
        keyword arguments of the form `prop_name=prop`, where `prop` is a
        :class:`Property` instance and `prop_name` is the name of the attribute
        of the property.

        .. versionadded:: 1.9.1

        .. warning::

            This method is not recommended for common usage because you should
            declare the properties in your class instead of using this method.

        For example::

            >>> print(wid.property('sticks', quiet=True))
            None
            >>> wid.apply_property(sticks=ObjectProperty(55, max=10))
            >>> print(wid.property('sticks', quiet=True))
            <kivy.properties.ObjectProperty object at 0x04303130>
        '''
        cdef Property prop
        cdef str name
        for name, prop in kwargs.items():
            prop.link(self, name)
            prop.link_deps(self, name)
            self.__properties[name] = prop
            setattr(self.__class__, name, prop)

    @property
    def proxy_ref(self):
        '''Default implementation of proxy_ref, returns self.
        .. versionadded:: 1.9.0
        '''
        return self


cdef class BoundCallback:

    def __cinit__(self, object func, tuple largs, dict kwargs, int is_ref,
                  uid=None):
        self.func = func
        self.largs = largs
        self.kwargs = kwargs
        self.is_ref = is_ref
        self.lock = unlocked
        self.prev = self.next = None
        self.uid = uid


cdef class EventObservers:
    '''A class that stores observers as a doubly linked list. See dispatch
    for more details on locking and deletion of observers.

    In all instances, largs and kwargs if None or empty are all converted
    to None internally before storing or comparing.
    '''

    def __cinit__(self, int dispatch_reverse=0, dispatch_value=1):
        self.dispatch_reverse = dispatch_reverse
        self.dispatch_value = dispatch_value
        self.last_callback = self.first_callback = None
        self.uid = 1  # start with 1 so uid is always evaluated to True

    cdef inline void bind(self, object observer, object src_observer, int is_ref) except *:
        '''Bind the observer to the event. If this observer has already been
        bound, we don't add it again.
        '''
        cdef BoundCallback callback = self.first_callback
        cdef BoundCallback new_callback
        cdef int cb_equal

        while callback is not None:
            if is_ref and not callback.is_ref:
                cb_equal = callback.func == src_observer
            elif callback.is_ref and not is_ref:
                cb_equal = callback.func() == observer
            elif is_ref:
                cb_equal = callback.func() == src_observer
            else:
                cb_equal = callback.func == observer
            if (callback.lock != deleted and callback.largs is None and
                callback.kwargs is None and cb_equal):
                return
            callback = callback.next

        new_callback = BoundCallback(observer, None, None, is_ref)
        if self.first_callback is None:
            self.last_callback = self.first_callback = new_callback
        else:
            self.last_callback.next = new_callback
            new_callback.prev = self.last_callback
            self.last_callback = new_callback

    cdef inline object fbind(self, object observer, tuple largs, dict kwargs,
                               int is_ref):
        '''Similar to bind, except it accepts largs, kwargs that is forwards.
        is_ref, if true, will mark the observer that it is a ref so that we
        can unref it before calling.
        '''
        cdef object uid = self.uid
        self.uid += 1
        cdef BoundCallback new_callback = BoundCallback(
            observer, largs if largs else None, kwargs if kwargs else None,
            is_ref, uid)

        if self.first_callback is None:
            self.last_callback = self.first_callback = new_callback
        else:
            self.last_callback.next = new_callback
            new_callback.prev = self.last_callback
            self.last_callback = new_callback
        return uid

    cdef inline void unbind(self, object observer, int stop_on_first) except *:
        '''Removes the observer. If is_ref, he observers will be derefed before
        comparing to observer, if they are refed. If stop_on_first, after the
        first match we return.
        '''
        cdef object f
        cdef BoundCallback callback = self.first_callback

        while callback is not None:
            # try a quick comparison
            if callback.lock == deleted or callback.largs is not None or callback.kwargs is not None:
                callback = callback.next
                continue

            # now match the actual callback function
            if callback.is_ref:
                f = callback.func()
            else:
                f = callback.func
            if f != observer:
                callback = callback.next
                continue

            self.remove_callback(callback)
            callback = callback.next

            if stop_on_first:
                return

    cdef inline void funbind(self, object observer, tuple largs, dict kwargs) except *:
        '''Similar to unbind, except we only remove the first match, and
        we don't deref the observers before comparing to observer. The
        largs and kwargs must match the largs and kwargs from when binding.
        '''
        cdef BoundCallback callback = self.first_callback
        largs = largs if largs else None
        kwargs = kwargs if kwargs else None

        while callback is not None:
            if (callback.lock == deleted or
                not callback.is_ref and callback.func != observer or
                callback.is_ref and callback.func() != observer or
                callback.largs != largs or callback.kwargs != kwargs):
                callback = callback.next
                continue

            self.remove_callback(callback)
            return

    cdef inline object unbind_uid(self, object uid):
        '''Remove the callback identified by the uid. If passed uid is None,
        a ValueError is raised.
        '''
        cdef BoundCallback callback = self.first_callback
        if not uid:
            raise ValueError(
                'uid, {}, that evaluates to False is not valid'.format(uid))

        while callback is not None:
            if callback.uid != uid:
                callback = callback.next
                continue

            if callback.lock != deleted:
                self.remove_callback(callback)
            return

    cdef inline void remove_callback(self, BoundCallback callback, int force=0) except *:
        '''Removes the callback from the doubly linked list. If the callback is
        locked, unless forced, the lock is changed to deleted and the callback
        is not removed.

        Assumes that callback.lock is either locked, or unlocked, not deleted
        except if force, then it can be anything.
        '''
        if callback.lock == locked and not force:
            callback.lock = deleted
        else:
            if callback.prev is not None:
                callback.prev.next = callback.next
            else:
                self.first_callback = callback.next
            if callback.next is not None:
                callback.next.prev = callback.prev
            else:
                self.last_callback = callback.prev

    cdef inline object _dispatch(
        self, object f, tuple slargs, dict skwargs, object obj, object value,
        tuple largs, dict kwargs):
        '''Dispatches the the callback with the args. f is the (derefed)
        callback. slargs, skwargs are the bound-time provided args. largs, kwargs
        are the dispatched args. The order of args is slargs, obj, value,
        skwargs updated with kwargs. If dispatch_value is False, value is skipped.
        '''
        cdef object result
        cdef dict d
        cdef tuple param = (obj, value) if self.dispatch_value else (obj, )
        cdef tuple fargs = None

        if slargs is not None and skwargs is not None:  # both kw and largs
            if largs is not None:
                fargs = slargs + param + largs
            else:
                fargs = slargs + param

            if kwargs is not None:
                d = dict(skwargs)
                d.update(kwargs)
            else:
                d = skwargs

            return f(*fargs, **d)
        elif slargs is not None:  # only largs
            if largs is not None:
                fargs = slargs + param + largs
            else:
                fargs = slargs + param

            if kwargs is None:
                return f(*fargs)
            else:
                return f(*fargs, **kwargs)
        elif skwargs is not None:  # only kwargs
            if kwargs is not None:
                d = dict(skwargs)
                d.update(kwargs)
            else:
                d = skwargs

            if largs is None:
                if self.dispatch_value:
                    return f(obj, value, **d)
                else:
                    return f(obj, **d)
            else:
                if self.dispatch_value:
                    return f(obj, value, *largs, **d)
                else:
                    return f(obj, *largs, **d)
        else:  # no args
            if largs is None:
                if kwargs is None:
                    if self.dispatch_value:
                        return f(obj, value)
                    else:
                        return f(obj)
                else:
                    if self.dispatch_value:
                        return f(obj, value, **kwargs)
                    else:
                        return f(obj, **kwargs)
            else:
                if kwargs is None:
                    if self.dispatch_value:
                        return f(obj, value, *largs)
                    else:
                        return f(obj, *largs)
                else:
                    if self.dispatch_value:
                        return f(obj, value, *largs, **kwargs)
                    else:
                        return f(obj, *largs, **kwargs)

    cdef inline int dispatch(self, object obj, object value, tuple largs,
                             dict kwargs, int stop_on_true) except 2:
        '''Dispatches obj, value to all bound observers. If largs and/or kwargs,
        they are forwarded after obj, value. if stop_on_true, if a observer returns
        true, the function stops and returns true.

        If dispatch_reverse is True, we dispatch starting with last bound callback,
        otherwise we start with the first.

        The logic and reason for locking callbacks is as followes. During a dispatch,
        arbitrary code can be executed, therefore, as we traverse and execute
        each callback, the callback may in turn bind. unbind or even cause a
        new dispatch recursively many times. Therefore, our goal should be to
        during a dispatch, allow such recursiveness, while at each level, only
        dispatch the callbacks that existed when we started dispatching, but
        not including callbacks removed during dispatching.

        Essentially, we want to make a copy of the callbacks as exited during
        start of dispatching, while allowing removal of callbacks. With a python
        list, we'd have to make a copy of the list and before each callback, we
        check the original list to see if the callback has been removed. We solve
        this issue for the doubly linked list using locks.

        At each recursion level, if a callback is already locked by a higher level,
        we can mark it deleted but not actually delete it or unlock it. Also, that level
        is responsible for deleting the callbacks it locked if a lower
        level marked them deleted, otherwise it just unlocks them before returning.
        So a callback locked by a level, is guaranteed to not be removed (but at most
        marked for deletion) by a recursive dispatch.

        Each callback as it is dispatched is locked. Also, the last callback
        scheduled to be executed is immediately locked, so that we know where to
        stop, in case new callbacks are added.
        '''
        cdef BoundCallback callback, final
        cdef object f, result
        cdef BoundLock current_lock, last_lock
        cdef int done = 0, res = 0, reverse = self.dispatch_reverse

        if reverse:  # dispatch starting from last until first
            callback = self.last_callback  # start callback
            final = self.first_callback  # last callback
        else:
            callback = self.first_callback
            final = self.last_callback
        if callback is None:
            return 0


        last_lock = final.lock  # save the state of the lock of final callback
        if last_lock == unlocked:  # lock the final callback
            final.lock = locked

        while not done and callback is not None:
            done = final is callback

            if callback.lock == deleted:
                callback = callback.prev if reverse else callback.next
                continue

            # save the lock state (currently only either locked or unlocked)
            current_lock = callback.lock
            if current_lock == unlocked:  # and lock it if unlocked
                callback.lock = locked

            if callback.is_ref:
                f = callback.func()
                if f is None:
                    self.remove_callback(callback, current_lock == unlocked)
                    callback = callback.prev if reverse else callback.next
                    continue
            else:
                f = callback.func

            result = self._dispatch(
                f, callback.largs, callback.kwargs, obj, value, largs, kwargs)

            if current_lock == unlocked:  # now unlock/delete if it was unlocked
                if callback.lock == deleted:
                    self.remove_callback(callback, 1)
                else:
                    callback.lock = unlocked

            if result and stop_on_true:
                res = done = 1
            callback = callback.prev if reverse else callback.next

        # now unlock/delete the final callback if we locked it
        if last_lock == unlocked:
            if final.lock == deleted:
                self.remove_callback(final, 1)
            else:
                final.lock = unlocked
        return res

    def __iter__(self):
        '''Binding/unbinding/dispatching while iterating can lead to invalid
        data.
        '''
        cdef BoundCallback callback = self.first_callback

        while callback is not None:
            yield (
                callback.func, callback.largs if callback.largs is not None else (),
                callback.kwargs if callback.kwargs is not None else {},
                callback.is_ref, callback.uid)
            callback = callback.next
