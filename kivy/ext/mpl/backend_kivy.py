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

try:
    import kivy
except ImportError:
    raise ImportError("this backend requires Kivy to be installed.")

from kivy.app import App
from kivy.graphics.texture import Texture
from kivy.graphics import Rectangle
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.base import EventLoop
from kivy.ext.mpl.backend_kivyagg import FigureCanvasKivyAgg
from kivy.uix.behaviors import FocusBehavior

try:
    kivy.require('1.9.0') # I would need to check which release of Kivy would be the best suitable.
except AttributeError:
    raise ImportError(
        "kivy version too old -- it must have require_version")

EventLoop.ensure_window()

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
        app = MPLKivyApp(figure = fig_canvas)

class RendererKivy(RendererBase):
    """
    The renderer handles drawing/rendering operations.

    This is a minimal do-nothing class that can be used to get started when
    writing a new backend. Refer to backend_bases.RendererBase for
    documentation of the classes methods.
    """
    def __init__(self, dpi):
        self.dpi = dpi

    def draw_path(self, gc, path, transform, rgbFace=None):
        pass

    # draw_markers is optional, and we get more correct relative
    # timings by leaving it out.  backend implementers concerned with
    # performance will probably want to implement it
#     def draw_markers(self, gc, marker_path, marker_trans, path, trans, rgbFace=None):
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
    # relative timings by leaving it out.  backend implementers concerned with
    # performance will probably want to implement it
#     def draw_quad_mesh(self, gc, master_transform, meshWidth, meshHeight,
#                        coordinates, offsets, offsetTrans, facecolors,
#                        antialiased, edgecolors):
#         pass

    def draw_image(self, gc, x, y, im):
        pass

    def draw_text(self, gc, x, y, s, prop, angle, ismath=False, mtext=None):
        pass

    def flipy(self):
        return True

    def get_canvas_width_height(self):
        return 100, 100

    def get_text_width_height_descent(self, s, prop, ismath):
        return 1, 1, 1

    def new_gc(self):
        return GraphicsContextKivy()

    def points_to_pixels(self, points):
        # if backend doesn't have dpi, e.g., postscript or svg
        return points
        # elif backend assumes a value for pixels_per_inch
        #return points/72.0 * self.dpi.get() * pixels_per_inch/72.0
        # else
        #return points/72.0 * self.dpi.get()


class GraphicsContextKivy(GraphicsContextBase):
    """
    The graphics context provides the color, line styles, etc...  See the gtk
    and postscript backends for examples of mapping the graphics context
    attributes (cap styles, join styles, line widths, colors) to a particular
    backend.  In GTK this is done by wrapping a gtk.gdk.GC object and
    forwarding the appropriate calls to it using a dictionary mapping styles
    to gdk constants.  In Postscript, all the work is done by the renderer,
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
    pass



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

# class Show(ShowBase):
#     def mainloop(self):
#         needmain = not wx.App.IsMainLoopRunning()
#         if needmain:
#             wxapp = wx.GetApp()
#             if wxapp is not None:
#                 wxapp.MainLoop()
# 
# class Show(ShowBase):
#     def mainloop(self):
#         # allow KeyboardInterrupt exceptions to close the plot window.
#         signal.signal(signal.SIGINT, signal.SIG_DFL)
#         global qApp
#         qApp.exec_()
# 
# class Show(ShowBase):
#     def mainloop(self):
#         if Gtk.main_level() == 0:
#             Gtk.main()

class Show(ShowBase):
    def mainloop(self):
        global app
        app.run()

show = Show()

# def show():
#     """
#     For image backends - is not required
#     For GUI backends - show() is usually the last line of a pylab script and
#     tells the backend that it is time to draw.  In interactive mode, this may
#     be a do nothing func.  See the GTK backend for an example of how to handle
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
    # examples.  Not all GUIs require explicit instantiation of a
    # main-level app (egg backend_gtk, backend_gtkagg) for pylab
    FigureClass = kwargs.pop('FigureClass', Figure)
    thisFig = FigureClass(*args, **kwargs)
    return new_figure_manager_given_figure(num, thisFig)


def new_figure_manager_given_figure(num, figure):
    """
    Create a new figure manager instance for the given figure.
    """
    canvas = FigureCanvasKivy(figure)
    _create_App(canvas)
    manager = FigureManagerKivy(canvas, num)
    return manager


