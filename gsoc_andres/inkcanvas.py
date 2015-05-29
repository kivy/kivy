from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.properties import (NumericProperty, ListProperty, BooleanProperty, DictProperty)
from random import random
from kivy.graphics import Color, Rectangle, Point, GraphicException, Ellipse, Line, SmoothLine

from math import sqrt
from colorsys import hsv_to_rgb
from gi.overrides.GLib import Source
from stroke import Stroke

from stroke import Stroke
from point import Point


class InkCanvas(FloatLayout):
    
    current_stroke = None
    strokes = []
    
    def on_touch_down(self, touch):
        color = (random(), random(), random())
        p = Point(touch.x, touch.y)
        self.current_stroke = Stroke()
        self.current_stroke.points.append(p)
        '''Calculate point size according to pressure'''
        #if 'pressure' in touch.profile:
        with self.canvas:
            Color(*color)
            touch.ud['line'] = Line(points = (touch.x, touch.y))
    
    def on_touch_move(self, touch):
        '''If pressure changed recalculate the point size'''
        self.current_stroke.points.append(Point(touch.x,touch.y))
        touch.ud['line'].points += [touch.x, touch.y]
        
    def on_touch_up(self, touch):
        self.strokes.append(self.current_stroke)
        print len(self.strokes)
        if touch.grab_current is not self:
            return
        
        touch.ungrab(self)
        #Raise event when created a new Stroke
    
    def remove_stroke(self):
        pass

class InkCanvasApp(App):
    title = 'InkCanvas'
    
    def build(self):
        return InkCanvas()
    
    def on_pause(self):
        return True

if __name__ == '__main__':
    InkCanvasApp().run()