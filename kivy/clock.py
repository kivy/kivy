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

    If the callback returns False, the schedule will be canceled and won't
    repeat.

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

If you schedule a callback that schedules a callback that schedules a ... etc
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

A triggered event is a way to defer a callback. It functions exactly like
schedule_once() and schedule_interval() except that it doesn't immediately
schedule the callback. Instead, one schedules the callback using the
:class:`ClockEvent` returned by it. This ensures that you can call the event
multiple times but it won't be scheduled more than once. This is not the case
with :meth:`Clock.schedule_once`::

    # will run the callback twice before the next frame
    Clock.schedule_once(my_callback)
    Clock.schedule_once(my_callback)

    # will run the callback once before the next frame
    event = Clock.create_trigger(my_callback)
    event()
    event()

    # will also run the callback only once before the next frame
    event = Clock.schedule_once(my_callback)  # now it's already scheduled
    event()  # won't be scheduled again
    event()

In addition, it is more convenient to create and bind to
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

:meth:`CyClockBase.create_trigger` has a timeout parameter that
behaves exactly like :meth:`CyClockBase.schedule_once`.

.. versionchanged:: 1.10.0

    :meth:`CyClockBase.create_trigger` now has a ``interval`` parameter.
    If False, the default, it'll create an event similar to
    :meth:`CyClockBase.schedule_once`. Otherwise it'll create an event
    similar to :meth:`CyClockBase.schedule_interval`.

Unscheduling
-------------

An event scheduled with :meth:`CyClockBase.schedule_once`,
:meth:`CyClockBase.schedule_interval`, or with
:meth:`CyClockBase.create_trigger` and then triggered can be unscheduled in
multiple ways. E.g::

    def my_callback(dt):
        pass

    # call my_callback every 0.5 seconds
    event = Clock.schedule_interval(my_callback, 0.5)

    # call my_callback in 5 seconds
    event2 = Clock.schedule_once(my_callback, 5)

    event_trig = Clock.create_trigger(my_callback, 5)
    event_trig()

    # unschedule using cancel
    event.cancel()

    # unschedule using Clock.unschedule
    Clock.unschedule(event2)

    # unschedule using Clock.unschedule with the callback
    # NOT RECOMMENDED
    Clock.unschedule(my_callback)

The best way to unschedule a callback is with :meth:`ClockEvent.cancel`.
:meth:`CyClockBase.unschedule` is mainly an alias for that for that function.
However, if the original callback itself is passed to
:meth:`CyClockBase.unschedule`, it'll unschedule all instances of that
callback (provided ``all`` is True, the default, other just the first match is
removed).

Calling :meth:`CyClockBase.unschedule` on the original callback is highly
discouraged because it's significantly slower than when using the event.

Threading and Callback Order
-----------------------------

Beginning with 1.10.0, all the events scheduled for the same frame, e.g.
all the events scheduled in the same frame with a ``timeout`` of ``0``,
well be executed in the order they were scheduled.

Also, all the scheduling and canceling methods are fully thread safe and
can be safely used from external threads.

As a a consequence, calling :meth:`CyClockBase.unschedule` with the original
callback is now significantly slower and highly discouraged. Instead, the
returned events should be used to cancel. As a tradeoff, all the other methods
are now significantly faster than before.

Advanced Clock Details
-----------------------

The following section goes into the internal kivy clock details as well
as the various clock options. It is meant only for advanced users.

Fundamentally, the Kivy clock attempts to execute any scheduled callback
rhythmically as determined by the specified fps (frame per second, see
``maxfps`` in :mod:`~kivy.config`). That is, ideally, given e.g. a desired fps
of 30, the clock will execute the callbacks at intervals of 1 / 30 seconds, or
every 33.33 ms. All the callbacks in a frame are given the same timestamp,
i.e. the ``dt`` passed to the callback are all the same and it's the difference
in time between the start of this and the previous frame.

Because of inherent indeterminism, the frames do not actually occur exactly
at intervals of the fps and ``dt`` may be under or over the desired fps.
Also, once the timeout is "close enough" to the desired timeout, as determined
internally, Kivy will execute the callback in the current frame even when the
"actual time" has not elapsed the ``timeout`` amount.

Kivy offers now, since ``1.10.0``, multiple clocks with different behaviors.

Default Clock
^^^^^^^^^^^^^^

