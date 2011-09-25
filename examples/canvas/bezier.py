#!/usr/bin/env python
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.graphics import Color, Bezier, Ellipse, Line, LineWidth

class BezierTest(Widget):
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

        b = Button(text='+', pos=(300, 0))
        b.bind(on_release=self.inc)
        self.add_widget(b)

        b = Button(text='-', pos=(400, 0))
        b.bind(on_release=self.dec)
        self.add_widget(b)

        b = Button(text='+', pos=(500, 0))
        b.bind(on_release=self.inc_)
        self.add_widget(b)

        b = Button(text='-', pos=(600, 0))
        b.bind(on_release=self.dec_)
        self.add_widget(b)


    def inc(self, _):
        self.bezier.dash_offset += 1

    def dec(self, _):
        self.bezier.dash_offset -= 1

    def inc_(self, _):
        self.line.dash_offset += 1

    def dec_(self, _):
        self.line.dash_offset -= 1

    def on_touch_down(self, touch):
        if self.collide_point(touch.pos[0], touch.pos[1]):
            for i, p in enumerate(zip(self.points[::2], self.points[1::2])):
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
            if self.current_point:
                self.points[(self.current_point - 1) * 2] = touch.pos[0] - self.pos[0]
                self.points[(self.current_point - 1) * 2 + 1] = touch.pos[1] - self.pos[1]
                self.bezier.points = self.points
                self.line.points = self.points + self.points[:2]
                return True
            return super(BezierTest, self).on_touch_move(touch)


class Main(App):
    def build(self):
        layout = FloatLayout()
        layout.add_widget(BezierTest(points=[
            0, 0,
            0.1 * 100, 0.2 * 100,
            0.2 * 100, 0.3 * 100,
            0.3 * 100, 0.3 * 100,
            0.4 * 100, 0.4 * 100,
            0.5 * 100, 0.5 * 100,
            0.6 * 100, 0.6 * 100,
            0.7 * 100, 0.6 * 100,
            0.8 * 100, 0.7 * 100,
            0.9 * 100, 0.8 * 100,
            100, 100,
            0, 100], loop=True))

        return layout

if __name__ == '__main__':
    Main().run()

