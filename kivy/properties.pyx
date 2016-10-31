'''
Properties
==========

The *Properties* classes are used when you create an
:class:`~kivy.event.EventDispatcher`.

.. warning::
        Kivy's Properties are **not to be confused** with Python's
        properties (i.e. the ``@property`` decorator and the <property> type).

Kivy's property classes support:

    Value Checking / Validation
        When you assign a new value to a property, the value is checked against
        validation constraints. For
        example, validation for an :class:`OptionProperty` will make sure that
        the value is in a predefined list of possibilities. Validation for a
        :class:`NumericProperty` will check that your value is a numeric type.
        This prevents many errors early on.

    Observer Pattern
        You can specify what should happen when a property's value changes.
        You can bind your own function as a callback to changes of a
        :class:`Property`. If, for example, you want a piece of code to be
        called when a widget's :class:`~kivy.uix.widget.Widget.pos` property
        changes, you can :class:`~kivy.event.EventDispatcher.bind` a function
        to it.

    Better Memory Management
        The same instance of a property is shared across multiple widget
        instances.

Comparison Python vs. Kivy
--------------------------

Basic example
~~~~~~~~~~~~~

Let's compare Python and Kivy properties by creating a Python class with 'a'
as a float property::

    class MyClass(object):
        def __init__(self, a=1.0):
            super(MyClass, self).__init__()
            self.a = a

With Kivy, you can do::

    class MyClass(EventDispatcher):
        a = NumericProperty(1.0)


Depth being tracked
~~~~~~~~~~~~~~~~~~~

Only the "top level" of a nested object is being tracked. For example::

    my_list_prop = ListProperty([1, {'hi': 0}])
    # Changing a top level element will trigger all `on_my_list_prop` callbacks
    my_list_prop[0] = 4
    # Changing a deeper element will be ignored by all `on_my_list_prop` callbacks
    my_list_prop[1]['hi'] = 4

The same holds true for all container-type kivy properties.

Value checking
~~~~~~~~~~~~~~

If you wanted to add a check for a minimum / maximum value allowed for a
property, here is a possible implementation in Python::

    class MyClass(object):
        def __init__(self, a=1):
            super(MyClass, self).__init__()
            self.a_min = 0
            self.a_max = 100
            self.a = a

        def _get_a(self):
            return self._a
        def _set_a(self, value):
            if value < self.a_min or value > self.a_max:
                raise ValueError('a out of bounds')
            self._a = value
        a = property(_get_a, _set_a)

The disadvantage is you have to do that work yourself. And it becomes
laborious and complex if you have many properties.
With Kivy, you can simplify the process::

    class MyClass(EventDispatcher):
        a = BoundedNumericProperty(1, min=0, max=100)

That's all!


Error Handling
~~~~~~~~~~~~~~

If setting a value would otherwise raise a ValueError, you have two options to
handle the error gracefully within the property. The first option is to use an
errorvalue parameter. An errorvalue is a substitute for the invalid value::

    # simply returns 0 if the value exceeds the bounds
    bnp = BoundedNumericProperty(0, min=-500, max=500, errorvalue=0)

The second option in to use an errorhandler parameter. An errorhandler is a
callable (single argument function or lambda) which can return a valid
substitute::

    # returns the boundary value when exceeded
    bnp = BoundedNumericProperty(0, min=-500, max=500,
        errorhandler=lambda x: 500 if x > 500 else -500)


Conclusion
~~~~~~~~~~

Kivy properties are easier to use than the standard ones. See the next chapter
for examples of how to use them :)


Observe Property changes
------------------------

As we said in the beginning, Kivy's Properties implement the `Observer pattern
<http://en.wikipedia.org/wiki/Observer_pattern>`_. That means you can
:meth:`~kivy.event.EventDispatcher.bind` to a property and have your own
function called when the value changes.

There are multiple ways to observe the changes.

Observe using bind()
~~~~~~~~~~~~~~~~~~~~

You can observe a property change by using the bind() method outside of the
class::

    class MyClass(EventDispatcher):
        a = NumericProperty(1)

    def callback(instance, value):
        print('My callback is call from', instance)
        print('and the a value changed to', value)

    ins = MyClass()
    ins.bind(a=callback)

    # At this point, any change to the a property will call your callback.
    ins.a = 5    # callback called
    ins.a = 5    # callback not called, because the value did not change
    ins.a = -1   # callback called

.. note::

    Property objects live at the class level and manage the values attached
    to instances. Re-assigning at class level will remove the Property. For
    example, continuing with the code above, `MyClass.a = 5` replaces
    the property object with a simple int.


Observe using 'on_<propname>'
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you defined the class yourself, you can use the 'on_<propname>' callback::

    class MyClass(EventDispatcher):
        a = NumericProperty(1)

        def on_a(self, instance, value):
            print('My property a changed to', value)

.. warning::

    Be careful with 'on_<propname>'. If you are creating such a callback on a
    property you are inheriting, you must not forget to call the superclass
    function too.

Binding to properties of properties.
------------------------------------

When binding to a property of a property, for example binding to a numeric
property of an object saved in a object property, updating the object property
to point to a new object will not re-bind the numeric property to the
new object. For example:

.. code-block:: kv

    <MyWidget>:
        Label:
            id: first
            text: 'First label'
        Label:
            id: second
            text: 'Second label'
        Button:
            label: first
            text: self.label.text
            on_press: self.label = second

When clicking on the button, although the label object property has changed
to the second widget, the button text will not change because it is bound to
the text property of the first label directly.

In `1.9.0`, the ``rebind`` option has been introduced that will allow the
automatic updating of the ``text`` when ``label`` is changed, provided it
was enabled. See :class:`ObjectProperty`.
'''

__all__ = ('Property',
           'NumericProperty', 'StringProperty', 'ListProperty',
           'ObjectProperty', 'BooleanProperty', 'BoundedNumericProperty',
           'OptionProperty', 'ReferenceListProperty', 'AliasProperty',
           'DictProperty', 'VariableListProperty', 'ConfigParserProperty')

include "graphics/config.pxi"


from weakref import ref
from kivy.compat import string_types
from kivy.config import ConfigParser
from functools import partial
from kivy.clock import Clock
from kivy.weakmethod import WeakMethod
from kivy.logger import Logger
from kivy.utils import get_color_from_hex


cdef float g_dpi = -1
cdef float g_density = -1
cdef float g_fontscale = -1

NUMERIC_FORMATS = ('in', 'px', 'dp', 'sp', 'pt', 'cm', 'mm')

cpdef float dpi2px(value, ext):
    # 1in = 2.54cm = 25.4mm = 72pt = 12pc
    global g_dpi, g_density, g_fontscale
    if g_dpi == -1:
        from kivy.metrics import Metrics
        g_dpi = Metrics.dpi
        g_density = Metrics.density
        g_fontscale = Metrics.fontscale
    cdef float rv = float(value)
    if ext == 'in':
        return rv * g_dpi
    elif ext == 'px':
        return rv
    elif ext == 'dp':
        return rv * g_density
    elif ext == 'sp':
        return rv * g_density * g_fontscale
    elif ext == 'pt':
        return rv * g_dpi / 72.
    elif ext == 'cm':
        return rv * g_dpi / 2.54
    elif ext == 'mm':
        return rv * g_dpi / 25.4

