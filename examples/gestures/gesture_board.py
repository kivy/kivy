#!/usr/bin/env python

from kivy.app import App

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Line
from kivy.gesture import Gesture, GestureDatabase

from my_gestures import cross, circle, check, square

def simplegesture(name, point_list):
    g = Gesture()
    g.add_stroke(point_list)
    g.normalize()
    g.name = name
    return g

class dispatch_before(object):
    """
    this is a decorator with arguments
    """
    def __init__(self, type_of_touch):
        self.type_of_touch = type_of_touch

    def __call__(self, f):
        def wrapped(instance, touch):
            if instance.collide_point(*touch.pos):
                for c in instance.children:
                    if c.dispatch(self.type_of_touch, touch):
                        return True

                f(instance, touch)

        return wrapped


class GestureBoard(FloatLayout):
    def __init__(self, *args, **kwargs):
        self.gdb = GestureDatabase()
        super(GestureBoard, self).__init__()
        self.gdb.add_gesture(cross)
        self.gdb.add_gesture(check)
        self.gdb.add_gesture(circle)
        self.gdb.add_gesture(square)

    @dispatch_before('on_touch_down')
    def on_touch_down(self, touch):
        userdata = touch.ud
        with self.canvas:
            Color(1, 1, 0)
            d = 30.
            Ellipse(pos=(touch.x - d/2, touch.y - d/2), size=(d, d))
            userdata['line'] = Line(points=(touch.x, touch.y))
        return True

    @dispatch_before('on_touch_move')
    def on_touch_move(self, touch):
        try:
            touch.ud['line'].points += [touch.x, touch.y]
            return True
        except (KeyError), e:
            pass

    @dispatch_before('on_touch_up')
    def on_touch_up(self, touch):
        try:
            g = simplegesture(
                    '',
                    zip(touch.ud['line'].points[::2], touch.ud['line'].points[1::2])
                    )
            print "gesture representation:", self.gdb.gesture_to_str(g)
            print "cross:", g.get_score(cross)
            print "check:", g.get_score(check)
            print "circle:", g.get_score(circle)
            print "square:", g.get_score(square)

            g2 = self.gdb.find(g, minscore=0.70)

            print g2
            if g2:
                if g2[1] == circle: print "circle"
                if g2[1] == square: print "square"
                if g2[1] == check: print "check"
                if g2[1] == cross: print "cross"
        except (KeyError), e:
            pass

        self.canvas.clear()

class DemoGesture(App):
    def build(self):
        return GestureBoard()

if __name__ == '__main__':
    DemoGesture().run()

