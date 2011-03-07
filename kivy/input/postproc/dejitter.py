'''
Dejitter
========

Prevent blob jittering.

A problem that is often faced (esp. in optical MT setups) is that of
jitterish BLOBs caused by bad camera characteristics. With this module
you can get rid of that jitter. You just define a threshold
`jitter_distance` in your config, and all touch movements that move
the touch by less than the jitter distance are considered 'bad'
movements caused by jitter and will be discarded.
'''

__all__ = ('InputPostprocDejitter', )

from kivy.config import Config


class InputPostprocDejitter(object):
    '''
    Get rid of jitterish BLOBs.
    Example ::

        [postproc]
        jitter_distance = 0.004
        jitter_ignore_devices = mouse,mactouch

    :Configuration:
        `jitter_distance`: float
            A float in range 0-1.
        `jitter_ignore_devices`: string
            A comma-seperated list of device identifiers that
            should not be processed by dejitter (because they're
            very precise already).
    '''

    def __init__(self):
        self.jitterdist = Config.getfloat('postproc', 'jitter_distance')
        ignore_devices = Config.get('postproc', 'jitter_ignore_devices')
        self.ignore_devices = ignore_devices.split(',')
        self.last_touches = {}

    def taxicab_distance(self, p, q):
        # Get the taxicab/manhattan/citiblock distance for efficiency reasons
        return abs(p[0]-q[0]) + abs(p[1]-q[1])

    def process(self, events):
        if not self.jitterdist:
            return events
        processed = []
        for etype, touch in events:
            if not touch.is_touch:
                continue
            if touch.device in self.ignore_devices:
                processed.append((etype, touch))
                continue
            if etype == 'begin':
                self.last_touches[touch.id] = touch.spos
            if etype == 'end':
                del self.last_touches[touch.id]
            if etype != 'update':
                processed.append((etype, touch))
                continue
            # Check whether the touch moved more than the jitter distance
            last_spos = self.last_touches[touch.id]
            dist = self.taxicab_distance(last_spos, touch.spos)
            if dist > self.jitterdist:
                # Only if the touch has moved more than the jitter dist we take
                # it into account and dispatch it. Otherwise suppress it.
                self.last_touches[touch.id] = touch.spos
                processed.append((etype, touch))
        return processed
