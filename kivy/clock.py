'''
Clock object
============

The :class:`Clock` object allows you to schedule a function call in the
future; once or on interval::

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
`functools.partial
<http://docs.python.org/library/functools.html#functools.partial>`_ python
module::

    from functools import partial

    def my_callback(value, key, *largs):
        pass

    Clock.schedule_interval(partial(my_callback, 'my value', 'my key'), 0.5)

Conversely, if you want to schedule a function that doesn't accept the dt
argument, you can use `lambda
<http://docs.python.org/2/reference/expressions.html#lambda>`_ expression
to write a short function that does accept dt.  For Example::

    def no_args_func():
        print("I accept no arguments, so don't schedule me in the clock")

    Clock.schedule_once(lambda dt: no_args_func(), 0.5)

.. note::

    You cannot unschedule an anonymous function unless you keep a reference to
    it.  It's better to add \*args to your function definition so that it can be
    called with or without the clock.

.. important::

    The callback is weak-referenced: you are responsible to keep a reference to
    your original object/callback. If you don't keep a reference, the Clock will
    never execute your callback. For example::

        class Foo(object):
            def start(self):
                Clock.schedule_interval(self.callback)

            def callback(self, dt):
                print('In callback')

        # a Foo object is created, the method start is called,
        # and the instance of foo is deleted
        # Because nobody keep a reference to the instance returned from Foo(),
        # the object will be collected by Python Garbage Collector. And you're
        # callback will be never called.
        Foo().start()

        # So you must do:
        foo = Foo()
        foo.start()

        # and keep the instance of foo, until you don't need it anymore!

.. _schedule-before-frame:

Schedule before frame
---------------------

.. versionadded:: 1.0.5

Sometimes you need to schedule a callback BEFORE the next frame. Starting
from 1.0.5, you can use a timeout of -1::

    Clock.schedule_once(my_callback, 0) # call after the next frame
    Clock.schedule_once(my_callback, -1) # call before the next frame

The Clock will execute all the callbacks with a timeout of -1 before
the next frame, even if you add a new callback with -1 from a running callback.
However, :class:`Clock` has an iteration limit for these callbacks, it defaults
to 10.

If you schedule a callback that schedules a callback that schedules a .. etc
more than 10 times, it will leave the loop and send a warning to the console,
then continue after the next frame. This is implemented to prevent bugs from
hanging or crashing the application.

If you need to increase the limit, set the :data:`max_iteration` property::

    from kivy.clock import Clock
    Clock.max_iteration = 20

.. _triggered-events:

Triggered Events
----------------

.. versionadded:: 1.0.5

A triggered event is a way to defer a callback exactly like schedule_once(),
but with some added convenience. The callback will only be scheduled once per
frame, even if you call the trigger twice (or more). This is not the case
with :func:`Clock.schedule_once`::

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
the triggered event than using :func:`Clock.schedule_once` in a function::

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

    :func:`Clock.create_trigger` also has a timeout parameter that behaves
    exactly like :func:`Clock.schedule_once`.

'''

__all__ = ('Clock', 'ClockBase', 'ClockEvent', 'mainthread')

from sys import platform
from os import environ
from kivy.context import register_context
from kivy.weakmethod import WeakMethod
from kivy.config import Config
from kivy.logger import Logger
import time

try:
    import ctypes
    if platform in ('win32', 'cygwin'):
        # Win32 Sleep function is only 10-millisecond resolution, so instead use
        # a waitable timer object, which has up to 100-nanosecond resolution
        # (hardware and implementation dependent, of course).

        _kernel32 = ctypes.windll.kernel32

        class _ClockBase(object):
            def __init__(self):
                self._timer = _kernel32.CreateWaitableTimerA(None, True, None)

            def usleep(self, microseconds):
                delay = ctypes.c_longlong(int(-microseconds * 10))
                _kernel32.SetWaitableTimer(self._timer, ctypes.byref(delay),
                    0, ctypes.c_void_p(), ctypes.c_void_p(), False)
                _kernel32.WaitForSingleObject(self._timer, 0xffffffff)

        _default_time = time.clock
    else:
        if platform == 'darwin':
            _libc = ctypes.CDLL('libc.dylib')
        else:
            _libc = ctypes.CDLL('libc.so')
        _libc.usleep.argtypes = [ctypes.c_ulong]
        _libc_usleep = _libc.usleep

        class _ClockBase(object):
            def usleep(self, microseconds):
                _libc_usleep(int(microseconds))

        _default_time = time.time

