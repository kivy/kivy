'''
Clock object
============

The :class:`Clock` object allows you to schedule a function call in the
future; once or repeatedly at specified intervals. You can get the time
elapsed between the scheduling and the calling of the callback via the
`dt` argument::

    # dt means delta-time
    def my_callback(dt):
        pass

    # call my_callback every 0.5 seconds
    Clock.schedule_interval(my_callback, 0.5)

    # call my_callback in 5 seconds
    Clock.schedule_once(my_callback, 5)

    # call my_callback as soon as possible (usually next frame.)
    Clock.schedule_once(my_callback)

.. note::

    If the callback returns False, the schedule will be removed.

If you want to schedule a function to call with default arguments, you can use
the `functools.partial
<http://docs.python.org/library/functools.html#functools.partial>`_ python
module::

    from functools import partial

    def my_callback(value, key, *largs):
        pass

    Clock.schedule_interval(partial(my_callback, 'my value', 'my key'), 0.5)

Conversely, if you want to schedule a function that doesn't accept the dt
argument, you can use a `lambda
<http://docs.python.org/2/reference/expressions.html#lambda>`_ expression
to write a short function that does accept dt. For Example::

    def no_args_func():
        print("I accept no arguments, so don't schedule me in the clock")

    Clock.schedule_once(lambda dt: no_args_func(), 0.5)

.. note::

    You cannot unschedule an anonymous function unless you keep a
    reference to it. It's better to add \*args to your function
    definition so that it can be called with an arbitrary number of
    parameters.

.. important::

    The callback is weak-referenced: you are responsible for keeping a
    reference to your original object/callback. If you don't keep a
    reference, the ClockBase will never execute your callback. For
    example::

        class Foo(object):
            def start(self):
                Clock.schedule_interval(self.callback, 0.5)

            def callback(self, dt):
                print('In callback')

        # A Foo object is created and the method start is called.
        # Because no reference is kept to the instance returned from Foo(),
        # the object will be collected by the Python Garbage Collector and
        # your callback will be never called.
        Foo().start()

        # So you should do the following and keep a reference to the instance
        # of foo until you don't need it anymore!
        foo = Foo()
        foo.start()


.. _schedule-before-frame:

Schedule before frame
---------------------

.. versionadded:: 1.0.5

Sometimes you need to schedule a callback BEFORE the next frame. Starting
from 1.0.5, you can use a timeout of -1::

    Clock.schedule_once(my_callback, 0) # call after the next frame
    Clock.schedule_once(my_callback, -1) # call before the next frame

The Clock will execute all the callbacks with a timeout of -1 before the
next frame even if you add a new callback with -1 from a running
callback. However, :class:`Clock` has an iteration limit for these
callbacks: it defaults to 10.

If you schedule a callback that schedules a callback that schedules a .. etc
more than 10 times, it will leave the loop and send a warning to the console,
then continue after the next frame. This is implemented to prevent bugs from
hanging or crashing the application.

If you need to increase the limit, set the :attr:`max_iteration` property::

    from kivy.clock import Clock
    Clock.max_iteration = 20

.. _triggered-events:

Triggered Events
----------------

.. versionadded:: 1.0.5

A triggered event is a way to defer a callback exactly like schedule_once(),
but with some added convenience. The callback will only be scheduled once per
frame even if you call the trigger twice (or more). This is not the case
with :meth:`Clock.schedule_once`::

    # will run the callback twice before the next frame
    Clock.schedule_once(my_callback)
    Clock.schedule_once(my_callback)

    # will run the callback once before the next frame
    t = Clock.create_trigger(my_callback)
    t()
    t()

Before triggered events, you may have used this approach in a widget::

    def trigger_callback(self, *largs):
        Clock.unschedule(self.callback)
        Clock.schedule_once(self.callback)

As soon as you call `trigger_callback()`, it will correctly schedule the
callback once in the next frame. It is more convenient to create and bind to
the triggered event than using :meth:`Clock.schedule_once` in a function::

    from kivy.clock import Clock
    from kivy.uix.widget import Widget

    class Sample(Widget):
        def __init__(self, **kwargs):
            self._trigger = Clock.create_trigger(self.cb)
            super(Sample, self).__init__(**kwargs)
            self.bind(x=self._trigger, y=self._trigger)

        def cb(self, *largs):
            pass

Even if x and y changes within one frame, the callback is only run once.

.. note::

    :meth:`ClockBase.create_trigger` also has a timeout parameter that
    behaves exactly like :meth:`ClockBase.schedule_once`.

Threading
----------

.. versionchanged:: 1.9.2

The kivy clock is now fully thread safe.
'''

__all__ = ('Clock', 'ClockBase', 'ClockEvent', 'mainthread')

