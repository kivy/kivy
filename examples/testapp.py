from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.text import Label as CoreLabel
from kivy.graphics import *


class TestApp(App):
    def build(self):
        return Button(text='Hello world')

TestApp().run()