cdef class Property:
    '''Base class for building more complex properties.

    This class handles all the basic setters and getters, None type handling,
    the observer list and storage initialisation. This class should not be
    directly instantiated.

    By default, a :class:`Property` always takes a default value::

        class MyObject(Widget):

            hello = Property('Hello world')

    The default value must be a value that agrees with the Property type. For
    example, you can't set a list to a :class:`StringProperty` because the
    StringProperty will check the default value.

    None is a special case: you can set the default value of a Property to
    None, but you can't set None to a property afterward.  If you really want
    to do that, you must declare the Property with `allownone=True`::

        class MyObject(Widget):

            hello = ObjectProperty(None, allownone=True)

        # then later
        a = MyObject()
        a.hello = 'bleh' # working
        a.hello = None # working too, because allownone is True.

    :Parameters:
        `default`:
            Specifies the default value for the property.
        `\*\*kwargs`:
            If the parameters include `errorhandler`, this should be a callable
            which must take a single argument and return a valid substitute
            value.

            If the parameters include `errorvalue`, this should be an object.
            If set, it will replace an invalid property value (overrides
            errorhandler).

            If the parameters include `force_dispatch`, it should be a boolean.
            If True, no value comparison will be done, so the property event
            will be dispatched even if the new value matches the old value (by
            default identical values are not dispatched to avoid infinite
            recursion in two-way binds). Be careful, this is for advanced use only.

    .. versionchanged:: 1.4.2
        Parameters errorhandler and errorvalue added

    .. versionchanged:: 1.9.0
        Parameter force_dispatch added
    '''

    def __cinit__(self):
        self._name = ''
        self.allownone = 0
        self.force_dispatch = 0
        self.defaultvalue = None
        self.errorvalue = None
        self.errorhandler = None
        self.errorvalue_set = 0


    def __init__(self, defaultvalue, **kw):
        self.defaultvalue = defaultvalue
        self.allownone = <int>kw.get('allownone', 0)
        self.force_dispatch = <int>kw.get('force_dispatch', 0)
        self.errorvalue = kw.get('errorvalue', None)
        self.errorhandler = kw.get('errorhandler', None)

        if 'errorvalue' in kw:
            self.errorvalue_set = 1

        if 'errorhandler' in kw and not callable(self.errorhandler):
            raise ValueError('errorhandler %s not callable' % self.errorhandler)

    property name:
        def __get__(self):
            return self._name

    def __repr__(self):
        return '<{} name={}>'.format(self.__class__.__name__, self._name)

    def __str__(self):
        return '<{} name={}>'.format(self.__class__.__name__, self._name)

    cdef init_storage(self, EventDispatcher obj, PropertyStorage storage):
        storage.value = self.convert(obj, self.defaultvalue)
        storage.observers = EventObservers()

    cpdef link(self, EventDispatcher obj, str name):
        '''Link the instance with its real name.

        .. warning::

            Internal usage only.

        When a widget is defined and uses a :class:`Property` class, the
        creation of the property object happens, but the instance doesn't know
        anything about its name in the widget class::

            class MyWidget(Widget):
                uid = NumericProperty(0)

        In this example, the uid will be a NumericProperty() instance, but the
        property instance doesn't know its name. That's why :meth:`link` is
        used in `Widget.__new__`. The link function is also used to create the
        storage space of the property for this specific widget instance.
        '''
        cdef PropertyStorage d
        if self._name != '' and name != self._name:
            d = obj.__storage.get(self._name, PropertyStorage())
        else:
            d = PropertyStorage()
        self._name = name
        obj.__storage[name] = d
        self.init_storage(obj, d)

    cpdef link_deps(self, EventDispatcher obj, str name):
        pass

    cpdef bind(self, EventDispatcher obj, observer):
        '''Add a new observer to be called only when the value is changed.
        '''
        cdef PropertyStorage ps = obj.__storage[self._name]
        ps.observers.bind(WeakMethod(observer), observer, 1)

    cpdef fbind(self, EventDispatcher obj, observer, int ref, tuple largs=(), dict kwargs={}):
        '''Similar to bind, except it doesn't check if the observer already
        exists. It also expands and forwards largs and kwargs to the callback.
        funbind or unbind_uid should be called when unbinding.
        It returns a unique positive uid to be used with unbind_uid.
        '''
        cdef PropertyStorage ps = obj.__storage[self._name]
        if ref:
            return ps.observers.fbind(WeakMethod(observer), largs, kwargs, 1)
        else:
            return ps.observers.fbind(observer, largs, kwargs, 0)

    cpdef unbind(self, EventDispatcher obj, observer):
        '''Remove the observer from our widget observer list.
        '''
        cdef PropertyStorage ps = obj.__storage[self._name]
        ps.observers.unbind(observer, 0)

    cpdef funbind(self, EventDispatcher obj, observer, tuple largs=(), dict kwargs={}):
        '''Remove the observer from our widget observer list bound with
        fbind. It removes the first match it finds, as opposed to unbind
        which searches for all matches.
        '''
        cdef PropertyStorage ps = obj.__storage[self._name]
        ps.observers.funbind(observer, largs, kwargs)

    cpdef unbind_uid(self, EventDispatcher obj, object uid):
        '''Remove the observer from our widget observer list bound with
        fbind using the uid.
        '''
        cdef PropertyStorage ps = obj.__storage[self._name]
        ps.observers.unbind_uid(uid)

    def __set__(self, EventDispatcher obj, val):
        self.set(obj, val)

    def __get__(self, EventDispatcher obj, objtype):
        if obj is None:
            return self
        return self.get(obj)

    cdef compare_value(self, a, b):
        try:
            return bool(a == b)
        except Exception as e:
            Logger.warn(
                'Property: Value comparison failed for {} with "{}". Consider setting '
                'force_dispatch to True to avoid this.'.format(self, e))
            return False

    cpdef set(self, EventDispatcher obj, value):
        '''Set a new value for the property.
        '''
        cdef PropertyStorage ps = obj.__storage[self._name]
        value = self.convert(obj, value)
        realvalue = ps.value
        if not self.force_dispatch and self.compare_value(realvalue, value):
            return False

        try:
            self.check(obj, value)
        except ValueError as e:
            if self.errorvalue_set == 1:
                value = self.errorvalue
                self.check(obj, value)
            elif self.errorhandler is not None:
                value = self.errorhandler(value)
                self.check(obj, value)
            else:
                raise e

        ps.value = value
        self.dispatch(obj)
        return True

    cpdef get(self, EventDispatcher obj):
        '''Return the value of the property.
        '''
        cdef PropertyStorage ps
        try:
            ps = obj.__storage[self._name]
        except KeyError:
            raise AttributeError(self._name)
        return ps.value

    #
    # Private part
    #

    cdef check(self, EventDispatcher obj, x):
        '''Check whether the value is correct or not, depending on the settings
        of the property class.

        :Returns:
            bool, True if the value correctly validates.
        '''
        if x is None:
            if not self.allownone:
                raise ValueError('None is not allowed for %s.%s' % (
                    obj.__class__.__name__,
                    self.name))
            else:
                return True

    cdef convert(self, EventDispatcher obj, x):
        '''Convert the initial value to a correctly validating value.
        Can be used for multiple types of arguments, simplifying to only one.
        '''
        return x

    cpdef dispatch(self, EventDispatcher obj):
        '''Dispatch the value change to all observers.

        .. versionchanged:: 1.1.0
            The method is now accessible from Python.

        This can be used to force the dispatch of the property, even if the
        value didn't change::

            button = Button()
            # get the Property class instance
            prop = button.property('text')
            # dispatch this property on the button instance
            prop.dispatch(button)

        '''
        cdef PropertyStorage ps = obj.__storage[self._name]
        ps.observers.dispatch(obj, ps.value, None, None, 0)


