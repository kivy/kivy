from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import six
import os
import scipy
import matplotlib
from matplotlib._pylab_helpers import Gcf
from matplotlib.backend_bases import RendererBase, GraphicsContextBase,\
    FigureManagerBase, FigureCanvasBase, NavigationToolbar2
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
from matplotlib.backend_bases import ShowBase
from matplotlib.mathtext import MathTextParser
from matplotlib import rcParams
from hashlib import md5
from matplotlib import _png
from matplotlib.font_manager import weight_as_number

try:
    import kivy
except ImportError:
    raise ImportError("this backend requires Kivy to be installed.")

from kivy.app import App
from kivy.graphics.texture import Texture
from kivy.graphics import Rectangle
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.actionbar import ActionBar, ActionView, \
                                ActionButton, ActionToggleButton, \
                                ActionPrevious, ActionOverflow, ActionSeparator
from kivy.base import EventLoop
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Line
from kivy.graphics import Rotate, Translate
from kivy.graphics.tesselator import Tesselator
from kivy.graphics.context_instructions import PopMatrix, PushMatrix
from kivy.logger import Logger
from kivy.graphics import Mesh
from kivy.resources import resource_find
from kivy.uix.stencilview import StencilView
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty
from kivy.clock import Clock

import numpy as np
import io
from _functools import partial
from math import cos, sin, pi

# try:
#     kivy.require('1.9.0') # I would need to check which release of
#     Kivy would be the best suitable.
# except AttributeError:
#     raise ImportError(
#         "kivy version too old -- it must have require_version")

_debug = True

app = None


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)


class MPLKivyApp(App):

    figure = ObjectProperty(None)
    toolbar = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(MPLKivyApp, self).__init__(**kwargs)
        self.figure = kwargs['figure']
        self.toolbar = kwargs['toolbar']

    def build(self):
        EventLoop.ensure_window()
        layout = FloatLayout()
        layout.clear_widgets()
        self.figure.size_hint_y = 0.9
        layout.add_widget(self.figure)
        self.toolbar.size_hint_y = 0.1
        layout.add_widget(self.toolbar)
        return layout

    def on_pause(self):
        return App.on_pause(self)

    def on_resume(self):
        App.on_resume(self)

    def on_stop(self):
        global app
        app = None


def _create_App(fig_canvas, toolbar):
    global app
    if app is None:
        if _debug:
            print("Starting up Kivy Application")
        app = MPLKivyApp(figure=fig_canvas, toolbar=toolbar)


