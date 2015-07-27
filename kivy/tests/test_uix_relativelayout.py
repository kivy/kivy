'''
uix.relativelayout tests
========================
'''

import unittest

from kivy.base import EventLoop
from kivy.input.motionevent import MotionEvent
from kivy.uix.relativelayout import RelativeLayout


# https://gist.github.com/tito/f111b6916aa6a4ed0851
# subclass for touch event in unit test
class UTMotionEvent(MotionEvent):

    def depack(self, args):
        self.is_touch = True
        self.sx = args['x']
        self.sy = args['y']
        self.profile = ['pos']
        super(UTMotionEvent, self).depack(args)


class UixRelativeLayoutTest(unittest.TestCase):

    def test_relativelayout_on_touch_move(self):
        EventLoop.ensure_window()
        rl = RelativeLayout()
        EventLoop.window.add_widget(rl)
        touch = UTMotionEvent("unittest", 1, {"x": .5, "y": .5})
        EventLoop.post_dispatch_input("begin", touch)
        touch.move({"x": .6, "y": .4})
        EventLoop.post_dispatch_input("update", touch)
        EventLoop.post_dispatch_input("end", touch)

    def test_relativelayout_coordinates(self):
        EventLoop.ensure_window()
        rl = RelativeLayout(pos=(100, 100))
        EventLoop.window.add_widget(rl)  # do_layout() called
        self.assertEqual(rl.to_parent(50, 50), (150, 150))
        self.assertEqual(rl.to_local(50, 50), (-50, -50))