cdef class NumericProperty(Property):
    '''Property that represents a numeric value.

    :Parameters:
        `defaultvalue`: int or float, defaults to 0
            Specifies the default value of the property.

    >>> wid = Widget()
    >>> wid.x = 42
    >>> print(wid.x)
    42
    >>> wid.x = "plop"
     Traceback (most recent call last):
       File "<stdin>", line 1, in <module>
       File "properties.pyx", line 93, in kivy.properties.Property.__set__
       File "properties.pyx", line 111, in kivy.properties.Property.set
       File "properties.pyx", line 159, in kivy.properties.NumericProperty.check
     ValueError: NumericProperty accept only int/float

    .. versionchanged:: 1.4.1
        NumericProperty can now accept custom text and tuple value to indicate a
        type, like "in", "pt", "px", "cm", "mm", in the format: '10pt' or (10,
        'pt').

    '''
    def __init__(self, defaultvalue=0, **kw):
        super(NumericProperty, self).__init__(defaultvalue, **kw)

    cdef init_storage(self, EventDispatcher obj, PropertyStorage storage):
        storage.numeric_fmt = 'px'
        Property.init_storage(self, obj, storage)

    cdef compare_value(self, a, b):
        return a == b

    cdef check(self, EventDispatcher obj, value):
        if Property.check(self, obj, value):
            return True
        if type(value) not in (int, float, long):
            raise ValueError('%s.%s accept only int/float/long (got %r)' % (
                obj.__class__.__name__,
                self.name, value))

    cdef convert(self, EventDispatcher obj, x):
        if x is None:
            return x
        tp = type(x)
        if tp is int or tp is float or tp is long:
            return x
        if tp is tuple or tp is list:
            if len(x) != 2:
                raise ValueError('%s.%s must have 2 components (got %r)' % (
                    obj.__class__.__name__,
                    self.name, x))
            return self.parse_list(obj, x[0], x[1])
        elif isinstance(x, string_types):
            return self.parse_str(obj, x)
        else:
            raise ValueError('%s.%s has an invalid format (got %r)' % (
                obj.__class__.__name__,
                self.name, x))

    cdef float parse_str(self, EventDispatcher obj, value):
        if value[-2:] in NUMERIC_FORMATS:
            return self.parse_list(obj, value[:-2], value[-2:])
        else:
            return float(value)

    cdef float parse_list(self, EventDispatcher obj, value, ext):
        cdef PropertyStorage ps = obj.__storage[self._name]
        ps.numeric_fmt = ext
        return dpi2px(value, ext)

    def get_format(self, EventDispatcher obj):
        '''
        Return the format used for Numeric calculation. Default is px (mean
        the value have not been changed at all). Otherwise, it can be one of
        'in', 'pt', 'cm', 'mm'.
        '''
        cdef PropertyStorage ps = obj.__storage[self._name]
        return ps.numeric_fmt


cdef class StringProperty(Property):
    '''Property that represents a string value.

    :Parameters:
        `defaultvalue`: string, defaults to ''
            Specifies the default value of the property.

    '''

    def __init__(self, defaultvalue='', **kw):
        super(StringProperty, self).__init__(defaultvalue, **kw)

    cdef compare_value(self, a, b):
        return a == b

    cdef check(self, EventDispatcher obj, value):
        if Property.check(self, obj, value):
            return True
        if not isinstance(value, string_types):
            raise ValueError('%s.%s accept only str' % (
                obj.__class__.__name__,
                self.name))

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
        self.last_op = '', None
        super(ObservableList, self).__init__(*largs[2:])

    def __setitem__(self, key, value):
        list.__setitem__(self, key, value)
        self.last_op = '__setitem__', key
        observable_list_dispatch(self)

    def __delitem__(self, key):
        list.__delitem__(self, key)
        self.last_op = '__delitem__', key
        observable_list_dispatch(self)

    def __setslice__(self, b, c, v):
        list.__setslice__(self, b, c, v)
        self.last_op = '__setslice__', (b, c)
        observable_list_dispatch(self)

    def __delslice__(self, b, c):
        list.__delslice__(self, b, c)
        self.last_op = '__delslice__', (b, c)
        observable_list_dispatch(self)

    def __iadd__(self, *largs):
        list.__iadd__(self, *largs)
        self.last_op = '__iadd__', None
        observable_list_dispatch(self)

    def __imul__(self, b):
        list.__imul__(self, b)
        self.last_op = '__imul__'. b
        observable_list_dispatch(self)

    def append(self, *largs):
        list.append(self, *largs)
        self.last_op = 'append', None
        observable_list_dispatch(self)

    def remove(self, *largs):
        list.remove(self, *largs)
        self.last_op = 'remove', None
        observable_list_dispatch(self)

    def insert(self, i, x):
        list.insert(self, i, x)
        self.last_op = 'insert', i
        observable_list_dispatch(self)

    def pop(self, *largs):
        cdef object result = list.pop(self, *largs)
        self.last_op = 'pop', largs
        observable_list_dispatch(self)
        return result

    def extend(self, *largs):
        list.extend(self, *largs)
        self.last_op = 'extend', None
        observable_list_dispatch(self)

    def sort(self, *largs):
        list.sort(self, *largs)
        self.last_op = 'sort', None
        observable_list_dispatch(self)

    def reverse(self, *largs):
        list.reverse(self, *largs)
        self.last_op = 'reverse', None
        observable_list_dispatch(self)


cdef class ListProperty(Property):
    '''Property that represents a list.

    :Parameters:
        `defaultvalue`: list, defaults to []
            Specifies the default value of the property.

    .. warning::

        When assigning a list to a :class:`ListProperty`, the list stored in
        the property is a shallow copy of the list and not the original list. This can
        be demonstrated with the following example::

            >>> class MyWidget(Widget):
            >>>     my_list = ListProperty([])

            >>> widget = MyWidget()
            >>> my_list = [1, 5, {'hi': 'hello'}]
            >>> widget.my_list = my_list
            >>> print(my_list is widget.my_list)
            False
            >>> my_list.append(10)
            >>> print(my_list, widget.my_list)
            [1, 5, {'hi': 'hello'}, 10] [1, 5, {'hi': 'hello'}]

        However, changes to nested levels will affect the property as well,
        since the property uses a shallow copy of my_list.

            >>> my_list[2]['hi'] = 'bye'
            >>> print(my_list, widget.my_list)
            [1, 5, {'hi': 'bye'}, 10] [1, 5, {'hi': 'bye'}]

    '''
    def __init__(self, defaultvalue=None, **kw):
        defaultvalue = defaultvalue or []

        super(ListProperty, self).__init__(defaultvalue, **kw)

    cpdef link(self, EventDispatcher obj, str name):
        Property.link(self, obj, name)
        cdef PropertyStorage ps = obj.__storage[self._name]
        ps.value = ObservableList(self, obj, ps.value)

    cdef check(self, EventDispatcher obj, value):
        if Property.check(self, obj, value):
            return True
        if type(value) is not ObservableList:
            raise ValueError('%s.%s accept only ObservableList' % (
                obj.__class__.__name__,
                self.name))

    cpdef set(self, EventDispatcher obj, value):
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

    def _weak_return(self, item):
        if isinstance(item, ref):
            return item()
        return item

    def __getattr__(self, attr):
        try:
            return self._weak_return(self.__getitem__(attr))
        except KeyError:
            return self._weak_return(
                            super(ObservableDict, self).__getattr__(attr))

    def __setattr__(self, attr, value):
        if attr in ('prop', 'obj'):
            super(ObservableDict, self).__setattr__(attr, value)
            return
        self.__setitem__(attr, value)

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        observable_dict_dispatch(self)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        observable_dict_dispatch(self)

    def clear(self, *largs):
        dict.clear(self, *largs)
        observable_dict_dispatch(self)

    def remove(self, *largs):
        dict.remove(self, *largs)
        observable_dict_dispatch(self)

    def pop(self, *largs):
        cdef object result = dict.pop(self, *largs)
        observable_dict_dispatch(self)
        return result

    def popitem(self, *largs):
        cdef object result = dict.popitem(self, *largs)
        observable_dict_dispatch(self)
        return result

    def setdefault(self, *largs):
        cdef object result = dict.setdefault(self, *largs)
        observable_dict_dispatch(self)
        return result

    def update(self, *largs):
        dict.update(self, *largs)
        observable_dict_dispatch(self)


