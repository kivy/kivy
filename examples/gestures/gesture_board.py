#!/usr/bin/env python

from kivy.app import App

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Line
from kivy.gesture import Gesture, GestureDatabase

from my_gestures import cross, circle, check, square

def simplegesture(name, point_list):
    """
    A simple helper function
    """
    g = Gesture()
    g.add_stroke(point_list)
    g.normalize()
    g.name = name
    return g

class GestureBoard(FloatLayout):
    """
    Our application main widget, derived from touchtracer example, use data
    constructed from touches to match symboles loaded from my_gestures.

    """
    def __init__(self, *args, **kwargs):
        super(GestureBoard, self).__init__()
        self.gdb = GestureDatabase()

        # add pre-recorded gestures to database
        self.gdb.add_gesture(cross)
        self.gdb.add_gesture(check)
        self.gdb.add_gesture(circle)
        self.gdb.add_gesture(square)

    def on_touch_down(self, touch):
        # start collecting points in touch.ud
        # create a line to display the points
        userdata = touch.ud
        with self.canvas:
            Color(1, 1, 0)
            d = 30.
            Ellipse(pos=(touch.x - d/2, touch.y - d/2), size=(d, d))
            userdata['line'] = Line(points=(touch.x, touch.y))
        return True

    def on_touch_move(self, touch):
        # store points of the touch movement
        try:
            touch.ud['line'].points += [touch.x, touch.y]
            return True
        except (KeyError), e:
            pass

    def on_touch_up(self, touch):
        # touch is over, display informations, and check if it matches some
        # known gesture.
        g = simplegesture(
                '',
                zip(touch.ud['line'].points[::2], touch.ud['line'].points[1::2])
                )
        # print the gesture representation, you can use that to add
        # gestures to my_gestures.py
        print "gesture representation:", self.gdb.gesture_to_str(g)

        # print match scores between all known gestures
        print "cross:", g.get_score(cross)
        print "check:", g.get_score(check)
        print "circle:", g.get_score(circle)
        print "square:", g.get_score(square)

        # use database to find the more alike gesture, if any
        g2 = self.gdb.find(g, minscore=0.70)

        print g2
        if g2:
            if g2[1] == circle: print "circle"
            if g2[1] == square: print "square"
            if g2[1] == check: print "check"
            if g2[1] == cross: print "cross"

        # erase the lines on the screen, this is a bit quick&dirty, since we
        # can have another touch event on the way...
        self.canvas.clear()

class DemoGesture(App):
    def build(self):
        return GestureBoard()

if __name__ == '__main__':
    DemoGesture().run()

