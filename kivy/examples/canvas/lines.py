'''
Line (SmoothLine) Experiment
============================

This demonstrates the experimental and unfinished SmoothLine feature
for fast line drawing. You should see a multi-segment
path at the top of the screen, and sliders and buttons along the bottom.
You can click to add new points to the segment, change the transparency
and width of the line, or hit 'Animate' to see a set of sine and cosine
animations. The Cap and Joint buttons don't work: SmoothLine has not
implemented these features yet.
'''

from kivy.app import App
from kivy.properties import OptionProperty, NumericProperty, ListProperty, \
        BooleanProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.clock import Clock
from math import cos, sin

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
            close: self.close
            dash_length: self.dash_length
            dash_offset: self.dash_offset
            dashes: self.dashes
        Color:
            rgba: .8, .8, .8, root.alpha_controlline
        Line:
            points: self.points
            close: self.close
            dash_length: self.dash_length
            dash_offset: self.dash_offset
            dashes: self.dashes
        Color:
            rgba: 1, .4, .4, root.alpha
        Line:
            points: self.points2
            joint: self.joint
            cap: self.cap
            width: self.linewidth
            close: self.close
            dash_length: self.dash_length
            dash_offset: self.dash_offset
            dashes: self.dashes

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

            Label:
                text: 'Close'
            ToggleButton:
                text: 'Close line'
                on_press: root.close = self.state == 'down'

            Label:
                text: 'Dashes'
            GridLayout:
                rows: 1
                ToggleButton:
                    group: 'dashes'
                    text: 'none'
                    state: 'down'
                    allow_no_selection: False
                    size_hint_x: None
                    width: self.texture_size[0]
                    padding_x: '5dp'
                    on_state:
                        if self.state == 'down': root.dashes = []
                        if self.state == 'down': root.dash_length = 1
                        if self.state == 'down': root.dash_offset = 0
                ToggleButton:
                    id: constant
                    group: 'dashes'
                    text: 'Constant: '
                    allow_no_selection: False
                    size_hint_x: None
                    width: self.texture_size[0]
                    padding_x: '5dp'
                    on_state:
                        if self.state == 'down': root.dashes = []
                        if self.state == 'down': root.dash_length = \
                            int(dash_len.text or 1)
                        if self.state == 'down': root.dash_offset = \
                            int(dash_offset.text or 0)
                Label:
                    text: 'len'
                    size_hint_x: None
                    width: self.texture_size[0]
                    padding_x: '5dp'
                TextInput:
                    id: dash_len
                    size_hint_x: None
                    width: '30dp'
                    input_filter: 'int'
                    multiline: False
                    text: '1'
                    on_text: if constant.state == 'down': \
                        root.dash_length = int(self.text or 1)
                Label:
                    text: 'offset'
                    size_hint_x: None
                    width: self.texture_size[0]
                    padding_x: '5dp'
                TextInput:
                    id: dash_offset
                    size_hint_x: None
                    width: '30dp'
                    input_filter: 'int'
                    multiline: False
                    text: '0'
                    on_text: if constant.state == 'down': \
                        root.dash_offset = int(self.text or 0)
                ToggleButton:
                    id: dash_list
                    group: 'dashes'
                    text: 'List: '
                    allow_no_selection: False
                    size_hint_x: None
                    width: self.texture_size[0]
                    padding_x: '5dp'
                    on_state:
                        if self.state == 'down': root.dashes = list(map(lambda\
                            x: int(x or 0), dash_list_in.text.split(',')))
                        if self.state == 'down': root.dash_length = 1
                        if self.state == 'down': root.dash_offset = 0
                TextInput:
                    id: dash_list_in
                    size_hint_x: None
                    width: '180dp'
                    multiline: False
                    text: '4,3,10,15'
                    on_text: if dash_list.state == 'down': root.dashes = \
                        list(map(lambda x: int(x or 0), self.text.split(',')))

        AnchorLayout:
            GridLayout:
                cols: 1
                size_hint: None, None
                size: self.minimum_size
                ToggleButton:
                    size_hint: None, None
                    size: 100, 44
                    text: 'Animate'
                    on_state: root.animate(self.state == 'down')
                Button:
                    size_hint: None, None
                    size: 100, 44
                    text: 'Clear'
                    on_press: root.points = root.points2 = []

''')


class LinePlayground(FloatLayout):

    alpha_controlline = NumericProperty(1.0)
    alpha = NumericProperty(0.5)
    close = BooleanProperty(False)
    points = ListProperty([(500, 500),
                          [300, 300, 500, 300],
                          [500, 400, 600, 400]])
    points2 = ListProperty([])
    joint = OptionProperty('none', options=('round', 'miter', 'bevel', 'none'))
    cap = OptionProperty('none', options=('round', 'square', 'none'))
    linewidth = NumericProperty(10.0)
    dt = NumericProperty(0)
    dash_length = NumericProperty(1)
    dash_offset = NumericProperty(0)
    dashes = ListProperty([])

    _update_points_animation_ev = None

    def on_touch_down(self, touch):
        if super(LinePlayground, self).on_touch_down(touch):
            return True
        touch.grab(self)
        self.points.append(touch.pos)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.points[-1] = touch.pos
            return True
        return super(LinePlayground, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            return True
        return super(LinePlayground, self).on_touch_up(touch)

    def animate(self, do_animation):
        if do_animation:
            self._update_points_animation_ev = Clock.schedule_interval(
                self.update_points_animation, 0)
        elif self._update_points_animation_ev is not None:
            self._update_points_animation_ev.cancel()

    def update_points_animation(self, dt):
        cy = self.height * 0.6
        cx = self.width * 0.1
        w = self.width * 0.8
        step = 20
        points = []
        points2 = []
        self.dt += dt
        for i in range(int(w / step)):
            x = i * step
            points.append(cx + x)
            points.append(cy + cos(x / w * 8. + self.dt) * self.height * 0.2)
            points2.append(cx + x)
            points2.append(cy + sin(x / w * 8. + self.dt) * self.height * 0.2)
        self.points = points
        self.points2 = points2


class TestLineApp(App):
    def build(self):
        return LinePlayground()


if __name__ == '__main__':
    TestLineApp().run()
