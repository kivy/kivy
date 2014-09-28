from cpython.ref cimport PyObject

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


ctypedef struct BoundCallabck:
    PyObject *func
    PyObject *largs
    PyObject *kwargs
    BoundCallabck *next
    BoundCallabck *previous
    int is_ref

cdef inline void release_callback(BoundCallabck *callback)

cdef class EventObservers:
    # The first callback that was bound.
    cdef BoundCallabck *first_callback
    # The last callback that was bound.
    cdef BoundCallabck *last_callback
    # If dispatching should occur in normal or reverse order of binding.
    cdef int dispatch_reverse
    # If in dispatch, the value parameter is dispatched or ignored.
    cdef int dispatch_value

    cdef inline void bind(self, object observer)
    cdef inline int fast_bind(self, object observer, tuple largs, dict kwargs, int is_ref)
    cdef inline void unbind(self, object observer, int is_ref, int stop_on_first)
    cdef inline void fast_unbind(self, object observer, tuple largs, dict kwargs)
    cdef inline int dispatch(self, object obj, object value, tuple largs, dict kwargs, int stop_on_true)
