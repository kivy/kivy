

__all__ = ('CyClockBase', 'ClockEvent')

from kivy.weakmethod import WeakMethod
from kivy.logger import Logger
from threading import Lock


cdef class ClockEvent(object):
    ''' A class that describes a callback scheduled with kivy's :attr:`Clock`.
    This class is never created by the user; instead, kivy creates and returns
    an instance of this class when scheduling a callback.

    An event can be triggered (scheduled) by calling it. If it's already
    scheduled, nothing will happen, otherwise it'll be scheduled. E.g.::

        event = Clock.schedule_once(my_callback, .5)
        event()  # nothing will happen since it's already scheduled.
        event.cancel()  # cancel it
        event()  # now it's scheduled again.
    '''

    def __init__(
            self, CyClockBase clock, int loop, callback, double timeout,
            double starttime, cid=None, int trigger=False, **kwargs):
        super(ClockEvent, self).__init__(**kwargs)
        self._is_triggered = False
        self.next = None
        self.prev = None
        self.cid = None
        self.clock = clock
        self.loop = loop
        self.weak_callback = None
        self.callback = callback
        self.timeout = timeout
        self._last_dt = starttime
        self._dt = 0.

        if trigger:
            self._is_triggered = True
            clock._lock_acquire()

            if clock._root_event is None:
                clock._last_event = clock._root_event = self
            else:
                clock._last_event.next = self
                self.prev = clock._last_event
                clock._last_event = self
            clock._lock_release()

    def __call__(self, *largs):
        ''' Schedules the callback associated with this instance.
        If the callback is already scheduled, it will not be scheduled again.
        '''
        self.clock._lock_acquire()

        if not self._is_triggered:
            self._is_triggered = True
            self._last_dt = self.clock._last_tick

            if self.clock._root_event is None:
                self.clock._last_event = self.clock._root_event = self
            else:
                self.clock._last_event.next = self
                self.prev = self.clock._last_event
                self.clock._last_event = self
            self.clock._lock_release()
            return True
        self.clock._lock_release()

    cpdef get_callback(self):
        '''Returns the callback associated with the event. Callbacks get stored
        with a indirect ref so that it doesn't keep objects alive. If the callback
        is dead, None is returned.
        '''
        cdef object callback = self.callback
        if callback is not None:
            return callback
        callback = self.weak_callback
        if callback.is_dead():
            return None
        return callback()

    @property
    def is_triggered(self):
        '''Returns whether the event is scheduled to have its callback executed by
        the kivy thread.
        '''
        return self._is_triggered

    cpdef cancel(self):
        ''' Cancels the callback if it was scheduled to be called. If not
        scheduled, nothing happens.
        '''
        self.clock._lock_acquire()
        if self._is_triggered:
            self._is_triggered = False

            # update the cap of the list
            if self.clock._cap_event is self:
                # cap is next, so we have reached the end of the list
                # because current one being processed is going to be the last event now
                if self.clock._cap_event is self.clock._next_event:
                   self.clock._cap_event = None
                else:
                    self.clock._cap_event = self.prev  # new cap

            # update the next event pointer
            if self.clock._next_event is self:
                self.clock._next_event = self.next

            if self.prev is None:  # we're first
                if self.next is None:  # we're also last
                    self.clock._last_event = self.clock._root_event = None
                else:  # there are more past us
                    self.clock._root_event = self.next
                    self.next.prev = None
            else:  # there are some behind us
                if self.next is None:  # we are last
                    self.clock._last_event = self.prev
                    self.prev.next = None
                else:  # we are in middle
                    self.prev.next = self.next
                    self.next.prev = self.prev
            self.prev = self.next = None

        self.clock._lock_release()

    cpdef release(self):
        '''(internal method) Converts the callback into a indirect ref.
        '''
        self.weak_callback = WeakMethod(self.callback)
        self.callback = None

    cpdef tick(self, double curtime):
        '''(internal method) Processes the event for the kivy thread.
        '''
        cdef object callback, ret
        # timeout happened ? (check also if we would miss from 5ms) this
        # 5ms increase the accuracy if the timing of animation for
        # example.
        if curtime - self._last_dt < self.timeout - 0.005:
            return True

        # calculate current timediff for this event
        self._dt = curtime - self._last_dt
        self._last_dt = curtime

        # get the callback
        callback = self.get_callback()
        if callback is None:
            self.cancel()
            return self.loop

        # if it's a trigger, allow to retrigger inside the callback
        # we have to remove event here, otherwise, if we remove later, the user
        # might have canceled in the callback and then re-triggered. That'd
        # result in the removal of the re-trigger
        if not self.loop:
            self.cancel()

        # call the callback
        ret = callback(self._dt)

        # if the user returns False explicitly, remove the event
        if self.loop and ret is False:
            self.cancel()
            return False
        return self.loop

    def __repr__(self):
        return '<ClockEvent callback=%r>' % self.get_callback()


