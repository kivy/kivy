from kivy.uix.scatter import Scatter
from kivy.app import App

class MyScatter(Scatter):
    pass

class ScatterApp(App):
    def build(self):
        s = MyScatter(size=(400, 400), size_hint=(None, None))
        s.top = 500
        return s

ScatterApp().run()
