from kivy._event cimport EventDispatcher

cdef class Property:
    cdef str _name
    cdef int allownone
    cdef public object defaultvalue
    cdef init_storage(self, EventDispatcher obj, dict storage)
    cpdef link(self, EventDispatcher obj, str name)
    cpdef link_deps(self, EventDispatcher obj, str name)
    cpdef bind(self, EventDispatcher obj, observer)
    cpdef unbind(self, EventDispatcher obj, observer)
    cdef compare_value(self, a, b)
    cpdef set(self, EventDispatcher obj, value)
    cpdef get(self, EventDispatcher obj)
    cdef check(self, EventDispatcher obj, x)
    cdef convert(self, EventDispatcher obj, x)
    cpdef dispatch(self, EventDispatcher obj)

cdef class NumericProperty(Property):
    cdef float parse_str(self, EventDispatcher obj, value)
    cdef float parse_list(self, EventDispatcher obj, value, str ext)

cdef class StringProperty(Property):
    pass

cdef class ListProperty(Property):
    pass

cdef class DictProperty(Property):
    pass

cdef class ObjectProperty(Property):
    pass

cdef class BooleanProperty(Property):
    pass

cdef class BoundedNumericProperty(Property):
    cdef int use_min
    cdef int use_max
    cdef long min
    cdef long max

cdef class OptionProperty(Property):
    cdef list options

cdef class ReferenceListProperty(Property):
    cdef list properties
    cpdef trigger_change(self, EventDispatcher obj, value)

cdef class AliasProperty(Property):
    cdef object getter
    cdef object setter
    cdef list bind_objects
    cdef int use_cache
    cpdef trigger_change(self, EventDispatcher obj, value)
