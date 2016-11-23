'''
Backend KivyAgg
=====

.. versionadded:: 1.9.1

.. image:: images/backend_agg_example.jpg
    :align: right

The :class:`FigureCanvasKivyAgg` widget is used to create a matplotlib graph.
The render will cover the whole are of the widget unless something different is
specified using a :meth:`blit`.
When you are creating a FigureCanvasKivyAgg widget, you must at least
initialize it with a matplotlib figure object. This class uses agg to get a
static image of the plot and then the image is render using a
:class:`~kivy.graphics.texture.Texture`.


Examples
--------

Example of a simple Hello world matplotlib App::

    fig, ax = plt.subplots()
    ax.text(0.6, 0.5, "hello", size=50, rotation=30.,
            ha="center", va="center",
            bbox=dict(boxstyle="round",
                      ec=(1., 0.5, 0.5),
                      fc=(1., 0.8, 0.8),
                      )
            )
    ax.text(0.5, 0.4, "world", size=50, rotation=-30.,
            ha="right", va="top",
            bbox=dict(boxstyle="square",
                      ec=(1., 0.5, 0.5),
                      fc=(1., 0.8, 0.8),
                      )
            )
    canvas = FigureCanvasKivyAgg(figure=fig)

The object canvas can be added as a widget into the kivy tree widget.
If a change is done on the figure an update can be performed using
:meth:`~kivy.ext.mpl.backend_kivyagg.FigureCanvasKivyAgg.draw`.::

    # update graph
    canvas.draw()

The plot can be exported to png with
:meth:`~kivy.ext.mpl.backend_kivyagg.FigureCanvasKivyAgg.print_png`, as an
argument receives the `filename`.::

    # export to png
    canvas.print_png("my_plot.png")


Backend KivyAgg Events
-----------------------

The events available are the same events available from Backend Kivy.::

    def my_callback(event):
        print('press released from test', event.x, event.y, event.button)

    fig.canvas.mpl_connect('mpl_event', my_callback)

'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

__all__ = ('FigureCanvasKivyAgg')

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
                                show, new_figure_manager

register_backend('png', 'backend_kivyagg', 'PNG File Format')

toolbar = None
my_canvas = None


def new_figure_manager_given_figure(num, figure):
    '''Create a new figure manager instance and a new figure canvas instance
       for the given figure.
    '''
    canvas = FigureCanvasKivyAgg(figure)
    manager = FigureManagerKivy(canvas, num)
    global my_canvas
    global toolbar
    toolbar = manager.toolbar.actionbar if manager.toolbar else None
    my_canvas = canvas
    return manager


class FigureCanvasKivyAgg(FigureCanvasKivy, FigureCanvasAgg):
    '''FigureCanvasKivyAgg class. See module documentation for more
    information.

    .. versionadded:: 1.9.1
    '''

    def __init__(self, figure, **kwargs):
        self.figure = figure
        self.bind(size=self._on_size_changed)
        super(FigureCanvasKivyAgg, self).__init__(figure=self.figure, **kwargs)
        self.img = None
        self.img_texture = None
        self.blit()

    def draw(self):
        '''
        Draw the figure using the agg renderer
        '''
        self.canvas.clear()
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
        texture.blit_buffer(bytes(buf_rgba), colorfmt='rgba', bufferfmt='ubyte')
        self.img_texture = texture

    filetypes = FigureCanvasKivy.filetypes.copy()
    filetypes['png'] = 'Portable Network Graphics'

    def _print_image(self, filename, *args, **kwargs):
        '''Write out format png. The image is saved with the filename given.
        '''
        l, b, w, h = self.figure.bbox.bounds
        if self.img_texture is None:
            texture = Texture.create(size=(w, h))
            texture.blit_buffer(bytes(self.get_renderer().buffer_rgba()),
                                colorfmt='rgba', bufferfmt='ubyte')
            texture.flip_vertical()
            img = Image(texture)
        else:
            img = Image(self.img_texture)
        img.save(filename)

''' Standard names that backend.__init__ is expecting '''
FigureCanvas = FigureCanvasKivyAgg
FigureManager = FigureManagerKivy
show = show
