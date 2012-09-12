cdef class Property:
    cdef str _name
    cdef int allownone
    cdef public object defaultvalue
    cdef init_storage(self, object obj, dict storage)
    cpdef link(self, object obj, str name)
    cpdef link_deps(self, object obj, str name)
    cpdef bind(self, obj, observer)
    cpdef unbind(self, obj, observer)
    cdef compare_value(self, a, b)
    cpdef set(self, obj, value)
    cpdef get(self, obj)
    cdef check(self, obj, x)
    cdef convert(self, obj, x)
    cpdef dispatch(self, obj)

cdef class NumericProperty(Property):
    cdef float parse_str(self, object obj, value)
    cdef float parse_list(self, object obj, value, str ext)

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
    cpdef trigger_change(self, obj, value)

cdef class AliasProperty(Property):
    cdef object getter
    cdef object setter
    cdef list bind_objects
    cdef int use_cache
    cpdef trigger_change(self, obj, value)
