import unittest
from kivy.app import App
from kivy.clock import Clock
import os.path
from kivy import lang


class AppTest(unittest.TestCase):
    def test_start_raw_app(self):
        lang._delayed_start = None
        a = App()
        Clock.schedule_once(a.stop, .1)
        a.run()

    def test_start_app_with_kv(self):
        class TestKvApp(App):
            pass

        lang._delayed_start = None
        a = TestKvApp()
        Clock.schedule_once(a.stop, .1)
        a.run()

    def test_user_data_dir(self):
        a = App()
        data_dir = a.user_data_dir
        if not os.path.exists(data_dir):
            raise Exception("user_data_dir didnt exists")
