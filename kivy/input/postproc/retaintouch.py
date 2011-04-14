'''
Retain Touch
============

Reuse touch to counter finger lost behavior
'''

__all__ = ('InputPostprocRetainTouch', )

from kivy.config import Config
from kivy.vector import Vector
import time


class InputPostprocRetainTouch(object):
    '''
    InputPostprocRetainTouch is a post-processor to delay the 'up' event of a
    touch, to reuse it under certains conditions. This module is designed to
    prevent finger lost on some hardware/setup.

    Retain touch can be configured in the Kivy config file ::

        [postproc]
            retain_time = 100
            retain_distance = 50

    Distance parameter is in 0-1000, and time is in millisecond.
    '''

    def __init__(self):
        self.timeout = Config.getint('postproc', 'retain_time') / 1000.0
        self.distance = Config.getint('postproc', 'retain_distance') / 1000.0
        self._available = []
        self._links = {}

    def process(self, events):
        # check if module is disabled
        if self.timeout == 0:
            return events

        d = time.time()
        for etype, touch in events[:]:
            if not touch.is_touch:
                continue
            if etype == 'end':
                events.remove((etype, touch))
                if touch.uid in self._links:
                    selection = self._links[touch.uid]
                    selection.ud.__pp_retain_time__ = d
                    self._available.append(selection)
                    del self._links[touch.uid]
                else:
                    touch.ud.__pp_retain_time__ = d
                    self._available.append(touch)
            elif etype == 'update':
                if touch.uid in self._links:
                    selection = self._links[touch.uid]
                    selection.x = touch.x
                    selection.y = touch.y
                    selection.sx = touch.sx
                    selection.sy = touch.sy
                    events.remove((etype, touch))
                    events.append((etype, selection))
                else:
                    pass
            elif etype == 'begin':
                # new touch, found the nearest one
                selection = None
                selection_distance = 99999
                for touch2 in self._available:
                    touch_distance = Vector(touch2.spos).distance(touch.spos)
                    if touch_distance > self.distance:
                        continue
                    if touch2.__class__ != touch.__class__:
                        continue
                    if touch_distance < selection_distance:
                        # eligible for continuation
                        selection_distance = touch_distance
                        selection = touch2
                if selection is None:
                    continue

                self._links[touch.uid] = selection
                self._available.remove(selection)
                events.remove((etype, touch))

        for touch in self._available[:]:
            t = touch.ud.__pp_retain_time__
            if d - t > self.timeout:
                self._available.remove(touch)
                events.append(('end', touch))

        return events
