'''
Show border
===========

Visualize widget's boundary.

The idea is taken from
http://robertour.com/2013/10/02/easy-way-debugging-kivy-interfaces/
'''

__all__ = ('start', 'stop')

from kivy.lang import Builder


KV_CODE = '''
<Widget>:
    canvas.after:
        Line:
            rectangle: self.x + 1, self.y + 1, self.width - 1, self.height - 1
            dash_offset: 5
            dash_length: 3
'''


def start(win, ctx):
    Builder.load_string(KV_CODE, filename=__file__)


def stop(win, ctx):
    Builder.unload_file(__file__)
