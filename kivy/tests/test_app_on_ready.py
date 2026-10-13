import unittest

from kivy.app import App
from kivy.uix.button import Button


class ReadyFlagApp(App):
    def build(self):
        self.ready_called = False
        return Button(text='Hello')

    def on_ready(self):
        self.ready_called = True


class TestOnReady(unittest.TestCase):
    @staticmethod
    def test_on_ready_is_called():
        app = ReadyFlagApp()
        # Simulate what backend does after first frame render
        app._trigger_ready_once()
        assert app.ready_called is True
