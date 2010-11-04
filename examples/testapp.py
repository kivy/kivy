from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import *


class TestApp(App):
    def build(self):
        a = Widget()
        texture = Image('kivy.jpg').texture
        with a.canvas:
            Rectangle(size=(345, 345), texture=texture)
        return a

TestApp().run()