The default clock (``default``) behaves as described above. When a callback
with a timeout of zero or non-zero is scheduled, they are executed at the frame
that is near the timeout, which is a function of the fps. So a timeout of zero
would still result in a delay of one frame or about 1 / fps, typically a bit
less but sometimes more depending on the CPU usage of the other events
scheduled for that frame.

In a test using a fps of 30, a callback with a timeout of 0, 0.001, and 0.05,
resulted in a mean callback delay of 0.02487, 0.02488, and 0.05011 seconds,
respectively. When tested with a fps of 600 the delay for 0.05 was similar,
except the standard deviation was reduced resulting in overall better accuracy.

Interruptible Clock
^^^^^^^^^^^^^^^^^^^^

The default clock suffers from the quantization problem, as frames occur only
on intervals and any scheduled timeouts will not be able to occur during an
interval. For example, with the timeout of 0.05, while the mean was 0.05011,
its values ranged between 0.02548 - 0.07348 and a standard deviation of 0.002.
Also, there's the minimum timeout of about 0.02487.

The interruptible clock (``interrupt``) will execute timeouts even during a
frame. So a timeout of zero will execute as quickly as possible and similarly
a non-zero timeout will be executed even during the interval.

This clock, and all the clocks described after this have an option,
:attr:`ClockBaseInterruptBehavior.interupt_next_only`. When True, any of the
behavior new behavior will only apply to the callbacks with a timeout of
zero. Non-zero timeouts will behave like in the default clock. E.g. for this
clock when True, only zero timeouts will execute during the the interval.

In a test using a fps of 30, a callback with a timeout of 0, 0.001, and 0.05,
resulted in a mean callback delay of 0.00013, 0.00013, and 0.04120 seconds,
respectively when :attr:`ClockBaseInterruptBehavior.interupt_next_only` was
False. Also, compared to the default clock the standard deviation was reduced.
When :attr:`ClockBaseInterruptBehavior.interupt_next_only` was True, the values
were 0.00010, 0.02414, and 0.05034, respectively.

Free Clock
^^^^^^^^^^^

The interruptible clock may not be ideal for all cases because all the events
are executed during the intervals and events are not executed anymore
rhythmically as multiples of the fps. For example, there may not be any benefit
for the graphics to update in a sub-interval, so the additional accuracy
wastes CPU.

The Free clock (``free_all``) solves this by having ``Clock.xxx_free`` versions
of all the Clock scheduling methods. By free, we mean the event is free from
the fps because it's not fps limited. E.g.
:meth:`CyClockBaseFree.create_trigger_free` corresponds to
:meth:`CyClockBase.create_trigger`. Only when an event scheduled using the
``Clock.xxx_free`` methods is present will the clock interrupt and execute
the events during the interval. So, if no ``free`` event is present the clock
behaves like the ``default`` clock, otherwise it behaves like the ``interrupt``
clock.

In a test using a fps of 30, a callback with a timeout of 0s, 0.001s, and
0.05s, resulted in a mean callback delay of 0.00012s, 0.00017s, and 0.04121s
seconds, respectively when it was a free event and 0.02403s, 0.02405s, and
0.04829s, respectively when it wasn't.

Free Only Clock
^^^^^^^^^^^^^^^^^

The Free clock executes all events when a free event was scheduled. This
results in normal events also being execute in the middle of the interval
when a free event is scheduled. For example, above, when a free event was
absent, a normal event with a 0.001s timeout was delayed for 0.02405s. However,
if a free event happened to be also scheduled, the normal event was only
delayed 0.00014s, which may be undesirable.

The Free only clock (``free_only``) solves it by only executing free events
during the interval and normal events are always executed like with the
default clock. For example, in the presence of a free event, a normal event
with a timeout of 0.001s still had a delay of 0.02406. So this clock,
treats free and normal events independently, with normal events always being
fps limited, but never the free events.

Summary
^^^^^^^^

The kivy clock type to use can be set with the ``kivy_clock`` option the
:mod:`~kivy.config`. If ``KIVY_CLOCK`` is present in the environment it
overwrites the config selection. Its possible values are as follows:

* When ``kivy_clock`` is ``default``, the normal clock, :class:`ClockBase`,
  which limits callbacks to the maxfps quantization - is used.
* When ``kivy_clock`` is ``interrupt``, a interruptible clock,
  :class:`ClockBaseInterrupt`, which doesn't limit any callbacks to the
  maxfps - is used. Callbacks will be executed at any time.
* When ``kivy_clock`` is ``free_all``, a interruptible clock,
  :class:`ClockBaseFreeInterruptAll`, which doesn't limit any callbacks to the
  maxfps in the presence of free events, but in their absence it limits events
  to the fps quantization interval - is used.
