

__all__ = ('ClockNotRunningError', 'ClockEvent', 'CyClockBase',
           'FreeClockEvent', 'CyClockBaseFree')


cdef extern from "float.h":
    double DBL_MAX

from kivy.weakmethod import WeakMethod
from kivy.logger import Logger
from threading import Lock, RLock


class ClockNotRunningError(RuntimeError):
    """Raised by the kivy Clock when scheduling an event if the
    Kivy Clock has already finished (:class:`~CyClockBase.stop_clock` was
    called).
    """


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
            double starttime, cid=None, int trigger=False,
            clock_ended_callback=None, release_ref=True, **kwargs):
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
        self.weak_clock_ended_callback = None
        self.clock_ended_callback = clock_ended_callback
        self.release_ref = release_ref

        if trigger:
            clock._lock_acquire()
            # only fail if clock_ended_callback was provided from the lifecycle_aware API
            if self.clock.has_ended and (
                    self.clock_ended_callback is not None or
                    self.weak_clock_ended_callback is not None):
                clock._lock_release()
                raise ClockNotRunningError

            self._is_triggered = True

            if clock._root_event is None:
                clock._last_event = clock._root_event = self
            else:
                clock._last_event.next = self
                self.prev = clock._last_event
                clock._last_event = self
            clock._lock_release()

            self.clock.on_schedule(self)

    def __call__(self, *largs):
        ''' Schedules the callback associated with this instance.
        If the callback is already scheduled, it will not be scheduled again.
        '''
        # The lock must be held continuously between checking whether the clock
        # ended and triggering the event. Otherwise, if the clock has not ended,
        # then in between checking whether it ended and scheduling the event in
        # this thread, the main thread could have stopped the clock and
        # processed all the clock_ended_callbacks. So this event would be scheduled,
        # but callback and clock_ended_callback won't be called.
        self.clock._lock_acquire()
        # only fail if clock_ended_callback was provided from the lifecycle_aware API
        if self.clock.has_ended and (
                self.clock_ended_callback is not None or
                self.weak_clock_ended_callback is not None):
            self.clock._lock_release()
            raise ClockNotRunningError

        trigger = not self._is_triggered
        if trigger:
            self._is_triggered = True
            self._last_dt = self.clock._last_tick

            if self.clock._root_event is None:
                self.clock._last_event = self.clock._root_event = self
            else:
                self.clock._last_event.next = self
                self.prev = self.clock._last_event
                self.clock._last_event = self

        self.clock._lock_release()

        if trigger:
            self.clock.on_schedule(self)

    cpdef get_callback(self):
        '''Returns the callback associated with the event. Callbacks get stored
        with a indirect ref so that it doesn't keep objects alive. If the callback
        is dead, None is returned.
        '''
        cdef object callback = self.callback
        if callback is not None:
            return callback
        return self.weak_callback()

    cpdef get_clock_ended_callback(self):
        """Returns the clock_ended_callback associated with the event.
        Callbacks get stored with a indirect ref so that it doesn't keep
        objects alive. If the callback is dead or wasn't provided,
        None is returned.
        """
        cdef object callback = self.clock_ended_callback
        if callback is not None:
            return callback
        if self.weak_clock_ended_callback is None:
            return None
        return self.weak_clock_ended_callback()

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

        if self.clock_ended_callback is not None:
            self.weak_clock_ended_callback = WeakMethod(self.clock_ended_callback)
            self.clock_ended_callback = None

    cpdef tick(self, double curtime):
        '''(internal method) Processes the event for the kivy thread.
        '''
        cdef object callback, ret
        # timeout happened ? if less than resolution process it
        if curtime - self._last_dt < self.timeout - self.clock.get_resolution():
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
        # this may raise an exception, but the state must remain clean so we
        # can still cancel the event if the exception is handled and suppressed
        ret = callback(self._dt)

        # if the user returns False explicitly, remove the event
        if self.loop and ret is False:
            self.cancel()
            return False
        return self.loop

    def __repr__(self):
        return '<ClockEvent ({}) callback={}>'.format(self.timeout, self.get_callback())