class RendererKivy(RendererBase):
    """
    The renderer handles drawing/rendering operations.

    This is a minimal do-nothing class that can be used to get started when
    writing a new backend. Refer to backend_bases.RendererBase for
    documentation of the classes methods.
    """
    def __init__(self, dpi, widget):
        self.dpi = dpi
        self.widget = widget
        #  Can be enhanced by using TextToPath matplotlib, textpath.py
        self.mathtext_parser = MathTextParser("Bitmap")
        self.list_goraud_triangles = []
        self._clipd = {}
        self.clip_rectangles = []

    def contains(self, widget, x, y):
        ''' Returns whether or not a stroke_point is inside the widget '''
        left = widget.x
        bottom = widget.y
        top = widget.y + widget.height
        right = widget.x + widget.width
        return (left <= x <= right and
                bottom <= y <= top)

    def handle_clip_rectangle(self, gc, x, y):
        '''It checks whether the point (x,y) collides with any already
        existent stencil. If so it returns the index position of the
        stencil it collides with. if the new clip rectangle bounds are
        None it draws in the canvas otherwise it finds the correspondent
        stencil or creates a new one for the new graphics instructions.'''
        collides = self.collides_with_existent_stencil(x, y)
        if collides > -1:
            return collides
        new_bounds = gc.get_clip_rectangle()
        if new_bounds is not None:
            x = int(new_bounds.bounds[0])
            y = int(new_bounds.bounds[1])
            w = int(new_bounds.bounds[2])
            h = int(new_bounds.bounds[3])
            collides = self.collides_with_existent_stencil(x, y)
            if collides == -1:
                cliparea = StencilView(pos=(x, y), size=(w, h))
                self.clip_rectangles.append(cliparea)
                self.widget.add_widget(cliparea)
                return len(self.clip_rectangles) - 1
            else:
                return collides
        else:
            return -2

    def collides_with_existent_stencil(self, x, y):
        idx = -1
        for cliparea in self.clip_rectangles:
            idx += 1
            if self.contains(cliparea, x, y):
                return idx
        return -1

    def draw_path(self, gc, path, transform, rgbFace=None):
        points_line = []
        polygons = path.to_polygons(transform, self.widget.width,
                                    self.widget.height)
        for polygon in polygons:
            vertices = []
            for x, y in polygon:
                points_line += [float(x), float(y), ]
            tess = Tesselator()
            tess.add_contour(points_line)
            if not tess.tesselate():
                print("Tesselator didn't work :(")
                return
            newclip = self.handle_clip_rectangle(gc, x, y)
            if newclip > -1:
                self.draw_graphics(self.clip_rectangles[newclip], gc, tess,
                                points_line, rgbFace)
            else:
                self.draw_graphics(self.widget, gc, tess, points_line, rgbFace)

    def draw_graphics(self, widget, gc, polygons, points_line, rgbFace):
        if isinstance(gc.line['dash_list'], tuple):
            gc.line['dash_list'] = list(gc.line['dash_list'])
        with widget.canvas:
            if rgbFace is not None:
                Color(*rgbFace)
                for vertices, indices in polygons.meshes:
                    Mesh(
                        vertices=vertices,
                        indices=indices,
                        mode=str("triangle_fan")
                    )
            Color(*gc.get_rgb())
            Line(points=points_line, width=int(gc.line['width'] / 2),
                dash_length=gc.line['dash_length'],
                dash_offset=gc.line['dash_offset'],
                 dash_joint=gc.line['joint_style'],
                 dash_list=gc.line['dash_list'])

    def draw_image(self, gc, x, y, im):
        bbox = gc.get_clip_rectangle()
        if bbox is not None:
            l, b, w, h = bbox.bounds
        else:
            l = 0
            b = 0,
            w = self.widget.width
            h = self.widget.height
        h, w = im.get_size_out()
        rows, cols, image_str = im.as_rgba_str()
        texture = Texture.create(size=(w, h))
        texture.blit_buffer(image_str, colorfmt='rgba', bufferfmt='ubyte')
        with self.widget.canvas:
            Color(1.0, 1.0, 1.0, 1.0)
            Rectangle(texture=texture, pos=(x, y), size=(w, h))

    def draw_gouraud_triangle(self, gc, points, colors, transform):
        RendererBase.draw_gouraud_triangle(self, gc, points, colors, transform)
        print("Entering draw_gouraud_triangle")
        assert len(points) == len(colors)
        assert points.ndim == 3
        assert points.shape[1] == 3
        assert points.shape[2] == 2
        assert colors.ndim == 3
        assert colors.shape[1] == 3
        assert colors.shape[2] == 4
        shape = points.shape
        points = points.reshape((shape[0] * shape[1], 2))
        tpoints = trans.transform(points)
        tpoints = tpoints.reshape(shape)
        name = self.list_goraud_triangles.append((tpoints, colors))
        ''' Implement this pseudocode with points and colors:
        http://www-users.mat.uni.torun.pl/~wrona/3d_tutor/tri_fillers.html '''

    def draw_gouraud_triangles(self, gc, triangles_array, colors_array,
        transform):
        print ("Entra en draw_gouraud_triangles")
