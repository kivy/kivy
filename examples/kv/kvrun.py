#!/usr/bin/env python

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder

class KvApp(App):
    def _print_fps(self, *largs):
        print 'FPS:', Clock.get_fps()
    def build(self):
        Clock.schedule_interval(self._print_fps, 1)
        return Builder.load_file(self.options['filename'])

if __name__ == '__main__':
    import sys
    import os

    if len(sys.argv) < 2:
        print 'Usage: %s filename.kv' % os.path.basename(sys.argv[0])
        sys.exit(1)

    KvApp(filename=sys.argv[1]).run()
