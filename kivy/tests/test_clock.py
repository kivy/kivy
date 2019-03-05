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
        Clock._events = [[] for i in range(256)]

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

    def test_unschedule_event(self):
        from kivy.clock import Clock
        ev = Clock.schedule_once(callback)
        Clock.unschedule(ev)
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

    def test_trigger_create(self):
        from kivy.clock import Clock
        trigger = Clock.create_trigger(callback, 0)
        trigger()
        self.assertEqual(counter, 0)
        Clock.tick()
        self.assertEqual(counter, 1)

    def test_trigger_cancel(self):
        from kivy.clock import Clock
        trigger = Clock.create_trigger(callback, 5.)
        trigger()
        trigger.cancel()
        Clock.tick()
        self.assertEqual(counter, 0)

    def test_trigger_interval(self):
        from kivy.clock import Clock
        trigger = Clock.create_trigger(callback, 0, interval=True)
        trigger()
        Clock.tick()
        self.assertEqual(counter, 1)
        Clock.tick()
        self.assertEqual(counter, 2)

    def test_trigger_decorator(self):
        from kivy.clock import Clock, triggered

        @triggered()
        def triggered_callback():
            callback(dt=0)

        triggered_callback()
        self.assertEqual(counter, 0)
        Clock.tick()
        self.assertEqual(counter, 1)

    def test_trigger_decorator_cancel(self):
        from kivy.clock import Clock, triggered

        @triggered()
        def triggered_callback():
            callback(dt=0)

        triggered_callback()
        triggered_callback.cancel()
        Clock.tick()
        self.assertEqual(counter, 0)
