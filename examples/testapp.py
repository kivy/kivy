from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.video import Video
from kivy.core.image import Image
from kivy.graphics import *

from random import random


tex = Image('examples/kivy.jpg').texture
class TestApp(App):
    def build(self):
        w = Widget()
        with w.canvas:
            Color(0,1,0,1)
            Ellipse(texture=tex)
            Rectangle(pos=(300,300))

        return w

TestApp().run()
