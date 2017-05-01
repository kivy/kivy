'''
Animations tests
================
'''

import unittest
import gc
from time import time, sleep
from kivy.animation import Animation, AnimationTransition
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Scale
from kivy.weakproxy import WeakProxy


class AnimationTestCase(unittest.TestCase):
    def sleep(self, t):
        start = time()
        while time() < start + t:
            sleep(.01)
            Clock.tick()

    def setUp(self):
        self.assertEqual(len(Animation._instances), 0)
        self.a = Animation(x=100, d=1, t='out_bounce')
        self.w = Widget()

    def tearDown(self):
        self.assertEqual(len(Animation._instances), 0)

    def test_start_animation(self):
        self.a.start(self.w)
        self.sleep(1.5)
        self.assertAlmostEqual(self.w.x, 100)

    def test_animation_duration_0(self):
        a = Animation(x=100, d=0)
        a.start(self.w)
        self.sleep(.5)

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

    def test_weakref(self):
        widget = Widget()
        anim = Animation(x=100)
        anim.start(widget.proxy_ref)
        del widget
        gc.collect()
        try:
            self.sleep(1.)
        except ReferenceError:
            pass


class SequentialAnimationTestCase(unittest.TestCase):

    def sleep(self, t):
        start = time()
        while time() < start + t:
            sleep(.01)
            Clock.tick()

    def setUp(self):
        self.assertEqual(len(Animation._instances), 0)
        self.a = Animation(x=100, d=1, t='out_bounce')
        self.a += Animation(x=0, d=1, t='out_bounce')
        self.w = Widget()

    def tearDown(self):
        self.assertEqual(len(Animation._instances), 0)

    def test_cancel_all(self):
        self.a.start(self.w)
        self.sleep(.5)
        Animation.cancel_all(self.w)

    def test_cancel_all_2(self):
        self.a.start(self.w)
        self.sleep(.5)
        Animation.cancel_all(self.w, 'x')

    def test_stop_all(self):
        self.a.start(self.w)
        self.sleep(.5)
        Animation.stop_all(self.w)

    def test_stop_all_2(self):
        self.a.start(self.w)
        self.sleep(.5)
        Animation.stop_all(self.w, 'x')

    def _test_on_progress(self, anim, widget, progress):
        self._on_progress_called = True

    def _test_on_complete(self, anim, widget):
        self._on_complete_called = True

    def test_events(self):
        self._on_progress_called = False
        self._on_complete_called = False
        self.a.bind(on_progress=self._test_on_progress,
                    on_complete=self._test_on_complete)
        self.a.start(self.w)
        self.sleep(.5)
        self.assertTrue(self._on_progress_called)
        self.sleep(2)
        self.assertTrue(self._on_progress_called)
        self.assertTrue(self._on_complete_called)
