'''
uix.relativelayout tests
========================
'''

import unittest

from kivy.base import EventLoop
from kivy.tests import UTMotionEvent
from kivy.uix.relativelayout import RelativeLayout


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
