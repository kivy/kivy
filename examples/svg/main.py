import sys
from glob import glob
from os.path import join, dirname
from kivy.uix.scatter import Scatter
from kivy.uix.widget import Widget
from kivy.app import App
from kivy.graphics.svg import Svg


class SvgWidget(Scatter):

    def __init__(self, filename):
        super(SvgWidget, self).__init__()
        with self.canvas:
            Svg(filename)

class SvgApp(App):

    def build(self):
        root = Widget()

        filenames = sys.argv[1:]
        if not filenames:
            filenames = glob(join(dirname(__file__), '*.svg'))

        for filename in filenames:
            svg = SvgWidget(filename)
            root.add_widget(svg)

        return root

if __name__ == '__main__':
    SvgApp().run()

