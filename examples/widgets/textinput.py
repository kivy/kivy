from kivy.uix.textinput import TextInput
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scatter import Scatter
from kivy.base import runTouchApp

if __name__ == '__main__':
    root = Scatter(size_hint=(None, None))
    root.add_widget(TextInput(size_hint=(None, None), size=(100, 50)))
    runTouchApp(root)
