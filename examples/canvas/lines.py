from kivy.app import App
from kivy.properties import OptionProperty, NumericProperty, ListProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder

Builder.load_string('''
<LinePlayground>:
    canvas:
        Color:
            rgba: .4, .4, 1, root.alpha
        Line:
            points: self.points
            joint: self.joint
            cap: self.cap
            width: self.linewidth
        Color:
            rgba: .8, .8, .8, root.alpha_controlline
        Line:
            points: self.points

    GridLayout:
        cols: 2
        size_hint: 1, None
        height: 44 * 5

        GridLayout:
            cols: 2

            Label:
                text: 'Alpha'
            Slider:
                value: root.alpha
                on_value: root.alpha = float(args[1])
                min: 0.
                max: 1.
            Label:
                text: 'Alpha Control Line'
            Slider:
                value: root.alpha_controlline
                on_value: root.alpha_controlline = float(args[1])
                min: 0.
                max: 1.
            Label:
                text: 'Width'
            Slider:
                value: root.linewidth
                on_value: root.linewidth = args[1]
                min: 1
                max: 40
            Label:
                text: 'Cap'
            GridLayout:
                rows: 1
                ToggleButton:
                    group: 'cap'
                    text: 'none'
                    on_press: root.cap = self.text
                ToggleButton:
                    group: 'cap'
                    text: 'round'
                    on_press: root.cap = self.text
                ToggleButton:
                    group: 'cap'
                    text: 'square'
                    on_press: root.cap = self.text
            Label:
                text: 'Joint'
            GridLayout:
                rows: 1
                ToggleButton:
                    group: 'joint'
                    text: 'none'
                    on_press: root.joint = self.text
                ToggleButton:
                    group: 'joint'
                    text: 'round'
                    on_press: root.joint = self.text
                ToggleButton:
                    group: 'joint'
                    text: 'miter'
                    on_press: root.joint = self.text
                ToggleButton:
                    group: 'joint'
                    text: 'bevel'
                    on_press: root.joint = self.text

        AnchorLayout:
            Button:
                size_hint: None, None
                size: 100, 44
                text: 'Clear'
                on_press: root.points = []

''')


class LinePlayground(FloatLayout):
    alpha_controlline = NumericProperty(1.0)
    alpha = NumericProperty(0.5)
    points = ListProperty([500, 500, 300, 300, 500, 300, 500, 400, 600, 400])
    joint = OptionProperty('none', options=('round', 'miter', 'bevel', 'none'))
    cap = OptionProperty('none', options=('round', 'square', 'none'))
    linewidth = NumericProperty(10.0)

    def on_touch_down(self, touch):
        if super(LinePlayground, self).on_touch_down(touch):
            return True
        touch.grab(self)
        self.points = self.points + list(touch.pos)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.points[-2:] = list(touch.pos)
            return True
        return super(LinePlayground, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            return True
        return super(LinePlayground, self).on_touch_up(touch)


class TestLineApp(App):
    def build(self):
        return LinePlayground()


if __name__ == '__main__':
    TestLineApp().run()