cdef class CyClockBase(object):
    '''The base clock object with event support.
    '''

    def __init__(self, **kwargs):
        super(CyClockBase, self).__init__(**kwargs)
        self._root_event = None
        self._last_event = None
        self._next_event = None
        self._cap_event = None
        self._lock = Lock()
        self._lock_acquire = self._lock.acquire
        self._lock_release = self._lock.release

        self.max_iteration = 10

    cpdef create_trigger(self, callback, timeout=0, interval=False):
        '''Create a Trigger event. Check module documentation for more
        information.

        :returns:

            A :class:`ClockEvent` instance. To schedule the callback of this
            instance, you can call it.

        .. versionadded:: 1.0.5

        ..versionchanged:: 1.9.2

            ``interval`` has been added. If True, it create a event that is called
            every <timeout> seconds similar to :meth:`schedule_interval`. Defaults to
            False.
        '''
        cdef ClockEvent ev = ClockEvent(self, interval, callback, timeout, 0)
        ev.release()
        return ev

    cpdef schedule_once(self, callback, timeout=0):
        '''Schedule an event in <timeout> seconds. If <timeout> is unspecified
        or 0, the callback will be called after the next frame is rendered.

        :returns:

            A :class:`ClockEvent` instance. As opposed to
            :meth:`create_trigger` which only creates the trigger event, this
            method also schedules it.

        .. versionchanged:: 1.0.5
            If the timeout is -1, the callback will be called before the next
            frame (at :meth:`tick_draw`).
        '''
        cdef ClockEvent event
        if not callable(callback):
            raise ValueError('callback must be a callable, got %s' % callback)

        event = ClockEvent(
            self, False, callback, timeout, self._last_tick, None, True)
        return event

    cpdef schedule_interval(self, callback, timeout):
        '''Schedule an event to be called every <timeout> seconds.

        :returns:

            A :class:`ClockEvent` instance. As opposed to
            :meth:`create_trigger` which only creates the trigger event, this
            method also schedules it.
        '''
        cdef ClockEvent event
        if not callable(callback):
            raise ValueError('callback must be a callable, got %s' % callback)

        event = ClockEvent(
            self, True, callback, timeout, self._last_tick, None, True)
        return event

    cpdef unschedule(self, callback, all=True):
        '''Remove a previously scheduled event.

        :parameters:

            `callback`: :class:`ClockEvent` or a callable.
                If it's a :class:`ClockEvent` instance, then the callback
                associated with this event will be canceled if it is
                scheduled.

                If it's a callable, then the callable will be unscheduled if it
                was scheduled.

                ..warning::

                    Passing the callback function rather than the returned
                    :class:`ClockEvent` will result in a significantly slower
                    unscheduling.
            `all`: bool
                If True and if `callback` is a callable, all instances of this
                callable will be unscheduled (i.e. if this callable was
                scheduled multiple times). Defaults to `True`.

        .. versionchanged:: 1.9.0
            The all parameter was added. Before, it behaved as if `all` was
            `True`.
        '''
        cdef ClockEvent ev, cancel
        cdef list events
        if isinstance(callback, ClockEvent):
            ev = callback
            ev.cancel()
        else:
            if all:
                events = []
                self._lock_acquire()

                ev = self._root_event
                while ev is not None:
                    if ev.get_callback() == callback:
                        events.append(ev)
                    ev = ev.next

                self._lock_release()
                for ev in events:
                    ev.cancel()
            else:
                cancel = None
                self._lock_acquire()

                ev = self._root_event
                while ev is not None:
                    if ev.get_callback() == callback:
                        cancel = ev
                        break
                    ev = ev.next
                self._lock_release()
                if cancel is not None:
                    cancel.cancel()

    cpdef _release_references(self):
        # call that function to release all the direct reference to any
        # callback and replace it with a weakref
        cdef list events = []
        cdef ClockEvent ev
        self._lock_acquire()

        ev = self._root_event
        while ev is not None:
            if ev.callback is not None:
                events.append(ev)
            ev = ev.next

        self._lock_release()
        for ev in events:
            ev.release()

    cpdef _process_events(self):
        cdef ClockEvent event
        cdef int done = False

        self._lock_acquire()
        if self._root_event is None:
            self._lock_release()
            return

        self._cap_event = self._last_event
        event = self._root_event
        while not done:
            self._next_event = event.next
            done = self._cap_event is event or self._cap_event is None
            '''We have to worry about this case:

            If in this iteration the cap event is canceled then at end of this
            iteration _cap_event will have shifted to current event (or to the
            event before that if current_event is done) which will not be checked
            again for being the cap event and done will never be True
            since we are passed the current event. So, when canceling,
            if _next_event is the canceled event and it's also the _cap_event
            _cap_event is set to None.
            '''

            self._lock_release()

            try:
                event.tick(self._last_tick)
            except:
                raise
            else:
                self._lock_acquire()
            event = self._next_event

        self._cap_event = None
        self._lock_release()

    cpdef _process_events_before_frame(self):
        cdef ClockEvent event
        cdef int count = self.max_iteration
        cdef int found = True
        cdef int done = False

        while found:
            count -= 1
            if count == -1:
                Logger.critical(
                    'Clock: Warning, too much iteration done before'
                    ' the next frame. Check your code, or increase'
                    ' the Clock.max_iteration attribute')
                break

            # search event that have timeout = -1
            found = False
            done = False

            self._lock_acquire()
            if self._root_event is None:
                self._lock_release()
                return

            self._cap_event = self._last_event
            event = self._root_event
            while not done:
                if event.timeout != -1:
                    done = self._cap_event is event or self._cap_event is None
                    event = event.next
                    continue

                self._next_event = event.next
                done = self._cap_event is event or self._cap_event is None
                self._lock_release()
                found = True

                try:
                    event.tick(self._last_tick)
                except:
                    raise
                else:
                    self._lock_acquire()
                event = self._next_event
            self._cap_event = None
            self._lock_release()

    def get_events(self):
        '''Returns the list of :class:`ClockEvent` currently scheduled.
        '''
        cdef list events = []
        cdef ClockEvent ev

        self._lock_acquire()
        ev = self._root_event
        while ev is not None:
            events.append(ev)
            ev = ev.next
        self._lock_release()
        return events