cdef class DictProperty(Property):
    '''Property that represents a dict.

    :Parameters:
        `defaultvalue`: dict, defaults to None
            Specifies the default value of the property.
        `rebind`: bool, defaults to False
            See :class:`ObjectProperty` for details.

    .. versionchanged:: 1.9.0
        `rebind` has been introduced.

    .. warning::

        Similar to :class:`ListProperty`, when assigning a dict to a
        :class:`DictProperty`, the dict stored in the property is a shallow copy of the
        dict and not the original dict. See :class:`ListProperty` for details.
    '''
    def __init__(self, defaultvalue=None, rebind=False, **kw):
        defaultvalue = defaultvalue or {}

        super(DictProperty, self).__init__(defaultvalue, **kw)
        self.rebind = rebind

    cpdef link(self, EventDispatcher obj, str name):
        Property.link(self, obj, name)
        cdef PropertyStorage ps = obj.__storage[self._name]
        ps.value = ObservableDict(self, obj, ps.value)

    cdef check(self, EventDispatcher obj, value):
        if Property.check(self, obj, value):
            return True
        if type(value) is not ObservableDict:
            raise ValueError('%s.%s accept only ObservableDict' % (
                obj.__class__.__name__,
                self.name))

    cpdef set(self, EventDispatcher obj, value):
        value = ObservableDict(self, obj, value)
        Property.set(self, obj, value)


cdef class ObjectProperty(Property):
    '''Property that represents a Python object.

    :Parameters:
        `defaultvalue`: object type
            Specifies the default value of the property.
        `rebind`: bool, defaults to False
            Whether kv rules using this object as an intermediate attribute
            in a kv rule, will update the bound property when this object
            changes.

            That is the standard behavior is that if there's a kv rule
            ``text: self.a.b.c.d``, where ``a``, ``b``, and ``c`` are
            properties with ``rebind`` ``False`` and ``d`` is a
            :class:`StringProperty`. Then when the rule is applied, ``text``
            becomes bound only to ``d``. If ``a``, ``b``, or ``c`` change,
            ``text`` still remains bound to ``d``. Furthermore, if any of them
            were ``None`` when the rule was initially evaluated, e.g. ``b`` was
            ``None``; then ``text`` is bound to ``b`` and will not become bound
            to ``d`` even when ``b`` is changed to not be ``None``.

            By setting ``rebind`` to ``True``, however, the rule will be
            re-evaluated and all the properties rebound when that intermediate
            property changes. E.g. in the example above, whenever ``b`` changes
            or becomes not ``None`` if it was ``None`` before, ``text`` is
            evaluated again and becomes rebound to ``d``. The overall result is
            that ``text`` is now bound to all the properties among ``a``,
            ``b``, or ``c`` that have ``rebind`` set to ``True``.
        `\*\*kwargs`: a list of keyword arguments
            `baseclass`
                If kwargs includes a `baseclass` argument, this value will be
                used for validation: `isinstance(value, kwargs['baseclass'])`.

    .. warning::

        To mark the property as changed, you must reassign a new python object.

    .. versionchanged:: 1.9.0
        `rebind` has been introduced.

    .. versionchanged:: 1.7.0

        `baseclass` parameter added.
    '''
    def __init__(self, defaultvalue=None, rebind=False, **kw):
        self.baseclass = kw.get('baseclass', object)
        super(ObjectProperty, self).__init__(defaultvalue, **kw)
        self.rebind = rebind

    cdef check(self, EventDispatcher obj, value):
        if Property.check(self, obj, value):
            return True
        if not isinstance(value, self.baseclass):
            raise ValueError('{}.{} accept only object based on {}'.format(
                obj.__class__.__name__,
                self.name,
                self.baseclass.__name__))

cdef class BooleanProperty(Property):
    '''Property that represents only a boolean value.

    :Parameters:
        `defaultvalue`: boolean
            Specifies the default value of the property.
    '''

    def __init__(self, defaultvalue=True, **kw):
        super(BooleanProperty, self).__init__(defaultvalue, **kw)

    cdef check(self, EventDispatcher obj, value):
        if Property.check(self, obj, value):
            return True
        if not isinstance(value, object):
            raise ValueError('%s.%s accept only bool' % (
                obj.__class__.__name__,
                self.name))

