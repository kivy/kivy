'''
Properties
==========

The *Properties* classes are used when you create a
:class:`~kivy.uix.widget.Widget`.

.. warning::
        Kivy's Properties are **not to be confused** with Python's
        properties (i.e. the ``@property`` decorator and the <property> type).

Kivy's property classes support:

    Value Checking / Validation
        When you assign a new value to a property, the value is checked to pass
        some constraints implemented in the class. I.e., validation is
        performed. For example, an :class:`OptionProperty` will make sure that
        the value is in a predefined list of possibilities.
        A :class:`NumericProperty` will check that your value is a numeric type,
        i.e. int, float, etc.
        This prevents many errors early on.

    Observer Pattern
        You can specify what should happen when a property's value changes.
        You can bind your own function as a callback to changes of a
        :class:`Property`. If, for example, you want a piece of code to be
        called when a widget's :class:`~kivy.uix.widget.Widget.pos` property
        changes, you can :class:`~kivy.uix.widget.Widget.bind` a function to it.

    Better Memory Management
        The same instance of a property is shared across multiple widget
        instances. The value storage is independent of the Widget.

'''

#cython: profile=True
#cython: embedsignature=True


__all__ = ('NumericProperty', 'StringProperty', 'ListProperty',
           'ObjectProperty', 'BooleanProperty', 'BoundedNumericProperty',
           'OptionProperty', 'ReferenceListProperty', 'AliasProperty',
           'NumericProperty', 'Property')


cdef class Property:
    '''Base class for building more complex properties.

    This class handles all the basic setters and getters, None type handling,
    the observer list and storage initialisation. This class should not be
    directly instantiated.
    '''

    cdef str _name
    cdef int allownone
    cdef object defaultvalue
    cdef dict storage

    def __cinit__(self):
        self._name = ''
        self.allownone = 0
        self.defaultvalue = None
        self.storage = {}

    def __init__(self, defaultvalue, **kw):
        self.defaultvalue = defaultvalue
        self.allownone = <int>kw.get('allownone', 0)

    property name:
        def __get__(self):
            return self._name

    cdef init_storage(self, dict storage):
        storage['value'] = self.defaultvalue
        storage['allownone'] = self.allownone
        storage['observers'] = []

    cpdef link(self, object obj, str name):
        '''Link the instance with its real name.

        .. warning::

            Internal usage only.

        When a widget is defined and uses a :class:`Property` class, the
        creation of the property object happens, but the instance doesn't know
        anything about its name in the widget class::

            class MyWidget(Widget):
                uid = NumericProperty(0)

        In this example, the uid will be a NumericProperty() instance, but the
        property instance doesn't know its name. That's why :func:`link` is used
        in Widget.__new__. The link function is also used to create the storage
        space of the property for this specific widget instance.
        '''
        d = dict()
        self._name = name
        self.init_storage(d)
        self.storage[obj.__uid] = d

    cpdef link_deps(self, object obj, str name):
        pass

    cpdef unlink(self, obj):
        '''Destroy the storage of a widget
        '''
        if obj in self.storage:
            del self.storage[obj.__uid]

    cpdef bind(self, obj, observer):
        '''Add a new observer to be called only when the value is changed
        '''
        observers = self.storage[obj.__uid]['observers']
        if not observer in observers:
            observers.append(observer)

    cpdef unbind(self, obj, observer):
        '''Remove the observer from our widget observer list
        '''
        if obj.__uid not in self.storage:
            return
        observers = self.storage[obj.__uid]['observers']
        if observer in observers:
            observers.remove(observer)

    def __set__(self, obj, val):
        self.set(obj, val)

    def __get__(self, obj, objtype):
        if obj is None:
            return self
        return self.get(obj)

    cdef compare_value(self, a, b):
        return a == b

    cpdef set(self, obj, value):
        '''Set a new value for the property
        '''
        value = self.convert(obj, value)
        d = self.storage[obj.__uid]
        realvalue = d['value']
        if self.compare_value(realvalue, value):
            return False
        self.check(obj, value)
        d['value'] = value
        self.dispatch(obj)
        return True

    cpdef get(self, obj):
        '''Return the value of the property
        '''
        return self.storage[obj.__uid]['value']

    #
    # Private part
    #

    cdef check(self, obj, x):
        '''Check if the value is correct or not, depending on the settings of
        the property class.

        :Returns:
            bool, True if the value correctly validates.
        '''
        if x is None:
            if not self.storage[obj.__uid]['allownone']:
                raise ValueError('None is not allowed')
            else:
                return True

    cdef convert(self, obj, x):
        '''Convert the initial value to a correctly validating value.
        Can be used for multiple types of argument, and simplify into only one.
        '''
        return x

    cdef dispatch(self, obj):
        '''Dispatch the value change to all observers
        '''
        observers = self.storage[obj.__uid]['observers']
        value = self.storage[obj.__uid]['value']
        for observer in observers:
            observer(obj, value)


