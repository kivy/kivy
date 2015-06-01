from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.properties import (NumericProperty, ListProperty, BooleanProperty, DictProperty)
from random import random
from kivy.graphics import Color, Rectangle, Point, GraphicException, Ellipse, Line, SmoothLine

from math import sqrt
from colorsys import hsv_to_rgb
from gi.overrides.GLib import Source
from stroke import Stroke

from enum import Enum, unique

from stroke import Stroke
from point import Point



class InkCanvas(FloatLayout):
    
    def __init__(self, **kwargs):
        FloatLayout.__init__(self, **kwargs)
        self.mode = self.Mode.draw
        self.strokes = []
    
    def on_touch_down(self, touch):
        #capture touch and add group_id to stroke to associate it
        ud = touch.ud
        ud['group'] = g = str(touch.uid)

        if self.mode == self.Mode.draw:
            color = (random(), random(), random())
            stroke = Stroke(group_id=g)
            stroke.points.append(Point(touch.x, touch.y))
            touch.ud['stroke'] = stroke
            '''Calculate point size according to pressure'''
            #if 'pressure' in touch.profile:
            with self.canvas:
                Color(*color)
                touch.ud['line'] = Line(points = (touch.x, touch.y), width = 1.0)
        elif self.mode == self.Mode.erase:
            #find points and delete them
            pass
    
    def on_touch_move(self, touch):
        '''If pressure changed recalculate the point size'''
        if self.mode == self.Mode.draw:
            touch.ud['stroke'].points.append(Point(touch.x,touch.y))
            touch.ud['line'].points += [touch.x, touch.y]
        elif self.mode == self.Mode.erase:
            pass

    def on_touch_up(self, touch):
        #Bug the touch up is raised even out of the bounds of inkcanvas.
        if self.mode == self.Mode.draw:
            self.strokes.append(touch.ud['stroke'])
            print self.strokes
            if touch.grab_current is not self:
                return
            touch.ungrab(self)
        elif self.mode == self.Mode.erase:
            pass
        print "On touch up"
        #Raise event when created a new Stroke
    
    def remove_stroke(self):
        pass
    
    @unique
    class Mode(Enum):
        draw = 1
        erase = 2
        touch = 3