#         self.draw_gouraud_triangles(gc, points.reshape((1, 3, 2)),
#                                     colors.reshape((1, 3, 4)), trans)

    def draw_text(self, gc, x, y, s, prop, angle, ismath=False, mtext=None):
        x, y = int(x), int(y)
        if x < 0 or y < 0:
            return
        if ismath:
            self.draw_mathtext(gc, x, y, s, prop, angle)
        else:
            font = resource_find(prop.get_name() + ".ttf")
            if font is None:
                plot_text = CoreLabel(font_size=prop.get_size_in_points())
            else:
                plot_text = CoreLabel(font_size=prop.get_size_in_points(),
                                font_name=prop.get_name())
            plot_text.text = "{}".format(s)
            if prop.get_style() == 'italic':
                plot_text.italic = True
            if weight_as_number(prop.get_weight()) > 500:
                plot_text.bold = True
            plot_text.refresh()
            with self.widget.canvas:
                if isinstance(angle, float):
                    PushMatrix()
                    Rotate(angle=angle, origin=(x, y))
                    Rectangle(pos=(x, y), texture=plot_text.texture,
                              size=plot_text.texture.size)
                    PopMatrix()
                else:
                    Rectangle(pos=(x, y), texture=plot_text.texture,
                              size=plot_text.texture.size)

    def draw_mathtext(self, gc, x, y, s, prop, angle):
        """
        Draw the math text using matplotlib.mathtext
        """
        ftimage, depth = self.mathtext_parser.parse(s, self.dpi, prop)
        w = ftimage.get_width()
        h = ftimage.get_height()
        texture = Texture.create(size=(w, h))
        texture.blit_buffer(ftimage.as_rgba_str(), colorfmt='rgba',
                            bufferfmt='ubyte')
        texture.flip_vertical()
        with self.widget.canvas:
            Rectangle(texture=texture, pos=(x, y), size=(w, h))

    def draw_markers(self, gc, marker_path, marker_trans, path,
        trans, rgbFace=None):
        RendererBase.draw_markers(self, gc, marker_path, marker_trans, path,
                                  trans, rgbFace=rgbFace)

    def flipy(self):
        return False

    def get_canvas_width_height(self):
        return self.widget.width, self.widget.height

    def get_text_width_height_descent(self, s, prop, ismath):
        if ismath:
            ftimage, depth = self.mathtext_parser.parse(s, self.dpi, prop)
            w = ftimage.get_width()
            h = ftimage.get_height()
            return w, h, depth
        font = resource_find(prop.get_name() + ".ttf")
        if font is None:
            plot_text = CoreLabel(font_size=prop.get_size_in_points())
        else:
            plot_text = CoreLabel(font_size=prop.get_size_in_points(),
                            font_name=prop.get_name())
        plot_text.text = str(s.encode("utf-8"))
        plot_text.refresh()
        return plot_text.texture.size[0], plot_text.texture.size[1], 1

    def new_gc(self):
        return GraphicsContextKivy(self.widget)

    def points_to_pixels(self, points):
        # if backend doesn't have dpi, e.g., postscript or svg
        return points
        # elif backend assumes a value for pixels_per_inch
        #return points/72.0 * self.dpi.get() * pixels_per_inch/72.0
        # else
        #return points/72.0 * self.dpi.get()


class NavigationToolbar2Kivy(NavigationToolbar2):

    savefile = ObjectProperty(None)
    text_input = ObjectProperty(None)

    def __init__(self, canvas, **kwargs):
        self.actionbar = ActionBar(pos_hint={'top': 1.0})
        super(NavigationToolbar2Kivy, self).__init__(canvas)
        self.ctx = None

    def _init_toolbar(self):
        basedir = os.path.join(rcParams['datapath'], 'images')
        actionview = ActionView()
        actionprevious = ActionPrevious(title="Navigation", with_previous=False)
        actionoverflow = ActionOverflow()
        actionview.add_widget(actionprevious)
        actionview.add_widget(actionoverflow)
        actionview.use_separator = True
        self.actionbar.add_widget(actionview)
        for text, tooltip_text, image_file, callback in self.toolitems:
            if text is None:
                actionview.add_widget(ActionSeparator())
                continue
            fname = os.path.join(basedir, image_file + '.png')
            if text in ['Pan', 'Zoom']:
                action_button = ActionToggleButton(text=text, icon=fname)
            else:
                action_button = ActionButton(text=text, icon=fname)
            action_button.bind(on_press=getattr(self, callback))
            actionview.add_widget(action_button)

    def configure_subplots(self):
        pass

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_save(self):
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def save(self, path, filename):
        with open(os.path.join(path, filename), 'w') as stream:
            stream.write(self.text_input.text)
        self.dismiss_popup()

    def save_figure(self, *args):
        self.show_save()


