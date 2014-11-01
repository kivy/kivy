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
    # The callback that dispatch is currently dispatching
    cdef BoundCallabck *current_dispatch
    # if unbind unbinds current_dispatch, this is set to true so that we don't
    # dispatch this again. dispatch then manuually removes it.
    cdef int unbound_dispatched_callback
    # when binding while dispatching, don't dispatch from new_callback and down
    # because those callbacks didn't exist when we started dispatching
    cdef BoundCallabck *new_callback
    # this needs to be here to enable cython cyclic gc
    cdef object dummy_obj

    cdef inline void release_callbacks(self) except *
    cdef inline void bind(self, object observer) except *
    cdef inline void fast_bind(self, object observer, tuple largs, dict kwargs, int is_ref) except *
    cdef inline void unbind(self, object observer, int is_ref, int stop_on_first) except *
    cdef inline void fast_unbind(self, object observer, tuple largs, dict kwargs) except *
    cdef inline int dispatch(self, object obj, object value, tuple largs, dict kwargs, int stop_on_true) except 2
