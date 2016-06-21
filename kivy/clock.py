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

__all__ = ('Clock', 'CyClockBase', 'ClockBase', 'ClockEvent', 'mainthread')

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
from kivy._clock import CyClockBase, ClockEvent


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


class ClockBase(CyClockBase):
    '''A clock object with event support.
    '''

    _dt = 0.0001
    _last_fps_tick = None
    _start_tick = 0
    _last_tick = 0
    _fps = 0
    _rfps = 0
    _fps_counter = 0
    _rfps_counter = 0
    _frames = 0
    _frames_displayed = 0
    _max_fps = 30.
    _sleep_obj = None

    MIN_SLEEP = 0.005
    SLEEP_UNDERSHOOT = MIN_SLEEP - 0.001

    def __init__(self):
        super(ClockBase, self).__init__()
        self._sleep_obj = _get_sleep_obj()
        self._start_tick = self._last_tick = self.time()
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

    def usleep(self, microseconds):
        '''Sleeps for the number of microseconds.
        '''
        _usleep(microseconds, self._sleep_obj)

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
