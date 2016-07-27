
cdef class ClockEvent(object):

    cdef int _is_triggered
    cdef public ClockEvent next
    '''The next :class:`ClockEvent` in order they were scheduled.
    '''
    cdef public ClockEvent prev
    '''The previous :class:`ClockEvent` in order they were scheduled.
    '''
    cdef public object cid
    cdef public CyClockBase clock
    '''The :class:`CyClockBase` instance associated with the event.
    '''
    cdef public int loop
    '''Whether this event repeats at intervals of :attr:`timeout`.
    '''
    cdef public object weak_callback
    cdef public object callback
    cdef public double timeout
    '''The duration after scheduling when the callback should be executed.
    '''
    cdef public double _last_dt
    cdef public double _dt

    cpdef get_callback(self)
    cpdef cancel(self)
    cpdef release(self)
    cpdef tick(self, double curtime)


cdef class FreeClockEvent(ClockEvent):

    cdef public int free
    '''Whether this event was scheduled as a free event.
    '''


cdef class CyClockBase(object):

    cdef public double _last_tick
    cdef public int max_iteration
    '''The maximum number of callback iterations at the end of the frame, before the next
    frame. If more iterations occur, a warning is issued.
    '''

    cdef public double clock_resolution
    '''If the remaining time until the event timeout is less than :attr:`clock_resolution`,
    the clock will execute the callback even if it hasn't exactly timed out.

    If -1, the default, the resolution will be computed from config's ``maxfps``.
    Otherwise, the provided value is used. Defaults to -1.
    '''

    cdef public double _max_fps

    cdef public ClockEvent _root_event
    '''The first event in the chain. Can be None.
    '''
    cdef public ClockEvent _next_event
    '''During frame processing when we service the events, this points to the next
    event that will be processed. After ticking an event, we continue with
    :attr:`_next_event`.

    If a event that is canceled is the :attr:`_next_event`, :attr:`_next_event`
    is shifted to point to the after after this, or None if it's at the end of the
    chain.
    '''
    cdef public ClockEvent _cap_event
    '''The cap event is the last event in the chain for each frame.
    For a particular frame, events may be added dynamically after this event,
    and the current frame should not process them.

    Similarly to :attr:`_next_event`,
    when canceling the :attr:`_cap_event`, :attr:`_cap_event` is shifted to the
    one previous to it.
    '''
    cdef public ClockEvent _last_event
    '''The last event in the chain. New events are added after this. Can be None.
    '''
    cdef public object _lock
    cdef public object _lock_acquire
    cdef public object _lock_release

    cpdef get_resolution(self)
    cpdef create_trigger(self, callback, timeout=*, interval=*)
    cpdef schedule_once(self, callback, timeout=*)
    cpdef schedule_interval(self, callback, timeout)
    cpdef unschedule(self, callback, all=*)
    cpdef _release_references(self)
    cpdef _process_events(self)
    cpdef _process_events_before_frame(self)
    cpdef get_min_timeout(self)
    cpdef get_events(self)


cdef class CyClockBaseFree(CyClockBase):

    cpdef create_trigger_free(self, callback, timeout=*, interval=*)
    cpdef schedule_once_free(self, callback, timeout=*)
    cpdef schedule_interval_free(self, callback, timeout)
    cpdef _process_free_events(self, double last_tick)
    cpdef get_min_free_timeout(self)
