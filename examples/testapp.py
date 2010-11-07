from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.video import Video
from kivy.core.text import Label as CoreLabel
from kivy.graphics import *

from random import random

class TestApp(App):
    def build(self):
        v = Video(source='/home/tito/code/pymt/examples/apps/videoplayer/softboy.avi', play=True)
        v.bind(on_load=self._load)
        return v
    def _load(self, *largs):
        print 'LOAD'
        with self.root.canvas:
            Color(1, 1, 1)
            Rectangle(texture=self.root.texture)

TestApp().run()
