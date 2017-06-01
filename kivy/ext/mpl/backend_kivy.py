from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import six

import matplotlib
from matplotlib._pylab_helpers import Gcf
from matplotlib.backend_bases import RendererBase, GraphicsContextBase,\
    FigureManagerBase, FigureCanvasBase
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
from matplotlib.backend_bases import ShowBase
from matplotlib.mathtext import MathTextParser

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
from kivy.base import EventLoop
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Line
from kivy.graphics import Rotate, Translate
from kivy.graphics.context_instructions import PopMatrix, PushMatrix
from kivy.logger import Logger
from kivy.graphics import Mesh

from math import cos, sin, pi
# try:
#     kivy.require('1.9.0') # I would need to check which release of
#     Kivy would be the best suitable.
# except AttributeError:
#     raise ImportError(
#         "kivy version too old -- it must have require_version")

# EventLoop.ensure_window()

_debug = True

app = None


class MPLKivyApp(App):

    def __init__(self, **kwargs):
        super(MPLKivyApp, self).__init__(**kwargs)
        self.figure = kwargs['figure']

    def build(self):
        return self.figure

    def on_pause(self):
        return App.on_pause(self)

    def on_resume(self):
        App.on_resume(self)


def _create_App(fig_canvas):
    global app
    if app is None:
        if _debug:
            print("Starting up Kivy Application")
        app = MPLKivyApp(figure=fig_canvas)


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
        self.mathtext_parser = MathTextParser("Agg")
        self.list_goraud_triangles = []

    def draw_path(self, gc, path, transform, rgbFace=None):
        points_line = []
        polygons = path.to_polygons(transform, self.widget.width,
                                    self.widget.height)
        for polygon in polygons:
            x_list = []
            y_list = []
            for x, y in polygon:
                x_list.append(int(x))
                y_list.append(int(y))
                points_line.append(int(x))
                points_line.append(int(y))
            with self.widget.canvas:
                if rgbFace is not None:
                    Color(*rgbFace)
                    Mesh(vertices=self._regular_polygon(1.0, len(polygon),
                        x_list, y_list), indices=range(len(polygon)),
                         mode=str('triangle_fan'))
                else:
                    Color(*gc.get_rgb())
                    Line(points=points_line, width=1.0,
                         dash_length=gc.line['dash_length'],
                         dash_offset=gc.line['dash_offset'],
                         dash_joint=gc.line['joint_style'])

    def _regular_polygon(self, radius, sides, x, y):
        r = radius
        a = 2 * pi / sides
        vertices = []
        for i in xrange(sides):
            vertices += [
                x[i] + cos(i * a) * r,
                y[i] + sin(i * a) * r,
                cos(i * a),
                sin(i * a),
            ]
        return vertices

    def draw_image(self, gc, x, y, im):
        print('draw_image', gc, x, y, im)

    ''' Under development '''
    def draw_gouraud_triangle(self, gc, points, colors, transform):
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

    def draw_text(self, gc, x, y, s, prop, angle, ismath=False, mtext=None):
        if ismath:
            s = self.strip_math(s)  # remove latex formatting from mathtext
        x, y = float(x), float(y)
        if x < 0 or y < 0:
            return
        plot_text = CoreLabel(font_size=prop.get_size_in_points(),
                              font_name=prop.get_name())
        plot_text.text = str(s.encode("utf-8"))
        if(prop.get_style() == 'italic'):
            plot_text.italic = True
        if(prop.get_weight() > 500):
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

    # draw_markers is optional, and we get more correct relative
    # timings by leaving it out. backend implementers concerned with
    # performance will probably want to implement it
#     def draw_markers(self, gc, marker_path, marker_trans, path,
#     trans, rgbFace=None):
#         pass

    # draw_path_collection is optional, and we get more correct
    # relative timings by leaving it out. backend implementers concerned with
    # performance will probably want to implement it
#     def draw_path_collection(self, gc, master_transform, paths,
#                              all_transforms, offsets, offsetTrans, facecolors,
#                              edgecolors, linewidths, linestyles,
#                              antialiaseds):
#         pass

    # draw_quad_mesh is optional, and we get more correct
    # relative timings by leaving it out. backend implementers concerned with
    # performance will probably want to implement it
