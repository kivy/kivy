'''
Animations tests
================
'''

import unittest
from time import time, sleep
from kivy.animation import Animation, AnimationTransition
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Scale


class AnimationTestCase(unittest.TestCase):
    def sleep(self, t):
        start = time()
        while time() < start + t:
            sleep(.01)
            Clock.tick()

    def setUp(self):
        self.a = Animation(x=100, d=1, t='out_bounce')
        self.w = Widget()

    def test_start_animation(self):
        self.a.start(self.w)
        self.sleep(1.5)
        self.assertAlmostEqual(self.w.x, 100)

    def test_stop_animation(self):
        self.a.start(self.w)
        self.sleep(.5)
        self.a.stop(self.w)
        self.assertNotAlmostEqual(self.w.x, 100)
        self.assertNotAlmostEqual(self.w.x, 0)

    def test_stop_all(self):
        self.a.start(self.w)
        self.sleep(.5)
        Animation.stop_all(self.w)

    def test_stop_all_2(self):
        self.a.start(self.w)
        self.sleep(.5)
        Animation.stop_all(self.w, 'x')

    def test_duration(self):
        self.assertEqual(self.a.duration, 1)

    def test_transition(self):
        self.assertEqual(self.a.transition, AnimationTransition.out_bounce)

    def test_animated_properties(self):
        self.assertEqual(self.a.animated_properties['x'], 100)

    def test_animated_instruction(self):
        instruction = Scale(3)
        self.a.start(instruction)
        self.assertEqual(self.a.animated_properties['x'], 100)
        self.assertAlmostEqual(instruction.x, 3)
        self.sleep(1.5)
        self.assertAlmostEqual(instruction.x, 100)


class SequentialAnimationTestCase(unittest.TestCase):

    def sleep(self, t):
        start = time()
        while time() < start + t:
            sleep(.01)
            Clock.tick()

    def setUp(self):
        self.a = Animation(x=100, d=1, t='out_bounce')
        self.a += Animation(x=0, d=1, t='out_bounce')
        self.w = Widget()

    def test_stop_all(self):
        self.a.start(self.w)
        self.sleep(.5)
        Animation.stop_all(self.w)

    def test_stop_all_2(self):
        self.a.start(self.w)
        self.sleep(.5)
        Animation.stop_all(self.w, 'x')
