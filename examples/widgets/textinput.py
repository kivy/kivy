from kivy.uix.textinput import TextInput
from kivy.uix.anchorlayout import AnchorLayout
from kivy.base import runTouchApp

if __name__ == '__main__':
    root = AnchorLayout()
    root.add_widget(TextInput(size_hint=(None, None), size=(100, 50)))
    runTouchApp(root)
