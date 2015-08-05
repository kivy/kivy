'''
Backend KivyAgg
=====

.. versionadded:: 1.9.1

.. image:: images/backend_agg_example.jpg
    :align: right

The :class:`FigureCanvasKivyAgg` widget is used to create a matplotlib graph.
will cover the whole "parent" window. When you are creating a popup, you
must at least set a :attr:`Popup.title` and :attr:`Popup.content`.

Remember that the default size of a Widget is size_hint=(1, 1). If you don't
want your popup to be fullscreen, either use size hints with values less than 1
(for instance size_hint=(.8, .8)) or deactivate the size_hint and use
fixed size attributes.


.. versionchanged:: 1.4.0
    The :class:`Popup` class now inherits from
    :class:`~kivy.uix.modalview.ModalView`. The :class:`Popup` offers a default
    layout with a title and a separation bar.

Examples
--------

Example of a simple 400x400 Hello world popup::

    popup = Popup(title='Test popup',
        content=Label(text='Hello world'),
        size_hint=(None, None), size=(400, 400))

By default, any click outside the popup will dismiss/close it. If you don't
want that, you can set
:attr:`~kivy.uix.modalview.ModalView.auto_dismiss` to False::

    popup = Popup(title='Test popup', content=Label(text='Hello world'),
                  auto_dismiss=False)
    popup.open()

To manually dismiss/close the popup, use
:attr:`~kivy.uix.modalview.ModalView.dismiss`::

    popup.dismiss()

Both :meth:`~kivy.uix.modalview.ModalView.open` and
:meth:`~kivy.uix.modalview.ModalView.dismiss` are bindable. That means you
can directly bind the function to an action, e.g. to a button's on_press::

    # create content and add to the popup
    content = Button(text='Close me!')
    popup = Popup(content=content, auto_dismiss=False)

    # bind the on_press event of the button to the dismiss function
    content.bind(on_press=popup.dismiss)

    # open the popup
    popup.open()


Popup Events
------------

There are two events available: `on_open` which is raised when the popup is
opening, and `on_dismiss` which is raised when the popup is closed.
For `on_dismiss`, you can prevent the
popup from closing by explictly returning True from your callback::

    def my_callback(instance):
        print('Popup', instance, 'is being dismissed but is prevented!')
        return True
    popup = Popup(content=Label(text='Hello world'))
    popup.bind(on_dismiss=my_callback)
    popup.open()

'''

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
    canvas.draw()
    manager = FigureManagerKivy(canvas, num)
    _create_App(canvas, manager.toolbar.actionbar)
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

    '''
    FigureCanvasKivyAgg
    ===================
    The ::
        # Create a Point
        pointA = Point(2,3)
        pointB = Point(4,5)
        distance = pointA.distance_to(pointB)
    '''

    def __init__(self, figure, **kwargs):
        if _debug:
            print('FigureCanvasKivyAgg: ', figure)
        self.figure = figure
        super(FigureCanvasKivyAgg, self).__init__(figure=self.figure, **kwargs)
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

''' Standard names that backend.__init__ is expecting '''
FigureCanvas = FigureCanvasKivyAgg
FigureManager = FigureManagerKivy
show = kivy.ext.mpl.backend_kivy.show
