
cdef class ClockEvent(object):

    cdef int _is_triggered
    cdef public ClockEvent next
    cdef public ClockEvent prev
    cdef public object cid
    cdef public CyClockBase clock
    cdef public int loop
    cdef public object weak_callback
    cdef public object callback
    cdef public double timeout
    cdef public double _last_dt
    cdef public double _dt

    cpdef get_callback(self)
    cpdef cancel(self)
    cpdef release(self)
    cpdef tick(self, double curtime)


cdef class CyClockBase(object):

    cdef public double _last_tick
    cdef public int max_iteration

    cdef public ClockEvent _root_event
    cdef public ClockEvent _next_event
    cdef public ClockEvent _last_event
    cdef public object _lock
    cdef public object _lock_acquire
    cdef public object _lock_release

    cpdef create_trigger(self, callback, timeout=*)
    cpdef schedule_once(self, callback, timeout=*)
    cpdef schedule_interval(self, callback, timeout)
    cpdef unschedule(self, callback, all=*)
    cpdef _release_references(self)
    cpdef _process_events(self)
    cpdef _process_events_before_frame(self)
