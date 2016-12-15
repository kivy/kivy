from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout


class Root(BoxLayout):
    pass


class ColorusageApp(App):
    def build(self):
        return Root()

if __name__ == "__main__":
    ColorusageApp().run()