class GraphicsContextKivy(GraphicsContextBase):
    """
    The graphics context provides the color, line styles, etc... See the gtk
    and postscript backends for examples of mapping the graphics context
    attributes (cap styles, join styles, line widths, colors) to a particular
    backend. In GTK this is done by wrapping a gtk.gdk.GC object and
    forwarding the appropriate calls to it using a dictionary mapping styles
    to gdk constants. In Postscript, all the work is done by the renderer,
    mapping line styles to postscript calls.

    If it's more appropriate to do the mapping at the renderer level (as in
    the postscript backend), you don't need to override any of the GC methods.
    If it's more appropriate to wrap an instance (as in the GTK backend) and
    do the mapping here, you'll need to override several of the setter
    methods.

    The base GraphicsContext stores colors as a RGB tuple on the unit
    interval, e.g., (0.5, 0.0, 1.0). You may need to map this to colors
    appropriate for your backend.
    """

    _capd = {
        'butt': 'square',
        'projecting': 'square',
        'round': 'round',
    }

    def __init__(self, renderer):
        #super(GraphicsContextBase, self).__init__()
        GraphicsContextBase.__init__(self)
        self.renderer = renderer
        self.line = {}
        self.line['cap_style'] = self.get_capstyle()
        self.line['joint_style'] = self.get_joinstyle()
        self.line['dash_offset'] = None
        self.line['dash_length'] = None
        self.line['dash_list'] = []

    def set_capstyle(self, cs):
        GraphicsContextBase.set_capstyle(self, cs)
        self.line['cap_style'] = self._capd[self._capstyle]

    def set_joinstyle(self, js):
        GraphicsContextBase.set_joinstyle(self, js)
        self.line['join_style'] = js

    def set_clip_rectangle(self, rectangle):
        GraphicsContextBase.set_clip_rectangle(self, rectangle)

    def set_dashes(self, dash_offset, dash_list):
        GraphicsContextBase.set_dashes(self, dash_offset, dash_list)
        # dash_list is a list with numbers denoting the number of points
        # in a dash and if it is on or off.
        if dash_list is not None:
            self.line['dash_list'] = dash_list
        if dash_offset is not None:
            self.line['dash_offset'] = int(dash_offset)
            # needs improvement since kivy seems not to support
            # dashes with different lengths and offsets

    def set_foreground(self, fg, isRGBA=False):
        GraphicsContextBase.set_foreground(self, fg, isRGBA=isRGBA)
        with self.renderer.canvas.before:
            Color(*self.get_rgb())
            Rectangle(pos=self.renderer.pos, size=self.renderer.size)

    def set_graylevel(self, frac):
        GraphicsContextBase.set_graylevel(self, frac)
        with self.renderer.canvas.before:
            Color(*self.get_rgb())
            Rectangle(pos=self.renderer.pos, size=self.renderer.size)

    def set_linewidth(self, w):
        GraphicsContextBase.set_linewidth(self, w)
        self.line['width'] = w

########################################################################
#
# The following functions and classes are for pylab and implement
# window/figure managers, etc...
#
########################################################################


def draw_if_interactive():
    """
    For image backends - is not required
    For GUI backends - this should be overriden if drawing should be done in
    interactive python mode
    """
    if matplotlib.is_interactive():
        figManager = Gcf.get_active()
        if figManager is not None:
            figManager.canvas.draw_idle()


class Show(ShowBase):
    def mainloop(self):
        global app
        if app is not None:
            app.run()

show = Show()

# def show():
#     """
#     For image backends - is not required
#     For GUI backends - show() is usually the last line of a pylab script and
#     tells the backend that it is time to draw. In interactive mode, this may
#     be a do nothing func. See the GTK backend for an example of how to handle
#     interactive versus batch mode
#     """
#     for manager in Gcf.get_all_fig_managers():
#         # do something to display the GUI
#         manager.show()


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
    canvas = FigureCanvasKivy(figure)
    canvas.draw()
    manager = FigureManagerKivy(canvas, num)
    _create_App(canvas, manager.toolbar.actionbar)
#     manager.show()
    return manager


