#!/usr/bin/env python

from kivy.app import App
from kivy.lang import Builder

class KvApp(App):
    def build(self):
        return Builder.load_file(self.options['filename'])

if __name__ == '__main__':
    import sys
    import os

    if len(sys.argv) < 2:
        print 'Usage: %s filename.kv' % os.path.basename(sys.argv[0])
        sys.exit(1)

    KvApp(filename=sys.argv[1]).run()
