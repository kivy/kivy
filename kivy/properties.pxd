from kivy._event cimport EventDispatcher, EventObservers

cdef class PropertyStorage:
    cdef object value
    cdef EventObservers observers
    cdef object numeric_fmt
    cdef long bnum_min
    cdef long bnum_max
    cdef float bnum_f_min
    cdef float bnum_f_max
    cdef int bnum_use_min
    cdef int bnum_use_max
    cdef list options
    cdef tuple properties
    cdef int stop_event
    cdef object getter
    cdef object setter
    cdef int alias_initial

cdef class Property:
    cdef str _name
    cdef int allownone
    cdef int force_dispatch
    cdef object comparator
    cdef object errorvalue
    cdef object errorhandler
    cdef int errorvalue_set
    cdef public object defaultvalue
    cdef int deprecated
    cdef init_storage(self, EventDispatcher obj, PropertyStorage storage)
    cpdef link(self, EventDispatcher obj, str name)
    cpdef link_deps(self, EventDispatcher obj, str name)
    cpdef bind(self, EventDispatcher obj, observer)
    cpdef fbind(self, EventDispatcher obj, observer, int ref, tuple largs=*, dict kwargs=*)
    cpdef unbind(self, EventDispatcher obj, observer)
    cpdef funbind(self, EventDispatcher obj, observer, tuple largs=*, dict kwargs=*)
    cpdef unbind_uid(self, EventDispatcher obj, object uid)
    cdef compare_value(self, a, b)
    cpdef set(self, EventDispatcher obj, value)
    cpdef get(self, EventDispatcher obj)
    cdef check(self, EventDispatcher obj, x)
    cdef convert(self, EventDispatcher obj, x)
    cpdef dispatch(self, EventDispatcher obj)

cdef class NumericProperty(Property):
    cdef float parse_str(self, EventDispatcher obj, value) except *
    cdef float parse_list(self, EventDispatcher obj, value, ext) except *

cdef class StringProperty(Property):
    pass

cdef class ListProperty(Property):
    pass

cdef class DictProperty(Property):
    cdef public int rebind

cdef class ObjectProperty(Property):
    cdef object baseclass
    cdef public int rebind

cdef class BooleanProperty(Property):
    pass

cdef class BoundedNumericProperty(Property):
    cdef int use_min
    cdef int use_max
    cdef long min
    cdef long max
    cdef float f_min
    cdef float f_max

cdef class OptionProperty(Property):
    cdef list options

cdef class ReferenceListProperty(Property):
    cdef list properties
    cpdef trigger_change(self, EventDispatcher obj, value)
    cpdef setitem(self, EventDispatcher obj, key, value)

cdef class AliasProperty(Property):
    cdef object getter
    cdef object setter
    cdef list bind_objects
    cdef int use_cache
    cdef public int rebind
    cpdef trigger_change(self, EventDispatcher obj, value)

cdef class VariableListProperty(Property):
    cdef public int length
    cdef _convert_numeric(self, EventDispatcher obj, x)
    cdef float parse_str(self, EventDispatcher obj, value) except *
    cdef float parse_list(self, EventDispatcher obj, value, ext) except *

cdef class ConfigParserProperty(Property):
    cdef object config
    cdef object section
    cdef object key
    cdef object val_type
    cdef object verify
    cdef object obj
    cdef object last_value  # last string config value
    cdef object config_name
    cpdef _edit_setting(self, section, key, value)
    cdef inline object _parse_str(self, object value)

cdef class ColorProperty(Property):
    cdef list parse_str(self, EventDispatcher obj, value)