from sys import platform
from os import environ
from functools import wraps, partial
from kivy.context import register_context
from kivy.weakmethod import WeakMethod
from kivy.config import Config
from kivy.logger import Logger
from kivy.compat import clock as _default_time
import time
from threading import Lock

try:
    import ctypes
    if platform in ('win32', 'cygwin'):
        # Win32 Sleep function is only 10-millisecond resolution, so
        # instead use a waitable timer object, which has up to
        # 100-nanosecond resolution (hardware and implementation
        # dependent, of course).

        _kernel32 = ctypes.windll.kernel32

        class _ClockBase(object):
            def __init__(self):
                self._timer = _kernel32.CreateWaitableTimerA(None, True, None)

            def usleep(self, microseconds):
                delay = ctypes.c_longlong(int(-microseconds * 10))
                _kernel32.SetWaitableTimer(
                    self._timer, ctypes.byref(delay), 0,
                    ctypes.c_void_p(), ctypes.c_void_p(), False)
                _kernel32.WaitForSingleObject(self._timer, 0xffffffff)
    else:
        if platform == 'darwin':
            _libc = ctypes.CDLL('libc.dylib')
        else:
            from ctypes.util import find_library
            _libc = ctypes.CDLL(find_library('c'), use_errno=True)

            def _libc_clock_gettime_wrapper():
                from os import strerror

                class struct_tv(ctypes.Structure):
                    _fields_ = [('tv_sec', ctypes.c_long),
                                ('tv_usec', ctypes.c_long)]

                _clock_gettime = _libc.clock_gettime
                _clock_gettime.argtypes = [ctypes.c_long,
                                           ctypes.POINTER(struct_tv)]

                if 'linux' in platform:
                    _clockid = 4  # CLOCK_MONOTONIC_RAW (Linux specific)
                elif 'freebsd' in platform:
                    # clockid constants from sys/time.h
                    # _clockid = 4 # CLOCK_MONOTONIC (FreeBSD specific)
                    # 11: CLOCK_MONOTONIC_PRECISE (FreeBSD known OK for 10.2)
                    _clockid = 11
                    # _clockid = 12
                    # 12: CLOCK_MONOTONIC_FAST (FreeBSD specific)
                    Logger.debug('clock.py: {{{:s}}} clock ID {:d}'.format(
                        platform, _clockid))
                else:
                    _clockid = 1  # CLOCK_MONOTONIC

                tv = struct_tv()

                def _time():
                    if _clock_gettime(ctypes.c_long(_clockid),
                                      ctypes.pointer(tv)) != 0:
                        _ernno = ctypes.get_errno()
                        raise OSError(_ernno, strerror(_ernno))
                    return tv.tv_sec + (tv.tv_usec * 0.000000001)

                return _time

            _default_time = _libc_clock_gettime_wrapper()

        _libc.usleep.argtypes = [ctypes.c_ulong]
        _libc_usleep = _libc.usleep

        class _ClockBase(object):
            def usleep(self, microseconds):
                _libc_usleep(int(microseconds))

except (OSError, ImportError, AttributeError):
    # ImportError: ctypes is not available on python-for-android.
    # AttributeError: ctypes is now available on python-for-android, but
    #   "undefined symbol: clock_gettime". CF #3797
    # OSError: if the libc cannot be readed (like with buildbot: invalid ELF
    # header)

    _default_sleep = time.sleep

    class _ClockBase(object):
        def usleep(self, microseconds):
            _default_sleep(microseconds / 1000000.)


