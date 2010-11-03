'''
Double Tap: search touch for a double tap
'''

__all__ = ('InputPostprocDoubleTap', )

from kivy.config import Config
from kivy.vector import Vector
from kivy.clock import Clock

class InputPostprocDoubleTap(object):
    '''
    InputPostProcDoubleTap is a post-processor to check if a touch is a double tap or not.
    Double tap can be configured in the Kivy config file ::

        [kivy]
            double_tap_time = 250
            double_tap_distance = 20

    Distance parameter is in 0-1000, and time is in millisecond.
    '''
    def __init__(self):
        self.double_tap_distance = Config.getint('kivy', 'double_tap_distance') / 1000.0
        self.double_tap_time = Config.getint('kivy', 'double_tap_time') / 1000.0
        self.touches = {}

    def find_double_tap(self, ref):
        '''Find a double tap touch within self.touches.
        The touch must be not a previous double tap, and the distance must be
        ok'''
        for touchid in self.touches:
            if ref.uid == touchid:
                continue
            type, touch = self.touches[touchid]
            if type != 'up':
                continue
            if touch.is_double_tap:
                continue
            distance = Vector.distance(
                Vector(ref.sx, ref.sy),
                Vector(touch.osxpos, touch.osypos))
            if distance > self.double_tap_distance:
                continue
            touch.double_tap_distance = distance
            return touch
        return None


    def process(self, events):
        # first, check if a touch down have a double tap
        for type, touch in events:
            if type == 'down':
                touch_double_tap = self.find_double_tap(touch)
                if touch_double_tap:
                    touch.is_double_tap = True
                    touch.double_tap_time = touch.time_start - touch_double_tap.time_start
                    touch.double_tap_distance = touch_double_tap.double_tap_distance

            # add the touch internaly
            self.touches[touch.uid] = (type, touch)

        # second, check if up-touch is timeout for double tap
        time_current = Clock.get_time()
        for touchid in self.touches.keys()[:]:
            type, touch = self.touches[touchid]
            if type != 'up':
                continue
            if time_current - touch.time_start < self.double_tap_time:
                continue
            del self.touches[touchid]

        return events
