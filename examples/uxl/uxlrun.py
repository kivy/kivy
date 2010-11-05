#!/usr/bin/env python

from kivy.app import App
from kivy.uxl import UxlBuilder

class UxlApp(App):
    def build(self):
        uxl = UxlBuilder(filename=self.options['filename'])
        return uxl.root

if __name__ == '__main__':
    import sys
    import os

    if len(sys.argv) < 2:
        print 'Usage: %s filename.uxl' % os.path.basename(sys.argv[0])
        sys.exit(1)

    UxlApp(filename=sys.argv[1]).run()