class ClockEvent(object):
    ''' A class that describes a callback scheduled with kivy's :attr:`Clock`.
    This class is never created by the user; instead, kivy creates and returns
    an instance of this class when scheduling a callback.

    .. warning::
        Most of the methods of this class are internal and can change without
        notice. The only exception are the :meth:`cancel` and
        :meth:`__call__` methods.
    '''

    _is_triggered = False
    next = None
    prev = None
    cid = None

    def __init__(self, clock, loop, callback, timeout, starttime, cid=None,
                 trigger=False):
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
                last = clock._last_event
                last.next = self
                self.prev = last
                clock._last_event = self
            clock._lock_release()

    def __call__(self, *largs):
        ''' Schedules the callback associated with this instance.
        If the callback is already scheduled, it will not be scheduled again.
        '''
        clock = self.clock
        clock._lock_acquire()

        if not self._is_triggered:
            self._is_triggered = True
            self._last_dt = self.clock._last_tick
            self.next = None

            if clock._root_event is None:
                clock._last_event = clock._root_event = self
                self.prev = self.next = None
            else:
                last = clock._last_event
                last.next = self
                self.prev = last
                clock._last_event = self
            clock._lock_release()
            return True
        clock._lock_release()

    def get_callback(self):
        callback = self.callback
        if callback is not None:
            return callback
        callback = self.weak_callback
        if callback.is_dead():
            return None
        return callback()

    @property
    def is_triggered(self):
        return self._is_triggered

    def cancel(self):
        ''' Cancels the callback if it was scheduled to be called.
        '''
        clock = self.clock
        clock._lock_acquire()
        if self._is_triggered:
            self._is_triggered = False
            next, prev = self.next, self.prev

            # update the next event pointer
            if clock._next_event is self:
                clock._next_event = next

            if prev is None:  # we're first
                if next is None:  # we're also last
                    clock._last_event = clock._root_event = None
                else:  # there are more past us
                    clock._root_event = next
                    next.prev = None
            else:  # there are some behind us
                if next is None:  # we are last
                    clock._last_event = prev
                    prev.next = None
                else:  # we are in middle
                    prev.next = next
                    next.prev = prev

        clock._lock_release()

    def release(self):
        self.weak_callback = WeakMethod(self.callback)
        self.callback = None

    def tick(self, curtime, remove=None):
        # timeout happened ? (check also if we would miss from 5ms) this
        # 5ms increase the accuracy if the timing of animation for
        # example.
        if curtime - self._last_dt < self.timeout - 0.005:
            return True

        # calculate current timediff for this event
        self._dt = curtime - self._last_dt
        self._last_dt = curtime
        loop = self.loop

        # get the callback
        callback = self.get_callback()
        if callback is None:
            self.cancel()
            return loop

        # if it's a trigger, allow to retrigger inside the callback
        # we have to remove event here, otherwise, if we remove later, the user
        # might have canceled in the callback and then re-triggered. That'd
        # result in the removal of the re-trigger
        if not loop:
            self.cancel()

        # call the callback
        ret = callback(self._dt)

        # if the user returns False explicitly, remove the event
        if loop and ret is False:
            self.cancel()
            return False
        return loop

    def __repr__(self):
        return '<ClockEvent callback=%r>' % self.get_callback()