cdef class FreeClockEvent(ClockEvent):
    '''The event returned by the ``Clock.XXX_free`` methods of
    :class:`CyClockBaseFree`. It stores whether the event was scheduled as a
    free event.
    '''

    def __init__(self, free, *largs, **kwargs):
        self.free = free
        ClockEvent.__init__(self, *largs, **kwargs)


cdef class CyClockBase(object):
    '''The base clock object with event support.
    '''

    def __cinit__(self, **kwargs):
        self.clock_resolution = -1
        self._max_fps = 60
        self.max_iteration = 20

    def __init__(self, **kwargs):
        super(CyClockBase, self).__init__(**kwargs)
        self._root_event = None
        self._last_event = None
        self._next_event = None
        self._cap_event = None
        self._lock = Lock()
        self._lock_acquire = self._lock.acquire
        self._lock_release = self._lock.release
        self._del_queue = []
        self._del_safe_lock = RLock()
        self._del_safe_done = False
        self.has_ended = False
        self.has_started = False

    def start_clock(self):
        """Must be called to start the clock.

        Once :meth:`stop_clock` is called, it cannot be started again.
        """
        self._lock_acquire()
        try:
            if self.has_started:
                return

            self.has_started = True
            # for now don't raise an exception when restarting because kivy's
            # graphical tests are not setup to handle clock isolation so they try
            # to restart the clock
            # if self.has_ended:
            #     raise TypeError('Clock already ended. Cannot re-start the Clock')
        finally:
            self._lock_release()

    def stop_clock(self):
        """Stops the clock and cleans up.

        This must be called to process the lifecycle_aware callbacks etc.
        """
        self._lock_acquire()
        try:
            if self.has_ended:
                return

            self.has_ended = True
        finally:
            self._lock_release()
        self._process_clock_ended_callbacks()

    cpdef get_resolution(self):
        '''Returns the minimum resolution the clock has. It's a function of
        :attr:`clock_resolution` and ``maxfps`` provided at the config.
        '''
        cdef double resolution = self.clock_resolution
        # timeout happened ? (check also if we would miss from 5ms) this
        # 5ms increase the accuracy if the timing of animation for
        # example.
        if resolution < 0:
            if self._max_fps:
                resolution = 1 / (3. * self._max_fps)
            else:
                resolution = 0.0001
        return resolution

    def on_schedule(self, event):
        '''Function that is called internally every time an event is triggered
        for this clock. It takes the event as a parameter.

        The order of ``on_schedule`` calls are not guaranteed to be in the same
        order that the events are scheduled. Similarly, it is possible that the
        event being scheduled was canceled before this is called on the event.
        That's because :meth:`on_schedule` may be called from different threads.
        '''
        pass

    cpdef ClockEvent create_lifecycle_aware_trigger(
            self, callback, clock_ended_callback, timeout=0, interval=False,
            release_ref=True):
        '''Create a Trigger event similarly to :meth:`create_trigger`, but the event
        is sensitive to the clock's state.

        If this event is triggered after the clock has stopped (:meth:`stop_clock`), then a
        :class:`ClockNotRunningError` will be raised. If the error is not raised,
        then either ``callback`` or ``clock_ended_callback`` will be
        called. ``callback`` will be called when the event
        is normally executed. If the clock is stopped before it can be executed,
        provided the app exited normally without crashing and the event wasn't manually
        canceled, and the callbacks are not garbage collected then
        ``clock_ended_callback`` will be called instead when the clock is stopped.

        :Parameters:

            `callback`: callable
                The callback to execute from kivy. It takes a single parameter - the
                current elapsed kivy time.
            `clock_ended_callback`: callable
                A callback that will be called if the clock is stopped
                while the event is still scheduled to be called. The callback takes
                a single parameter - the event object. When the event is successfully
                scheduled, if the app exited normally and the event wasn't canceled,
                and the callbacks are not garbage collected - it is guaranteed that
                either ``callback`` or ``clock_ended_callback`` would have been called.
            `timeout`: float
                How long to wait before calling the callback.
            `interval`: bool
                Whether the callback should be called once (False) or repeatedly
                with a period of ``timeout`` (True) like :meth:`schedule_interval`.
            `release_ref`: bool
                If True, the default, then if ``callback`` or ``clock_ended_callback``
                is a class method and the object has no references to it, then
                the object may be garbage collected and the callbacks won't be called.
                If False, the clock keeps a reference to the object preventing it
                from being garbage collected - so it will be called.

        :returns:

            A :class:`ClockEvent` instance. To schedule the callback of this
            instance, you can call it.

        .. versionadded:: 2.0.0
        '''
        cdef ClockEvent ev = ClockEvent(
            self, interval, callback, timeout, 0,
            clock_ended_callback=clock_ended_callback, release_ref=release_ref)
        if release_ref:
            ev.release()
        return ev

    cpdef ClockEvent create_trigger(
            self, callback, timeout=0, interval=False, release_ref=True):
        '''Create a Trigger event. It is thread safe but not ``__del__`` or
        ``__dealloc__`` safe (see :meth:`schedule_del_safe`).
        Check module documentation for more information.

        To cancel the event before it is executed, call :meth:`ClockEvent.cancel`
        on the returned event.
        To schedule it again, simply call the event (``event()``) and it'll be safely
        rescheduled if it isn't already scheduled.

        :Parameters:

            `callback`: callable
                The callback to execute from kivy. It takes a single parameter - the
                current elapsed kivy time.
            `timeout`: float
                How long to wait before calling the callback.
            `interval`: bool
                Whether the callback should be called once (False) or repeatedly
                with a period of ``timeout`` (True) like :meth:`schedule_interval`.
            `release_ref`: bool
                If True, the default, then if ``callback``
                is a class method and the object has no references to it, then
                the object may be garbage collected and the callbacks won't be called.
                If False, the clock keeps a reference to the object preventing it
                from being garbage collected - so it will be called.

        :returns:

            A :class:`ClockEvent` instance. To schedule the callback of this
            instance, you can call it.

        .. versionadded:: 1.0.5

        .. versionchanged:: 1.10.0

            ``interval`` has been added.

        .. versionchanged:: 2.0.0

            ``release_ref`` has been added.
        '''
        cdef ClockEvent ev = ClockEvent(
            self, interval, callback, timeout, 0, release_ref=release_ref)
        if release_ref:
            ev.release()
        return ev

    cpdef schedule_lifecycle_aware_del_safe(self, callback, clock_ended_callback):
        '''Schedule a callback that is thread safe and ``__del__`` or
        ``__dealloc__`` safe similarly to :meth:`schedule_del_safe`, but the callback
        is sensitive to the clock's state.

        If this event is triggered after the clock has stopped (:meth:`stop_clock`), then a
        :class:`ClockNotRunningError` will be raised. If the error is not raised,
        then either ``callback`` or ``clock_ended_callback`` will be
        called. ``callback`` will be called when the callback
        is normally executed. If the clock is stopped before it can be executed,
        provided the app exited normally without crashing then
        ``clock_ended_callback`` will be called instead when the clock is stopped.

        :Parameters:

            `callback`: Callable
                The callback the execute from kivy. It takes no parameters and
                cannot be canceled.
            `clock_ended_callback`: callable
                A callback that will be called if the clock is stopped
                while the callback is still scheduled to be called. The callback takes
                a single parameter - the callback. If the
                app exited normally, it is guaranteed that either ``callback``
                or ``clock_ended_callback`` would have been called.

        .. versionadded:: 2.0.0
        '''
        with self._del_safe_lock:
            if self._del_safe_done:
                raise ClockNotRunningError
            self._del_queue.append((callback, clock_ended_callback))

    cpdef schedule_del_safe(self, callback):
        '''Schedule a callback that is thread safe and ``__del__`` or
        ``__dealloc__`` safe.

        It's unsafe to call various kinds of code from ``__del__`` or
        ``__dealloc__`` methods because they can be executed at any time. Most
        Kivy's Clock methods are unsafe to call the Clock from these methods. Instead,
        use this method, which is thread safe and ``__del__`` or ``__dealloc__``
        safe, to schedule the callback in the kivy thread. It'll be executed
        in order after the normal events are processed.

        :Parameters:

            `callback`: Callable
                The callback the execute from kivy. It takes no parameters and
                cannot be canceled.

        .. versionadded:: 1.11.0
        '''
        self._del_queue.append((callback, None))

    cpdef ClockEvent schedule_once(self, callback, timeout=0):
        '''Schedule an event in <timeout> seconds. If <timeout> is unspecified
        or 0, the callback will be called after the next frame is rendered.
        See :meth:`create_trigger` for advanced scheduling and more details.

        To cancel the event before it is executed, call :meth:`ClockEvent.cancel`
        on the returned event.
        If the callback is a class method, a weakref to the object is created and it
        may be garbage collected if there's no other reference to the object.

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

    cpdef ClockEvent schedule_interval(self, callback, timeout):
        '''Schedule an event to be called every <timeout> seconds.
        See :meth:`create_trigger` for advanced scheduling and more details.

        To cancel the event before it is executed, call :meth:`ClockEvent.cancel`
        on the returned event.
        If the callback is a class method, a weakref to the object is created and it
        may be garbage collected if there's no other reference to the object.

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

        An :class:`ClockEvent` can also be canceled directly by calling
        :meth:`ClockEvent.cancel`.

        :parameters:

            `callback`: :class:`ClockEvent` or a callable.
                If it's a :class:`ClockEvent` instance, then the callback
                associated with this event will be canceled if it is
                scheduled.

                If it's a callable, then the callable will be unscheduled if it
                was scheduled.

                .. warning::

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
            if ev.callback is not None and ev.release_ref:
                events.append(ev)
            ev = ev.next

        self._lock_release()
        for ev in events:
            ev.release()

    cpdef _process_del_safe_events(self):
        callbacks = self._del_queue[:]
        del self._del_queue[:len(callbacks)]
        for callback, _ in callbacks:
            try:
                callback()
            except BaseException as e:
                self.handle_exception(e)

    cpdef _process_events(self):
        cdef ClockEvent event
        cdef int done = False

        self._lock_acquire()
        if self._root_event is None:
            self._lock_release()
            self._process_del_safe_events()
            return

        self._cap_event = self._last_event
        event = self._root_event
        while not done and event is not None:
            self._next_event = event.next
            done = self._cap_event is event or self._cap_event is None
            '''Usage of _cap_event: We have to worry about this case:

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
            except BaseException as e:
                # cancel the event either way
                event.cancel()
                self.handle_exception(e)
            self._lock_acquire()
            event = self._next_event

        self._next_event = self._cap_event = None
        self._lock_release()

        self._process_del_safe_events()

    cpdef _process_events_before_frame(self):
        cdef ClockEvent event
        cdef int count = self.max_iteration
        cdef int found = True
        cdef int done = False

        while found:
            count -= 1
            if count == -1:
                remaining_events = '\n'.join(
                    map(str, self.get_before_frame_events()))
                Logger.critical(
                    f'Clock: Warning, too much iteration done before'
                    f' the next frame. Check your code, or increase'
                    f' the Clock.max_iteration attribute. Remaining events:\n'
                    f'{remaining_events}')
                break

            # search event that have timeout = -1
            found = False
            done = False

            self._lock_acquire()
            if self._root_event is None:
                self._lock_release()
                return

            # see _process_events for the logic
            self._cap_event = self._last_event
            event = self._root_event
            while not done and event is not None:
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
                except BaseException as e:
                    # cancel the event either way
                    event.cancel()
                    self.handle_exception(e)
                self._lock_acquire()
                event = self._next_event
            self._next_event = self._cap_event = None
            self._lock_release()

    cpdef get_min_timeout(self):
        '''Returns the remaining time since the start of the current frame
        for the event with the smallest timeout.
        '''
        cdef ClockEvent ev
        cdef double val = DBL_MAX
        self._lock_acquire()
        ev = self._root_event
        while ev is not None:
            if ev.timeout <= 0:
                val = 0
                break
            val = min(val, ev.timeout + ev._last_dt)
            ev = ev.next
        self._lock_release()

        return val

    cpdef get_events(self):
        '''Returns the list of :class:`ClockEvent` instances currently scheduled.
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

    cpdef get_before_frame_events(self):
        '''Returns the list of :class:`ClockEvent` instances that are scheduled
        to be called before the next frame (``-1`` timeout).

        .. versionadded:: 2.1.0
        '''
        cdef list events = []
        cdef ClockEvent ev

        self._lock_acquire()
        ev = self._root_event
        while ev is not None:
            if ev.timeout == -1:
                events.append(ev)
            ev = ev.next
        self._lock_release()
        return events

    def handle_exception(self, e):
        """Provides an opportunity to handle an event's exception.

        If desired, the exception is handled, otherwise it should be raised
        again. By default it is raised again.

        :param e: The exception to be handled.

        .. versionadded:: 2.0.0
        """
        raise

    cpdef _process_clock_ended_del_safe_events(self):
        with self._del_safe_lock:
            self._del_safe_done = True
            callbacks = self._del_queue[:]

        del self._del_queue[:len(callbacks)]
        for callback, clock_ended_callback in callbacks:
            try:
                if clock_ended_callback is not None:
                    clock_ended_callback(callback)
            except BaseException as e:
                self.handle_exception(e)

    cpdef _process_clock_ended_callbacks(self):
        # at this point, if an event is scheduled, it should raise an exception
        cdef ClockEvent event
        cdef int done = False

        self._lock_acquire()
        if self._root_event is None:
            self._lock_release()
            self._process_clock_ended_del_safe_events()
            return

        # see _process_events for the logic
        self._cap_event = self._last_event
        event = self._root_event
        while not done and event is not None:
            self._next_event = event.next
            done = self._cap_event is event or self._cap_event is None
            self._lock_release()

            callback = event.get_clock_ended_callback()
            if callback is not None:
                try:
                    callback(event)
                except BaseException as e:
                    self.handle_exception(e)
            self._lock_acquire()
            event = self._next_event

        self._next_event = self._cap_event = None
        self._lock_release()

        self._process_clock_ended_del_safe_events()


