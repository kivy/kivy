from kivy.app import App
from kivy.uix.widget import Widget


class MyPaintWidget(Widget):
    def on_touch_down(self, touch):
        print touch

class MyPaintApp(App):
    def build(self):
        return MyPaintWidget()


if __name__ == '__main__':
    MyPaintApp().run()
