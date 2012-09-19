# -*- coding: utf-8 -*-

from kivy.properties import StringProperty, ListProperty, \
        NumericProperty, ObjectProperty, BooleanProperty, DictProperty
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.logger import Logger

from math import sin, pi, pow, sqrt, log
import os 

base_dir = os.path.dirname(__file__)


class CarouselImage(Widget):
    carousel = ObjectProperty(None)
    index = NumericProperty(0)
    source = StringProperty('')
    t_delta = NumericProperty(0) #angle inside parent
    opacity = NumericProperty(1)
    border = NumericProperty(0.1)
    serie = BooleanProperty(False)
    ratio = NumericProperty(0)
    main = BooleanProperty(False)

    def __init__(self,**kwargs):
        super(CarouselImage, self).__init__(**kwargs)
        #add background rectangle
        if self.serie == True : 
            source = os.path.join(base_dir, 'serie-image_cropped.png')
        else : 
            source = os.path.join(base_dir, 'photo-ombre2.png') 
        self.rect = Image(
                          source = source,
                          keep_ratio = False,
                          allow_stretch = True
                          )
        #add image
        self.im = Image(
                        source =self.source,
                        allow_stretch = True, 
                        )
        self.add_widget(self.im)
        self.add_widget(self.rect) 
        #calculate ratio
        self.ratio = self.im.image_ratio
        #update once
        Clock.schedule_interval(self.update2,0)
        #bind
        self.bind(pos = self.update)

    def update(self,instance,val):
        w,h = size = self.size
        x,y = pos = self.pos
        b = self.border
        if self.serie :
            b += .09 
        alpha = self.carousel.opacity
        o = self.opacity 
        if o <= 0.17 and o > 0: 
            alpha = alpha * abs(1 - o*10)
        if o <= 0.1 : 
            alpha = 0
            o = 0
        if self.main: o += 0.3
        c = [o,o,o,alpha]
        self.rect.size = size
        if self.serie :
            self.rect.width -= self.width * .08 
        self.rect.pos = pos
        self.rect.color = c
        self.im.size = ( round(w*(1-2*b),0), round(h*(1-2*b),0) )
        self.im.pos = ( round(x + w*b,0), round(y + h*b,0))
        if self.serie : 
            self.im.x -= self.im.width * .1
        self.im.color = c

    def update2(self,dt):
        self.update(1,1)


class CarouselImage2(CarouselImage): 
    #enhanced with a 'play' image over the image when video
    is_video = BooleanProperty(False)

    def __init__(self,**kwargs):
        super(CarouselImage2, self).__init__(**kwargs)
        if self.source.rsplit('.')[1] == 'png' : 
            self.is_video = True 
            self.play = Image(source = 'play.png')
            self.add_widget(self.play)

    def update(self,instance,val):
        super(CarouselImage2, self).update(instance,val)
        if not self.is_video : return
        self.play.size = (50,50)
        self.play.pos = self.pos[0] + self.size[0] * 0.5 - self.play.size[0] * 0.5, self.pos[1] + self.size[1] * 0.5 - self.play.size[1] * 0.5
        self.play.color = self.im.color 


