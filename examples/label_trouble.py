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

root = None
tex = Image('examples/test-rect.png').texture
label = CoreLabel(text="oo", font_size=32)


class TestApp(App):
    def build(self):
        global root
        label.refresh()
        print "XXXXXXXX", label.texture, tex.size
        w = Widget()
        with w.canvas:
            Color(.5,.5,.5,.5)
            Rectangle(size=(500,500))
            Color(1,1,1,1)
            Rectangle(texture=label.texture)
            #Rectangle(pos=(300,300), texture=tex)
        root = w
        return w


def update_texture(*args):
    label.refresh()
    with root.canvas:
        Color(0,1,0,1)
        Rectangle(texture=label.texture)


Clock.schedule_interval(update_texture, 2)

TestApp().run()
