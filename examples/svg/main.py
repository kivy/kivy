'''
SVG Demo
========

This experimental application demonstrates using SVG (Scalable Vector Graphics).
You should see a number of images piled on top of each other if you run without
command line arguments. You can choose specific images by running
'python main.py -- ship.svg sun.svg'. The images are rendered in a Scatter
widget and you can touch to drag or double touch to rotate and
scale images.

The image tiger.svg is large and renders correctly while the image music.svg
is wider but may not render on some devices. The image ship.svg, the image
sun.svg, and the image cloud.svg are examples of simple images.
'''

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
            svg.scale = 5.   # show images zoomed in.
            svg.center = Window.center

if __name__ == '__main__':
    SvgApp().run()
