#!/usr/bin/env python
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.slider import Slider
from kivy.graphics import Color, Bezier, Line


class BezierTest(FloatLayout):

    def __init__(self, points=[], loop=False, *args, **kwargs):
        super(BezierTest, self).__init__(*args, **kwargs)
        self.d = 10
        self.points = points
        self.loop = loop
        self.current_point = None

        with self.canvas:
            Color(1.0, 0.0, 0.0)

            self.bezier = Bezier(
                    points=self.points,
                    segments=150,
                    loop=self.loop,
                    dash_length=100,
                    dash_offset=10)

            Color(1.0, 0.0, 1.0)
            self.line = Line(
                    points=self.points+self.points[:2],
                    dash_offset=10,
                    dash_length=100)

        s = Slider(y=0, pos_hint={'x': .3}, size_hint=(.7, None), height=50)
        s.bind(value=self._set_bezier_dash_offset)
        self.add_widget(s)

        s = Slider(y=50, pos_hint={'x': .3}, size_hint=(.7, None), height=50)
        s.bind(value=self._set_line_dash_offset)
        self.add_widget(s)

    def _set_bezier_dash_offset(self, instance, value):
        # effect to reduce length while increase offset
        self.bezier.dash_length = 100 - value
        self.bezier.dash_offset = value

    def _set_line_dash_offset(self, instance, value):
        # effect to reduce length while increase offset
        self.line.dash_length = 100 - value
        self.line.dash_offset = value

    def on_touch_down(self, touch):
        if self.collide_point(touch.pos[0], touch.pos[1]):
            for i, p in enumerate(list(zip(self.points[::2], self.points[1::2]))):
                if (
                        abs(touch.pos[0] - self.pos[0] - p[0]) < self.d and
                        abs(touch.pos[1] - self.pos[1] - p[1]) < self.d):
                    self.current_point = i + 1
                    return True
            return super(BezierTest, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(touch.pos[0], touch.pos[1]):
            if self.current_point:
                self.current_point = None
                return True
            return super(BezierTest, self).on_touch_up(touch)

    def on_touch_move(self, touch):
        if self.collide_point(touch.pos[0], touch.pos[1]):
            c = self.current_point
            if c:
                self.points[(c - 1) * 2] = touch.pos[0] - self.pos[0]
                self.points[(c - 1) * 2 + 1] = touch.pos[1] - self.pos[1]
                self.bezier.points = self.points
                self.line.points = self.points + self.points[:2]
                return True
            return super(BezierTest, self).on_touch_move(touch)


class Main(App):

    def build(self):
        from math import cos, sin, radians
        x = y = 150
        l = 100
        # Pacman !
        points = [x, y]
        for i in range(45, 360, 45):
            i = radians(i)
            points.extend([x + cos(i) * l, y + sin(i) * l])
        return BezierTest(points=points, loop=True)

if __name__ == '__main__':
    Main().run()

