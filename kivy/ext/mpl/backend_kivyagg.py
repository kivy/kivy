"""
This is a fully functional do nothing backend to provide a template to
backend writers. It is fully functional in that you can select it as
a backend with

  import matplotlib
  matplotlib.use('Template')

and your matplotlib scripts will (should!) run without error, though
no output is produced. This provides a nice starting point for
backend writers because you can selectively implement methods
(draw_rectangle, draw_lines, etc...) and slowly see your figure come
to life w/o having to have a full blown implementation before getting
any results.

Copy this to backend_xxx.py and replace all instances of 'template'
with 'xxx'. Then implement the class methods and functions below, and
add 'xxx' to the switchyard in matplotlib/backends/__init__.py and
'xxx' to the backends list in the validate_backend methon in
matplotlib/__init__.py and you're off. You can use your backend with::

  import matplotlib
  matplotlib.use('xxx')
  from pylab import *
  plot([1,2,3])
  show()

matplotlib also supports external backends, so you can place you can
use any module in your PYTHONPATH with the syntax::

  import matplotlib
  matplotlib.use('module://my_backend')

where my_backend.py is your module name. This syntax is also
recognized in the rc file and in the -d argument in pylab, e.g.,::

  python simple_plot.py -dmodule://my_backend

If your backend implements support for saving figures (i.e. has a print_xyz()
method) you can register it as the default handler for a given file type

  from matplotlib.backend_bases import register_backend
  register_backend('xyz', 'my_backend', 'XYZ File Format')
  ...
  plt.savefig("figure.xyz")

The files that are most relevant to backend_writers are

  matplotlib/backends/backend_your_backend.py
  matplotlib/backend_bases.py
  matplotlib/backends/__init__.py
  matplotlib/__init__.py
  matplotlib/_pylab_helpers.py

Naming Conventions

  * classes Upper or MixedUpperCase

  * varables lower or lowerUpper

  * functions lower or underscore_separated

"""

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

try:
    import kivy
    from kivy.graphics.texture import Texture
    from kivy.graphics import Rectangle
    from kivy.uix.widget import Widget
    from kivy.base import EventLoop
except ImportError:
    raise ImportError("this backend requires Kivy to be installed.")

try:
    kivy.require('1.9.0')
except AttributeError:
    raise ImportError(
        "kivy version too old -- it must have require_version")

from PIL import Image
EventLoop.ensure_window()

_debug = True


def new_figure_manager(num, *args, **kwargs):
    """
    Create a new figure manager instance
    """
    # if a main-level app must be created, this (and
    # new_figure_manager_given_figure) is the usual place to
    # do it -- see backend_wx, backend_wxagg and backend_tkagg for
    # examples. Not all GUIs require explicit instantiation of a
    # main-level app (egg backend_gtk, backend_gtkagg) for pylab
    FigureClass = kwargs.pop('FigureClass', Figure)
    thisFig = FigureClass(*args, **kwargs)
    return new_figure_manager_given_figure(num, thisFig)


def new_figure_manager_given_figure(num, figure):
    """
    Create a new figure manager instance for the given figure.
    """
    canvas = FigureCanvasKivyAgg(figure)
    manager = FigureManagerKivyAgg(canvas, num)
    return manager


class FigureCanvasKivyAgg(FigureCanvasAgg, Widget):
    """
    The canvas the figure renders into. Calls the draw and print fig
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
        FigureCanvasAgg.__init__(self, figure)
        Widget.__init__(self, **kwargs)
        self.figure = figure
        self.blit()

    def draw(self):
        """
        Draw the figure using the renderer
        """
        FigureCanvasAgg.draw(self)
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
            buf_rgba = reg.to_string_argb()
        texture = Texture.create(size=(w, h))
        texture.blit_buffer(buf_rgba, colorfmt='rgba', bufferfmt='ubyte')
        texture.flip_vertical()
        with self.canvas:
            Rectangle(texture=texture, pos=self.pos, size=(w, h))
        #renderer = RendererKivyAgg(self.figure.dpi)
        #self.figure.draw(renderer)

    # You should provide a print_xxx function for every file format
    # you can write.

    # If the file type is not in the base set of filetypes,
    # you should add it to the class-scope filetypes dictionary as follows:
    filetypes = FigureCanvasBase.filetypes.copy()
    filetypes['foo'] = 'My magic Foo format'

    def blit(self, bbox=None):
        # If bbox is None, blit the entire canvas to the widget. Otherwise
        # blit only the area defined by the bbox.
        self.blitbox = bbox

    def print_foo(self, filename, *args, **kwargs):
        """
        Write out format foo. The dpi, facecolor and edgecolor are restored
        to their original values after this call, so you don't need to
        save and restore them.
        """
        l, b, w, h = self.figure.bbox.bounds
        im = Image.frombuffer('RGBA', (w, h), self.get_renderer().buffer_rgba(),
                              "raw", "RGBA", 0, 1)
        im.save(filename)

    def get_default_filetype(self):
        return 'foo'


class FigureManagerKivyAgg(FigureManagerBase):
    """
    Wrap everything up into a window for the pylab interface

    For non interactive backends, the base class does all the work
    """
    pass

########################################################################
#
# Now just provide the standard names that backend.__init__ is expecting
#
########################################################################

FigureCanvas = FigureCanvasKivyAgg
FigureManager = FigureManagerKivyAgg
