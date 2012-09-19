# -*- coding: utf-8 -*-
import kivy
kivy.require('1.0.8')
from kivy.app import App

from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout 
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.clock import Clock
from kivy.lang import Builder

from kivy.graphics.transformation import Matrix
from kivy.vector import Vector
from math import radians
import os

base_dir = os.path.dirname(__file__)
kv = os.path.join(base_dir, 'main.kv')
Builder.load_file(kv)


####################################### ZOOM IMAGE  ##########################################

class ZIScatter(Scatter):
    zoom_image = ObjectProperty( Widget() )
    init_pos = ObjectProperty( (75,70) )

    def __init__(self,**kwargs):
        super(ZIScatter, self).__init__(**kwargs)
        Clock.schedule_interval(self.clear_canvas, 0)
        Clock.schedule_interval(self.control_pos, 0)

    def clear_canvas(self, dt):
        self.canvas.clear() 

    def control_pos(self, dt):
        if self.scale <= 1.1 : 
            self.reset()
            pass  

    def transform_with_touch(self, touch):
        init_pos = self.center
        init_scale = self.scale
        init_touch_len = len(self._touches)

        # just do a simple one finger drag
        if len(self._touches) == 1 and self.scale >1.05 : #THIS IS NOT IN ORIGINAL SCATTER:
            # _last_touch_pos has last pos in correct parent space,
            # just like incoming touch
            dx = (touch.x - self._last_touch_pos[touch][0]) \
                    * self.do_translation_x
            dy = (touch.y - self._last_touch_pos[touch][1]) \
                    * self.do_translation_y
            self.apply_transform(Matrix().translate(dx, dy, 0))

        elif len(self._touches) == 1 and self.scale <1.05 : #THIS IS NOT IN ORIGINAL SCATTER:
            return

        else : #TO AVOID RETURN IN ORIGINAL SCATTER
            # we have more than one touch...
            points = [Vector(self._last_touch_pos[t]) for t in self._touches]

            # we only want to transform if the touch is part of the two touches
            # furthest apart! So first we find anchor, the point to transform
            # around as the touch farthest away from touch
            anchor = max(points, key=lambda p: p.distance(touch.pos))

            # now we find the touch farthest away from anchor, if its not the
            # same as touch. Touch is not one of the two touches used to transform
            farthest = max(points, key=anchor.distance)
            if points.index(farthest) != self._touches.index(touch):
                return

            # ok, so we have touch, and anchor, so we can actually compute the
            # transformation
            old_line = Vector(*touch.ppos) - anchor
            new_line = Vector(*touch.pos) - anchor

            angle = radians(new_line.angle(old_line)) * self.do_rotation
            self.apply_transform(Matrix().rotate(angle, 0, 0, 1), anchor=anchor)

            if self.do_scale:
                scale = new_line.length() / old_line.length()
                new_scale = scale * self.scale
                if new_scale < self.scale_min or new_scale > self.scale_max:
                    scale = 1.0
                self.apply_transform(Matrix().scale(scale, scale, scale),
                                 anchor=anchor)

        #avoid scatter leaving its box
        s = self.scale
        x, y = self.pos
        w, h = self.size
        #check every corner
        limitx = limity = False
        if (x > self.zoom_image.x or x + w*s < self.zoom_image.x + self.zoom_image.width) :
            limitx = True
        if (y > self.zoom_image.y or y + h*s < self.zoom_image.y + self.zoom_image.height):  
            limity = True
        if limitx or limity:  
            #cancel previous apply_transform            
            if init_touch_len == 1:
                ddx = ddy = 0
                if limitx: ddx = - dx
                if limity: ddy = - dy
                self.apply_transform(Matrix().translate(ddx, ddy, 0))
            else:
                if self.do_scale:
                    self.apply_transform(Matrix().scale(scale/init_scale, scale/init_scale, scale/init_scale),
                                 anchor=anchor)  
    
    def on_touch_down(self, touch):
        x, y = touch.x, touch.y
        # if the touch isnt on the widget we do nothing
        if self.zoom_image.collide_point(x, y):
            if touch.is_double_tap : 
                self.reset()
            super(ZIScatter, self).on_touch_down(touch)

    def on_touch_up(self, touch):
                
        ###TAKEN FROM ORIGINAL SCATTER
        x, y = touch.x, touch.y
        # if the touch isnt on the widget we do nothing, just try children
        if self.zoom_image.collide_point(x, y): #MODIFIED ORIGINAL SCATTER !!   
          if not touch.grab_current == self:
            touch.push()
            touch.apply_transform_2d(self.to_local)
            if super(Scatter, self).on_touch_up(touch):
                touch.pop()
                return True
            touch.pop()

        # remove it from our saved touches
        if touch in self._touches and touch.grab_state:
            touch.ungrab(self)
            del self._last_touch_pos[touch]
            self._touches.remove(touch)

        # stop propagating if its within our bounds
        if self.collide_point(x, y):
            pass#return True #MODIFIED ORIGINAL SCATTER !!  
        
       
    def reset(self):
        self.center = self.init_pos
        self.scale = 1    


class ZoomImage(FloatLayout):
    scatter = ObjectProperty( ZIScatter() )
    source = StringProperty( '105_01.jpg' )
    im = ObjectProperty( None )
    opacity = NumericProperty(1)
    
    def __init__(self,**kwargs):
        super(ZoomImage, self).__init__(**kwargs)
        self.bind(source = self.refresh)    

    def reset(self):
        self.scatter.reset()

    def refresh(self, instance, val):
        self.im.source = self.source
    


from kivy.factory import Factory
Factory.register('ZoomImage', cls=ZoomImage)
Factory.register('ZIScatter', cls=ZIScatter)

######################################## APP LAUNCHER ###########################################

class ZiApp(App):

    def build(self):
        self.zoomi = ZoomImage(size = (350,350), pos = (100,200) )
        return self.zoomi


if __name__ in ('__main__','__android__'):
    ZiApp().run()


