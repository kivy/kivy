import unittest
from kivy.app import App
from kivy.clock import Clock


class AppTest(unittest.TestCase):
    def test_start_raw_app(self):
        a = App()
        Clock.schedule_once(a.stop, .1)
        a.run()

    def test_start_app_with_kv(self):
        class TestKvApp(App):
            pass

        a = TestKvApp()
        Clock.schedule_once(a.stop, .1)
        a.run()
