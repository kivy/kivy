from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button


class SpecialButton(Button):
    pass


class CustomLayout(BoxLayout):
    pass


class TestApp(App):
    def build(self):
        return Builder.load_file('layout.kv')

if __name__ == '__main__':
    TestApp().run()