* When ``kivy_clock`` is ``free_only``, a interruptible clock,
  :class:`ClockBaseFreeInterruptAll`, which treats free and normal events
  independently; normal events are fps limited while free events are not - is
  used.

'''

__all__ = (
    'Clock', 'ClockEvent', 'FreeClockEvent', 'CyClockBase', 'CyClockBaseFree',
    'ClockBaseBehavior', 'ClockBaseInterruptBehavior',
    'ClockBaseInterruptFreeBehavior', 'ClockBase', 'ClockBaseInterrupt',
    'ClockBaseFreeInterruptAll', 'ClockBaseFreeInterruptOnly', 'mainthread')

from sys import platform
from os import environ
from functools import wraps, partial
from kivy.context import register_context
from kivy.config import Config
from kivy.logger import Logger
from kivy.compat import clock as _default_time, PY2
import time
try:
    from kivy._clock import CyClockBase, ClockEvent, FreeClockEvent, \
        CyClockBaseFree
except ImportError:
    Logger.error(
        'Clock: Unable to import kivy._clock. Have you perhaps forgotten to '
        'compile kivy? Kivy contains Cython code which needs to be compiled. '
        'A missing kivy._clock often indicates the Cython code has not been '
        'compiled. Please follow the installation instructions and make sure '
        'to compile Kivy')
    raise

try:
    from multiprocessing import Event as MultiprocessingEvent
except ImportError:  # https://bugs.python.org/issue3770
    from threading import Event as MultiprocessingEvent
from threading import Event as ThreadingEvent

# some reading: http://gameprogrammingpatterns.com/game-loop.html


def _get_sleep_obj():
    pass


try:
    import ctypes
    if platform in ('win32', 'cygwin'):
        # Win32 Sleep function is only 10-millisecond resolution, so
        # instead use a waitable timer object, which has up to
        # 100-nanosecond resolution (hardware and implementation
        # dependent, of course).

        _kernel32 = ctypes.windll.kernel32

        def _get_sleep_obj():
            return _kernel32.CreateWaitableTimerA(None, True, None)

        def _usleep(microseconds, obj=None):
            delay = ctypes.c_longlong(int(-microseconds * 10))
            _kernel32.SetWaitableTimer(
                obj, ctypes.byref(delay), 0,
                ctypes.c_void_p(), ctypes.c_void_p(), False)
            _kernel32.WaitForSingleObject(obj, 0xffffffff)
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

        def _usleep(microseconds, obj=None):
            _libc_usleep(int(microseconds))

except (OSError, ImportError, AttributeError):
    # ImportError: ctypes is not available on python-for-android.
    # AttributeError: ctypes is now available on python-for-android, but
    #   "undefined symbol: clock_gettime". CF #3797
    # OSError: if the libc cannot be readed (like with buildbot: invalid ELF
    # header)

    def _usleep(microseconds, obj=None):
        time.sleep(microseconds / 1000000.)


class ClockBaseBehavior(object):
    '''The base of the kivy clock.
    '''

    _dt = 0.0001
    _last_fps_tick = None
    _start_tick = 0
    _fps = 0
    _rfps = 0
    _fps_counter = 0
    _rfps_counter = 0
    _frames = 0
    _frames_displayed = 0
    _events_duration = 0
    '''The measured time that it takes to process all the events etc, excepting
    any sleep or waiting time. It is the average and is updated every 5
    seconds.
    '''

    _duration_count = 0
    _sleep_time = 0
    _duration_ts0 = 0

    MIN_SLEEP = 0.005
    '''The minimum time to sleep. If the remaining time is less than this,
    the event loop will continuo
    '''
    SLEEP_UNDERSHOOT = MIN_SLEEP - 0.001

    def __init__(self, **kwargs):
        super(ClockBaseBehavior, self).__init__(**kwargs)
        self._duration_ts0 = self._start_tick = self._last_tick = self.time()
        self._max_fps = float(Config.getint('graphics', 'maxfps'))

    @property
    def frametime(self):
        '''Time spent between the last frame and the current frame
        (in seconds).

        .. versionadded:: 1.8.0
        '''
        return self._dt

    @property
    def frames(self):
        '''Number of internal frames (not necessarily drawed) from the start of
        the clock.

        .. versionadded:: 1.8.0
        '''
        return self._frames

    @property
    def frames_displayed(self):
        '''Number of displayed frames from the start of the clock.
        '''
        return self._frames_displayed

    def usleep(self, microseconds):
        '''Sleeps for the number of microseconds.
        '''
        pass

    def idle(self):
        '''(internal) waits here until the next frame.
        '''
        fps = self._max_fps
        if fps > 0:
            min_sleep = self.get_resolution()
            undershoot = 4 / 5. * min_sleep
            usleep = self.usleep
            ready = self._check_ready

            done, sleeptime = ready(fps, min_sleep, undershoot)
            while not done:
                usleep(1000000 * sleeptime)
                done, sleeptime = ready(fps, min_sleep, undershoot)

        current = self.time()
        self._dt = current - self._last_tick
        self._last_tick = current
        return current

    def _check_ready(self, fps, min_sleep, undershoot):
        sleeptime = 1 / fps - (self.time() - self._last_tick)
        return sleeptime - undershoot <= min_sleep, sleeptime - undershoot

    def tick(self):
        '''Advance the clock to the next step. Must be called every frame.
        The default clock has a tick() function called by the core Kivy
        framework.'''

        self._release_references()

        ts = self.time()
        current = self.idle()

        # tick the current time
        self._frames += 1
        self._fps_counter += 1

        # compute how long the event processing takes
        self._duration_count += 1
        self._sleep_time += current - ts
        t_tot = current - self._duration_ts0
        if t_tot >= 1.:
            self._events_duration = \
                (t_tot - self._sleep_time) / float(self._duration_count)
            self._duration_ts0 = current
            self._sleep_time = self._duration_count = 0

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

    time = staticmethod(partial(_default_time))


ClockBaseBehavior.time.__doc__ = \
    '''Proxy method for :func:`~kivy.compat.clock`. '''


class ClockBaseInterruptBehavior(ClockBaseBehavior):
    '''A kivy clock which can be interrupted during a frame to execute events.
    '''

    interupt_next_only = False
    _event = None
    _get_min_timeout_func = None

    def __init__(self, interupt_next_only=False, **kwargs):
        super(ClockBaseInterruptBehavior, self).__init__(**kwargs)
        self._event = MultiprocessingEvent() if PY2 else ThreadingEvent()
        self.interupt_next_only = interupt_next_only
        self._get_min_timeout_func = self.get_min_timeout

    def usleep(self, microseconds):
        self._event.clear()
        self._event.wait(microseconds / 1000000.)

    def on_schedule(self, event):
        fps = self._max_fps
        if not fps:
            return

        if not event.timeout or (
                not self.interupt_next_only and event.timeout <=
                1 / fps -  # remaining time
                (self.time() - self._last_tick) +  # elapsed time
                4 / 5. * self.get_resolution()):  # resolution fudge factor
            self._event.set()

    def idle(self):
        fps = self._max_fps
        event = self._event
        resolution = self.get_resolution()
        if fps > 0:
            done, sleeptime = self._check_ready(
                fps, resolution, 4 / 5. * resolution)
            if not done:
                event.wait(sleeptime)

        current = self.time()
        self._dt = current - self._last_tick
        self._last_tick = current
        event.clear()
        # anything scheduled from now on, if scheduled for the upcoming frame
        # will cause a timeout of the event on the next idle due to on_schedule
        # `self._last_tick = current` must happen before clear, otherwise the
        # on_schedule computation is wrong when exec between the clear and
        # the `self._last_tick = current` bytecode.
        return current

    def _check_ready(self, fps, min_sleep, undershoot):
        if self._event.is_set():
            return True, 0

        t = self._get_min_timeout_func()
        if not t:
            return True, 0

        if not self.interupt_next_only:
            curr_t = self.time()
            sleeptime = min(1 / fps - (curr_t - self._last_tick), t - curr_t)
        else:
            sleeptime = 1 / fps - (self.time() - self._last_tick)
        return sleeptime - undershoot <= min_sleep, sleeptime - undershoot


class ClockBaseInterruptFreeBehavior(ClockBaseInterruptBehavior):
    '''A base class for the clock that interrupts the sleep interval for
    free events.
    '''

    def __init__(self, **kwargs):
        super(ClockBaseInterruptFreeBehavior, self).__init__(**kwargs)
        self._get_min_timeout_func = self.get_min_free_timeout

    def on_schedule(self, event):
        if not event.free:  # only wake up for free events
            return
        # free events should use real time not frame time
        event._last_dt = self.time()
        return super(ClockBaseInterruptFreeBehavior,
                     self).on_schedule(event)


class ClockBase(ClockBaseBehavior, CyClockBase):
    '''The ``default`` kivy clock. See module for details.
    '''

    _sleep_obj = None

    def __init__(self, **kwargs):
        super(ClockBase, self).__init__(**kwargs)
        self._sleep_obj = _get_sleep_obj()

    def usleep(self, microseconds):
        _usleep(microseconds, self._sleep_obj)


class ClockBaseInterrupt(ClockBaseInterruptBehavior, CyClockBase):
    '''The ``interrupt`` kivy clock. See module for details.
    '''

    pass


class ClockBaseFreeInterruptAll(
        ClockBaseInterruptFreeBehavior, CyClockBaseFree):
    '''The ``free_all`` kivy clock. See module for details.
    '''

    pass


class ClockBaseFreeInterruptOnly(
        ClockBaseInterruptFreeBehavior, CyClockBaseFree):
    '''The ``free_only`` kivy clock. See module for details.
    '''

    def idle(self):
        fps = self._max_fps
        current = self.time()
        event = self._event
        if fps > 0:
            min_sleep = self.get_resolution()
            usleep = self.usleep
            undershoot = 4 / 5. * min_sleep
            min_t = self.get_min_free_timeout
            interupt_next_only = self.interupt_next_only

            sleeptime = 1 / fps - (current - self._last_tick)
            while sleeptime - undershoot > min_sleep:
                if event.is_set():
                    do_free = True
                else:
                    t = min_t()
                    if not t:
                        do_free = True
                    elif interupt_next_only:
                        do_free = False
                    else:
                        sleeptime = min(sleeptime, t - current)
                        do_free = sleeptime - undershoot <= min_sleep

                if do_free:
                    event.clear()
                    self._process_free_events(current)
                else:
                    event.wait(sleeptime - undershoot)
                current = self.time()
                sleeptime = 1 / fps - (current - self._last_tick)

        self._dt = current - self._last_tick
        self._last_tick = current
        event.clear()  # this needs to stay after _last_tick
        return current


def mainthread(func):
    '''Decorator that will schedule the call of the function for the next
    available frame in the mainthread. It can be useful when you use
    :class:`~kivy.network.urlrequest.UrlRequest` or when you do Thread
    programming: you cannot do any OpenGL-related work in a thread.

    Please note that this method will return directly and no result can be
    returned::

        @mainthread
        def callback(self, *args):
            print('The request succeeded!',
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


def triggered(timeout=0, interval=False):
    '''Decorator that will trigger the call of the function at the specified
    timeout, through the method :meth:`CyClockBase.create_trigger`. Subsequent
    calls to the decorated function (while the timeout is active) are ignored.

    It can be helpful when an expensive funcion (i.e. call to a server) can be
    triggered by different methods. Setting a proper timeout will delay the
    calling and only one of them wil be triggered.

        @triggered(timeout, interval=False)
        def callback(id):
            print('The callback has been called with id=%d' % id)

        >> callback(id=1)
        >> callback(id=2)
        The callback has been called with id=2

    The decorated callback can also be unscheduled using:

        >> callback.cancel()

    .. versionadded:: 1.10.1
    '''

    def wrapper_triggered(func):

        _args = []
        _kwargs = {}

        def cb_function(dt):
            func(*tuple(_args), **_kwargs)

        cb_trigger = Clock.create_trigger(
            cb_function,
            timeout=timeout,
            interval=interval)

        @wraps(func)
        def trigger_function(*args, **kwargs):
            _args[:] = []
            _args.extend(list(args))
            _kwargs.clear()
            _kwargs.update(kwargs)
            cb_trigger()

        def trigger_cancel():
            cb_trigger.cancel()

        setattr(trigger_function, 'cancel', trigger_cancel)

        return trigger_function

    return wrapper_triggered


if 'KIVY_DOC_INCLUDE' in environ:
    #: Instance of :class:`ClockBaseBehavior`.
    Clock = None
else:
    _classes = {'default': ClockBase, 'interrupt': ClockBaseInterrupt,
                'free_all': ClockBaseFreeInterruptAll,
                'free_only': ClockBaseFreeInterruptOnly}
    _clk = environ.get('KIVY_CLOCK', Config.get('kivy', 'kivy_clock'))
    if _clk not in _classes:
        raise Exception(
            '{} is not a valid kivy clock. Valid clocks are {}'.format(
                _clk, sorted(_classes.keys())))

    Clock = register_context('Clock', _classes[_clk])
    '''The kivy Clock instance. See module documentation for details.
    '''