class ImageCarousel(Widget):
    sources = ListProperty( [ ['1.jpg'],['2.jpg'],['3.jpg'],['4.jpg'], ['1.jpg'],['2.jpg'] ] ) #Sources of images as a list
    opacity = NumericProperty(0)
    speed_ratio = NumericProperty(0.2)
    display_size = ObjectProperty( (400,200) ) #only height is important
    speed = NumericProperty(0) #deals with rotation kinetic
    max_speed = NumericProperty(0.6)
    decc = NumericProperty(1) #speed must be nul
    vertical = BooleanProperty(False) #images are vertical
    symetry = NumericProperty(1) #left -1, right 1 #behaves like a symetry
    translation = NumericProperty(0) #translate the carousel display compare to its touch area (not the touch area)
    fatter = BooleanProperty(True) #if not many images in sources, display them all permanently #Careful : sources are duplicated
    direct_access_mode = BooleanProperty(False) #you can only validate the front image (the lighty one) if False, any if True but not move the carousel by grabbing it then
    elliptic_ratio = NumericProperty(.7)#rotation elliptic width coefficient (circle if 1) 

    def __init__(self,**kwargs):
        super(ImageCarousel, self).__init__(**kwargs)
        self.size_hint = (None, None)
        self.reset()
        Clock.schedule_interval(self.update, 0)
        self.register_event_type('on_item_touched')
        
    def reset(self):
        self.touches = {}
        self.n = n = len(self.sources)#nb of elements     
        self.h = self.display_size[1]/2. #height/2.#Average height of an image
        self.rot = 0 #current rotation value (then converted to radians)
        self.direction = 0
        self.images = {}
        self.front_image_index = 0
        #load images:
        index = 0
        #Specific case of making it look fatter
        if self.fatter and n <= 8:
            s = self.sources
            for i in range(0,len(s)): 
                self.sources.append(s[i])
            self.n = 2*n 
            n = self.n
        #load images    
        for i in self.sources :
            t_delta = 2*pi/float(n) * index #angle between images 
            if len(i) > 1 : 
                serie = True
            else : 
                serie = False
            self.images[index] = CarouselImage2(source = i[0], t_delta = t_delta, index = index, carousel =self, serie = serie )
            self.add_widget(self.images[index])
            index += 1
        self.moved = True
        self.update(0)

    def on_touch_down(self,touch):
        id = touch.id
        x,y = touch.pos
        if self.collide_point(x,y):
            if len(self.touches) == 0:
                self.touches[id] = touch
                #self.last_touch = touch
                self.decc = 0
        #check if collides with a child 
        for i in self.children:
            if isinstance(i, CarouselImage):
                if i.collide_point(x,y):
                    self.on_item_touched(i.index, i.source) 
                    return True
        super(ImageCarousel, self).on_touch_down(touch)

    def on_touch_up(self,touch):
        id = touch.id
        if id in self.touches.keys() :
            self.decc = self.speed
            self.speed = 0 
            del( self.touches[id] )
        super(ImageCarousel, self).on_touch_up(touch)

    def on_touch_move(self,touch):
        if touch.id in self.touches.keys():
            self.process_touch_move(touch)
        super(ImageCarousel, self).on_touch_move(touch)
        
    def update_image(self,index):
        d = self.symetry #orientation left or right
        #translate images in order to reach the border of the widget 
        if d == 1 :
            translation = -self.display_size[1]*.5 + 10 + self.translation 
        else : 
            translation = self.display_size[1]*.5 - 10 + self.translation
        image = self.images[index]
        t = image.t_delta
        rot = self.rot + t
        n = self.n
        #width ratio of the rotation circle
        r = 1 
        if n <= 5 :
            if d == 1: 
                a = .15 
            else : a = .11 
            r = r - a * (6 - n)
        #pos
        s = sin(rot) *r
        y = s * self.h
        s = sin(d*(rot + pi/2.)) *r
        ratio = self.elliptic_ratio #0.66 #narrow or enlarge the elliptic rotation width (circle if 1) 
        delta_x = s * self.h * ratio
        v = 1
        if self.vertical: 
            v = 0
        x = v*(self.h + d*delta_x)
        x += self.x + translation
        if self.symetry == -1: 
            x -= image.width
        y += self.y + self.height / 2.
        image.pos = (x,y)
        #size 
        h = self.h * ( sin( d*(rot + pi/2.) ) + 0.7 )#+3/2. )
        ratio = self.display_size[1]/h #self.height/h
        #for display, only height actually counts in order to get a square 
        w = self.display_size[1] / ratio #height / ratio        
        #adjust ratio to image now
        ratio = image.ratio
        if ratio != 1:
            if ratio >1:
                h = w / ratio
            else : 
                w = h * ratio
        image.size = (w,h)
        #opacity
        o = 0.1 + (0.4*d*sin(rot + pi/2.) )
        if self.front_image_index == index :
            image.main = True
        else : 
            image.main = False
        image.opacity = o       

    def update(self, dt):
        #deccelerate
        self.deccelerate()
        
        if self.moved == False : return
        list = []
        for index,image in self.images.iteritems():
            self.update_image(index)
            list.append( (image.height*image.width,index) )
        #biggest is closest, put its widget on top
        #list of index ordered by height
        for i in sorted(list):
            image = self.images[ i[1] ]
            self.remove_widget(image)
            self.add_widget(image)
        #make the front one brighter
        self.front_image_index = f = sorted(list)[-1][1]
        image = self.images[ f ]
        image.opacity += 0.1
        self.moved = False
        #rotate
        s = self.speed
        if s == 0 : 
            s = self.decc
        o = self.symetry 
        if self.direction > 0 : 
            self.rot += o*s*self.speed_ratio 
        else : 
            self.rot -= o*s*self.speed_ratio
        self.moved = True 

    def process_touch_move(self,touch):
        #deduce direction and distance
        t = touch 
        self.direction = - t.dx + t.dy
        speed = (abs(t.dsx) + abs(t.dsy))*60
        if speed > self.max_speed : 
            speed = self.max_speed
        self.speed = speed 
            
    def deccelerate(self):
        s = self.decc
        if s >0 : 
            s -= .02
        else : 
            s = 0
        self.decc = s
        
    def on_item_touched(self, index, source):
        Logger.debug('Carousel: image index selected %s within %s' % (str(index), str(self.sources)) )
        if self.front_image_index == index :
            Logger.debug('Carousel: Front image was touched = %s' % source)
            #do something
            """
            parent = self.parent
            if parent is not None :
                parent.display_content2(self,index, source)
            """
        else : 
            if self.direct_access_mode :
                self.images[self.front_image_index].main = False  
                self.front_image_index = index
                self.images[index].main = True
                self.on_item_touched(index, source)

    def move(self):
        self.speed = 0
        self.decc = 1    

#################################################################################################

from kivy.factory import Factory
Factory.register('CarouselImage', cls=CarouselImage)
Factory.register('CarouselImage2', cls=CarouselImage2)
Factory.register('ImageCarousel', cls=ImageCarousel)

######################################## APP LAUNCHER ###########################################
import kivy
kivy.require('1.0.8')
from kivy.app import App

class ImageCarouselApp(App):

    def build(self):
        self.car = ImageCarousel(size = (800,800), display_size = (400,400), pos= (100,100), direct_access_mode = False, symetry = 1, opacity = 1)
        return self.car


if __name__ in ('__main__','__android__'):
    ImageCarouselApp().run()

    
