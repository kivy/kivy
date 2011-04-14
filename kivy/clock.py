'''
Clock object
============

The :class:`Clock` object allow you to schedule a function call. The scheduling
can be repetitive or just once.

You can add new event like this::

    def my_callback(dt):
        pass

    # call my_callback every 0.5 seconds
    Clock.schedule_interval(my_callback, 0.5)

    # call my_callback in 5 seconds
    Clock.schedule_once(my_callback, 5)

    # call my_callback as soon as possible (usually next frame.)
    Clock.schedule_once(my_callback)

.. note::

    If the callback return False, the schedule will be removed.

Schedule before frame
---------------------

.. versionadded:: 1.0.5

Sometime, you want to schedule a callback to be called BEFORE the next frame.
Starting from 1.0.5, you can use a timeout of -1 for doing that::

    Clock.schedule_once(my_callback, 0) # call after the next frame
    Clock.schedule_once(my_callback, -1) # call before the next frame

The :class:`Clock` will execute all the callback with a timeout of -1 before
the next frame. Even if you add new callback with -1. Clock have a limit of
iteration for thoses callback, defaulted to 10.

If you schedule a layout that reschedule a layout that reschedule a layout...
more than 10 times, it will leave his loop, send a warning on the console, and
will continue after next frame. This is implemented to prevent infinite layout
in case of a bug.

If you want to increase that limit, you can do::

    from kivy.clock import Clock
    Clock.max_iteration = 20

Triggered Events
----------------

.. versionadded:: 1.0.5

A triggered event is a Event than can be started when it will be triggered.
Before triggered events, you might done this approach in your code::

    def callback(self):
        print 'my callback is called'

    def trigger_callback(self, *largs):
        Clock.unschedule(self.callback)
        Clock.schedule_once(self.callback)

With triggered event, you don't need anymore of trigger_callback. You can do::

    trigger_callback = Clock.create_trigger(self.callback)

And same as the previous approach, as soon as you'll call the
`trigger_callback()`, it will correctly schedule the call of the callback in the
next frame.

.. note::

    :func:`Clock.create_trigger` use internally schedule_once. You can use the
    same parameters.
'''

__all__ = ('Clock', 'ClockBase', 'ClockEvent')

from os import environ
from time import time, sleep
from kivy.weakmethod import WeakMethod
from kivy.config import Config
from kivy.logger import Logger


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
            if not cid in events:
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

    def do(self, dt):
        callback = self.get_callback()
        if callback is None:
            return False
        callback(dt)

    def release(self):
        self.weak_callback = WeakMethod(self.callback)
        self.callback = None

    def tick(self, curtime):
        # timeout happen ?
        if curtime - self._last_dt < self.timeout:
            return True

        # calculate current timediff for this event
        self._dt = curtime - self._last_dt
        self._last_dt = curtime

        # get the callback
        callback = self.get_callback()
        if callback is None:
            self._is_triggered = False
            return False

        # call the callback
        ret = callback(self._dt)

        # if it's a once event, don't care about the result
        # just remove the event
        if not self.loop:
            self._is_triggered = False
            return False

        # if the user returns False explicitly,
        # remove the event
        if ret is False:
            self._is_triggered = False
            return False

        return True

    def __repr__(self):
        return '<ClockEvent callback=%r>' % self.get_callback()


class ClockBase(object):
    '''A clock object, that support events
    '''
    __slots__ = ('_dt', '_last_fps_tick', '_last_tick', '_fps', '_rfps',
                 '_start_tick', '_fps_counter', '_rfps_counter', '_events',
                 '_max_fps', 'max_iteration')

    def __init__(self):
        self._dt = 0.0001
        self._start_tick = self._last_tick = time()
        self._fps = 0
        self._rfps = 0
        self._fps_counter = 0
        self._rfps_counter = 0
        self._last_fps_tick = None
        self._events = {}
        self._max_fps = float(Config.getint('graphics', 'maxfps'))

        #: .. versionadded:: 1.0.5
        #: When a schedule_once is used with -1, you can add a limit on how much
        #: iteration will be allowed. That is here to prevent too much relayout.
        # XXX Adjust this value.
        self.max_iteration = 10

    @property
    def frametime(self):
        '''Time spended between last frame and current frame (in seconds)
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
            fps = self._max_fps
            s = 1 / fps - (time() - self._last_tick)
            if s > 0:
                sleep(s)

        # tick the current time
        current = time()
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
        '''Get the current FPS calculated by the clock
        '''
        return self._fps

    def get_rfps(self):
        '''Get the current "real" FPS calculated by the clock.
        This counter reflect the real frame displayed on the screen.

        In contrary to get_fps(), this function return a counter of the number
        of frame, not a average of frame per seconds
        '''
        return self._rfps

    def get_time(self):
        '''Get the last tick made by the clock'''
        return self._last_tick

    def get_boottime(self):
        '''Get time in seconds from the application start'''
        return self._last_tick - self._start_tick

    def create_trigger(self, callback, timeout=0):
        '''Create a Trigger event. Check module information for more
        information.

        .. versionadded:: 1.0.5
        '''
        cid = _hash(callback)
        return ClockEvent(self, False, callback, timeout, 0, cid)

    def schedule_once(self, callback, timeout=0):
        '''Schedule an event in <timeout> seconds.

        .. note::
            .. versionadded:: 1.0.5
            If the timeout is -1, the callback will be called before the next
            frame (at :func:`tick_draw`).
        '''
        cid = _hash(callback)
        event = ClockEvent(self, False, callback, timeout, self._last_tick, cid)
        events = self._events
        if not cid in events:
            events[cid] = []
        events[cid].append(event)
        return event

    def schedule_interval(self, callback, timeout):
        '''Schedule a event to be call every <timeout> seconds'''
        cid = _hash(callback)
        event = ClockEvent(self, True, callback, timeout, self._last_tick, cid)
        events = self._events
        if not cid in events:
            events[cid] = []
        events[cid].append(event)
        return event

    def unschedule(self, callback):
        '''Remove a previous schedule event.
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
                    if event.get_callback() is callback:
                        events[cid].remove(event)

    def _release_references(self):
        # call that function to release all the direct reference to any callback
        # and replace it with a weakref
        events = self._events
        for cid in events:
            [x.release() for x in events[cid] if x.callback is not None]

    def _remove_empty(self):
        # remove empty entry in the event list
        events = self._events
        for cid in events.keys()[:]:
            if not events[cid]:
                del events[cid]

    def _process_events(self):
        events = self._events
        for cid in events.keys()[:]:
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
            if count < 0:
                Logger.critical('Clock: Warning, too much iteration done before'
                                ' the next frame. Check your code, or increase '
                                'the Clock.max_iteration attribute')

            # search event that have timeout = -1
            found = False
            for cid in events.keys()[:]:
                for event in events[cid][:]:
                    if event.timeout != -1:
                        continue
                    found = True
                    if event.tick(self._last_tick) is False:
                        # event may be already removed by the callback
                        if event in events[cid]:
                            events[cid].remove(event)

        if count != self.max_iteration - 1:
            i = self.max_iteration - count + 1
            Logger.trace('Clock: we done %d iteration before the frame' % i)


if 'KIVY_DOC_INCLUDE' in environ:
    #: Instance of the ClockBase, available for everybody
    Clock = None
else:
    Clock = ClockBase()

