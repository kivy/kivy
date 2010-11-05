#!/usr/bin/env python

from kivy.app import App
from kivy.uxl import Uxl

class UxlApp(App):
    def build(self):
        return Uxl.load_file(self.options['filename'])

if __name__ == '__main__':
    import sys
    import os

    if len(sys.argv) < 2:
        print 'Usage: %s filename.uxl' % os.path.basename(sys.argv[0])
        sys.exit(1)

    UxlApp(filename=sys.argv[1]).run()
