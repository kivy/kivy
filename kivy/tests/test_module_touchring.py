import unittest
from kivy.config import Config
Config.set('modules', 'touchring', '')
from kivy.app import runTouchApp, stopTouchApp
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.tests.common import UnitTestTouch


class TouchCounter(Factory.Widget):

    def __init__(self, **kwargs):
        super(TouchCounter, self).__init__(**kwargs)
        self.n_down = 0
        self.n_move = 0
        self.n_up = 0

    def on_touch_down(self, touch):
        self.n_down += 1
        return super(TouchCounter, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        self.n_move += 1
        return super(TouchCounter, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        self.n_up += 1
        return super(TouchCounter, self).on_touch_up(touch)


class TouchCountTestCase(unittest.TestCase):

    def setUp(self):
        self.root = TouchCounter()

    def tearDown(self):
        root = self.root
        root.parent.remove_widget(root)

    def assertTouchCount(self, touchcounter, n_down, n_move, n_up):
        self.assertEqual(touchcounter.n_down, n_down)
        self.assertEqual(touchcounter.n_move, n_move)
        self.assertEqual(touchcounter.n_up, n_up)

    def test_single_touch(self):
        root = self.root

        def func(dt):
            self.assertTouchCount(root, 0, 0, 0)
            touch = UnitTestTouch(0, 0)

            touch.touch_down()
            self.assertTouchCount(root, 1, 0, 0)
            touch.touch_move(20, 20)
            self.assertTouchCount(root, 1, 1, 0)
            touch.touch_up()
            self.assertTouchCount(root, 1, 1, 1)

            stopTouchApp()

        Clock.schedule_once(func, 0)
        runTouchApp(root)

    def test_multiple_touch(self):
        root = self.root

        def func(dt):
            self.assertTouchCount(root, 0, 0, 0)
            touch1 = UnitTestTouch(0, 0)
            touch2 = UnitTestTouch(100, 100)

            touch1.touch_down()
            self.assertTouchCount(root, 1, 0, 0)
            touch2.touch_down()
            self.assertTouchCount(root, 2, 0, 0)
            touch2.touch_move(30, 30)
            self.assertTouchCount(root, 2, 1, 0)
            touch1.touch_move(20, 20)
            self.assertTouchCount(root, 2, 2, 0)
            touch2.touch_move(200, 200)
            self.assertTouchCount(root, 2, 3, 0)
            touch2.touch_up()
            self.assertTouchCount(root, 2, 3, 1)
            touch1.touch_up()
            self.assertTouchCount(root, 2, 3, 2)

            stopTouchApp()

        Clock.schedule_once(func, 0)
        runTouchApp(root)