cdef class BoundedNumericProperty(Property):
    '''Property that represents a numeric value within a minimum bound and/or
    maximum bound -- within a numeric range.

    :Parameters:
        `default`: numeric
            Specifies the default value of the property.
        `\*\*kwargs`: a list of keyword arguments
            If a `min` parameter is included, this specifies the minimum
            numeric value that will be accepted.
            If a `max` parameter is included, this specifies the maximum
            numeric value that will be accepted.
    '''
    def __cinit__(self):
        self.use_min = 0
        self.use_max = 0
        self.min = 0
        self.max = 0
        self.f_min = 0.0
        self.f_max = 0.0

    def __init__(self, *largs, **kw):
        value = kw.get('min', None)
        if value is None:
            self.use_min = 0
        elif type(value) is float:
                self.use_min = 2
                self.f_min = value
        else:
            self.use_min = 1
            self.min = value

        value = kw.get('max', None)
        if value is None:
            self.use_max = 0
        elif type(value) is float:
            self.use_max = 2
            self.f_max = value
        else:
            self.use_max = 1
            self.max = value

        Property.__init__(self, *largs, **kw)

    cdef init_storage(self, EventDispatcher obj, PropertyStorage storage):
        Property.init_storage(self, obj, storage)
        storage.bnum_min = self.min
        storage.bnum_max = self.max
        storage.bnum_f_min = self.f_min
        storage.bnum_f_max = self.f_max
        storage.bnum_use_min = self.use_min
        storage.bnum_use_max = self.use_max

    def set_min(self, EventDispatcher obj, value):
        '''Change the minimum value acceptable for the BoundedNumericProperty,
        only for the `obj` instance. Set to None if you want to disable it::

            class MyWidget(Widget):
                number = BoundedNumericProperty(0, min=-5, max=5)

            widget = MyWidget()
            # change the minimum to -10
            widget.property('number').set_min(widget, -10)
            # or disable the minimum check
            widget.property('number').set_min(widget, None)

        .. warning::

            Changing the bounds doesn't revalidate the current value.

        .. versionadded:: 1.1.0
        '''
        cdef PropertyStorage ps = obj.__storage[self._name]
        if value is None:
            ps.bnum_use_min = 0
        elif type(value) is float:
            ps.bnum_f_min = value
            ps.bnum_use_min = 2
        else:
            ps.bnum_min = value
            ps.bnum_use_min = 1

    def get_min(self, EventDispatcher obj):
        '''Return the minimum value acceptable for the BoundedNumericProperty
        in `obj`. Return None if no minimum value is set::

            class MyWidget(Widget):
                number = BoundedNumericProperty(0, min=-5, max=5)

            widget = MyWidget()
            print(widget.property('number').get_min(widget))
            # will output -5

        .. versionadded:: 1.1.0
        '''
        cdef PropertyStorage ps = obj.__storage[self._name]
        if ps.bnum_use_min == 1:
            return ps.bnum_min
        elif ps.bnum_use_min == 2:
            return ps.bnum_f_min

    def set_max(self, EventDispatcher obj, value):
        '''Change the maximum value acceptable for the BoundedNumericProperty,
        only for the `obj` instance. Set to None if you want to disable it.
        Check :attr:`set_min` for a usage example.

        .. warning::

            Changing the bounds doesn't revalidate the current value.

        .. versionadded:: 1.1.0
        '''
        cdef PropertyStorage ps = obj.__storage[self._name]
        if value is None:
            ps.bnum_use_max = 0
        elif type(value) is float:
            ps.bnum_f_max = value
            ps.bnum_use_max = 2
        else:
            ps.bnum_max = value
            ps.bnum_use_max = 1

    def get_max(self, EventDispatcher obj):
        '''Return the maximum value acceptable for the BoundedNumericProperty
        in `obj`. Return None if no maximum value is set. Check
        :attr:`get_min` for a usage example.

        .. versionadded:: 1.1.0
        '''
        cdef PropertyStorage ps = obj.__storage[self._name]
        if ps.bnum_use_max == 1:
            return ps.bnum_max
        if ps.bnum_use_max == 2:
            return ps.bnum_f_max

    cdef compare_value(self, a, b):
        return a == b

    cdef check(self, EventDispatcher obj, value):
        if Property.check(self, obj, value):
            return True
        cdef PropertyStorage ps = obj.__storage[self._name]
        if ps.bnum_use_min == 1:
            _min = ps.bnum_min
            if value < _min:
                raise ValueError('%s.%s is below the minimum bound (%d)' % (
                    obj.__class__.__name__,
                    self.name, _min))
        elif ps.bnum_use_min == 2:
            _f_min = ps.bnum_f_min
            if value < _f_min:
                raise ValueError('%s.%s is below the minimum bound (%f)' % (
                    obj.__class__.__name__,
                    self.name, _f_min))
        if ps.bnum_use_max == 1:
            _max = ps.bnum_max
            if value > _max:
                raise ValueError('%s.%s is above the maximum bound (%d)' % (
                    obj.__class__.__name__,
                    self.name, _max))
        elif ps.bnum_use_max == 2:
            _f_max = ps.bnum_f_max
            if value > _f_max:
                raise ValueError('%s.%s is above the maximum bound (%f)' % (
                    obj.__class__.__name__,
                    self.name, _f_max))
        return True

    property bounds:
        '''Return min/max of the value.

        .. versionadded:: 1.0.9
        '''

        def __get__(self):
            if self.use_min == 1:
                _min = self.min
            elif self.use_min == 2:
                _min = self.f_min
            else:
                _min = None

            if self.use_max == 1:
                _max = self.max
            elif self.use_max == 2:
                _max = self.f_max
            else:
                _max = None

            return _min, _max


cdef class OptionProperty(Property):
    '''Property that represents a string from a predefined list of valid
    options.

    If the string set in the property is not in the list of valid options
    (passed at property creation time), a ValueError exception will be raised.

    :Parameters:
        `default`: any valid type in the list of options
            Specifies the default value of the property.
        `\*\*kwargs`: a list of keyword arguments
            Should include an `options` parameter specifying a list (not tuple)
            of valid options.

    For example::

        class MyWidget(Widget):
            state = OptionProperty("None", options=["On", "Off", "None"])

    '''
    def __cinit__(self):
        self.options = []

    def __init__(self, *largs, **kw):
        self.options = list(kw.get('options', []))
        super(OptionProperty, self).__init__(*largs, **kw)

    cdef init_storage(self, EventDispatcher obj, PropertyStorage storage):
        Property.init_storage(self, obj, storage)
        storage.options = self.options[:]

    cdef check(self, EventDispatcher obj, value):
        if Property.check(self, obj, value):
            return True
        cdef PropertyStorage ps = obj.__storage[self._name]
        if value not in ps.options:
            raise ValueError('%s.%s is set to an invalid option %r. '
                             'Must be one of: %s' % (
                             obj.__class__.__name__,
                             self.name,
                             value, ps.options))

    property options:
        '''Return the options available.

        .. versionadded:: 1.0.9
        '''

        def __get__(self):
            return self.options

class ObservableReferenceList(ObservableList):
    def __setitem__(self, key, value, update_properties=True):
        list.__setitem__(self, key, value)
        if update_properties:
            self.prop.setitem(self.obj(), key, value)

    def __setslice__(self, start, stop, value, update_properties=True):  # Python 2 only method
        list.__setslice__(self, start, stop, value)
        if update_properties:
            self.prop.setitem(self.obj(), slice(start, stop), value)