class FigureCanvasKivy(FocusBehavior, Widget, FigureCanvasBase):
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
            print('FigureCanvasKivy: ', figure)
        Window.bind(mouse_pos=self._on_mouse_pos)
        self.bind(size=self._on_size_changed)
        self.inside_figure = True
        self.figure = figure
        super(FigureCanvasKivy, self).__init__(figure=self.figure, **kwargs)
        self.focus = True

    def draw(self):
        """
        Draw the figure using the KivyRenderer
        """
        self.clear_widgets()
        self.canvas.clear()
        renderer = RendererKivy(self.figure.dpi, self)
        self.figure.draw(renderer)

    def on_touch_down(self, touch):
        if super(FigureCanvasKivy, self).on_touch_down(touch):
            return True
        FigureCanvasBase.motion_notify_event(self, touch.x,
                                             touch.y, guiEvent=None)
        if self.collide_point(*touch.pos):
            touch.grab(self)
            if(touch.button == "scrollup" or touch.button == "scrolldown"):
                FigureCanvasBase.scroll_event(self, touch.x,
                                              touch.y, 5, guiEvent=None)
            else:
                FigureCanvasBase.button_press_event(self, touch.x, touch.y,
                                                self.get_mouse_button(touch),
                                                dblclick=False, guiEvent=None)
            if self.inside_figure:
                FigureCanvasBase.enter_notify_event(self, guiEvent=None,
                                                    xy=None)
        else:
            if not self.inside_figure:
                FigureCanvasBase.leave_notify_event(self, guiEvent=None)
        return False

    def on_touch_move(self, touch):
        inside = self.collide_point(touch.x, touch.y)
        FigureCanvasBase.motion_notify_event(self, touch.x, touch.y,
                                             guiEvent=None)
        if inside and self.inside_figure:
            FigureCanvasBase.enter_notify_event(self, guiEvent=None, xy=None)
            self.inside_figure = False
        elif not inside and not self.inside_figure:
            FigureCanvasBase.leave_notify_event(self, guiEvent=None)
            self.inside_figure = True
        return False

    def get_mouse_button(self, touch):
        if touch.button == "left":
            return 1
        elif touch.button == "middle":
            return 2
        elif touch.button == "right":
            return 3
        return -1

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            if touch.button == "scrollup" or touch.button == "scrolldown":
                FigureCanvasBase.scroll_event(self, touch.x, touch.y,
                                              5, guiEvent=None)
            else:
                FigureCanvasBase.button_release_event(self, touch.x, touch.y,
                                                    touch.button, guiEvent=None)
            touch.ungrab(self)
        else:
            return super(FigureCanvasKivy, self).on_touch_up(touch)
        return False

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        FigureCanvasBase.key_press_event(self, keycode[1], guiEvent=None)
        return super(FigureCanvasKivy, self).keyboard_on_key_down(window,
                                                    keycode, text, modifiers)

    def keyboard_on_key_up(self, window, keycode):
        FigureCanvasBase.key_release_event(self, keycode[1], guiEvent=None)
        return super(FigureCanvasKivy, self).keyboard_on_key_up(window, keycode)

    def _on_mouse_pos(self, *args):
        pos = args[1]
        inside = self.collide_point(*pos)
        FigureCanvasBase.motion_notify_event(self, pos[0], pos[1],
                                                guiEvent=None)
        if inside and self.inside_figure:
            FigureCanvasBase.enter_notify_event(self, guiEvent=None, xy=None)
            self.inside_figure = False
        elif not inside and not self.inside_figure:
            FigureCanvasBase.leave_notify_event(self, guiEvent=None)
            self.inside_figure = True

    def _on_size_changed(self, *args):
        print("self.size", self.size)
        w, h = self.size
        dpival = self.figure.dpi
        winch = w / dpival
        hinch = h / dpival
        self.figure.set_size_inches(winch, hinch)
#         FigureCanvasBase.resize_event(self)
        self.draw()

    def callback(self, *largs):
        self.draw()

    def close_event(self, guiEvent=None):
        FigureCanvasBase.close_event(self, guiEvent=guiEvent)

    def blit(self, bbox=None):
        '''
        If bbox is None, blit the entire canvas to the widget. Otherwise
        blit only the area defined by the bbox.
        '''
        self.blitbox = bbox

    filetypes = FigureCanvasBase.filetypes.copy()
    filetypes['png'] = 'Portable Network Graphics'

    def print_png(self, filename, *args, **kwargs):
        Clock.schedule_once(partial(self._print_image, filename), 1)

    def get_default_filetype(self):
        return 'png'

    def _print_image(self, filename, *largs):
        self.export_to_png(filename)


class FigureManagerKivy(FigureManagerBase):
    """
    Wrap everything up into a window for the pylab interface

    For non interactive backends, the base class does all the work
    """

    def __init__(self, canvas, num):
        if _debug:
            print('FigureManagerKivy: ', canvas)
        super(FigureManagerKivy, self).__init__(canvas, num)
        self.canvas = canvas
        self.toolbar = self._get_toolbar()

    def show(self):
        global app
        if app is not None:
            app.run()

    def get_window_title(self):
        return EventLoop.window.title

    def set_window_title(self, title):
        EventLoop.window.title = title

    def resize(self, w, h):
        print("Enter resize")
        Window.size(w, h)

    def _get_toolbar(self):
        if rcParams['toolbar'] == 'toolbar2':
            toolbar = NavigationToolbar2Kivy(self.canvas)
        else:
            toolbar = None
        return toolbar

    def destroy(self):
        global app
        if app is not None:
            app.stop()

########################################################################
#
# Now just provide the standard names that backend.__init__ is expecting
#
########################################################################

FigureCanvas = FigureCanvasKivy
FigureManager = FigureManagerKivy
