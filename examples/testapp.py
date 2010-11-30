from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.video import Video
from kivy.core.image import Image
from kivy.graphics import *
from kivy.core.text import Label as CoreLabel

from random import random

tex1 = Image('examples/test-rect.png').texture
tex2 = Image('examples/kivy.jpg').texture

class TestApp(App):
    def build(self):
        w = Widget()
        with w.canvas:
            Color(1,1,1,1)
            Rectangle(size=(200,200), texture=tex1)
            Color(1,1,1,1)
            Ellipse(pos=(300,200), texture=tex2)
        return w

TestApp().run()
