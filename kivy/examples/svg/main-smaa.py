import sys
from glob import glob
from os.path import join, dirname
from kivy.uix.scatter import Scatter
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.app import App
from kivy.graphics.svg import Svg
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder


smaa_ui = '''
#:kivy 1.8.0

BoxLayout:
    orientation: 'horizontal'
    pos_hint: {'top': 1}
    size_hint_y: None
    height: '48dp'
    padding: '2dp'
    spacing: '2dp'
    Label:
        text: 'Quality:'
    ToggleButton:
        text: 'Low'
        group: 'smaa-quality'
        on_release: app.smaa.quality = 'low'
    ToggleButton:
        text: 'Medium'
        group: 'smaa-quality'
        on_release: app.smaa.quality = 'medium'
    ToggleButton:
        text: 'High'
        group: 'smaa-quality'
        on_release: app.smaa.quality = 'high'
    ToggleButton:
        text: 'Ultra'
        group: 'smaa-quality'
        state: 'down'
        on_release: app.smaa.quality = 'ultra'

    Label:
        text: 'Debug:'
    ToggleButton:
        text: 'None'
        group: 'smaa-debug'
        state: 'down'
        on_release: app.smaa.debug = ''
    ToggleButton:
        text: 'Source'
        group: 'smaa-debug'
        on_release: app.smaa.debug = 'source'
    ToggleButton:
        text: 'Edges'
        group: 'smaa-debug'
        on_release: app.smaa.debug = 'edges'
    ToggleButton:
        text: 'Blend'
        group: 'smaa-debug'
        on_release: app.smaa.debug = 'blend'

'''


class SvgWidget(Scatter):

    def __init__(self, filename):
        super(SvgWidget, self).__init__()
        with self.canvas:
            svg = Svg(filename)

        self.size = svg.width, svg.height


class SvgApp(App):

    def build(self):
        from kivy.garden.smaa import SMAA

        Window.bind(on_keyboard=self._on_keyboard_handler)

        self.smaa = SMAA()
        self.effects = [self.smaa, Widget()]
        self.effect_index = 0
        self.label = Label(text='SMAA', top=Window.height)
        self.effect = effect = self.effects[0]
        self.root = FloatLayout()
        self.root.add_widget(effect)

        if 0:
            from kivy.graphics import Color, Rectangle
            wid = Widget(size=Window.size)
            with wid.canvas:
                Color(1, 1, 1, 1)
                Rectangle(size=Window.size)
            effect.add_widget(wid)

        if 1:
            # from kivy.uix.image import Image
            # root.add_widget(Image(source='data/logo/kivy-icon-512.png',
            #                      size=(800, 600)))

            filenames = sys.argv[1:]
            if not filenames:
                filenames = glob(join(dirname(__file__), '*.svg'))

            for filename in filenames:
                svg = SvgWidget(filename)
                effect.add_widget(svg)

            effect.add_widget(self.label)
            svg.scale = 5.
            svg.center = Window.center

        if 0:
            wid = Scatter(size=Window.size)
            from kivy.graphics import Color, Triangle, Rectangle
            with wid.canvas:
                Color(0, 0, 0, 1)
                Rectangle(size=Window.size)
                Color(1, 1, 1, 1)
                w, h = Window.size
                cx, cy = w / 2., h / 2.
                Triangle(points=[cx - w * 0.25, cy - h * 0.25,
                                 cx, cy + h * 0.25,
                                 cx + w * 0.25, cy - h * 0.25])
            effect.add_widget(wid)

        if 0:
            from kivy.uix.button import Button
            from kivy.uix.slider import Slider
            effect.add_widget(Button(text='Hello World'))
            effect.add_widget(Slider(pos=(200, 200)))

        control_ui = Builder.load_string(smaa_ui)
        self.root.add_widget(control_ui)

    def _on_keyboard_handler(self, instance, key, *args):
        if key == 32:
            self.effect_index = (self.effect_index + 1) % 2
            childrens = self.effect.children[:]
            self.effect.clear_widgets()
            self.root.remove_widget(self.effect)
            self.effect = self.effects[self.effect_index]
            self.root.add_widget(self.effect)
            for child in reversed(childrens):
                self.effect.add_widget(child)
            self.label.text = self.effect.__class__.__name__
            Window.title = self.label.text


if __name__ == '__main__':
    SvgApp().run()