cdef class ReferenceListProperty(Property):
    '''Property that allows the creation of a tuple of other properties.

    For example, if `x` and `y` are :class:`NumericProperty`\s, we can create a
    :class:`ReferenceListProperty` for the `pos`. If you change the value of
    `pos`, it will automatically change the values of `x` and `y` accordingly.
    If you read the value of `pos`, it will return a tuple with the values of
    `x` and `y`.

    For example::

        class MyWidget(EventDispatcher):
            x = NumericProperty(0)
            y = NumericProperty(0)
            pos = ReferenceListProperty(x, y)

    '''
    def __cinit__(self):
        self.properties = list()

    def __init__(self, *largs, **kw):
        for prop in largs:
            self.properties.append(prop)
        Property.__init__(self, largs, **kw)

    cdef init_storage(self, EventDispatcher obj, PropertyStorage storage):
        Property.init_storage(self, obj, storage)
        storage.properties = tuple(self.properties)
        storage.stop_event = 0

    cpdef link(self, EventDispatcher obj, str name):
        Property.link(self, obj, name)
        cdef PropertyStorage ps = obj.__storage[self._name]
        ps.value = ObservableReferenceList(self, obj, ps.value)

    cpdef link_deps(self, EventDispatcher obj, str name):
        cdef Property prop
        Property.link_deps(self, obj, name)
        for prop in self.properties:
            prop.fbind(obj, self.trigger_change, 0)

    cpdef trigger_change(self, EventDispatcher obj, value):
        cdef PropertyStorage ps = obj.__storage[self._name]
        if ps.stop_event:
            return
        p = ps.properties

        try:
            ps.value.__setslice__(0, len(p),
                    [prop.get(obj) for prop in p],
                    update_properties=False)
        except AttributeError:
            ps.value.__setitem__(slice(len(p)),
                    [prop.get(obj) for prop in p],
                    update_properties=False)

        self.dispatch(obj)

    cdef convert(self, EventDispatcher obj, value):
        if not isinstance(value, (list, tuple)):
            raise ValueError('%s.%s must be a list or a tuple' % (
                obj.__class__.__name__,
                self.name))
        return list(value)

    cdef check(self, EventDispatcher obj, value):
        cdef PropertyStorage ps = obj.__storage[self._name]
        if len(value) != len(ps.properties):
            raise ValueError('%s.%s value length is immutable' % (
                obj.__class__.__name__,
                self.name))

    cpdef set(self, EventDispatcher obj, _value):
        cdef int idx
        cdef list value
        cdef PropertyStorage ps = obj.__storage[self._name]
        value = self.convert(obj, _value)
        if not self.force_dispatch and self.compare_value(ps.value, value):
            return False
        self.check(obj, value)
        # prevent dependency loop
        ps.stop_event = 1
        props = ps.properties
        for idx in xrange(len(props)):
            prop = props[idx]
            x = value[idx]
            prop.set(obj, x)
        ps.stop_event = 0
        try:
            ps.value.__setslice__(0, len(value), value,
                    update_properties=False)
        except AttributeError:
            ps.value.__setitem__(slice(len(value)), value,
                    update_properties=False)
        self.dispatch(obj)
        return True

    cpdef setitem(self, EventDispatcher obj, key, value):
        cdef PropertyStorage ps = obj.__storage[self._name]
        cdef bint res = False

        ps.stop_event = 1
        if isinstance(key, slice):
            props = ps.properties[key]
            for index in xrange(len(props)):
                prop = props[index]
                x = value[index]
                res = prop.set(obj, x) or res
        else:
            prop = ps.properties[key]
            res = prop.set(obj, value)
        ps.stop_event = 0
        if res:
            self.dispatch(obj)

    cpdef get(self, EventDispatcher obj):
        cdef PropertyStorage ps = obj.__storage[self._name]
        cdef tuple p = ps.properties
        try:
            ps.value.__setslice__(0, len(p),
                    [prop.get(obj) for prop in p],
                    update_properties=False)
        except AttributeError:
            ps.value.__setitem__(slice(len(p)),
                    [prop.get(obj) for prop in p],
                    update_properties=False)
        return ps.value

cdef class AliasProperty(Property):
    '''Create a property with a custom getter and setter.

    If you don't find a Property class that fits to your needs, you can make
    your own by creating custom Python getter and setter methods.

    Example from kivy/uix/widget.py::

        def get_right(self):
            return self.x + self.width
        def set_right(self, value):
            self.x = value - self.width
        right = AliasProperty(get_right, set_right, bind=['x', 'width'])

    :Parameters:
        `getter`: function
            Function to use as a property getter
        `setter`: function
            Function to use as a property setter. Properties listening to the
            alias property won't be updated when the property is set (e.g.
            `right = 10`), unless the `setter` returns `True`.
        `bind`: list/tuple
            Properties to observe for changes, as property name strings
        `cache`: boolean
            If True, the value will be cached, until one of the binded elements
            will changes
        `rebind`: bool, defaults to False
            See :class:`ObjectProperty` for details.

    .. versionchanged:: 1.9.0
        `rebind` has been introduced.

    .. versionchanged:: 1.4.0
        Parameter `cache` added.
    '''
    def __cinit__(self):
        self.getter = None
        self.setter = None
        self.use_cache = 0
        self.bind_objects = list()

    def __init__(self, getter, setter=None, rebind=False, **kwargs):
        Property.__init__(self, None, **kwargs)
        self.getter = getter
        self.setter = setter or self.__read_only
        self.rebind = rebind
        v = kwargs.get('bind')
        self.bind_objects = list(v) if v is not None else []
        if kwargs.get('cache'):
            self.use_cache = 1

    def __read_only(self, _obj, _value):
        raise AttributeError('property is read-only')

    cdef init_storage(self, EventDispatcher obj, PropertyStorage storage):
        Property.init_storage(self, obj, storage)
        storage.getter = self.getter
        storage.setter = self.setter
        storage.alias_initial = 1

    cpdef link_deps(self, EventDispatcher obj, str name):
        cdef Property oprop
        for prop in self.bind_objects:
            oprop = getattr(obj.__class__, prop)
            oprop.fbind(obj, self.trigger_change, 0)

    cpdef trigger_change(self, EventDispatcher obj, value):
        cdef PropertyStorage ps = obj.__storage[self._name]
        ps.alias_initial = 0
        dvalue = ps.getter(obj)
        if ps.value != dvalue:
            ps.value = dvalue
            self.dispatch(obj)

    cdef check(self, EventDispatcher obj, value):
        return True

    cpdef get(self, EventDispatcher obj):
        cdef PropertyStorage ps = obj.__storage[self._name]
        if self.use_cache:
            if ps.alias_initial:
                return ps.getter(obj)
            return ps.value
        return ps.getter(obj)

    cpdef set(self, EventDispatcher obj, value):
        cdef PropertyStorage ps = obj.__storage[self._name]
        if ps.setter(obj, value):
            ps.value = self.get(obj)
            self.dispatch(obj)