#     def draw_quad_mesh(self, gc, master_transform, meshWidth, meshHeight,
#                        coordinates, offsets, offsetTrans, facecolors,
#                        antialiased, edgecolors):
#         pass

    def flipy(self):
        return False

    def get_canvas_width_height(self):
        return self.widget.width, self.widget.height

    def get_text_width_height_descent(self, s, prop, ismath):
        if ismath:
            ox, oy, width, height, descent, font_image, used_characters = \
                self.mathtext_parser.parse(s, self.dpi, prop)
            return width, height, descent
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
        self.line['dash_offset'] = 0
        self.line['dash_length'] = 1

    def set_capstyle(self, cs):
        GraphicsContextBase.set_capstyle(self, cs)
        self.line['cap_style'] = self._capd[self._capstyle]

    def set_joinstyle(self, js):
        GraphicsContextBase.set_joinstyle(self, js)
        self.line['join_style'] = js

    def set_clip_rectangle(self, rectangle):
        GraphicsContextBase.set_clip_rectangle(self, rectangle)
        if rectangle is None:
            return
        l, b, w, h = rectangle.bounds
        self.rectangle = (int(l), self.renderer.height - int(b + h) + 1,
                     int(w), int(h))
#         self._cliprect = Bbox([[100,100],[100,100]])

    def set_dashes(self, dash_offset, dash_list):
        GraphicsContextBase.set_dashes(self, dash_offset, dash_list)
        # dash_list is a list with numbers denoting the number of points
        # in a dash and if it is on or off.
        if dash_list is not None:
            self.line['dash_offset'] = dash_offset
            self.line['dash_length'] = dash_list[0]
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
        print("calling show")
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
    _create_App(canvas)
    manager = FigureManagerKivy(canvas, num)
    #manager.show()
    return manager


class FigureCanvasKivy(FigureCanvasBase, Widget, FocusBehavior):
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
        #from kivy.core.window import Window
        if _debug:
            print('FigureCanvasKivy: ', figure)
        #Window.bind(mouse_pos=self._on_mouse_pos)
        self.bind(size=self._on_size_changed)
        self.inside_figure = True
        self.figure = figure
        #super(FigureCanvasKivy, self).__init__(figure, **kwargs)
        FocusBehavior.__init__(self, **kwargs)
        FigureCanvasBase.__init__(self, figure, **kwargs)
        Widget.__init__(self, **kwargs)

    def draw(self):
        """
        Draw the figure using the KivyRenderer
        """
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
                                        self, dblclick=False, guiEvent=None)
            if self.inside_figure:
                FigureCanvasBase.enter_notify_event(self, guiEvent=None,
                                                    xy=None)
        else:
            if not self.inside_figure:
                FigureCanvasBase.leave_notify_event(self, guiEvent=None)
        return True

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
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            if touch.button == "scrollup" or touch.button == "scrolldown":
                FigureCanvasBase.scroll_event(self, touch.x, touch.y,
                                              5, guiEvent=None)
            else:
                FigureCanvasBase.button_release_event(self, touch.x, touch.y,
                                                      self, guiEvent=None)
            touch.ungrab(self)
        else:
            return super(FigureCanvasKivy, self).on_touch_up(touch)
        return True

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        print(keycode[1])
        FigureCanvasBase.key_press_event(self, keycode[1], guiEvent=None)
        return super(FocusBehavior, self).keyboard_on_key_down(self, window,
                                                    keycode, text, modifiers)

    def keyboard_on_key_up(self, window, keycode):
        FigureCanvasBase.key_release_event(self, keycode[1], guiEvent=None)
        return super(FocusBehavior, self).keyboard_on_key_up(self,
                                                        window, keycode)

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
        w, h = self.size
        dpival = self.figure.dpi
        winch = w / dpival
        hinch = h / dpival
        self.figure.set_size_inches(winch, hinch)
        FigureCanvasBase.resize_event(self)
        self.draw()

    def close_event(self, guiEvent=None):
        FigureCanvasBase.close_event(self, guiEvent=guiEvent)

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
        texture.blit_buffer(self.get_renderer().buffer_rgba(), colorfmt='rgba',
                            bufferfmt='ubyte')
        texture.flip_vertical()
        img = Image(texture)
        img.save(filename)

    def get_default_filetype(self):
        return 'png'


class FigureManagerKivy(FigureManagerBase):
    """
    Wrap everything up into a window for the pylab interface

    For non interactive backends, the base class does all the work
    """

    def __init__(self, canvas, num):
        if _debug:
            print('FigureManagerKivy: ', canvas)
        super(FigureManagerKivy, self).__init__(canvas, num)

    def show(self):
        global app
        if app is not None:
            app.run()

    def get_window_title(self):
        return EventLoop.window.title

    def set_window_title(self, title):
        EventLoop.window.title = title

    def resize(self, w, h):
        Window.size(w, h)

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
