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

        [kivy]
            retain_time = 100
            retain_distance = 50

    Distance parameter is in 0-1000, and time is in millisecond.
    '''

    def __init__(self):
        self.timeout = Config.getint('kivy', 'retain_time') / 1000.0
        self.distance = Config.getint('kivy', 'retain_distance') / 1000.0
        self._available = []
        self._links = {}

    def process(self, events):
        # check if module is disabled
        if self.timeout == 0:
            return events

        d = time.time()
        for type, touch in events[:]:
            if type == 'up':
                events.remove((type, touch))
                if touch.uid in self._links:
                    selection = self._links[touch.uid]
                    selection.userdata['__retain_time'] = d
                    self._available.append(selection)
                    del self._links[touch.uid]
                else:
                    touch.userdata['__retain_time'] = d
                    self._available.append(touch)
            elif type == 'move':
                if touch.uid in self._links:
                    selection = self._links[touch.uid]
                    selection.x = touch.x
                    selection.y = touch.y
                    selection.sx = touch.sx
                    selection.sy = touch.sy
                    events.remove((type, touch))
                    events.append((type, selection))
                else:
                    pass
            elif type == 'down':
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
                events.remove((type, touch))

        for touch in self._available[:]:
            t = touch.userdata['__retain_time']
            if d - t > self.timeout:
                self._available.remove(touch)
                events.append(('up', touch))

        return events
