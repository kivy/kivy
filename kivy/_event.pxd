

cdef class ObjectWithUid(object):
    cdef readonly int uid


cdef class Observable(ObjectWithUid):
    cdef object __fast_bind_mapping


cdef class EventDispatcher(ObjectWithUid):
    cdef dict __event_stack
    cdef dict __properties
    cdef dict __storage
    cdef object __weakref__
    cpdef dict properties(self)
