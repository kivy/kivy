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

class InkCanvasBehavior(object):
    
    '''InkCanvas behavior.
    
    :Events:
        `on_touch_down`
            Fired when the element is touched.
        `on_touch_move`
            Fired when the element keeps being touched while the finger moves.
        `on_touch_up`
            Fired when a touch is lifted up.
    
    .. versionadded:: 1.9.0
    
    '''
    
    def __init__(self, **kwargs):
        super(InkCanvasBehavior, self).__init__(**kwargs)
        self.mode = self.Mode.draw
        self.strokes = []
    
    def on_touch_down(self, touch):
        #capture touch and add group_id to stroke to associate it
        if super(InkCanvasBehavior, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos):
            touch.grab(self)
            ud = touch.ud
            ud['group'] = g = str(touch.uid)
            pt = Point(touch.x, touch.y)
            if self.mode == self.Mode.draw:
                strk = Stroke(group_id=g)
                strk.isHighlighter(0.5)
                strk.points.append(pt)
                touch.ud['stroke'] = strk
                '''Calculate point size according to pressure'''
                #if 'pressure' in touch.profile:
                with self.canvas:
                    Color(*strk.color)
                    touch.ud['line'] = Line(points = (pt.X, pt.Y), width = 2.0, group=g)
            elif self.mode == self.Mode.erase:
                self.remove_stroke(pt)
    
    def on_touch_move(self, touch):
        '''If pressure changed recalculate the point size'''
        if super(InkCanvasBehavior, self).on_touch_move(touch):
            return True
        if touch.grab_current is self:
            pt = Point(touch.x, touch.y)
            if self.mode == self.Mode.draw:
                touch.ud['stroke'].points.append(pt)
                touch.ud['line'].points += [pt.X, pt.Y]
            elif self.mode == self.Mode.erase:
                self.remove_stroke(pt) 

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            if self.mode == self.Mode.draw:
                self.strokes.append(touch.ud['stroke'])
            elif self.mode == self.Mode.erase:
                pass
            touch.ungrab(self)
            #Fire event when created a new Stroke
        else:
            return super(InkCanvasBehavior, self).on_touch_up(touch)
        

    def remove_stroke(self, pt):
        for stroke in self.strokes:
            if stroke.hit_test(pt):
                self.canvas.remove_group(stroke.group_id)
    
    @unique
    class Mode(Enum):
        '''Diferent Modes for the InkCanvas, Allows for drawing, erase and touch.        
        '''
        draw = 1
        erase = 2
        touch = 3