class FigureCanvasKivy(FigureCanvasKivyAgg, FocusBehavior):
    """
    The canvas the figure renders into.  Calls the draw and print fig
    methods, creates the renderers, etc...

    Public attribute

      figure - A Figure instance

    Note GUI templates will want to connect events for button presses,
    mouse movements and key presses to functions that call the base
    class methods button_press_event, button_release_event,
    motion_notify_event, key_press_event, and key_release_event.  See,
    e.g., backend_gtk.py, backend_wx.py and backend_tkagg.py
    """
    
    def __init__(self, figure, **kwargs):
        if _debug:
            print('FigureCanvasKivy: ', figure)
        Window.bind(mouse_pos = self._on_mouse_pos)
        self.bind(size = self._on_size_changed)
        self.flag = True
        #super(FigureCanvasKivy, self).__init__(figure, **kwargs)
        FocusBehavior.__init__(self, **kwargs)
        FigureCanvasKivyAgg.__init__(self, figure, **kwargs)

#     def draw(self):
#         """
#         Draw the figure using the KivyRenderer
#         """

        #renderer = RendererKivy(self.figure.dpi)
        #self.figure.draw(renderer)
    
    def on_touch_down(self, touch):
        if super(FigureCanvasKivy, self).on_touch_down(touch):
            return True
        FigureCanvasKivyAgg.motion_notify_event(self, touch.x, touch.y, guiEvent=None)
        if self.collide_point(*touch.pos):
            touch.grab(self)
            if(touch.button == "scrollup" or touch.button == "scrolldown"):
                FigureCanvasKivyAgg.scroll_event(self, touch.x, touch.y, 5, guiEvent = None)
            else:
                FigureCanvasKivyAgg.button_press_event(self, touch.x, touch.y, self, dblclick=False, guiEvent=None)
            if self.flag:
                FigureCanvasKivyAgg.enter_notify_event(self, guiEvent=None, xy=None)
        else:
            if not self.flag:
                FigureCanvasKivyAgg.leave_notify_event(self, guiEvent=None)
        return True

    def on_touch_move(self, touch):
        inside = self.collide_point(touch.x, touch.y)        
        FigureCanvasKivyAgg.motion_notify_event(self, touch.x, touch.y, guiEvent=None)
        if inside and self.flag:
            FigureCanvasKivyAgg.enter_notify_event(self, guiEvent=None, xy=None)
            self.flag = False
        elif not inside and not self.flag:
            FigureCanvasKivyAgg.leave_notify_event(self, guiEvent=None)
            self.flag = True
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            if(touch.button == "scrollup" or touch.button == "scrolldown"):
                FigureCanvasKivyAgg.scroll_event(self, touch.x, touch.y, 5, guiEvent = None)
            else:
                FigureCanvasKivyAgg.button_release_event(self, touch.x, touch.y, self, guiEvent=None)
            touch.ungrab(self)
        else:
            return super(FigureCanvasKivy, self).on_touch_up(touch)
        return True

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        print(keycode[1])
        FigureCanvasKivyAgg.key_press_event(self, keycode[1], guiEvent = None)
        return super(FocusBehavior, self).keyboard_on_key_down(self, window, keycode, text, modifiers)

    def keyboard_on_key_up(self, window, keycode):
        FigureCanvasKivyAgg.key_release_event(self, keycode[1], guiEvent = None)
        return super(FocusBehavior, self).keyboard_on_key_up(self, window, keycode)

    def _on_mouse_pos(self, *args):
        pos = args[1]
        inside = self.collide_point(*pos)
        FigureCanvasKivyAgg.motion_notify_event(self, pos[0], pos[1], guiEvent=None)
        if inside and self.flag:
            FigureCanvasKivyAgg.enter_notify_event(self, guiEvent=None, xy=None)
            self.flag = False
        elif not inside and not self.flag:
            FigureCanvasKivyAgg.leave_notify_event(self, guiEvent=None)
            self.flag = True

    def _on_size_changed(self, *args):
        w, h = self.size
        dpival = self.figure.dpi
        winch = w / dpival
        hinch = h / dpival
        self.figure.set_size_inches(winch, hinch)
        FigureCanvasKivyAgg.resize_event(self)
        self.draw()

    def close_event(self, guiEvent=None):
        FigureCanvasKivyAgg.close_event(self, guiEvent=guiEvent)

    def draw_idle(self, *args, **kwargs):
        EventLoop.idle()
        self.draw()


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
        self.canvas.draw()

    def get_window_title(self):
        return EventLoop.window.title

    def set_window_title(self, title):
        EventLoop.window.title = title

    def resize(self, w, h):
        Window.size(w, h)

    def destroy(self):
        EventLoop.close()
########################################################################
#
# Now just provide the standard names that backend.__init__ is expecting
#
########################################################################

FigureCanvas = FigureCanvasKivy
FigureManager = FigureManagerKivy