cdef class VariableListProperty(Property):
    '''A ListProperty that allows you to work with a variable amount of
    list items and to expand them to the desired list size.

    For example, GridLayout's padding used to just accept one numeric value
    which was applied equally to the left, top, right and bottom of the
    GridLayout. Now padding can be given one, two or four values, which are
    expanded into a length four list [left, top, right, bottom] and stored
    in the property.

    :Parameters:
        `default`: a default list of values
            Specifies the default values for the list.
        `length`: int, one of 2 or 4.
            Specifies the length of the final list. The `default` list will
            be expanded to match a list of this length.
        `\*\*kwargs`: a list of keyword arguments
            Not currently used.

    Keeping in mind that the `default` list is expanded to a list of length 4,
    here are some examples of how VariabelListProperty's are handled.

    - VariableListProperty([1]) represents [1, 1, 1, 1].
    - VariableListProperty([1, 2]) represents [1, 2, 1, 2].
    - VariableListProperty(['1px', (2, 'px'), 3, 4.0]) represents [1, 2, 3, 4.0].
    - VariableListProperty(5) represents [5, 5, 5, 5].
    - VariableListProperty(3, length=2) represents [3, 3].

    .. versionadded:: 1.7.0
    '''

    def __init__(self, defaultvalue=None, length=4, **kw):
        if length == 4:
            defaultvalue = defaultvalue or [0, 0, 0, 0]
        elif length == 2:
            defaultvalue = defaultvalue or [0, 0]
        else:
            err = 'VariableListProperty requires a length of 2 or 4 (got %r)'
            raise ValueError(err % length)

        self.length = length
        super(VariableListProperty, self).__init__(defaultvalue, **kw)

    cpdef link(self, EventDispatcher obj, str name):
        Property.link(self, obj, name)
        cdef PropertyStorage ps = obj.__storage[self._name]
        ps.value = ObservableList(self, obj, ps.value)

    cdef compare_value(self, a, b):
        return a == b

    cdef check(self, EventDispatcher obj, value):
        if Property.check(self, obj, value):
            return True
        if type(value) not in (int, float, long, list, tuple, str):
            err = '%s.%s accepts only int/float/long/list/tuple/str (got %r)'
            raise ValueError(err % (obj.__class__.__name__, self.name, value))

    cdef convert(self, EventDispatcher obj, x):
        if x is None:
            return x

        tp = type(x)
        if isinstance(x, (list, tuple)):
            l = len(x)
            if l == 1:
                y = self._convert_numeric(obj, x[0])
                if self.length == 4:
                    return [y, y, y, y]
                elif self.length == 2:
                    return [y, y]
            elif l == 2:
                if x[1] in NUMERIC_FORMATS:
                    # defaultvalue is a list or tuple representing one value
                    y = self._convert_numeric(obj, x)
                    if self.length == 4:
                        return [y, y, y, y]
                    elif self.length == 2:
                        return [y, y]
                else:
                    y = self._convert_numeric(obj, x[0])
                    z = self._convert_numeric(obj, x[1])
                    if self.length == 4:
                        return [y, z, y, z]
                    elif self.length == 2:
                        return [y, z]
            elif l == 4:
                if self.length == 4:
                    return [self._convert_numeric(obj, y) for y in x]
                else:
                    err = '%s.%s must have 1 or 2 components (got %r)'
                    raise ValueError(err % (obj.__class__.__name__,
                        self.name, x))
            else:
                if self.length == 4:
                    err = '%s.%s must have 1, 2 or 4 components (got %r)'
                elif self.length == 2:
                    err = '%s.%s must have 1 or 2 components (got %r)'
                raise ValueError(err % (obj.__class__.__name__, self.name, x))
        elif tp is int or tp is long or tp is float or isinstance(x, string_types):
            y = self._convert_numeric(obj, x)
            if self.length == 4:
                return [y, y, y, y]
            elif self.length == 2:
                return [y, y]
        else:
            raise ValueError('%s.%s has an invalid format (got %r)' % (
                obj.__class__.__name__,
                self.name, x))

    cdef _convert_numeric(self, EventDispatcher obj, x):
        tp = type(x)
        if tp is int or tp is float or tp is long:
            return x
        if tp is tuple or tp is list:
            if len(x) != 2:
                raise ValueError('%s.%s must have 2 components (got %r)' % (
                    obj.__class__.__name__,
                    self.name, x))
            return self.parse_list(obj, x[0], x[1])
        elif isinstance(x, string_types):
            return self.parse_str(obj, x)
        else:
            raise ValueError('%s.%s has an invalid format (got %r)' % (
                obj.__class__.__name__,
                self.name, x))

    cdef float parse_str(self, EventDispatcher obj, value):
        return self.parse_list(obj, value[:-2], value[-2:])

    cdef float parse_list(self, EventDispatcher obj, value, ext):
        return dpi2px(value, ext)


