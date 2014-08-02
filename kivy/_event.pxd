

cdef class ObjectWithUid(object):
    cdef readonly int uid


cdef class Observable(ObjectWithUid):
    pass


cdef class EventDispatcher(Observable):
    cdef dict __event_stack
    cdef dict __properties
    cdef dict __storage
    cdef object __weakref__
    cpdef dict properties(self)
