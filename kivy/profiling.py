'''
Profiling
=========
'''

__all__ = ('Profiler', 'frame_profiler')

from os import environ, getpid
from json import dump
from time import time

class Profiler(object):
    def __init__(self, name):
        object.__init__(self)
        self.name = name
        self.enabled = False
        self.events = []
        self.marks = []
        self.last_start_index = 0

    def emit(self, event, t=None):
        if not self.enabled:
            return
        if t is None:
            t = time()
        if event == 'start-{}'.format(self.name):
            self.last_start_index = len(self.events)
        elif event == 'end-{}'.format(self.name):
            if self.marks and self.last_start_index:
                i = self.last_start_index
                self.events = self.events[:i] + self.marks + self.events[i:]
                self.marks = []
                self.last_start_index = 0
        self.events.append((t, event))
        return t

    def start(self):
        self.enabled = True

    def stop(self):
        self.enabled = False
        fn = 'frame-profiler-{}.json'.format(getpid())
        with open(fn, 'w') as fd:
            dump(self.events, fd)

    def mark(self, name, message):
        t = time()
        self.marks.append((t, 'mark-{}'.format(name), message))

# do we need to create a frame profiler?
frame_profiler = None
if 'KIVY_DOC' not in environ:
    if 'KIVY_FRAME_PROFILER' in environ:
        frame_profiler = Profiler('mainloop')
        frame_profiler.start()
        frame_profiler.emit('start-mainloop')

