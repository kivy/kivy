
cdef class EventDispatcher(object):
    cdef dict __event_stack
    cdef dict __properties
    cdef dict __storage
    cdef object __weakref__
    cpdef dict properties(self)
    cdef readonly int uid