except (OSError, ImportError):
    # ImportError: ctypes is not available on python-for-android.
    # OSError: if the libc cannot be readed (like with buildbot: invalid ELF
    # header)

    _default_time = time.time
    _default_sleep = time.sleep

    class _ClockBase(object):
        def usleep(self, microseconds):
            _default_sleep(microseconds / 1000000.)


def _hash(cb):
    try:
        return cb.__name__
    except:
        # if a callback with partial is used... use func
        try:
            return cb.func.__name__
        except:
            # nothing work, use default hash.
            return 'default'


class ClockEvent(object):

    def __init__(self, clock, loop, callback, timeout, starttime, cid):
        self.clock = clock
        self.cid = cid
        self.loop = loop
        self.weak_callback = None
        self.callback = callback
        self.timeout = timeout
        self._is_triggered = False
        self._last_dt = starttime
        self._dt = 0.

    def __call__(self, *largs):
        # if the event is not yet triggered, do it !
        if self._is_triggered is False:
            self._is_triggered = True
            events = self.clock._events
            cid = self.cid
            if cid not in events:
                events[cid] = []
            events[cid].append(self)
            # update starttime
            self._last_dt = self.clock._last_tick
            return True

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
        if self._is_triggered:
            events = self.clock._events
            cid = self.cid
            if cid in events and self in events[cid]:
                events[cid].remove(self)
        self._is_triggered = False

    def do(self, dt):
        callback = self.get_callback()
        if callback is None:
            return False
        callback(dt)

    def release(self):
        self.weak_callback = WeakMethod(self.callback)
        self.callback = None

    def tick(self, curtime):
        # timeout happened ? (check also if we would miss from 5ms)
        # this 5ms increase the accuracy if the timing of animation for example.
        if curtime - self._last_dt < self.timeout - 0.005:
            return True

        # calculate current timediff for this event
        self._dt = curtime - self._last_dt
        self._last_dt = curtime

        # get the callback
        callback = self.get_callback()
        if callback is None:
            self._is_triggered = False
            return False

        # if it's a trigger, allow to retrigger inside the callback
        if not self.loop:
            self._is_triggered = False

        # call the callback
        ret = callback(self._dt)

        # if it's a once event, don't care about the result
        # just remove the event
        if not self.loop:
            return False

        # if the user returns False explicitly,
        # remove the event
        if ret is False:
            return False

        return True

    def __repr__(self):
        return '<ClockEvent callback=%r>' % self.get_callback()


