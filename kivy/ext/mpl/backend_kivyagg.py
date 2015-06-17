from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import six

import matplotlib
from matplotlib._pylab_helpers import Gcf
from matplotlib.backend_bases import RendererBase, GraphicsContextBase,\
    FigureManagerBase, FigureCanvasBase
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backend_bases import register_backend
from kivy.uix.behaviors import FocusBehavior

try:
    import kivy
except ImportError:
    raise ImportError("this backend requires Kivy to be installed.")

from kivy.graphics.texture import Texture
from kivy.graphics import Rectangle
from kivy.uix.widget import Widget
from kivy.base import EventLoop
from kivy.core.image import Image

try:
    kivy.require('1.9.0')
except AttributeError:
    raise ImportError(
        "kivy version too old -- it must have require_version")

EventLoop.ensure_window()
register_backend('png', 'backend_kivyagg', 'PNG File Format')

_debug = True

'''
Backend KivyAgg
===================
This set of classes implement an interface in Kivy for matplotlib.
It uses the canonical Agg renderer which returns a static image,
which is placed on a texture in Kivy.::
'''

class FigureCanvasKivyAgg(FigureCanvasAgg, Widget):
    """
    A widget where the figure renders into. Calls the draw and print fig
    methods, creates the renderers, etc...

    Public attribute

      figure - A Figure instance

    Note GUI templates will want to connect events for button presses,
    mouse movements and key presses to functions that call the base
    class methods button_press_event, button_release_event,
    motion_notify_event, key_press_event, and key_release_event. See,
    e.g., backend_gtk.py, backend_wx.py and backend_tkagg.py
    """

    def __init__(self, figure, **kwargs):
        if _debug:
            print('FigureCanvasKivyAgg: ', figure)
        #super(FigureCanvasKivyAgg, self).__init__(**kwargs)
        Widget.__init__(self, **kwargs)
        FigureCanvasAgg.__init__(self, figure)
        self.img = None
        self.img_texture = None
        self.blit()

    def draw(self):
        '''
        Draw the figure using the renderer
        '''
        FigureCanvasAgg.draw(self)
        update = False
        if self.blitbox is None:
            l, b, w, h = self.figure.bbox.bounds
            w, h = int(w), int(h)
            buf_rgba = self.get_renderer().buffer_rgba()
        else:
            bbox = self.blitbox
            l, b, r, t = bbox.extents
            w = int(r) - int(l)
            h = int(t) - int(b)
            t = int(b) + h
            reg = self.copy_from_bbox(bbox)
            buf_rgba = reg.to_string()
        if self.img_texture is not None:
            oldw,oldh = self.img_texture.size
            if oldw != w or oldh != h:
                update = True
        if update or self.img_texture is None:
            texture = Texture.create(size=(w, h))
            texture.flip_vertical()
        else:
            texture = self.img_texture
        texture.blit_buffer(buf_rgba, colorfmt='rgba', bufferfmt='ubyte')
        self.img_texture = texture
        with self.canvas:
            Rectangle(texture=texture, pos=self.pos, size=(w, h))
        #renderer = RendererKivyAgg(self.figure.dpi)
        #self.figure.draw(renderer)

    # You should provide a print_xxx function for every file format
    # you can write.

    # If the file type is not in the base set of filetypes,
    # you should add it to the class-scope filetypes dictionary as follows:
    filetypes = FigureCanvasBase.filetypes.copy()
    filetypes['png'] = 'My image format'

    def blit(self, bbox=None):
        '''
        If bbox is None, blit the entire canvas to the widget. Otherwise
        blit only the area defined by the bbox.
        '''
        self.blitbox = bbox

    def print_png(self, filename, *args, **kwargs):
        '''
        Write out format png. The dpi, facecolor and edgecolor are restored
        to their original values after this call, so you don't need to
        save and restore them.
        '''
        l, b, w, h = self.figure.bbox.bounds
        texture = Texture.create(size=(w, h))
        texture.blit_buffer(self.get_renderer().buffer_rgba(), colorfmt='rgba', bufferfmt='ubyte')
        texture.flip_vertical()
        img = Image(texture)
        img.save(filename)

    def get_default_filetype(self):
        return 'png'


class FigureManagerKivyAgg(FigureManagerBase):
    '''
    Wrap everything up into a window for the pylab interface
    For non interactive backends, the base class does all the work
    '''
    pass

########################################################################
#
# Now just provide the standard names that backend.__init__ is expecting
#
########################################################################

FigureCanvas = FigureCanvasKivyAgg
FigureManager = FigureManagerKivyAgg