cdef class NumericProperty(Property):
    '''Property that represents a numeric value

    The NumericProperty accepts only int or float.

    >>> Widget.x = 42
    >>> print Widget.x
    42
    >>> Widget.x = "plop"
    Traceback (most recent call last):
        File "<stdin>", line 1, in <module>
        File "properties.pyx", line 93, in kivy.properties.Property.__set__
        File "properties.pyx", line 111, in kivy.properties.Property.set
        File "properties.pyx", line 159, in kivy.properties.NumericProperty.check
        ValueError: NumericProperty accepts only int/float
    '''
    cdef check(self, obj, value):
        if Property.check(self, obj, value):
            return True
        if type(value) not in (int, float):
            raise ValueError('NumericProperty accepts only int/float')


cdef class StringProperty(Property):
    '''Property that represents a string value.

    Only string or unicode are accepted.
    '''
    cdef check(self, obj, value):
        if Property.check(self, obj, value):
            return True
        if not isinstance(value, basestring):
            raise ValueError('StringProperty accepts only str/unicode')


class ObservableList(list):
    # Internal class to observe changes inside a native python list.
    def __init__(self, *largs):
        self.prop = largs[0]
        self.obj = largs[1]
        super(ObservableList, self).__init__(*largs[2:])

    def __setitem__(self, key, value):
        list.__setitem__(self, key, value)
        cdef Property prop = self.prop
        prop.dispatch(self.obj)

    def __delitem__(self, key):
        list.__delitem__(self, key)
        cdef Property prop = self.prop
        prop.dispatch(self.obj)

    def __setslice__(self, *largs):
        list.__setslice__(self, *largs)
        cdef Property prop = self.prop
        prop.dispatch(self.obj)

    def __delslice__(self, *largs):
        list.__delslice__(self, *largs)
        cdef Property prop = self.prop
        prop.dispatch(self.obj)

    def __iadd__(self, *largs):
        list.__iadd__(self, *largs)
        cdef Property prop = self.prop
        prop.dispatch(self.obj)

    def __imul__(self, *largs):
        list.__imul__(self, *largs)
        cdef Property prop = self.prop
        prop.dispatch(self.obj)

    def __add__(self, *largs):
        cdef object result = list.__add__(self, *largs)
        cdef Property prop = self.prop
        prop.dispatch(self.obj)
        return result

    def append(self, *largs):
        list.append(self, *largs)
        cdef Property prop = self.prop
        prop.dispatch(self.obj)

    def remove(self, *largs):
        list.remove(self, *largs)
        cdef Property prop = self.prop
        prop.dispatch(self.obj)

    def insert(self, *largs):
        list.insert(self, *largs)
        cdef Property prop = self.prop
        prop.dispatch(self.obj)

    def pop(self, *largs):
        list.pop(self, *largs)
        cdef Property prop = self.prop
        prop.dispatch(self.obj)

    def extend(self, *largs):
        list.extend(self, *largs)
        cdef Property prop = self.prop
        prop.dispatch(self.obj)

    def sort(self, *largs):
        list.sort(self, *largs)
        cdef Property prop = self.prop
        prop.dispatch(self.obj)