class ClockBase(_ClockBase):
    '''A clock object with event support.
    '''
    __slots__ = (
        '_dt', '_last_fps_tick', '_last_tick', '_fps', '_rfps', '_start_tick',
        '_fps_counter', '_rfps_counter', '_frames',
        '_frames_displayed', '_max_fps', 'max_iteration', '_root_event',
        '_next_event', '_last_event', '_lock', '_lock_acquire',
        '_lock_release')

    MIN_SLEEP = 0.005
    SLEEP_UNDERSHOOT = MIN_SLEEP - 0.001

    def __init__(self):
        super(ClockBase, self).__init__()
        self._dt = 0.0001
        self._start_tick = self._last_tick = self.time()
        self._fps = 0
        self._rfps = 0
        self._fps_counter = 0
        self._rfps_counter = 0
        self._last_fps_tick = None
        self._frames = 0
        self._frames_displayed = 0
        self._max_fps = float(Config.getint('graphics', 'maxfps'))
        self._root_event = None
        self._last_event = None
        self._next_event = None
        lock = self._lock = Lock()
        self._lock_acquire = lock.acquire
        self._lock_release = lock.release

        #: .. versionadded:: 1.0.5
        #:     When a schedule_once is used with -1, you can add a limit on
        #:     how iteration will be allowed. That is here to prevent too much
        #:     relayout.
        self.max_iteration = 10

    @property
    def frametime(self):
        '''Time spent between the last frame and the current frame
        (in seconds).

        .. versionadded:: 1.8.0
        '''
        return self._dt

    @property
    def frames(self):
        '''Number of internal frames (not necesseraly drawed) from the start of
        the clock.

        .. versionadded:: 1.8.0
        '''
        return self._frames

    @property
    def frames_displayed(self):
        '''Number of displayed frames from the start of the clock.
        '''
        return self._frames_displayed

    def tick(self):
        '''Advance the clock to the next step. Must be called every frame.
        The default clock has a tick() function called by the core Kivy
        framework.'''

        self._release_references()

        # do we need to sleep ?
        if self._max_fps > 0:
            min_sleep = self.MIN_SLEEP
            sleep_undershoot = self.SLEEP_UNDERSHOOT
            fps = self._max_fps
            usleep = self.usleep

            sleeptime = 1 / fps - (self.time() - self._last_tick)
            while sleeptime - sleep_undershoot > min_sleep:
                usleep(1000000 * (sleeptime - sleep_undershoot))
                sleeptime = 1 / fps - (self.time() - self._last_tick)

        # tick the current time
        current = self.time()
        self._dt = current - self._last_tick
        self._frames += 1
        self._fps_counter += 1
        self._last_tick = current

        # calculate fps things
        if self._last_fps_tick is None:
            self._last_fps_tick = current
        elif current - self._last_fps_tick > 1:
            d = float(current - self._last_fps_tick)
            self._fps = self._fps_counter / d
            self._rfps = self._rfps_counter
            self._last_fps_tick = current
            self._fps_counter = 0
            self._rfps_counter = 0

        # process event
        self._process_events()

        return self._dt

    def tick_draw(self):
        '''Tick the drawing counter.
        '''
        self._process_events_before_frame()
        self._rfps_counter += 1
        self._frames_displayed += 1

    def get_fps(self):
        '''Get the current average FPS calculated by the clock.
        '''
        return self._fps

    def get_rfps(self):
        '''Get the current "real" FPS calculated by the clock.
        This counter reflects the real framerate displayed on the screen.

        In contrast to get_fps(), this function returns a counter of the
        number of frames, not the average of frames per second.
        '''
        return self._rfps

    def get_time(self):
        '''Get the last tick made by the clock.'''
        return self._last_tick

    def get_boottime(self):
        '''Get the time in seconds from the application start.'''
        return self._last_tick - self._start_tick

    def create_trigger(self, callback, timeout=0):
        '''Create a Trigger event. Check module documentation for more
        information.

        :returns:

            A :class:`ClockEvent` instance. To schedule the callback of this
            instance, you can call it.

        .. versionadded:: 1.0.5
        '''
        ev = ClockEvent(self, False, callback, timeout, 0)
        ev.release()
        return ev

    def schedule_once(self, callback, timeout=0):
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
        if not callable(callback):
            raise ValueError('callback must be a callable, got %s' % callback)
        event = ClockEvent(
            self, False, callback, timeout, self._last_tick, None, True)
        return event

    def schedule_interval(self, callback, timeout):
        '''Schedule an event to be called every <timeout> seconds.

        :returns:

            A :class:`ClockEvent` instance. As opposed to
            :meth:`create_trigger` which only creates the trigger event, this
            method also schedules it.
        '''
        if not callable(callback):
            raise ValueError('callback must be a callable, got %s' % callback)
        event = ClockEvent(
            self, True, callback, timeout, self._last_tick, None, True)
        return event

    def unschedule(self, callback, all=True):
        '''Remove a previously scheduled event.

        :parameters:

            `callback`: :class:`ClockEvent` or a callable.
                If it's a :class:`ClockEvent` instance, then the callback
                associated with this event will be canceled if it is
                scheduled. If it's a callable, then the callable will be
                unscheduled if it is scheduled.
            `all`: bool
                If True and if `callback` is a callable, all instances of this
                callable will be unscheduled (i.e. if this callable was
                scheduled multiple times). Defaults to `True`.

        .. versionchanged:: 1.9.0
            The all parameter was added. Before, it behaved as if `all` was
            `True`.
        '''
        if isinstance(callback, ClockEvent):
            callback.cancel()
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

    def _release_references(self):
        # call that function to release all the direct reference to any
        # callback and replace it with a weakref
        events = []
        self._lock_acquire()

        ev = self._root_event
        while ev is not None:
            if ev.callback is not None:
                events.append(ev)
            ev = ev.next

        self._lock_release()
        for ev in events:
            ev.release()

    def _process_events(self):
        acquire, release = self._lock_acquire, self._lock_release

        acquire()
        event = self._root_event
        while event is not None:
            self._next_event = event.next
            release()

            try:
                event.tick(self._last_tick)
            except:
                raise
            else:
                acquire()
            event = self._next_event
        release()

    def _process_events_before_frame(self):
        acquire, release = self._lock_acquire, self._lock_release
        count = self.max_iteration
        found = True

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
            acquire()
            event = self._root_event
            while event is not None:
                if event.timeout != -1:
                    event = event.next
                    continue

                self._next_event = event.next
                release()
                found = True

                try:
                    event.tick(self._last_tick)
                except:
                    raise
                else:
                    acquire()
                event = self._next_event
            release()

    time = staticmethod(partial(_default_time))

ClockBase.time.__doc__ = '''Proxy method for :func:`~kivy.compat.clock`. '''


def mainthread(func):
    '''Decorator that will schedule the call of the function for the next
    available frame in the mainthread. It can be useful when you use
    :class:`~kivy.network.urlrequest.UrlRequest` or when you do Thread
    programming: you cannot do any OpenGL-related work in a thread.

    Please note that this method will return directly and no result can be
    returned::

        @mainthread
        def callback(self, *args):
            print('The request succedded!',
                  'This callback is called in the main thread.')

        self.req = UrlRequest(url='http://...', on_success=callback)

    .. versionadded:: 1.8.0
    '''
    @wraps(func)
    def delayed_func(*args, **kwargs):
        def callback_func(dt):
            func(*args, **kwargs)
        Clock.schedule_once(callback_func, 0)
    return delayed_func

if 'KIVY_DOC_INCLUDE' in environ:
    #: Instance of :class:`ClockBase`.
    Clock = None
else:
    Clock = register_context('Clock', ClockBase)