cdef class ConfigParserProperty(Property):
    ''' Property that allows one to bind to changes in the configuration values
    of a :class:`~kivy.config.ConfigParser` as well as to bind the ConfigParser
    values to other properties.

    A ConfigParser is composed of sections, where each section has a number of
    keys and values associated with these keys. ConfigParserProperty lets
    you automatically listen to and change the values of specified keys based
    on other kivy properties.

    For example, say we want to have a TextInput automatically write
    its value, represented as an int, in the `info` section of a ConfigParser.
    Also, the textinputs should update its values from the ConfigParser's
    fields. Finally, their values should be displayed in a label. In py::

        class Info(Label):

            number = ConfigParserProperty(0, 'info', 'number', 'example',
                                          val_type=int, errorvalue=41)

            def __init__(self, **kw):
                super(Info, self).__init__(**kw)
                config = ConfigParser(name='example')

    The above code creates a property that is connected to the `number` key in
    the `info` section of the ConfigParser named `example`. Initially, this
    ConfigParser doesn't exist. Then, in `__init__`, a ConfigParser is created
    with name `example`, which is then automatically linked with this property.
    then in kv:

    .. code-block:: kv

        BoxLayout:
            TextInput:
                id: number
                text: str(info.number)
            Info:
                id: info
                number: number.text
                text: 'Number: {}'.format(self.number)

    You'll notice that we have to do `text: str(info.number)`, this is because
    the value of this property is always an int, because we specified `int` as
    the `val_type`. However, we can assign anything to the property, e.g.
    `number: number.text` which assigns a string, because it is instantly
    converted with the `val_type` callback.

    .. note::

        If a file has been opened for this ConfigParser using
        :meth:`~kivy.config.ConfigParser.read`, then
        :meth:`~kivy.config.ConfigParser.write` will be called every property
        change, keeping the file updated.

    .. warning::

        It is recommend that the config parser object be assigned to the
        property after the kv tree has been constructed (e.g. schedule on next
        frame from init). This is because the kv tree and its properties, when
        constructed, are evaluated on its own order, therefore, any initial
        values in the parser might be overwritten by objects it's bound to.
        So in the example above, the TextInput might be initially empty,
        and if `number: number.text` is evaluated before
        `text: str(info.number)`, the config value will be overwritten with the
        (empty) text value.

    :Parameters:
        `default`: object type
            Specifies the default value for the key. If the parser associated
            with this property doesn't have this section or key, it'll be
            created with the current value, which is the default value
            initially.
        `section`: string type
            The section in the ConfigParser where the key / value will be
            written. Must be provided. If the section doesn't exist, it'll be
            created.
        `key`: string type
            The key in section `section` where the value will be written to.
            Must be provided. If the key doesn't exist, it'll be created and
            the current value written to it, otherwise its value will be used.
        `config`: string or :class:`~kivy.config.ConfigParser` instance.
            The ConfigParser instance to associate with this property if
            not None. If it's a string, the ConfigParser instance whose
            :attr:`~kivy.config.ConfigParser.name` is the value of `config`
            will be used. If no such parser exists yet, whenever a ConfigParser
            with this name is created, it will automatically be linked to this
            property.

            Whenever a ConfigParser becomes linked with a property, if the
            section or key doesn't exist, the current property value will be
            used to create that key, otherwise, the existing key value will be
            used for the property value; overwriting its current value. You can
            change the ConfigParser associated with this property if a string
            was used here, by changing the
            :attr:`~kivy.config.ConfigParser.name` of an existing or new
            ConfigParser instance. Or through :meth:`set_config`.
        `\*\*kwargs`: a list of keyword arguments
            `val_type`: a callable object
                The key values are saved in the ConfigParser as strings. When
                the ConfigParser value is read internally and assigned to the
                property or when the user changes the property value directly,
                if `val_type` is not None, it will be called with the new value
                as input and it should return the value converted to the proper
                type accepted ny this property. For example, if the property
                represent ints, `val_type` can simply be `int`.

                If the `val_type` callback raises a `ValueError`, `errorvalue`
                or `errorhandler` will be used if provided. Tip: the
                `getboolean` function of the ConfigParser might also be useful
                here to convert to a boolean type.
            `verify`: a callable object
                Can be used to restrict the allowable values of the property.
                For every value assigned to the property, if this is specified,
                `verify` is called with the new value, and if it returns `True`
                the value is accepted, otherwise, `errorvalue` or
                `errorhandler` will be used if provided or a `ValueError` is
                raised.

    .. versionadded:: 1.9.0
    '''

    def __cinit__(self):
        self.config = None
        self.config_name = ''
        self.section = ''
        self.key = ''
        self.val_type = None
        self.verify = None
        self.last_value = None  # the last string value in the config for this

    def __init__(self, defaultvalue, section, key, config, **kw):
        self.val_type = kw.pop('val_type', None)
        self.verify = kw.pop('verify', None)
        super(ConfigParserProperty, self).__init__(defaultvalue, **kw)
        self.section = section
        self.key = key

        if isinstance(config, string_types) and config:
            self.config_name = config
        elif isinstance(config, ConfigParser):
            self.config = config
        elif config is not None:
            raise ValueError(
            'config {}, is not a ConfigParser instance or a non-empty string'.
            format(config))

        if not self.section or not isinstance(section, string_types):
            raise ValueError('section {}, is not a non-empty string'.
                             format(section))
        if not self.key or not isinstance(key, string_types):
            raise ValueError('key {}, is not a non-empty string'.
                             format(key))
        if self.val_type is not None and not callable(self.val_type):
            raise ValueError(
                'val_type {} is not callable'.format(self.val_type))
        if self.verify is not None and not callable(self.verify):
            raise ValueError(
                'verify {} is not callable'.format(self.verify))

    cpdef link_deps(self, EventDispatcher obj, str name):
        # initialize the config objects
        cdef PropertyStorage ps
        Property.link_deps(self, obj, name)
        self.obj = ref(obj)

        # if the parser already exists, get it now
        if self.config is None:
            self.config = ConfigParser.get_configparser(self.config_name)
        if self.config is not None:
            self.config.adddefaultsection(self.section)
            self.config.setdefault(self.section, self.key, self.defaultvalue)

            ps = obj.__storage[self._name]
            ps.value = self._parse_str(self.config.get(self.section, self.key))
            # in case the value changed, save it
            self.config.set(self.section, self.key, ps.value)
            self.last_value = self.config.get(self.section, self.key)
            self.config.add_callback(self._edit_setting, self.section, self.key)
            self.config.write()
            #self.dispatch(obj)  # we need to dispatch, so not overwritten
        elif self.config_name:
            # ConfigParser will set_config when one named config is created
            Clock.schedule_once(partial(ConfigParser._register_named_property,
            self.config_name, (self.obj, self.name)), 0)

    cpdef _edit_setting(self, section, key, value):
        # callback of ConfigParser
        cdef object obj = self.obj()
        if obj is None or self.last_value == value:
            return

        self.last_value = value
        self.set(obj, value)

    cdef inline object _parse_str(self, object value):
        ''' Takes a ConfigParser's string (or any value supplied by the user),
        and converts it to the python type that this property represents
        (with :attr:`val_type` and :attr:`verify`).
        '''
        cdef object val = value
        cdef object obj = self.obj()
        cdef object name = obj.__class__.__name__ if obj else ''

        if self.val_type is not None:
            try:
                val = self.val_type(value)
                if self.verify is not None and not self.verify(val):
                    raise ValueError('{} is not allowed for {}.{}'. format(
                        val, name, self.name))
                return val
            except ValueError, e:
                if self.errorvalue_set == 1:
                    val = self.errorvalue
                elif self.errorhandler is not None:
                    val = self.errorhandler(val)
                else:
                    raise e

        if self.verify is not None:
            if not self.verify(val):
                raise ValueError('{} is not allowed for {}.{}'.format(val,
                    name, self.name))
        return val

    cpdef set(self, EventDispatcher obj, value):
        # Takes the a python object of the type used by this property
        # (see :attr:`val_type`), and saves it as a string in the config parser
        # (if available) and sets itself to this value.
        cdef PropertyStorage ps = obj.__storage[self._name]
        cdef object orig_value = value

        value = self._parse_str(value)
        realvalue = ps.value
        if self.compare_value(realvalue, value):
            fd = self.force_dispatch
            if not fd and self.compare_value(orig_value, value):
                return False
            else:
                # even if the resolved parsed value is the same, the original
                # value, e.g. str in config or user set value containing
                # invalid value might have been different, so we have to
                # change to the resolved value.
                if self.config:
                    self.config.set(self.section, self.key, value)
                    self.config.write()
                self.dispatch(obj)
                return True

        try:
            if self.verify is not None and not self.verify(value):
                raise ValueError('{} is not allowed for {}.{}'.
                format(value, obj.__class__.__name__, self.name))
        except ValueError, e:
            if self.errorvalue_set == 1:
                value = self.errorvalue
            elif self.errorhandler is not None:
                value = self.errorhandler(value)
            else:
                raise e

            if self.verify is not None and not self.verify(value):
                raise ValueError('{} is not allowed for {}.{}'.
                format(value, obj.__class__.__name__, self.name))

        ps.value = value
        if self.config is not None:
            self.config.set(self.section, self.key, value)
            self.config.write()
        self.dispatch(obj)
        return True

    def set_config(self, config):
        ''' Sets the ConfigParser object to be used by this property. Normally,
        the ConfigParser is set when initializing the Property using the
        `config` parameter.

        :Parameters:
            `config`: A :class:`~kivy.config.ConfigParser` instance.
                The instance to use for listening to and saving property value
                changes. If None, it disconnects the currently used
                `ConfigParser`.

        ::

            class MyWidget(Widget):
                username = ConfigParserProperty('', 'info', 'name', None)

            widget = MyWidget()
            widget.property('username').set_config(ConfigParser())
        '''
        cdef EventDispatcher obj = self.obj()
        cdef object value
        cdef PropertyStorage ps = obj.__storage[self._name]
        if self.config is config:
            return

        if self.config is not None:
            self.config.remove_callback(self._edit_setting, self.section,
                                        self.key)
        self.config = config
        if self.config is not None:
            self.config.adddefaultsection(self.section)
            self.config.setdefault(self.section, self.key, ps.value)
            self.config.write()
            self.config.add_callback(self._edit_setting, self.section,
                                     self.key)
            self.last_value = None
            self._edit_setting(self.section, self.key,
                               self.config.get(self.section, self.key))


cdef class ColorProperty(Property):
    '''Property that represents a color. The assignment can take either:

    - a list of 3 to 4 float value between 0-1 (kivy default)
    - a string in the format #rrggbb or #rrggbbaa

    :Parameters:
        `defaultvalue`: list or string, defaults to [1, 1, 1, 1]
            Specifies the default value of the property.

    .. versionadded:: 1.9.2
    '''
    def __init__(self, defaultvalue=None, **kw):
        defaultvalue = defaultvalue or [1, 1, 1, 1]
        super(ColorProperty, self).__init__(defaultvalue, **kw)

    cdef convert(self, EventDispatcher obj, x):
        if x is None:
            return x
        tp = type(x)
        if tp is tuple or tp is list:
            if len(x) != 3 and len(x) != 4:
                raise ValueError('{}.{} must have 3 or 4 components (got {!r})'.format(
                    obj.__class__.__name__, self.name, x))
            if len(x) == 3:
                return list(x) + [1]
            return list(x)
        elif isinstance(x, string_types):
            return self.parse_str(obj, x)
        else:
            raise ValueError('{}.{} has an invalid format (got {!r})'.format(
                obj.__class__.__name__, self.name, x))

    cdef list parse_str(self, EventDispatcher obj, value):
        return get_color_from_hex(value)
