'''
Double Tap
==========

Search touch for a double tap
'''

__all__ = ('InputPostprocDoubleTap', )

from kivy.config import Config
from kivy.vector import Vector
from kivy.clock import Clock


class InputPostprocDoubleTap(object):
    '''
    InputPostProcDoubleTap is a post-processor to check if
    a touch is a double tap or not.
    Double tap can be configured in the Kivy config file ::

        [postproc]
            double_tap_time = 250
            double_tap_distance = 20

    Distance parameter is in 0-1000, and time is in millisecond.
    '''

    def __init__(self):
        dist = Config.getint('postproc', 'double_tap_distance')
        self.double_tap_distance = dist / 1000.0
        time = Config.getint('postproc', 'double_tap_time')
        self.double_tap_time = time / 1000.0
        self.touches = {}

    def find_double_tap(self, ref):
        '''Find a double tap touch within self.touches.
        The touch must be not a previous double tap, and the distance must be
        ok'''
        for touchid in self.touches:
            if ref.uid == touchid:
                continue
            etype, touch = self.touches[touchid]
            if etype != 'end':
                continue
            if touch.is_double_tap:
                continue
            distance = Vector.distance(
                Vector(ref.sx, ref.sy),
                Vector(touch.osx, touch.osy))
            if distance > self.double_tap_distance:
                continue
            touch.double_tap_distance = distance
            return touch
        return None

    def process(self, events):
        # first, check if a touch down have a double tap
        for etype, touch in events:
            if not touch.is_touch:
                continue
            if etype == 'begin':
                double_tap = self.find_double_tap(touch)
                if double_tap:
                    touch.is_double_tap = True
                    time = touch.time_start - double_tap.time_start
                    touch.double_tap_time = time
                    distance = double_tap.double_tap_distance
                    touch.double_tap_distance = distance

            # add the touch internaly
            self.touches[touch.uid] = (etype, touch)

        # second, check if up-touch is timeout for double tap
        time_current = Clock.get_time()
        for touchid in self.touches.keys()[:]:
            etype, touch = self.touches[touchid]
            if etype != 'end':
                continue
            if time_current - touch.time_start < self.double_tap_time:
                continue
            del self.touches[touchid]

        return events
