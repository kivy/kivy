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


try:
    import kivy
except ImportError:
    raise ImportError("this backend requires Kivy to be installed.")

from kivy.graphics.texture import Texture
from kivy.graphics import Rectangle
from kivy.uix.widget import Widget
from kivy.base import EventLoop
from kivy.core.image import Image

from kivy.ext.mpl.backend_kivy import FigureCanvasKivy, FigureManagerKivy, \
                                _create_App

# try:
#     kivy.require('1.9.0')
# except AttributeError:
#     raise ImportError(
#         "kivy version too old -- it must have require_version")

# EventLoop.ensure_window()
register_backend('png', 'backend_kivyagg', 'PNG File Format')

_debug = True

'''
Backend KivyAgg
===================
This set of classes implement an interface in Kivy for matplotlib.
It uses the canonical Agg renderer which returns a static image,
which is placed on a texture in Kivy.::
'''


def new_figure_manager(num, *args, **kwargs):
    """
    Create a new figure manager instance
    """
    FigureClass = kwargs.pop('FigureClass', Figure)
    thisFig = FigureClass(*args, **kwargs)
    return new_figure_manager_given_figure(num, thisFig)


def new_figure_manager_given_figure(num, figure):
    """
    Create a new figure manager instance for the given figure.
    """
    canvas = FigureCanvasKivyAgg(figure)
    manager = FigureManagerKivy(canvas, num)
    return manager


class FigureCanvasKivyAgg(FigureCanvasKivy, FigureCanvasAgg, Widget):
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
        #super(FigureCanvasKivyAgg, self).__init__(figure, **kwargs)
        Widget.__init__(self, **kwargs)
        FigureCanvasKivy.__init__(self, figure)
        FigureCanvasAgg.__init__(self, figure)
        self.img = None
        self.img_texture = None
        self.blit()
        _create_App(self)

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
            oldw, oldh = self.img_texture.size
            if oldw != w or oldh != h:
                update = True
        if update or self.img_texture is None:
            texture = Texture.create(size=(w, h))
            texture.flip_vertical()
            with self.canvas:
                Rectangle(texture=texture, pos=self.pos, size=(w, h))
        else:
            texture = self.img_texture
        texture.blit_buffer(buf_rgba, colorfmt='rgba', bufferfmt='ubyte')
        self.img_texture = texture


class FigureManagerKivyAgg(FigureManagerBase):
    '''
    Wrap everything up into a window for the pylab interface
    For non interactive backends, the base class does all the work
    '''
    def show(self):
        FigureManagerBase.show(self)

    def destroy(self):
        FigureManagerBase.destroy(self)

########################################################################
#
# Now just provide the standard names that backend.__init__ is expecting
#
########################################################################

FigureCanvas = FigureCanvasKivyAgg
FigureManager = FigureManagerKivyAgg
show = kivy.ext.mpl.backend_kivy.show