class ClockBase(_ClockBase):
    '''A clock object with event support
    '''
    __slots__ = ('_dt', '_last_fps_tick', '_last_tick', '_fps', '_rfps',
                 '_start_tick', '_fps_counter', '_rfps_counter', '_events',
                 '_max_fps', 'max_iteration')

    MIN_SLEEP = 0.005
    SLEEP_UNDERSHOOT = MIN_SLEEP - 0.001

    def __init__(self):
        super(ClockBase, self).__init__()
        self._dt = 0.0001
        self._start_tick = self._last_tick = _default_time()
        self._fps = 0
        self._rfps = 0
        self._fps_counter = 0
        self._rfps_counter = 0
        self._last_fps_tick = None
        self._events = {}
        self._max_fps = float(Config.getint('graphics', 'maxfps'))

        #: .. versionadded:: 1.0.5
        #:     When a schedule_once is used with -1, you can add a limit on how
        #:     iteration will be allowed. That is here to prevent too much
        #:     relayout.
        self.max_iteration = 10

    @property
    def frametime(self):
        '''Time spent between last frame and current frame (in seconds)
        '''
        return self._dt

    def tick(self):
        '''Advance clock to the next step. Must be called every frame.
        The default clock have the tick() function called by Kivy'''

        self._release_references()
        if self._fps_counter % 100 == 0:
            self._remove_empty()

        # do we need to sleep ?
        if self._max_fps > 0:
            min_sleep = self.MIN_SLEEP
            sleep_undershoot = self.SLEEP_UNDERSHOOT
            fps = self._max_fps
            usleep = self.usleep

            sleeptime = 1 / fps - (_default_time() - self._last_tick)
            while sleeptime - sleep_undershoot > min_sleep:
                usleep(1000000 * (sleeptime - sleep_undershoot))
                sleeptime = 1 / fps - (_default_time() - self._last_tick)

        # tick the current time
        current = _default_time()
        self._dt = current - self._last_tick
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
        '''Tick the drawing counter
        '''
        self._process_events_before_frame()
        self._rfps_counter += 1

    def get_fps(self):
        '''Get the current average FPS calculated by the clock
        '''
        return self._fps

    def get_rfps(self):
        '''Get the current "real" FPS calculated by the clock.
        This counter reflects the real framerate displayed on the screen.

        In contrast to get_fps(), this function returns a counter of the number
        of frames, not an average of frames per second
        '''
        return self._rfps

    def get_time(self):
        '''Get the last tick made by the clock'''
        return self._last_tick

    def get_boottime(self):
        '''Get time in seconds from the application start'''
        return self._last_tick - self._start_tick

    def create_trigger(self, callback, timeout=0):
        '''Create a Trigger event. Check module documentation for more
        information.

        .. versionadded:: 1.0.5
        '''
        cid = _hash(callback)
        ev = ClockEvent(self, False, callback, timeout, 0, cid)
        ev.release()
        return ev

    def schedule_once(self, callback, timeout=0):
        '''Schedule an event in <timeout> seconds.

        .. versionchanged:: 1.0.5
            If the timeout is -1, the callback will be called before the next
            frame (at :func:`tick_draw`).

        '''
        if not callable(callback):
            raise ValueError('callback must be a callable, got %s' % callback)
        cid = _hash(callback)
        event = ClockEvent(self, False, callback, timeout, self._last_tick, cid)
        events = self._events
        if not cid in events:
            events[cid] = []
        events[cid].append(event)
        return event

    def schedule_interval(self, callback, timeout):
        '''Schedule an event to be called every <timeout> seconds'''
        if not callable(callback):
            raise ValueError('callback must be a callable, got %s' % callback)
        cid = _hash(callback)
        event = ClockEvent(self, True, callback, timeout, self._last_tick, cid)
        events = self._events
        if not cid in events:
            events[cid] = []
        events[cid].append(event)
        return event

    def unschedule(self, callback):
        '''Remove a previously scheduled event.
        '''
        events = self._events
        if isinstance(callback, ClockEvent):
            # already done, nothing to schedule
            if callback.is_done:
                return
            cid = callback.cid
            if cid in events:
                for event in events[cid][:]:
                    if event is callback:
                        events[cid].remove(event)
        else:
            cid = _hash(callback)
            if cid in events:
                for event in events[cid][:]:
                    if event.get_callback() == callback:
                        events[cid].remove(event)

    def _release_references(self):
        # call that function to release all the direct reference to any callback
        # and replace it with a weakref
        events = self._events
        for cid in list(events.keys())[:]:
            [x.release() for x in events[cid] if x.callback is not None]

    def _remove_empty(self):
        # remove empty entry in the event list
        events = self._events
        for cid in list(events.keys())[:]:
            if not events[cid]:
                del events[cid]

    def _process_events(self):
        events = self._events
        for cid in list(events.keys())[:]:
            for event in events[cid][:]:
                if event.tick(self._last_tick) is False:
                    # event may be already removed by the callback
                    if event in events[cid]:
                        events[cid].remove(event)

    def _process_events_before_frame(self):
        found = True
        count = self.max_iteration
        events = self._events
        while found:
            count -= 1
            if count == -1:
                Logger.critical('Clock: Warning, too much iteration done before'
                                ' the next frame. Check your code, or increase'
                                ' the Clock.max_iteration attribute')
                break

            # search event that have timeout = -1
            found = False
            for cid in list(events.keys())[:]:
                for event in events[cid][:]:
                    if event.timeout != -1:
                        continue
                    found = True
                    if event.tick(self._last_tick) is False:
                        # event may be already removed by the callback
                        if event in events[cid]:
                            events[cid].remove(event)


def mainthread(func):
    '''Decorator that will schedule the call of the function in the mainthread.
    It can be useful when you use :class:`~kivy.network.urlrequest.UrlRequest`,
    or when you do Thread programming: you cannot do any OpenGL-related work in
    a thread.

    Please note that this method will return directly, and no result can be
    fetched::

        @mainthread
        def callback(self, *args):
            print('The request succedded!'
                  'This callback is call in the main thread')

        self.req = UrlRequest(url='http://...', on_success=callback)

    .. versionadded:: 1.8.0
    '''
    def delayed_func(*args, **kwargs):
        def callback_func(dt):
            func(*args, **kwargs)
        Clock.schedule_once(callback_func, 0)
    return delayed_func

if 'KIVY_DOC_INCLUDE' in environ:
    #: Instance of the ClockBase, available for everybody
    Clock = None
else:
    Clock = register_context('Clock', ClockBase)

