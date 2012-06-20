'''
Animations tests
================
'''

import unittest
from time import sleep
from kivy.animation import Animation
from kivy.uix.widget import Widget


class AnimationTestCase(unittest.TestCase):

    def setUp(self):
        self.a = Animation(x=100, d=1, t='out_bounce')
        self.w = Widget()

    def test_start_animation(self):
        self.a.start(self.w)
        sleep(1)

    def test_stop_animation(self):
        self.a.start(self.w)
        sleep(.5)
        self.a.stop(self.w)

    def test_stop_all(self):
        self.a.start(self.w)
        sleep(.5)
        Animation.stop_all(self.w)