cdef class CyClockBaseFree(CyClockBase):
    '''A clock class that supports scheduling free events in addition to normal
    events.

    Each of the :meth:`~CyClockBase.create_trigger`,
    :meth:`~CyClockBase.schedule_once`, and :meth:`~CyClockBase.schedule_interval`
    methods, which create a normal event, have a corresponding method
    for creating a free event.
    '''

    cpdef FreeClockEvent create_lifecycle_aware_trigger(
            self, callback, clock_ended_callback, timeout=0, interval=False,
            release_ref=True):
        cdef FreeClockEvent event
        if not callable(callback):
            raise ValueError('callback must be a callable, got %s' % callback)

        event = FreeClockEvent(
            False, self, interval, callback, timeout, 0,
            clock_ended_callback=clock_ended_callback, release_ref=release_ref)
        if release_ref:
            event.release()
        return event

    cpdef FreeClockEvent create_trigger(
            self, callback, timeout=0, interval=False, release_ref=True):
        cdef FreeClockEvent event
        if not callable(callback):
            raise ValueError('callback must be a callable, got %s' % callback)

        event = FreeClockEvent(
            False, self, interval, callback, timeout, 0, release_ref=release_ref)
        if release_ref:
            event.release()
        return event

    cpdef FreeClockEvent schedule_once(self, callback, timeout=0):
        cdef FreeClockEvent event
        if not callable(callback):
            raise ValueError('callback must be a callable, got %s' % callback)

        event = FreeClockEvent(
            False, self, False, callback, timeout, self._last_tick, None, True)
        return event

    cpdef FreeClockEvent schedule_interval(self, callback, timeout):
        cdef FreeClockEvent event
        if not callable(callback):
            raise ValueError('callback must be a callable, got %s' % callback)

        event = FreeClockEvent(
            False, self, True, callback, timeout, self._last_tick, None, True)
        return event

    cpdef FreeClockEvent create_lifecycle_aware_trigger_free(
            self, callback, clock_ended_callback, timeout=0, interval=False,
            release_ref=True):
        '''Similar to :meth:`~CyClockBase.create_lifecycle_aware_trigger`, but instead creates
        a free event.
        '''
        cdef FreeClockEvent event
        if not callable(callback):
            raise ValueError('callback must be a callable, got %s' % callback)

        event = FreeClockEvent(
            True, self, interval, callback, timeout, 0,
            clock_ended_callback=clock_ended_callback, release_ref=release_ref)
        if release_ref:
            event.release()
        return event

    cpdef FreeClockEvent create_trigger_free(
            self, callback, timeout=0, interval=False, release_ref=True):
        '''Similar to :meth:`~CyClockBase.create_trigger`, but instead creates
        a free event.
        '''
        cdef FreeClockEvent event
        if not callable(callback):
            raise ValueError('callback must be a callable, got %s' % callback)

        event = FreeClockEvent(
            True, self, interval, callback, timeout, 0, release_ref=release_ref)
        if release_ref:
            event.release()
        return event

    cpdef FreeClockEvent schedule_once_free(self, callback, timeout=0):
        '''Similar to :meth:`~CyClockBase.schedule_once`, but instead creates
        a free event.
        '''
        cdef FreeClockEvent event
        if not callable(callback):
            raise ValueError('callback must be a callable, got %s' % callback)

        event = FreeClockEvent(
            True, self, False, callback, timeout, self._last_tick, None, True)
        return event

    cpdef FreeClockEvent schedule_interval_free(self, callback, timeout):
        '''Similar to :meth:`~CyClockBase.schedule_interval`, but instead creates
        a free event.
        '''
        cdef FreeClockEvent event
        if not callable(callback):
            raise ValueError('callback must be a callable, got %s' % callback)

        event = FreeClockEvent(
            True, self, True, callback, timeout, self._last_tick, None, True)
        return event

    cpdef _process_free_events(self, double last_tick):
        cdef FreeClockEvent event
        cdef int done = False

        self._lock_acquire()
        if self._root_event is None:
            self._lock_release()
            return

        self._cap_event = self._last_event
        event = self._root_event
        while not done and event is not None:
            if not event.free:
                done = self._cap_event is event or self._cap_event is None
                event = event.next
                continue

            self._next_event = event.next
            done = self._cap_event is event or self._cap_event is None

            self._lock_release()

            try:
                event.tick(last_tick)
            except BaseException as e:
                # cancel the event either way
                event.cancel()
                self.handle_exception(e)
            self._lock_acquire()
            event = self._next_event

        self._next_event = self._cap_event = None
        self._lock_release()

    cpdef get_min_free_timeout(self):
        '''Returns the remaining time since the start of the current frame
        for the *free* event with the smallest timeout.
        '''
        cdef FreeClockEvent ev
        cdef double val = DBL_MAX

        self._lock_acquire()
        ev = self._root_event
        while ev is not None:
            if ev.free:
                if ev.timeout <= 0:
                    val = 0
                    break
                val = min(val, ev.timeout + ev._last_dt)
            ev = ev.next
        self._lock_release()

        return val
