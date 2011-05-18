'''
Clock tests
===========
'''

import unittest

counter = 0


def callback(dt):
    global counter
    counter += 1


class ClockTestCase(unittest.TestCase):

    def setUp(self):
        from kivy.clock import Clock
        global counter
        counter = 0
        Clock._events = {}

    def test_schedule_once(self):
        from kivy.clock import Clock
        Clock.schedule_once(callback)
        Clock.tick()
        self.assertEqual(counter, 1)

    def test_schedule_once_twice(self):
        from kivy.clock import Clock
        Clock.schedule_once(callback)
        Clock.schedule_once(callback)
        Clock.tick()
        self.assertEqual(counter, 2)

    def test_schedule_once_draw_after(self):
        from kivy.clock import Clock
        Clock.schedule_once(callback, 0)
        Clock.tick_draw()
        self.assertEqual(counter, 0)
        Clock.tick()
        self.assertEqual(counter, 1)

    def test_schedule_once_draw_before(self):
        from kivy.clock import Clock
        Clock.schedule_once(callback, -1)
        Clock.tick_draw()
        self.assertEqual(counter, 1)
        Clock.tick()
        self.assertEqual(counter, 1)

    def test_unschedule(self):
        from kivy.clock import Clock
        Clock.schedule_once(callback)
        Clock.unschedule(callback)
        Clock.tick()
        self.assertEqual(counter, 0)

    def test_unschedule_after_tick(self):
        from kivy.clock import Clock
        Clock.schedule_once(callback, 5.)
        Clock.tick()
        Clock.unschedule(callback)
        Clock.tick()
        self.assertEqual(counter, 0)

    def test_unschedule_draw(self):
        from kivy.clock import Clock
        Clock.schedule_once(callback, 0)
        Clock.tick_draw()
        self.assertEqual(counter, 0)
        Clock.unschedule(callback)
        Clock.tick()
        self.assertEqual(counter, 0)
