from kivy.graphics.paths import Path
from kivy.graphics import Color, Line
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout

Builder.load_string('''
<Playground>:
    GridLayout:
        size_hint_x: None
        width: 200
        cols: 1
        padding: 10
        spacing: 5

        Button:
            text: 'New path'
            on_release: root.new_path()

        ToggleButton:
            text: 'Line to'
            group: 'pathaction'
            on_release: root.set_action('line_to')

        ToggleButton:
            text: 'Curve to'
            group: 'pathaction'
            on_release: root.set_action('curve_to')

        Button:
            text: 'Close path'
            on_release: root.close_path()


''')

class Playground(FloatLayout):
    path = ObjectProperty(None)
    action = StringProperty('')

    def __init__(self, **kw):
        super(Playground, self).__init__(**kw)
        with self.canvas:
            Color(1, 1, 1)
            self.gline = Line(points=[])
        self.action = ''
        self.new_path()

    def new_path(self):
        self.path = Path()
        self.update_path()

    def close_path(self):
        self.path.close()
        self.update_path()

    def set_action(self, action):
        self.action = action
        self.action_args = []

    def update_path(self):
        self.gline.points = self.path.points

    def on_touch_down(self, touch):
        if super(Playground, self).on_touch_down(touch):
            return True
        if self.action == 'line_to':
            self.path.line_to(touch.x, touch.y)
            self.update_path()
        elif self.action == 'curve_to':
            self.action_args += touch.pos
            if len(self.action_args) == 6:
                self.path.curve_to(*self.action_args)
                self.action_args = []
                self.update_path()


class PathApp(App):
    def build(self):
        return Playground()

if __name__ == '__main__':
    PathApp().run()
