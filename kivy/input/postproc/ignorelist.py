'''
Ignore list
===========

Ignore touch in some part on screen
'''

__all__ = ('InputPostprocIgnoreList', )

from kivy.config import Config
from kivy.utils import strtotuple


class InputPostprocIgnoreList(object):
    '''
    InputPostprocIgnoreList is a post-processor who remove touch in ignore list.
    Ignore list can be configured in the Kivy config file ::

        [postproc]
        # Format: [(xmin, ymin, xmax, ymax), ...]
        ignore = [(0.1, 0.1, 0.15, 0.15)]

    Ignore list coordinate are in 0-1, not in the screen width/height.
    '''

    def __init__(self):
        self.ignore_list = strtotuple(Config.get('postproc', 'ignore'))

    def collide_ignore(self, touch):
        x, y = touch.sx, touch.sy
        for l in self.ignore_list:
            xmin, ymin, xmax, ymax = l
            if x > xmin and x < xmax and y > ymin and y < ymax:
                return True

    def process(self, events):
        if not len(self.ignore_list):
            return events
        for etype, touch in events:
            if not touch.is_touch:
                continue
            if etype != 'begin':
                continue
            if self.collide_ignore(touch):
                touch.ud.__pp_ignore__ = True
        return [(etype, touch) for etype, touch in events \
                if not '__pp_ignore__' in touch.ud]
