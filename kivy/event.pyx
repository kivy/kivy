'''
Event dispatcher
================

All objects that produce events in Kivy implement :class:`EventDispatcher`,
providing a consistent interface for registering and manipulating event
handlers.


.. versionchanged:: 1.0.9

    Properties discovering and methods have been moved from
    :class:`~kivy.uix.widget.Widget` to :class:`EventDispatcher`

'''

__all__ = ('EventDispatcher', )


from kivy.weakmethod import WeakMethod
from kivy.properties cimport Property, ObjectProperty

cdef tuple forbidden_properties = ('touch_down', 'touch_move', 'touch_up')
cdef int widget_uid = 0
cdef dict cache_properties = {}

cdef class EventDispatcher(object):
    '''Generic event dispatcher interface

    See the module docstring for usage.
    '''

    cdef dict __event_stack
    cdef dict __properties

    def __cinit__(self, *largs, **kwargs):
        global widget_uid, cache_properties
        cdef dict widget_dict = self.__dict__
        cdef dict cp = cache_properties
        cdef dict attrs_found
        cdef list attrs
        cdef Property attr
        cdef str k
        self.__event_stack = {}
        __cls__ = self.__class__

        # XXX for the moment, we need to create a uniq id for properties.
        # Properties need a identifier to the class instance. hash() and id()
        # are longer than using a custom __uid. I hope we can figure out a way
        # of doing that without require any python code. :)
        widget_uid += 1
        widget_dict['__uid'] = widget_uid
        widget_dict['__storage'] = {}

        if __cls__ not in cp:
            attrs_found = cp[__cls__] = {}
            attrs = dir(__cls__)
            for k in attrs:
                uattr = getattr(__cls__, k)
                if not isinstance(uattr, Property):
                    continue
                if k in forbidden_properties:
                    raise Exception('The property <%s> have a forbidden name' % k)
                attrs_found[k] = uattr
        else:
            attrs_found = cp[__cls__]

        # First loop, link all the properties storage to our instance
        for k in attrs_found:
            attr = attrs_found[k]
            attr.link(self, k)

        # Second loop, resolve all the reference
        for k in attrs_found:
            attr = attrs_found[k]
            attr.link_deps(self, k)

        self.__properties = attrs_found

    def __init__(self, **kwargs):
        cdef str func, name, key
        cdef dict properties
        super(EventDispatcher, self).__init__()

        # Auto bind on own handler if exist
        properties = self.properties()
        for func in dir(self):
            if not func.startswith('on_'):
                continue
            name = func[3:]
            if name in properties:
                self.bind(**{name: getattr(self, func)})

        # Apply the existing arguments to our widget
        for key, value in kwargs.iteritems():
            if key in properties:
                setattr(self, key, value)

    def register_event_type(self, str event_type):
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
            w.dispatch('on_swipe')
        '''

        if not event_type.startswith('on_'):
            raise Exception('A new event must start with "on_"')

        # Ensure the user have at least declare the default handler
        if not hasattr(self, event_type):
            raise Exception(
                'Missing default handler <%s> in <%s>' % (
                event_type, self.__class__.__name__))

        # Add the event type to the stack
        if not event_type in self.__event_stack:
            self.__event_stack[event_type] = []

    def unregister_event_types(self, str event_type):
        '''Unregister an event type in the dispatcher
        '''
        if event_type in self.__event_stack:
            del self.__event_stack[event_type]

    def is_event_type(self, str event_type):
        '''Return True if the event_type is already registered.

        .. versionadded:: 1.0.4
        '''
        return event_type in self.__event_stack

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

        Usage in a class::

            class MyClass(BoxLayout):
                def __init__(self):
                    super(MyClass, self).__init__(**kwargs)
                    btn = Button(text='click on')
                    btn.bind(on_press=self.my_callback) #bind event
                    self.add_widget(btn)

                def my_callback(self,obj,value):
                    print 'press on button', obj, 'with date:', value

        '''
        for key, value in kwargs.iteritems():
            if key[:3] == 'on_':
                if key not in self.__event_stack:
                    continue
                # convert the handler to a weak method
                handler = WeakMethod(value)
                self.__event_stack[key].append(handler)
            else:
                self.__properties[key].bind(self, value)

    def unbind(self, **kwargs):
        '''Unbind properties from callback functions.

        Same usage as :func:`bind`.
        '''
        for key, value in kwargs.iteritems():
            if key[:3] == 'on_':
                if key not in self.__event_stack:
                    continue
                # we need to execute weak method to be able to compare
                for handler in self.__event_stack[key]:
                    if handler() != value:
                        continue
                    self.__event_stack[key].remove(handler)
                    break
            else:
                self.__properties[key].unbind(self, value)

    def dispatch(self, str event_type, *largs):
        '''Dispatch an event across all the handler added in bind().
        As soon as a handler return True, the dispatching stop
        '''
        cdef list event_stack = self.__event_stack[event_type]
        cdef object remove = event_stack.remove
        for value in event_stack[:]:
            handler = value()
            if handler is None:
                # handler have gone, must be removed
                remove(value)
                continue
            if handler(self, *largs):
                return True

        handler = getattr(self, event_type)
        return handler(*largs)

    #
    # Properties
    #
    def setter(self, name):
        '''Return the setter of a property. Useful if you want to directly bind
        a property to another.

        .. versionadded:: 1.0.9

        For example, if you want to position one widget next to you::

            self.bind(right=nextchild.setter('x'))
        '''
        return self.__properties[name].__set__

    def getter(self, name):
        '''Return the getter of a property.

        .. versionadded:: 1.0.9
        '''
        return self.__properties[name].__get__

    def property(self, name):
        '''Get a property instance from the name.

        .. versionadded:: 1.0.9

        :return:
        
            A :class:`~kivy.properties.Property` derivated instance corresponding
            to the name.
        '''
        return self.__properties[name]

    cpdef dict properties(self):
        '''Return all the properties in that class in a dictionnary of
        key/property class. Can be used for introspection.

        .. versionadded:: 1.0.9
        '''
        cdef dict ret, p
        ret = {}
        p = self.__properties
        for x in self.__dict__['__storage'].keys():
            ret[x] = p[x]
        return ret

    def create_property(self, name):
        '''Create a new property at runtime.

        .. versionadded:: 1.0.9

        .. warning::

            This function is designed for the Kivy language, don't use it in
            your code. You should declare the property in your class instead of
            using this method.

        :Parameters:
            `name`: string
                Name of the property

        The class of the property cannot be specified, it will always be an
        :class:`~kivy.properties.ObjectProperty` class. The default value of the
        property will be None, until you set a new value.

        >>> mywidget = Widget()
        >>> mywidget.create_property('custom')
        >>> mywidget.custom = True
        >>> print mywidget.custom
        True
        '''
        prop = ObjectProperty(None)
        prop.link(self, name)
        prop.link_deps(self, name)
        self.__properties[name] = prop
        setattr(self.__class__, name, prop)


