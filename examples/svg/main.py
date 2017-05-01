import sys
from glob import glob
from os.path import join, dirname
from kivy.uix.scatter import Scatter
from kivy.app import App
from kivy.graphics.svg import Svg
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout


class SvgWidget(Scatter):

    def __init__(self, filename, **kwargs):
        super(SvgWidget, self).__init__(**kwargs)
        with self.canvas:
            svg = Svg(filename)
        self.size = svg.width, svg.height


class SvgApp(App):

    def build(self):
        self.root = FloatLayout()

        filenames = sys.argv[1:]
        if not filenames:
            filenames = glob(join(dirname(__file__), '*.svg'))

        for filename in filenames:
            svg = SvgWidget(filename, size_hint=(None, None))
            self.root.add_widget(svg)
            svg.scale = 5.
            svg.center = Window.center


if __name__ == '__main__':
    SvgApp().run()