cdef class ListProperty(Property):
    '''Property that represents a list.

    Only lists are allowed, tuple or any other classes are forbidden.

    .. warning::

        To mark the property as changed, you must reassign a new list each
        time you want to add or remove an object. Don't rely on append(),
        remove() and pop() functions.
    '''
    cpdef link(self, object obj, str name):
        Property.link(self, obj, name)
        storage = self.storage[obj.__uid]
        storage['value'] = ObservableList(self, obj, storage['value'])

    cdef check(self, obj, value):
        if Property.check(self, obj, value):
            return True
        if type(value) is not ObservableList:
            raise ValueError('ListProperty accepts only ObservableList'
                             ' (should never happen.)')

    cpdef set(self, obj, value):
        value = ObservableList(self, obj, value)
        Property.set(self, obj, value)

cdef class ObjectProperty(Property):
    '''Property that represents a Python object.

    .. warning::

        To mark the property as changed, you must reassign a new python object.
    '''
    cdef check(self, obj, value):
        if Property.check(self, obj, value):
            return True
        if not isinstance(value, object):
            raise ValueError('ObjectProperty accepts only Python objects')

cdef class BooleanProperty(Property):
    '''Property that represents only boolean
    '''
    cdef check(self, obj, value):
        if Property.check(self, obj, value):
            return True
        if not isinstance(value, object):
            raise ValueError('BooleanProperty accepts only bool')

cdef class BoundedNumericProperty(Property):
    '''Property that represents a numeric value within a minimum bound and/or
    maximum bound (i.e. a numeric range).

    :Parameters:
        `min`: numeric
            If set, minimum bound will be used, with the value of min
        `max`: numeric
            If set, maximum bound will be used, with the value of max
    '''
    cdef int use_min
    cdef int use_max
    cdef long min
    cdef long max

    def __cinit__(self):
        self.use_min = 0
        self.use_max = 0
        self.min = 0
        self.max = 0

    def __init__(self, *largs, **kw):
        value = kw.get('min', None)
        if value is None:
            self.use_min = 0
        else:
            self.use_min = 1
            self.min = value
        value = kw.get('max', None)
        if value is None:
            self.use_max = 0
        else:
            self.use_max = 1
            self.max = value
        Property.__init__(self, *largs, **kw)

    cdef init_storage(self, dict storage):
        Property.init_storage(self, storage)
        storage['min'] = self.min
        storage['max'] = self.max
        storage['use_min'] = self.use_min
        storage['use_max'] = self.use_max

    cdef check(self, obj, value):
        if Property.check(self, obj, value):
            return True
        s = self.storage['obj']
        if s['use_min']:
            _min = s['min']
            if _min and value < _min:
                raise ValueError('Value is below the minimum bound (%d)' % _min)
        if s['use_max']:
            _max = s['max']
            if _max and value > _max:
                raise ValueError('Value is above the maximum bound (%d)' % _max)
        return True


cdef class OptionProperty(Property):
    '''Property that represents a string from a predefined list of valid
    options.

    If the string set in the property is not in the list of valid options
    (passed at property creation time), a ValueError exception will be raised.

    :Parameters:
        `options`: list (not tuple.)
            List of valid options
    '''
    cdef list options

    def __cinit__(self):
        self.options = []

    def __init__(self, *largs, **kw):
        self.options = <list>(kw.get('options', []))
        Property.__init__(self, *largs, **kw)

    cdef init_storage(self, dict storage):
        Property.init_storage(self, storage)
        storage['options'] = self.options[:]

    cdef check(self, obj, value):
        if Property.check(self, obj, value):
            return True
        valid_options = self.storage[obj.__uid]['options']
        if value not in valid_options:
            raise ValueError('Value %r is not a valid option. Must be one of: '
                             '%s' % (value, valid_options))


