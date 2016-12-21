'''
Triple Tap
==========

.. versionadded:: 1.7.0

Search touch for a triple tap
'''

__all__ = ('InputPostprocTripleTap', )

from time import time
from kivy.config import Config
from kivy.vector import Vector


class InputPostprocTripleTap(object):
    '''
    InputPostProcTripleTap is a post-processor to check if
    a touch is a triple tap or not.
    Triple tap can be configured in the Kivy config file::

        [postproc]
        triple_tap_time = 250
        triple_tap_distance = 20

    The distance parameter is in the range 0-1000 and time is in milliseconds.
    '''

    def __init__(self):
        dist = Config.getint('postproc', 'triple_tap_distance')
        self.triple_tap_distance = dist / 1000.0
        time = Config.getint('postproc', 'triple_tap_time')
        self.triple_tap_time = time / 1000.0
        self.touches = {}

    def find_triple_tap(self, ref):
        '''Find a triple tap touch within *self.touches*.
        The touch must be not be a previous triple tap and the distance
        must be be within the bounds specified. Additionally, the touch profile
        must be the same kind of touch.
        '''
        ref_button = None
        if 'button' in ref.profile:
            ref_button = ref.button

        for touchid in self.touches:
            if ref.uid == touchid:
                continue
            etype, touch = self.touches[touchid]
            if not touch.is_double_tap:
                continue
            if etype != 'end':
                continue
            if touch.is_triple_tap:
                continue
            distance = Vector.distance(
                Vector(ref.sx, ref.sy),
                Vector(touch.osx, touch.osy))
            if distance > self.triple_tap_distance:
                continue
            if touch.is_mouse_scrolling or ref.is_mouse_scrolling:
                continue
            touch_button = None
            if 'button' in touch.profile:
                touch_button = touch.button
            if touch_button != ref_button:
                continue
            touch.triple_tap_distance = distance
            return touch
        return None

    def process(self, events):
        if self.triple_tap_distance == 0 or self.triple_tap_time == 0:
            return events
        # first, check if a touch down have a triple tap
        for etype, touch in events:
            if not touch.is_touch:
                continue
            if etype == 'begin':
                triple_tap = self.find_triple_tap(touch)
                if triple_tap:
                    touch.is_double_tap = False
                    touch.is_triple_tap = True
                    tap_time = touch.time_start - triple_tap.time_start
                    touch.triple_tap_time = tap_time
                    distance = triple_tap.triple_tap_distance
                    touch.triple_tap_distance = distance

            # add the touch internally
            self.touches[touch.uid] = (etype, touch)

        # second, check if up-touch is timeout for triple tap
        time_current = time()
        to_delete = []
        for touchid in self.touches.keys():
            etype, touch = self.touches[touchid]
            if etype != 'end':
                continue
            if time_current - touch.time_start < self.triple_tap_time:
                continue
            to_delete.append(touchid)

        for touchid in to_delete:
            del self.touches[touchid]

        return events
