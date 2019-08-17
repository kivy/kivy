from glob import glob
from os.path import join, dirname, basename, abspath
from kivy.uix.scatter import Scatter
from kivy.app import App
from kivy.graphics.svg import Svg
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.logger import Logger

KV = """
#:import join os.path.join
#:import splitext os.path.splitext

<SvgWidget>:
    do_rotation: False

BoxLayout:
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            size: self.size
    Button:
        text: '<'
        on_press: app.index -= 1
        disabled: app.index == 0
        size_hint_x: None
        width: '20dp'

    BoxLayout:
        orientation: 'vertical'
        Spinner:
            text: '{}:{}'.format(app.index, app.filenames[app.index]) if app.filenames else ''
            values: ['{}:{}'.format(i, v) for (i, v) in enumerate(app.filenames)] if app.filenames else []

            on_text:
                if self.text: app.index = int(self.text.split(':')[0])

            color: 0, 0, 0, 1
            size_hint_y: None
            height: self.texture_size[1] * 2
            pos_hint: {'top': 1}

        FloatLayout:
            Scatter:
                do_rotation: False
                size_hint: None, None
                size: img.texture_size
                center_y: self.height and root.center_y
                scale: 4
                Image:
                    id: img
                    source:
                        (
                        join(app.dirname, 'png', 'full-' + splitext(app.filenames[app.index])[0] + '.png')
                        ) if app.filenames else ''

            SvgWidget:
                size_hint: None, None
                x: root.center_x
                source:
                    (
                    join(app.dirname, 'svggen', app.filenames[app.index])
                    ) if app.filenames else ''

            Label:
                text: app.current_error
                size_hint_y: None
                height: self.texture_size[1]
                color: .9, .2, .2, 1
                font_size: '20dp'

                canvas.before:
                    Color:
                        rgba: .5, .5, .5, .8
                    Rectangle:
                        pos: self.pos
                        size: self.size
    Button:
        text: '>'
        on_press: app.index += 1
        disabled: app.index == len(app.filenames) - 1
        size_hint_x: None
        width: '20dp'

"""


class SvgWidget(Scatter):
    source = StringProperty()

    def on_source(self, *args):
        if self.source:
            self.canvas.clear()
            try:
                with self.canvas:
                    svg = Svg(self.source)
                self.size = svg.width, svg.height
            except Exception as e:
                print("unable to load {}: \n {}".format(self.source, e))
                Logger.exception(e)
                app.current_error = str(e)
            else:
                app.current_error = ''


class SvgTestApp(App):
    filenames = ListProperty()
    index = NumericProperty()
    dirname = StringProperty()
    current_error = StringProperty()

    def build(self):
        print(__file__)
        self.dirname = join(dirname(__file__), 'svg-tests-2/tavmjong.free.fr/INKSCAPE/W3C_SVG/')
        self.filenames = sorted(basename(x) for x in glob('{}/svggen/*.svg'.format(self.dirname)))
        print(self.dirname)
        print(self.filenames)
        return Builder.load_string(KV)

if __name__ == '__main__':
    app = SvgTestApp()
    app.run()