cdef class ReferenceListProperty(Property):
    '''Property that allows to create a tuple of other properties.

    For example, if `x` and `y` are :class:`NumericProperty`s, we can create a
    :class:`ReferenceListProperty` for the `pos`. If you change the value of
    `pos`, it will automatically change the values of `x` and `y` accordingly.
    If you read the value of `pos`, it will return a tuple with the values of
    `x` and `y`.
    '''
    cdef list properties

    def __cinit__(self):
        self.properties = list()

    def __init__(self, *largs, **kw):
        for prop in largs:
            self.properties.append(prop)
        Property.__init__(self, largs, **kw)

    cdef init_storage(self, dict storage):
        Property.init_storage(self, storage)
        storage['properties'] = self.properties
        storage['stop_event'] = 0

    cpdef link_deps(self, object obj, str name):
        Property.link_deps(self, obj, name)
        for prop in self.properties:
            prop.bind(obj, self.trigger_change)
        self.trigger_change(obj, None)

    cpdef unlink(self, obj):
        for prop in self.properties:
            prop.unbind(obj, self.trigger_change)
        Property.unlink(self, obj)

    cpdef trigger_change(self, obj, value):
        s = self.storage[obj.__uid]
        p = s['properties']
        if s['stop_event']:
            return
        s['value'] = [p[x].get(obj) for x in xrange(len(p))]
        self.dispatch(obj)

    cdef convert(self, obj, value):
        if not isinstance(value, (list, tuple)):
            raise ValueError('Value must be a list or a tuple')
        return <list>value

    cdef check(self, obj, value):
        if len(value) != len(self.storage[obj.__uid]['properties']):
            raise ValueError('Value length is immutable')

    cpdef set(self, obj, value):
        cdef int idx
        storage = self.storage[obj.__uid]
        value = self.convert(obj, value)
        if self.compare_value(storage['value'], value):
            return False
        self.check(obj, value)
        # prevent dependency loop
        storage['stop_event'] = 1
        props = storage['properties']
        for idx in xrange(len(props)):
            prop = props[idx]
            x = value[idx]
            prop.set(obj, x)
        storage['stop_event'] = 0
        storage['value'] = value
        self.dispatch(obj)
        return True


cdef class AliasProperty(Property):
    '''Create a property with a custom getter and setter.

    If you didn't find a Property class that fits to your needs, you can still
    create Python getters and setters and create a property with both of them.

    Example from kivy/uix/widget.py ::

        def get_right(self):
            return self.x + self.width
        def set_right(self, value):
            self.x = value - self.width
        right = AliasProperty(get_right, set_right, bind=(x, width))

    :Parameters:
        `getter`: function
            Function to use as a property getter
        `setter`: function
            Function to use as a property setter
        `bind`: list/tuple
            List of properties to observe for changes
    '''
    cdef object getter
    cdef object setter
    cdef list bind_objects

    def __cinit__(self):
        self.getter = None
        self.setter = None
        self.bind_objects = list()

    def __init__(self, getter, setter, **kwargs):
        Property.__init__(self, None, **kwargs)
        self.getter = getter
        self.setter = setter
        self.bind_objects = list(kwargs.get('bind', []))

    cdef init_storage(self, dict storage):
        Property.init_storage(self, storage)
        storage['getter'] = self.getter
        storage['setter'] = self.setter

    cpdef link_deps(self, object obj, str name):
        for prop in self.bind_objects:
            oprop = getattr(obj.__class__, prop)
            oprop.bind(obj, self.trigger_change)

    cpdef unlink(self, obj):
        for prop in self.bind_objects:
            oprop = getattr(obj.__class__, prop)
            oprop.unbind(obj, self.trigger_change)
        Property.unlink(self, obj)

    cpdef trigger_change(self, obj, value):
        self.dispatch(obj)

    cdef check(self, obj, value):
        return True

    cpdef get(self, obj):
        return self.storage[obj.__uid]['getter'](obj)

    cpdef set(self, obj, value):
        if self.storage[obj.__uid]['setter'](obj, value):
            self.dispatch(obj)

