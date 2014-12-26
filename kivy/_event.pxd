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


cdef class EventObservers:
    # If dispatching should occur in normal or reverse order of binding.
    cdef int dispatch_reverse
    # If in dispatch, the value parameter is dispatched or ignored.
    cdef int dispatch_value
    # The callbacks and their args. Each element is a 4-tuple of (callback,
    # largs, kwargs, is_ref)
    cdef list callbacks
    # The index in callbacks of the next dispatched callback, -1 if not dispatching
    cdef int idx
    # The size of callbacks during a dispatch including only the original callbacks.
    # That is, as callbacks are unbound during a dispatch dlen is reduced
    # to account for that. It's only used if not dispatch_reverse
    cdef int dlen

    cdef inline void bind(self, object observer) except *
    cdef inline void fast_bind(self, object observer, tuple largs, dict kwargs, int is_ref) except *
    cdef inline void unbind(self, object observer, int is_ref, int stop_on_first) except *
    cdef inline void fast_unbind(self, object observer, tuple largs, dict kwargs) except *
    cdef inline int dispatch(self, object obj, object value, tuple largs, dict kwargs, int stop_on_true) except 2
    cdef inline object _dispatch(
        self, object f, tuple slargs, dict skwargs, object obj, object value, tuple largs, dict kwargs)
