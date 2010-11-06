from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.text import Label as CoreLabel
from kivy.graphics import *

from random import random

class TestApp(App):
    def build(self):
        def print_fps(dt):
            print 'FPS: ', Clock.get_fps()
        Clock.schedule_interval(print_fps, 1)
        a = Widget()
        for x in xrange(100):
            pos = random() * 500, random() * 500
            a.add_widget(Button(text=str(x), pos=pos))
        return a

TestApp().run()
