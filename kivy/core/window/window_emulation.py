
import kivy
from kivy.core import core_select_lib
from kivy.uix.scatter import ScatterPlane
from kivy.properties import AliasProperty
from kivy.config import Config
from kivy.logger import Logger
from kivy.clock import Clock


kivy.kivy_options['window'] = ('egl_rpi', 'pygame', 'sdl', 'x11')


# here we choose the class we may inherit from
WindowParent = core_select_lib('window', (
    ('egl_rpi', 'window_egl_rpi', 'WindowEglRpi'),
    ('pygame', 'window_pygame', 'WindowPygame'),
    ('sdl', 'window_sdl', 'WindowSDL'),
    ('x11', 'window_x11', 'WindowX11'),
#   ('emulation', 'window_emulation'), 
), False)


class Viewport(ScatterPlane):
    def __init__(self, win, **kwargs):

        self.win = win
        #kwargs.setdefault('size', (1920, 1080))
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('do_scale', False)
        kwargs.setdefault('do_translation', False)
        kwargs.setdefault('do_rotation', False)
        super(Viewport, self).__init__( **kwargs)
 
    def fit_to_window(self, *args):
        
        width = self.win._size[0]
        height = self.win._size[1]       
        
        if self.width < self.height: #portrait
            if width < height: #so is window   
                self.scale = width/float(self.width)
            else: #window is landscape..so rotate vieport
                self.scale = height/float(self.width)
                self.rotation = -90
        else: #landscape
            if width > height: #so is window   
                self.scale = width/float(self.width)
            else: #window is portrait..so rotate vieport
                self.scale = height/float(self.width)
                self.rotation = -90
 
        self.center = self.win._size[0] / 2., self.win._size[1] / 2
        for c in self.children:
            c.size = self.adjust_size(c)
 
    def add_widget(self, w, *args, **kwargs):
        super(Viewport, self).add_widget(w, *args, **kwargs)
        w.size = self.adjust_size(w)
        
    def adjust_size(self, widget):
        w_hint, h_hint = widget.size_hint
        width, height = self.size
        if w_hint:
            width *= w_hint
        if h_hint:
            height *= h_hint
        return width, height


class WindowEmulation(WindowParent):
    
    def __init__(self, *largs, **kw):
        self.emulation_width = int(Config.get('graphics', 'emulation_width'))
        self.emulation_height = int(Config.get('graphics', 'emulation_height'))
        self.viewport = None
        self.window_created = False
        super(WindowEmulation, self).__init__(*largs, **kw)
    
    def create_window(self, *largs):
        
        super(WindowEmulation, self).create_window(*largs)
        self.window_created = True
        
    def remove_widget(self, widget):
        if self.viewport:
            self.viewport.remove_widget(widget)
    
    def add_widget(self, widget):
        if self.viewport is None:
            self.viewport = Viewport(self, size=(self.emulation_width, self.emulation_height))
        self.viewport.add_widget(widget)
        if not len(self.children):
            super(WindowEmulation, self).add_widget(self.viewport)
        Clock.schedule_once(self.viewport.fit_to_window, -1)
        
    def on_resize(self, width, height):
        super(WindowEmulation, self).on_resize(width, height)
        self.viewport.fit_to_window()

    # make some property read-only
    def _get_viewport_width(self):
        if self.viewport:
            return self.viewport.width
        else:
            return super(WindowEmulation, self)._get_width()

    width = AliasProperty(_get_viewport_width, None, bind=('_rotation', '_size'))
    
    def _get_viewport_height(self):
        if self.viewport:
            return self.viewport.height
        else:
            return super(WindowEmulation, self)._get_height()
        
    height = AliasProperty(_get_viewport_height, None, bind=('_rotation', '_size'))

    def _get_center_of_viewport(self):
        if self.viewport:
            return self.viewport.width / 2., self.viewport.height / 2.
        else:
            return super(WindowEmulation, self)._get_center()

    center = AliasProperty(_get_center_of_viewport, None, bind=('width', 'height'))

    def _get_rotation(self):
        if self.viewport:
            return self.viewport.rotation
        else:
            return super(WindowEmulation, self)._get_rotation()

    def _set_rotation(self, x):
        if self.viewport:
            self.viewport.rotation = x
        else:
            super(WindowEmulation, self)._set_rotation(x)

    rotation = AliasProperty(_get_rotation, _set_rotation, bind=('_rotation', ))
