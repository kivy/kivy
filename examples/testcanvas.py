from kivy.app import App
from kivy.uix.widget import Widget
from kivy.core.image import Image
from kivy.graphics import *
from kivy.uix.svg import SVG
class TestApp(App):
    def build(self):
        s = SVG()
        s.source = 'examples/svg/test.svg'
        return s
TestApp().run()
