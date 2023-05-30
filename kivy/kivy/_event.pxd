from cpython.ref cimport PyObject

cdef dict cache_properties_per_cls

cdef class ObjectWithUid(object):
    cdef readonly int uid


cdef class Observable(ObjectWithUid):
    cdef object __fbind_mapping
    cdef object bound_uid


cdef class EventDispatcher(ObjectWithUid):
    cdef dict __event_stack
    cdef dict __properties
    cdef dict __storage
    cdef object __weakref__
    cdef public set _kwargs_applied_init
    cdef public object _proxy_ref
    cpdef dict properties(self)


cdef enum BoundLock:
    # the state of the BoundCallback, i.e. whether it can be deleted
    unlocked  # whether the BoundCallback is unlocked and can be deleted
    locked  # whether the BoundCallback is locked and cannot be deleted
    deleted  # whether the locked BoundCallback was marked for deletion

cdef class BoundCallback:
    cdef object func
    cdef tuple largs
    cdef dict kwargs
    cdef int is_ref  # if func is a ref to the function
    cdef BoundLock lock  # see BoundLock
    cdef BoundCallback next  # next callback in chain
    cdef BoundCallback prev  # previous callback in chain
    cdef object uid  # the uid given for this callback, None if not given
    cdef EventObservers observers

    cdef void set_largs(self, tuple largs)


cdef class EventObservers:
    # If dispatching should occur in normal or reverse order of binding.
    cdef int dispatch_reverse
    # If in dispatch, the value parameter is dispatched or ignored.
    cdef int dispatch_value
    # The first callback bound
    cdef BoundCallback first_callback
    # The last callback bound
    cdef BoundCallback last_callback
    # The uid to assign to the next bound callback.
    cdef object uid

    cdef inline BoundCallback make_callback(self, object observer, tuple largs, dict kwargs, int is_ref, uid=*)
    cdef inline void bind(self, object observer, object src_observer, int is_ref) except *
    cdef inline object fbind(self, object observer, tuple largs, dict kwargs, int is_ref)
    cdef inline BoundCallback fbind_callback(self, object observer, tuple largs, dict kwargs, int is_ref)
    cdef inline void fbind_existing_callback(self, BoundCallback callback)
    cdef inline void unbind(self, object observer, int stop_on_first) except *
    cdef inline void funbind(self, object observer, tuple largs, dict kwargs) except *
    cdef inline object unbind_uid(self, object uid)
    cdef inline object unbind_callback(self, BoundCallback callback)
    cdef inline void remove_callback(self, BoundCallback callback, int force=*) except *
    cdef inline object _dispatch(
        self, object f, tuple slargs, dict skwargs, object obj, object value, tuple largs, dict kwargs)
    cdef inline int dispatch(self, object obj, object value, tuple largs, dict kwargs, int stop_on_true) except 2
