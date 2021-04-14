from kivy._event cimport EventDispatcher, EventObservers, BoundCallback, \
    cache_properties_per_cls
from kivy._metrics cimport dpi2px, pixel_scale_observers

cdef class PropertyStorage:
    cdef object value
    cdef EventObservers observers
    cdef Property property_obj


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
    cdef PropertyStorage create_property_storage(self)
    cdef inline PropertyStorage get_property_storage(self, EventDispatcher obj)
    cpdef set_name(self, EventDispatcher obj, str name)
    cpdef PropertyStorage link_eagerly(self, EventDispatcher obj)
    cpdef PropertyStorage link(self, EventDispatcher obj, str name)
    cpdef link_deps(self, EventDispatcher obj, str name)
    cpdef bind(self, EventDispatcher obj, observer)
    cpdef fbind(self, EventDispatcher obj, observer, int ref, tuple largs=*, dict kwargs=*)
    cpdef unbind(self, EventDispatcher obj, observer, int stop_on_first=*)
    cpdef funbind(self, EventDispatcher obj, observer, tuple largs=*, dict kwargs=*)
    cpdef unbind_uid(self, EventDispatcher obj, object uid)
    cdef compare_value(self, a, b)
    cpdef set(self, EventDispatcher obj, value)
    cpdef get(self, EventDispatcher obj)
    cdef check(self, EventDispatcher obj, x, PropertyStorage property_storage)
    cdef convert(self, EventDispatcher obj, x, PropertyStorage property_storage)
    cpdef dispatch(self, EventDispatcher obj)
    cdef _dispatch(self, EventDispatcher obj, PropertyStorage ps)


cdef class NumericPropertyStorage(PropertyStorage):
    cdef object numeric_fmt
    cdef object original_num


cdef class NumericProperty(Property):
    cdef float parse_str(
            self, EventDispatcher obj, value, NumericPropertyStorage ps) except *
    cdef float parse_list(
            self, EventDispatcher obj, value, ext, NumericPropertyStorage ps) except *

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


cdef class BoundedNumericPropertyStorage(PropertyStorage):
    cdef long bnum_min
    cdef long bnum_max
    cdef float bnum_f_min
    cdef float bnum_f_max
    cdef int bnum_use_min
    cdef int bnum_use_max


cdef class BoundedNumericProperty(Property):
    cdef int use_min
    cdef int use_max
    cdef long min
    cdef long max
    cdef float f_min
    cdef float f_max


cdef class OptionPropertyStorage(PropertyStorage):
    cdef list options


cdef class OptionProperty(Property):
    cdef list options


cdef class ReferenceListPropertyStorage(PropertyStorage):
    cdef tuple properties
    cdef int stop_event


cdef class ReferenceListProperty(Property):
    cdef list properties
    cpdef trigger_change(self, EventDispatcher obj, value)
    cpdef setitem(self, EventDispatcher obj, key, value)


cdef class AliasPropertyStorage(PropertyStorage):
    cdef object getter
    cdef object setter
    cdef int alias_initial


cdef class AliasProperty(Property):
    cdef object getter
    cdef object setter
    cdef int watch_before_use
    cdef list bind_objects
    cdef int use_cache
    cdef public int rebind
    cpdef trigger_change(self, EventDispatcher obj, value)


cdef class VariableListPropertyStorage(PropertyStorage):
    cdef object original_num
    cdef int uses_scaling


cdef class VariableListProperty(Property):
    cdef public int length
    cdef _convert_numeric(self, EventDispatcher obj, x, VariableListPropertyStorage ps)
    cdef float parse_str(
            self, EventDispatcher obj, value, VariableListPropertyStorage ps
    ) except *
    cdef float parse_list(
            self, EventDispatcher obj, value, ext, VariableListPropertyStorage ps
    ) except *


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
    cdef object parse_list(self, EventDispatcher obj, value)
