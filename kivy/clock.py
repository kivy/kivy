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
'''

__all__ = ('Clock', 'ClockBase')

from os import environ
from time import time, sleep
from kivy.weakmethod import WeakMethod
from kivy.config import Config


class _Event(object):

    def __init__(self, loop, callback, timeout, starttime):
        self.loop = loop
        self.callback = WeakMethod(callback)
        self.timeout = timeout
        self._last_dt = starttime
        self._dt = 0.

    def do(self, dt):
        if self.callback.is_dead():
            return False
        self.callback()(dt)

    def tick(self, curtime):
        # timeout happen ?
        if curtime - self._last_dt < self.timeout:
            return True

        # calculate current timediff for this event
        self._dt = curtime - self._last_dt
        self._last_dt = curtime

        # call the callback
        if self.callback.is_dead():
            return False
        ret = self.callback()(self._dt)

        # if it's a once event, don't care about the result
        # just remove the event
        if not self.loop:
            return False

        # if the user returns False explicitly,
        # remove the event
        if ret is False:
            return False

        return True


class ClockBase(object):
    '''A clock object, that support events
    '''
    __slots__ = ('_dt', '_last_fps_tick', '_last_tick', '_fps', '_rfps',
            '_fps_counter', '_rfps_counter', '_events', '_max_fps')

    def __init__(self):
        self._dt = 0.0001
        self._last_tick = time()
        self._fps = 0
        self._rfps = 0
        self._fps_counter = 0
        self._rfps_counter = 0
        self._last_fps_tick = None
        self._events = []
        self._max_fps = float(Config.getint('graphics', 'fps'))

    @property
    def frametime(self):
        '''Time spended between last frame and current frame (in seconds)
        '''
        return self._dt

    def tick(self):
        '''Advance clock to the next step. Must be called every frame.
        The default clock have the tick() function called by Kivy'''

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

    def schedule_once(self, callback, timeout=0):
        '''Schedule an event in <timeout> seconds'''
        event = _Event(False, callback, timeout, self._last_tick)
        self._events.append(event)
        return event

    def schedule_interval(self, callback, timeout):
        '''Schedule a event to be call every <timeout> seconds'''
        event = _Event(True, callback, timeout, self._last_tick)
        self._events.append(event)
        return event

    def unschedule(self, callback):
        '''Remove a previous schedule event'''
        self._events = [x for x in self._events if x.callback() != callback]

    def _process_events(self):
        for event in self._events[:]:
            if event.tick(self._last_tick) is False:
                # event may be already removed by the callback
                if event in self._events:
                    self._events.remove(event)


if 'KIVY_DOC_INCLUDE' in environ:
    #: Instance of the ClockBase, available for everybody
    Clock = None
else:
    Clock = ClockBase()

