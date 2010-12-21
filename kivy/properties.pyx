'''
Properties
==========

The properties classes are used for creating :class:`~kivy.uix.widget.Widget`.
Theses classes are supporting :
    - Observer pattern: you can bind a property to be called when the value is
      changing.
    - Better memory management: the same instance of a property is shared across
      multiple widget instance. The value storage is independant of the Widget.

'''

#cython: profile=True
#cython: embedsignature=True


__all__ = ('NumericProperty', 'StringProperty', 'ListProperty',
           'ObjectProperty', 'BooleanProperty', 'BoundedNumericProperty',
           'OptionProperty', 'ReferenceListProperty', 'AliasProperty',
           'NumericProperty', 'Property')

cdef class Property:
    '''Base class for build more complex property.
    
    This class handle all the basics setter and getter, None handling,
    observers list, and storage initialisation. This class should not be
    directly instanciated.
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
        '''Link the instance with his real name.

        .. warning::

            Internal usage only.

        When a widget definition use a :class:`Property` class, the creation of
        the property happen, but the instance don't know anything about his name
        in the widget class ::

            class MyWidget(Widget):
                uid = NumericProperty(0)

        On this example, the uid will be a NumericProperty() instance, but the
        property instance don't know his name. That's why :func:`link` is used
        in Widget.__new__. The link function is also used to create the storage
        of the property for this specific widget instance.
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
        if obj not in self.storage:
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
        '''Check if the value is correct or not, depending the settings of the
        property class.
        '''
        if x is None:
            if not self.storage[obj.__uid]['allownone']:
                raise ValueError('None is not allowed')
            else:
                return True

    cdef convert(self, obj, x):
        '''Convert the initial value to a correct value.
        Can be used for multiple type of argument, and simplify into only one.
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
    '''Property that represent a numeric value

    The NumericProperty accept only int or float.

    >>> Widget.x = 42
    >>> print Widget.x
    42
    >>> Widget.x = "plop"
    Traceback (most recent call last):
        File "<stdin>", line 1, in <module>
        File "properties.pyx", line 93, in kivy.properties.Property.__set__
        File "properties.pyx", line 111, in kivy.properties.Property.set
        File "properties.pyx", line 159, in kivy.properties.NumericProperty.check
        ValueError: NumericProperty accept only int/float
    '''
    cdef check(self, obj, value):
        if Property.check(self, obj, value):
            return True
        if type(value) not in (int, float):
            raise ValueError('NumericProperty accept only int/float')


cdef class StringProperty(Property):
    '''Property that represent a string value.

    Only string or unicode are accepted.
    '''
    cdef check(self, obj, value):
        if Property.check(self, obj, value):
            return True
        if not isinstance(value, basestring):
            raise ValueError('StringProperty accept only str/unicode')

cdef class ListProperty(Property):
    '''Property that represent a list.

    Only list are allowed, tuple or any other classes are forbidden.

    .. warning::

        To mark the property as changed, you must reassign a new list each
        time you want to add or remove an object. Don't rely on append(),
        remove() and pop() functions.
    '''
    cdef check(self, obj, value):
        if Property.check(self, obj, value):
            return True
        if type(value) is not list:
            raise ValueError('ListProperty accept only list')

cdef class ObjectProperty(Property):
    '''Property that represent an Python object.

    .. warning::

        To mark the property as changed, you must reassign a new python object.
    '''
    cdef check(self, obj, value):
        if Property.check(self, obj, value):
            return True
        if not isinstance(value, object):
            raise ValueError('ObjectProperty accept only object')

cdef class BooleanProperty(Property):
    '''Property that represent only boolean
    '''
    cdef check(self, obj, value):
        if Property.check(self, obj, value):
            return True
        if not isinstance(value, object):
            raise ValueError('BooleanProperty accept only bool')

cdef class BoundedNumericProperty(Property):
    '''Property that represent a numeric value, with the possibility of assign
    minimum bound and/or maximum bound.

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
                raise ValueError('Value is below the maximum bound (%d)' % _max)
        return True


cdef class OptionProperty(Property):
    '''Property that represent a string from a specific list.

    If the string set in the property are not from the list passed at the
    creation, you will have an exception.

    :Parameters:
        `options`: list (not tuple.)
            List of available options
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
        if value not in self.storage[obj.__uid]['options']:
            raise ValueError('Value is not in available options')


cdef class ReferenceListProperty(Property):
    '''Property that allow to create tuple of other properties.

    For example, if `x` and `y` are :class:`NumericProperty`, we can create a
    :class:`ReferenceListProperty` for the `pos`. If you change the value of
    `pos`, it will automaticly change the values of `x` and `y`. If you read the
    value of `pos`, it will return a tuple with the value of `x` and `y`.
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
        if type(value) not in (list, tuple):
            raise ValueError('Value must be a list or tuple')
        return <list>value

    cdef check(self, obj, value):
        if len(value) != len(self.storage[obj.__uid]['properties']):
            raise ValueError('Value must have the same size as beginning')

    cpdef set(self, obj, value):
        cdef int idx
        storage = self.storage[obj.__uid]
        value = self.convert(obj, value)
        if self.compare_value(storage['value'], value):
            return False
        self.check(obj, value)
        # prevent dependice loop
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

    If you don't found a Property class that fit to your needs, you can still
    create Python getter and setter, and create a property with both of them.

    Exemple from the kivy/uix/widget.py ::

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
            prop.bind(obj, self.trigger_change)

    cpdef unlink(self, obj):
        for prop in self.bind_objects:
            prop.unbind(obj, self.trigger_change)
        Property.unlink(self, obj)

    cpdef trigger_change(self, obj, value):
        self.dispatch(obj)

    cdef check(self, obj, value):
        return True

    cpdef get(self, obj):
        return self.storage[obj.__uid]['getter'](obj)

    cpdef set(self, obj, value):
        self.storage[obj.__uid]['setter'](obj, value)

cdef class NumpyProperty(Property):
    '''Property that represent a numpy matrix.

    This property exist only to be able to compare matrix content.
    To prevent observer to be called if the matrix is assign, but didn't change,
    we must compare 2 matrix (previous and new). But numpy is unable to use a
    classic == comparaison. We are using ::

        (a == b).all().

    See numpy documentation for more information.
    '''
    cdef init_storage(self, dict storage):
        Property.init_storage(self, storage)
        storage['value'] = self.defaultvalue.copy()

    cdef compare_value(self, a, b):
        return (a == b).all()

