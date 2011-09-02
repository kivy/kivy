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
        instances.

'''

#cython: profile=True
#cython: embedsignature=True


__all__ = ('Property',
           'NumericProperty', 'StringProperty', 'ListProperty',
           'ObjectProperty', 'BooleanProperty', 'BoundedNumericProperty',
           'OptionProperty', 'ReferenceListProperty', 'AliasProperty',
           'DictProperty')

from weakref import ref

cdef class Property:
    '''Base class for building more complex properties.

    This class handles all the basic setters and getters, None type handling,
    the observer list and storage initialisation. This class should not be
    directly instantiated.

    By default, a :class:`Property` always take a default value::

        class MyObject(Widget):

            hello = Property('Hello world')

    The default value must be a value that agreed about the Property type. For
    example, you can't set a list to a :class:`StringProperty`, because the
    StringProperty will check the default value.

    None is a special case: you can set the default value of a Property to None,
    but you can't set None to a property afterwise.
    If you really want to do that, you must declare the Property with
    `allownone=True`::

        class MyObject(Widget):

            hello = ObjectProperty(None, allownone=True)

        # then later
        a = MyObject()
        a.hello = 'bleh' # working
        a.hello = None # working too, because allownone is True.
    '''

    cdef str _name
    cdef int allownone
    cdef object defaultvalue

    def __cinit__(self):
        self._name = ''
        self.allownone = 0
        self.defaultvalue = None

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
        obj.__storage[name] = d

    cpdef link_deps(self, object obj, str name):
        pass

    cpdef bind(self, obj, observer):
        '''Add a new observer to be called only when the value is changed
        '''
        observers = obj.__storage[self._name]['observers']
        if not observer in observers:
            observers.append(observer)

    cpdef unbind(self, obj, observer):
        '''Remove the observer from our widget observer list
        '''
        observers = obj.__storage[self._name]['observers']
        for obj in observers[:]:
            if obj is observer:
                observers.remove(obj)

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
        d = obj.__storage[self._name]
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
        return obj.__storage[self._name]['value']

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
            if not obj.__storage[self._name]['allownone']:
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
        cdef dict storage = obj.__storage[self._name]
        observers = storage['observers']
        value = storage['value']
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
            raise ValueError('NumericProperty<%s> accepts only int/float' % self.name)


cdef class StringProperty(Property):
    '''Property that represents a string value.

    Only string or unicode are accepted.
    '''
    cdef check(self, obj, value):
        if Property.check(self, obj, value):
            return True
        if not isinstance(value, basestring):
            raise ValueError('StringProperty<%s> accepts only str/unicode' %
                             self.name)

cdef inline void observable_list_dispatch(object self):
    cdef Property prop = self.prop
    obj = self.obj()
    if obj is not None:
        prop.dispatch(obj)

class ObservableList(list):
    # Internal class to observe changes inside a native python list.
    def __init__(self, *largs):
        self.prop = largs[0]
        self.obj = ref(largs[1])
        super(ObservableList, self).__init__(*largs[2:])

    def __setitem__(self, key, value):
        list.__setitem__(self, key, value)
        observable_list_dispatch(self)

    def __delitem__(self, key):
        list.__delitem__(self, key)
        observable_list_dispatch(self)

    def __setslice__(self, *largs):
        list.__setslice__(self, *largs)
        observable_list_dispatch(self)

    def __delslice__(self, *largs):
        list.__delslice__(self, *largs)
        observable_list_dispatch(self)

    def __iadd__(self, *largs):
        list.__iadd__(self, *largs)
        observable_list_dispatch(self)

    def __imul__(self, *largs):
        list.__imul__(self, *largs)
        observable_list_dispatch(self)

    def __add__(self, *largs):
        cdef object result = list.__add__(self, *largs)
        observable_list_dispatch(self)
        return result

    def append(self, *largs):
        list.append(self, *largs)
        observable_list_dispatch(self)

    def remove(self, *largs):
        list.remove(self, *largs)
        observable_list_dispatch(self)

    def insert(self, *largs):
        list.insert(self, *largs)
        observable_list_dispatch(self)

    def pop(self, *largs):
        list.pop(self, *largs)
        observable_list_dispatch(self)

    def extend(self, *largs):
        list.extend(self, *largs)
        observable_list_dispatch(self)

    def sort(self, *largs):
        list.sort(self, *largs)
        observable_list_dispatch(self)


cdef class ListProperty(Property):
    '''Property that represents a list.

    Only lists are allowed, tuple or any other classes are forbidden.
    '''
    cpdef link(self, object obj, str name):
        Property.link(self, obj, name)
        storage = obj.__storage[self._name]
        storage['value'] = ObservableList(self, obj, storage['value'])

    cdef check(self, obj, value):
        if Property.check(self, obj, value):
            return True
        if type(value) is not ObservableList:
            raise ValueError('ListProperty<%s> accepts only ObservableList'
                             ' (should never happen.)' % self.name)

    cpdef set(self, obj, value):
        value = ObservableList(self, obj, value)
        Property.set(self, obj, value)

cdef inline void observable_dict_dispatch(object self):
    cdef Property prop = self.prop
    prop.dispatch(self.obj)

class ObservableDict(dict):
    # Internal class to observe changes inside a native python dict.
    def __init__(self, *largs):
        self.prop = largs[0]
        self.obj = largs[1]
        super(ObservableDict, self).__init__(*largs[2:])

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        observable_dict_dispatch(self)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        observable_dict_dispatch(self)

    def clear(self, *largs):
        dict.append(self, *largs)
        observable_dict_dispatch(self)

    def remove(self, *largs):
        dict.remove(self, *largs)
        observable_dict_dispatch(self)

    def pop(self, *largs):
        dict.pop(self, *largs)
        observable_dict_dispatch(self)

    def popitem(self, *largs):
        dict.popitem(self, *largs)
        observable_dict_dispatch(self)

    def setdefault(self, *largs):
        dict.setdefault(self, *largs)
        observable_dict_dispatch(self)

    def update(self, *largs):
        dict.update(self, *largs)
        observable_dict_dispatch(self)



cdef class DictProperty(Property):
    '''Property that represents a dict.

    Only dict are allowed, any other classes are forbidden.
    '''
    cpdef link(self, object obj, str name):
        Property.link(self, obj, name)
        storage = obj.__storage[self._name]
        storage['value'] = ObservableDict(self, obj, storage['value'])

    cdef check(self, obj, value):
        if Property.check(self, obj, value):
            return True
        if type(value) is not ObservableDict:
            raise ValueError('DictProperty<%s> accepts only ObservableDict'
                             ' (should never happen.)' % self.name)

    cpdef set(self, obj, value):
        value = ObservableDict(self, obj, value)
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
            raise ValueError('ObjectProperty<%s> accepts only Python objects' %
                            self.name)

cdef class BooleanProperty(Property):
    '''Property that represents only boolean
    '''
    cdef check(self, obj, value):
        if Property.check(self, obj, value):
            return True
        if not isinstance(value, object):
            raise ValueError('BooleanProperty<%s> accepts only bool' % self.name)

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
                raise ValueError('BoundedNumericProperty<%s> is below the '
                                 'minimum bound (%d)' % (self.name, _min))
        if s['use_max']:
            _max = s['max']
            if _max and value > _max:
                raise ValueError('BoundedNumericProperty<%s> is above the '
                                 'maximum bound (%d)' % (self.name, _max))
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
        valid_options = obj.__storage[self._name]['options']
        if value not in valid_options:
            raise ValueError('OptionProperty<%s> have an invalid option %r. '
                             'Must be one of: %s' % (self.name,
                             value, valid_options))


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

    cpdef trigger_change(self, obj, value):
        s = obj.__storage[self._name]
        if s['stop_event']:
            return
        p = s['properties']
        s['value'] = [p[x].get(obj) for x in xrange(len(p))]
        self.dispatch(obj)

    cdef convert(self, obj, value):
        if not isinstance(value, (list, tuple)):
            raise ValueError('ReferenceListProperty<%s> must be a list or a '
                             'tuple' % self.name)
        return list(value)

    cdef check(self, obj, value):
        if len(value) != len(obj.__storage[self._name]['properties']):
            raise ValueError('ReferenceListProperty<%s> value length is '
                             'immutable' % self.name)

    cpdef set(self, obj, _value):
        cdef int idx
        cdef list value
        storage = obj.__storage[self._name]
        value = self.convert(obj, _value)
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

    cpdef get(self, obj):
        s = obj.__storage[self._name]
        p = s['properties']
        s['value'] = [p[x].get(obj) for x in xrange(len(p))]
        return s['value']

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

    cpdef trigger_change(self, obj, value):
        cvalue = obj.__storage[self._name]['value']
        dvalue = self.get(obj)
        if cvalue != dvalue:
            obj.__storage[self._name]['value'] = dvalue
            self.dispatch(obj)

    cdef check(self, obj, value):
        return True

    cpdef get(self, obj):
        return obj.__storage[self._name]['getter'](obj)

    cpdef set(self, obj, value):
        if obj.__storage[self._name]['setter'](obj, value):
            obj.__storage[self._name]['value'] = self.get(obj)
            self.dispatch(obj)

