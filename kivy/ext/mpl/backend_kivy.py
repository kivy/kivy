'''
Backend Kivy
=====

.. versionadded:: 1.9.1

.. image:: images/backend_kivy_example.jpg
    :align: right

The :class:`FigureCanvasKivy` widget is used to create a matplotlib graph.
This widget has the same properties as
:class:`kivy.ext.mpl.backend_kivyagg.Backend_KivyAgg`. This widget instead
of rendering a static image, uses the kivy graphics instructions
:class:`kivy.graphics.Line` and :class:`kivy.graphics.Mesh` to render on the
canvas.


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
    canvas = FigureCanvasKivy(figure=fig)

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


Backend Kivy Events
-----------------------

All ten matplotlib events are available: `button_press_event` which is raised
on a mouse button clicked or on touch down, `button_release_event` which is
raised when a click button is released or on touch up, `key_press_event` which
is raised when a key is pressed, `key_release_event` which is raised when a key
is released, `motion_notify_event` which is raised when the mouse is on motion,
`resize_event` which is raised when the dimensions of the widget change,
`scroll_event` which is raised when the mouse scroll wheel is rolled,
`figure_enter_event` which is raised when mouse enters a new figure,
`figure_leave_event` which is raised when mouse leaves a figure,
`close_event` which is raised when the window is closed.::

    def press(event):
        print('press released from test', event.x, event.y, event.button)


    def release(event):
        print('release released from test', event.x, event.y, event.button)


    def keypress(event):
        print('key down', event.key)


    def keyup(event):
        print('key up', event.key)


    def motionnotify(event):
        print('mouse move to ', event.x, event.y)


    def resize(event):
        print('resize from mpl ', event)


    def scroll(event):
        print('scroll event from mpl ', event.x, event.y, event.step)


    def figure_enter(event):
        print('figure enter mpl')


    def figure_leave(event):
        print('figure leaving mpl')


    def close(event):
        print('closing figure')


    fig.canvas.mpl_connect('button_press_event', press)
    fig.canvas.mpl_connect('button_release_event', release)
    fig.canvas.mpl_connect('key_press_event', keypress)
    fig.canvas.mpl_connect('key_release_event', keyup)
    fig.canvas.mpl_connect('motion_notify_event', motionnotify)
    fig.canvas.mpl_connect('resize_event', resize)
    fig.canvas.mpl_connect('scroll_event', scroll)
    fig.canvas.mpl_connect('figure_enter_event', figure_enter)
    fig.canvas.mpl_connect('figure_leave_event', figure_leave)
    fig.canvas.mpl_connect('close_event', close)

'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import six
import os
import matplotlib
import matplotlib.transforms as transforms
from matplotlib._pylab_helpers import Gcf
from matplotlib.backend_bases import RendererBase, GraphicsContextBase,\
    FigureManagerBase, FigureCanvasBase, NavigationToolbar2, TimerBase
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox, Affine2D
from matplotlib.backend_bases import ShowBase
from matplotlib.mathtext import MathTextParser
from matplotlib import rcParams
from hashlib import md5
from matplotlib import _png
from matplotlib.font_manager import weight_as_number
from matplotlib import _path

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
from kivy.graphics.instructions import InstructionGroup
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
from kivy.uix.textinput import TextInput
from kivy.lang import Builder
from kivy.logger import Logger
from distutils.version import LooseVersion

_mpl_1_5 = LooseVersion(matplotlib.__version__) >= LooseVersion('1.5.0')

import numpy as np
import io
import textwrap
from functools import partial
from math import cos, sin, pi

try:
    kivy.require('1.9.0')  # I would need to check which release of
    # Kivy would be the best suitable.
except AttributeError:
    raise ImportError(
        "kivy version too old -- it must have require_version")

toolbar = None
my_canvas = None


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)


class MPLKivyApp(App):
    '''Creates the App initializing a FloatLayout with a figure and toolbar
       widget.
    '''
    figure = ObjectProperty(None)
    toolbar = ObjectProperty(None)

    def build(self):
        EventLoop.ensure_window()
        layout = FloatLayout()
        if self.figure:
            self.figure.size_hint_y = 0.9
            layout.add_widget(self.figure)
        if self.toolbar:
            self.toolbar.size_hint_y = 0.1
            layout.add_widget(self.toolbar)
        return layout


def draw_if_interactive():
    '''Handle whether or not the backend is in interactive mode or not.
    '''
    if matplotlib.is_interactive():
        figManager = Gcf.get_active()
        if figManager:
            figManager.canvas.draw_idle()


class Show(ShowBase):
    '''mainloop needs to be overwritten to define the show() behavior for kivy
       framework.
    '''
    def mainloop(self):
        app = App.get_running_app()
        if app is None:
            app = MPLKivyApp(figure=my_canvas, toolbar=toolbar)
            app.run()

show = Show()


def new_figure_manager(num, *args, **kwargs):
    '''Create a new figure manager instance for the figure given.
    '''
    # if a main-level app must be created, this (and
    # new_figure_manager_given_figure) is the usual place to
    # do it -- see backend_wx, backend_wxagg and backend_tkagg for
    # examples. Not all GUIs require explicit instantiation of a
    # main-level app (egg backend_gtk, backend_gtkagg) for pylab
    FigureClass = kwargs.pop('FigureClass', Figure)
    thisFig = FigureClass(*args, **kwargs)
    return new_figure_manager_given_figure(num, thisFig)


def new_figure_manager_given_figure(num, figure):
    '''Create a new figure manager instance for the given figure.
    '''
    canvas = FigureCanvasKivy(figure)
    manager = FigureManagerKivy(canvas, num)
    global my_canvas
    global toolbar
    toolbar = manager.toolbar.actionbar if manager.toolbar else None
    my_canvas = canvas
    return manager


class RendererKivy(RendererBase):
    '''The kivy renderer handles drawing/rendering operations. A RendererKivy
       should be initialized with a FigureCanvasKivy widget. On initialization
       a MathTextParser is instantiated to generate math text inside a
       FigureCanvasKivy widget. Additionally a list to store clip_rectangles
       is defined for elements that need to be clipped inside a rectangle such
       as axes. The rest of the render is performed using kivy graphics
       instructions.
    '''
    def __init__(self, widget):
        super(RendererKivy, self).__init__()
        self.widget = widget
        self.dpi = widget.figure.dpi
        self._markers = {}
        #  Can be enhanced by using TextToPath matplotlib, textpath.py
        self.mathtext_parser = MathTextParser("Bitmap")
        self.list_goraud_triangles = []
        self.clip_rectangles = []

    def contains(self, widget, x, y):
        '''Returns whether or not a point is inside the widget. The value
           of the point is defined in x, y as kivy coordinates.
        '''
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
           stencil or creates a new one for the new graphics instructions.
           The point x,y is given in matplotlib coordinates.
        '''
        x = self.widget.x + x
        y = self.widget.y + y
        collides = self.collides_with_existent_stencil(x, y)
        if collides > -1:
            return collides
        new_bounds = gc.get_clip_rectangle()
        if new_bounds:
            x = self.widget.x + int(new_bounds.bounds[0])
            y = self.widget.y + int(new_bounds.bounds[1])
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

    def draw_path_collection(self, gc, master_transform, paths, all_transforms,
        offsets, offsetTrans, facecolors, edgecolors,
        linewidths, linestyles, antialiaseds, urls,
        offset_position):
        '''Draws a collection of paths selecting drawing properties from
           the lists *facecolors*, *edgecolors*, *linewidths*,
           *linestyles* and *antialiaseds*. *offsets* is a list of
           offsets to apply to each of the paths. The offsets in
           *offsets* are first transformed by *offsetTrans* before being
           applied.  *offset_position* may be either "screen" or "data"
           depending on the space that the offsets are in.
        '''
        len_path = len(paths[0].vertices) if len(paths) > 0 else 0
        uses_per_path = self._iter_collection_uses_per_path(
            paths, all_transforms, offsets, facecolors, edgecolors)
        # check whether an optimization is needed by calculating the cost of
        # generating and use a path with the cost of emitting a path in-line.
        should_do_optimization = \
            len_path + uses_per_path + 5 < len_path * uses_per_path
        if not should_do_optimization:
            return RendererBase.draw_path_collection(
                self, gc, master_transform, paths, all_transforms,
                offsets, offsetTrans, facecolors, edgecolors,
                linewidths, linestyles, antialiaseds, urls,
                offset_position)
        # Generate an array of unique paths with the respective transformations
        path_codes = []
        for i, (path, transform) in enumerate(self._iter_collection_raw_paths(
            master_transform, paths, all_transforms)):
            transform = Affine2D(transform.get_matrix()).scale(1.0, -1.0)
            polygons = path.to_polygons(transform)
            path_codes.append(polygons)
        # Apply the styles and rgbFace to each one of the raw paths from
        # the list. Additionally a transformation is being applied to
        # translate each independent path
        for xo, yo, path_poly, gc0, rgbFace in self._iter_collection(
            gc, master_transform, all_transforms, path_codes, offsets,
            offsetTrans, facecolors, edgecolors, linewidths, linestyles,
            antialiaseds, urls, offset_position):
            list_canvas_instruction = self.get_path_instructions(gc0, path_poly,
                                    closed=True, rgbFace=rgbFace)
            for widget, instructions in list_canvas_instruction:
                widget.canvas.add(PushMatrix())
                widget.canvas.add(Translate(xo, yo))
                widget.canvas.add(instructions)
                widget.canvas.add(PopMatrix())

    def collides_with_existent_stencil(self, x, y):
        '''Check all the clipareas and returns the index of the clip area that
           contains this point. The point x, y is given in kivy coordinates.
        '''
        idx = -1
        for cliparea in self.clip_rectangles:
            idx += 1
            if self.contains(cliparea, x, y):
                return idx
        return -1

    def get_path_instructions(self, gc, polygons, closed=False, rgbFace=None):
        '''With a graphics context and a set of polygons it returns a list
           of InstructionGroups required to render the path.
        '''
        instructions_list = []
        points_line = []
        for polygon in polygons:
            for x, y in polygon:
                x = x + self.widget.x
                y = y + self.widget.y
                points_line += [float(x), float(y), ]
            tess = Tesselator()
            tess.add_contour(points_line)
            if not tess.tesselate():
                Logger.warning("Tesselator didn't work :(")
                return
            newclip = self.handle_clip_rectangle(gc, x, y)
            if newclip > -1:
                instructions_list.append((self.clip_rectangles[newclip],
                        self.get_graphics(gc, tess, points_line, rgbFace,
                                          closed=closed)))
            else:
                instructions_list.append((self.widget,
                        self.get_graphics(gc, tess, points_line, rgbFace,
                                          closed=closed)))
        return instructions_list

    def get_graphics(self, gc, polygons, points_line, rgbFace, closed=False):
        '''Return an instruction group which contains the necessary graphics
           instructions to draw the respective graphics.
        '''
        instruction_group = InstructionGroup()
        if isinstance(gc.line['dash_list'], tuple):
            gc.line['dash_list'] = list(gc.line['dash_list'])
        if rgbFace is not None:
            instruction_group.add(Color(*rgbFace))
            for vertices, indices in polygons.meshes:
                instruction_group.add(Mesh(
                    vertices=vertices,
                    indices=indices,
                    mode=str("triangle_fan")
                ))
        instruction_group.add(Color(*gc.get_rgb()))
        if _mpl_1_5 and closed:
            points_poly_line = points_line[:-2]
        else:
            points_poly_line = points_line
        if gc.line['width'] > 0:
            instruction_group.add(Line(points=points_poly_line,
                width=int(gc.line['width'] / 2),
                dash_length=gc.line['dash_length'],
                dash_offset=gc.line['dash_offset'],
                dash_joint=gc.line['joint_style'],
                dash_list=gc.line['dash_list']))
        return instruction_group

    def draw_image(self, gc, x, y, im):
        '''Render images that can be displayed on a matplotlib figure.
           These images are generally called using imshow method from pyplot.
           A Texture is applied to the FigureCanvas. The position x, y is
           given in matplotlib coordinates.
        '''
        x = self.widget.x + x
        y = self.widget.y + y
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

#     def draw_gouraud_triangle(self, gc, points, colors, transform):
#         RendererBase.draw_gouraud_triangle(self, gc, points, colors,
#         transform)
#         assert len(points) == len(colors)
#         assert points.ndim == 3
#         assert points.shape[1] == 3
#         assert points.shape[2] == 2
#         assert colors.ndim == 3
#         assert colors.shape[1] == 3
#         assert colors.shape[2] == 4
#         shape = points.shape
#         points = points.reshape((shape[0] * shape[1], 2))
#         tpoints = trans.transform(points)
#         tpoints = tpoints.reshape(shape)
#         name = self.list_goraud_triangles.append((tpoints, colors))
#         ''' Implement this pseudocode with points and colors:
#         http://www-users.mat.uni.torun.pl/~wrona/3d_tutor/tri_fillers.html '''
#
#     def draw_gouraud_triangles(self, gc, triangles_array, colors_array,
#         transform):
#         self.draw_gouraud_triangles(gc, points.reshape((1, 3, 2)),
#                                     colors.reshape((1, 3, 4)), trans)

    def draw_text(self, gc, x, y, s, prop, angle, ismath=False, mtext=None):
        '''Render text that is displayed in the canvas. The position x, y is
           given in matplotlib coordinates. A `GraphicsContextKivy` is given
           to render according to the text properties such as color, size, etc.
           An angle is given to change the orientation of the text when needed.
           If the text is a math expression it will be rendered using a
           MathText parser.
        '''
        if mtext and mtext.get_rotation_mode() == "anchor":
            # Get anchor coordinates.
            transform = mtext.get_transform()
            ax, ay = transform.transform_point(mtext.get_position())
            ay = self.widget.height - ay

            angle_rad = angle * np.pi / 180.
            dir_vert = np.array([np.sin(angle_rad), np.cos(angle_rad)])
            v_offset = np.dot(dir_vert, [(x - ax), (y - ay)])
            ax = ax + v_offset * dir_vert[0]
            ay = ay + v_offset * dir_vert[1]
            x = ax
            y = ay

            w, h, d = self.get_text_width_height_descent(s, prop, ismath)
            ha = mtext.get_ha()
            if ha == "center":
                x -= w / 2
            elif ha == "right":
                x -= w
            elif ha == "left":
                x += w
            va = mtext.get_va()
            if va == "top":
                y -= h
            elif va == "center":
                y -= h / 2
            elif va == "bottom":
                y += h

        x += self.widget.x
        y += self.widget.y

#         with self.widget.canvas:
#             Color(1.0, 1.0, 0.0, 1.0)
#             Rectangle(pos=(x,y), size=(w,h))

        if ismath:
            self.draw_mathtext(gc, x, y, s, prop, angle)
        else:
            font = resource_find(prop.get_name() + ".ttf")
            if font is None:
                plot_text = CoreLabel(font_size=prop.get_size_in_points())
            else:
                plot_text = CoreLabel(font_size=prop.get_size_in_points(),
                                font_name=prop.get_name())
            plot_text.text = six.text_type("{}".format(s))
            if prop.get_style() == 'italic':
                plot_text.italic = True
            if weight_as_number(prop.get_weight()) > 500:
                plot_text.bold = True
            plot_text.refresh()
            with self.widget.canvas:
                if isinstance(angle, float):
                    PushMatrix()
                    Rotate(angle=angle, origin=(int(x), int(y)))
                    Rectangle(pos=(int(x), int(y)), texture=plot_text.texture,
                              size=plot_text.texture.size)
                    PopMatrix()
                else:
                    Rectangle(pos=(int(x), int(y)), texture=plot_text.texture,
                              size=plot_text.texture.size)

    def draw_mathtext(self, gc, x, y, s, prop, angle):
        '''Draw the math text using matplotlib.mathtext. The position
           x,y is given in Kivy coordinates.
        '''
        ftimage, depth = self.mathtext_parser.parse(s, self.dpi, prop)
        w = ftimage.get_width()
        h = ftimage.get_height()
        texture = Texture.create(size=(w, h))
        if _mpl_1_5:
            texture.blit_buffer(ftimage.as_rgba_str()[0][0], colorfmt='rgba',
                                bufferfmt='ubyte')
        else:
            texture.blit_buffer(ftimage.as_rgba_str(), colorfmt='rgba',
                                bufferfmt='ubyte')
        texture.flip_vertical()
        with self.widget.canvas:
            Rectangle(texture=texture, pos=(x, y), size=(w, h))

    def draw_path(self, gc, path, transform, rgbFace=None):
        '''Produce the rendering of the graphics elements using
           :class:`kivy.graphics.Line` and :class:`kivy.graphics.Mesh` kivy
           graphics instructions. The paths are converted into polygons and
           assigned either to a clip rectangle or to the same canvas for
           rendering. Paths are received in matplotlib coordinates. The
           aesthetics is defined by the `GraphicsContextKivy` gc.
        '''
        polygons = path.to_polygons(transform, self.widget.width,
                                    self.widget.height)
        list_canvas_instruction = self.get_path_instructions(gc, polygons,
                                    closed=True, rgbFace=rgbFace)
        for widget, instructions in list_canvas_instruction:
            widget.canvas.add(instructions)

    def draw_markers(self, gc, marker_path, marker_trans, path,
        trans, rgbFace=None):
        '''Markers graphics instructions are stored on a dictionary and
           hashed through graphics context and rgbFace values. If a marker_path
           with the corresponding graphics context exist then the instructions
           are pulled from the markers dictionary.
        '''
        if not len(path.vertices):
            return
        # get a string representation of the path
        path_data = self._convert_path(
            marker_path,
            marker_trans + Affine2D().scale(1.0, -1.0),
            simplify=False)
        # get a string representation of the graphics context and rgbFace.
        style = str(gc._get_style_dict(rgbFace))
        dictkey = (path_data, str(style))
        # check whether this marker has been created before.
        list_instructions = self._markers.get(dictkey)
        # creating a list of instructions for the specific marker.
        if list_instructions is None:
            polygons = marker_path.to_polygons(marker_trans)
            self._markers[dictkey] = self.get_path_instructions(gc,
                                        polygons, rgbFace=rgbFace)
        # Traversing all the positions where a marker should be rendered
        for vertices, codes in path.iter_segments(trans, simplify=False):
            if len(vertices):
                x, y = vertices[-2:]
                for widget, instructions in self._markers[dictkey]:
                    widget.canvas.add(PushMatrix())
                    widget.canvas.add(Translate(x, y))
                    widget.canvas.add(instructions)
                    widget.canvas.add(PopMatrix())

    def flipy(self):
        return False

    def _convert_path(self, path, transform=None, clip=None, simplify=None,
                      sketch=None):
        if clip:
            clip = (0.0, 0.0, self.width, self.height)
        else:
            clip = None
        if _mpl_1_5:
            return _path.convert_to_string(
                path, transform, clip, simplify, sketch, 6,
                [b'M', b'L', b'Q', b'C', b'z'], False).decode('ascii')
        else:
            return _path.convert_to_svg(path, transform, clip, simplify, 6)

    def get_canvas_width_height(self):
        '''Get the actual width and height of the widget.
        '''
        return self.widget.width, self.widget.height

    def get_text_width_height_descent(self, s, prop, ismath):
        '''This method is needed specifically to calculate text positioning
           in the canvas. Matplotlib needs the size to calculate the points
           according to their layout
        '''
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
        '''Instantiate a GraphicsContextKivy object
        '''
        return GraphicsContextKivy(self.widget)

    def points_to_pixels(self, points):
        return points / 72.0 * self.dpi


class NavigationToolbar2Kivy(NavigationToolbar2):
    '''This class extends from matplotlib class NavigationToolbar2 and
       creates an action bar which is added to the main app to allow the
       following operations to the figures.

        Home: Resets the plot axes to the initial state.
        Left: Undo an operation performed.
        Right: Redo an operation performed.
        Pan: Allows to drag the plot.
        Zoom: Allows to define a rectangular area to zoom in.
        Configure: Loads a pop up for repositioning elements.
        Save: Loads a Save Dialog to generate an image.
    '''

    def __init__(self, canvas, **kwargs):
        self.actionbar = ActionBar(pos_hint={'top': 1.0})
        super(NavigationToolbar2Kivy, self).__init__(canvas)
        self.rubberband_color = (1.0, 0.0, 0.0, 1.0)
        self.lastrect = None
        self.save_dialog = Builder.load_string(textwrap.dedent('''\
            <SaveDialog>:
                text_input: text_input
                BoxLayout:
                    size: root.size
                    pos: root.pos
                    orientation: "vertical"
                    FileChooserListView:
                        id: filechooser
                        on_selection: text_input.text = self.selection and\
                        self.selection[0] or ''

                    TextInput:
                        id: text_input
                        size_hint_y: None
                        height: 30
                        multiline: False

                    BoxLayout:
                        size_hint_y: None
                        height: 30
                        Button:
                            text: "Cancel"
                            on_release: root.cancel()

                        Button:
                            text: "Save"
                            on_release: root.save(filechooser.path,\
                            text_input.text)
            '''))

    def _init_toolbar(self):
        '''A Toolbar is created with an ActionBar widget in which buttons are
           added with a specific behavior given by a callback. The buttons
           properties are given by matplotlib.
        '''
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
                action_button = ActionToggleButton(text=text, icon=fname,
                                                   group='pz')
            else:
                action_button = ActionButton(text=text, icon=fname)
            action_button.bind(on_press=getattr(self, callback))
            actionview.add_widget(action_button)

    def configure_subplots(self, *largs):
        '''It will be implemented later.'''
        pass

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_save(self):
        '''Displays a popup widget to perform a save operation.'''
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def save(self, path, filename):
        self.canvas.export_to_png(os.path.join(path, filename))
        self.dismiss_popup()

    def save_figure(self, *args):
        self.show_save()

    def draw_rubberband(self, event, x0, y0, x1, y1):
        w = abs(x1 - x0)
        h = abs(y1 - y0)
        rect = [int(val)for val in (min(x0, x1), min(y0, y1), w, h)]
        if self.lastrect is None:
            self.canvas.canvas.add(Color(*self.rubberband_color))
        else:
            self.canvas.canvas.remove(self.lastrect)
        self.lastrect = Line(rectangle=rect, width=1.0, dash_length=5.0,
                dash_offset=5.0)
        self.canvas.canvas.add(self.lastrect)

    def release_zoom(self, event):
        self.lastrect = None
        return super(NavigationToolbar2Kivy, self).release_zoom(event)


class GraphicsContextKivy(GraphicsContextBase, object):
    '''The graphics context provides the color, line styles, etc... All the
       mapping between matplotlib and kivy styling is done here.
       The GraphicsContextKivy stores colors as a RGB tuple on the unit
       interval, e.g., (0.5, 0.0, 1.0) such as in the Kivy framework.
       Lines properties and styles are set accordingly to the kivy framework
       definition for Line.
    '''

    _capd = {
        'butt': 'square',
        'projecting': 'square',
        'round': 'round',
    }
    line = {}

    def __init__(self, renderer):
        super(GraphicsContextKivy, self).__init__()
        self.renderer = renderer
        self.line['cap_style'] = self.get_capstyle()
        self.line['joint_style'] = self.get_joinstyle()
        self.line['dash_offset'] = None
        self.line['dash_length'] = None
        self.line['dash_list'] = []

    def set_capstyle(self, cs):
        '''Set the cap style based on the kivy framework cap styles.
        '''
        GraphicsContextBase.set_capstyle(self, cs)
        self.line['cap_style'] = self._capd[self._capstyle]

    def set_joinstyle(self, js):
        '''Set the join style based on the kivy framework join styles.
        '''
        GraphicsContextBase.set_joinstyle(self, js)
        self.line['join_style'] = js

    def set_dashes(self, dash_offset, dash_list):
        GraphicsContextBase.set_dashes(self, dash_offset, dash_list)
        # dash_list is a list with numbers denoting the number of points
        # in a dash and if it is on or off.
        if dash_list is not None:
            self.line['dash_list'] = dash_list
        if dash_offset is not None:
            self.line['dash_offset'] = int(dash_offset)

    def set_linewidth(self, w):
        GraphicsContextBase.set_linewidth(self, w)
        self.line['width'] = w

    def _get_style_dict(self, rgbFace):
        '''Return the style string. style is generated from the
           GraphicsContext and rgbFace
        '''
        attrib = {}
        forced_alpha = self.get_forced_alpha()
        if rgbFace is None:
            attrib['fill'] = 'none'
        else:
            if tuple(rgbFace[:3]) != (0, 0, 0):
                attrib['fill'] = str(rgbFace)
            if len(rgbFace) == 4 and rgbFace[3] != 1.0 and not forced_alpha:
                attrib['fill-opacity'] = str(rgbFace[3])

        if forced_alpha and self.get_alpha() != 1.0:
            attrib['opacity'] = str(self.get_alpha())

        offset, seq = self.get_dashes()
        if seq is not None:
            attrib['line-dasharray'] = ','.join(['%f' % val for val in seq])
            attrib['line-dashoffset'] = six.text_type(float(offset))

        linewidth = self.get_linewidth()
        if linewidth:
            rgb = self.get_rgb()
            attrib['line'] = str(rgb)
            if not forced_alpha and rgb[3] != 1.0:
                attrib['line-opacity'] = str(rgb[3])
            if linewidth != 1.0:
                attrib['line-width'] = str(linewidth)
            if self.get_joinstyle() != 'round':
                attrib['line-linejoin'] = self.get_joinstyle()
            if self.get_capstyle() != 'butt':
                attrib['line-linecap'] = _capstyle_d[self.get_capstyle()]
        return attrib


class FigureCanvasKivy(FocusBehavior, Widget, FigureCanvasBase):
    '''FigureCanvasKivy class. See module documentation for more information.

    .. versionadded:: 1.9.1
    '''

    def __init__(self, figure, **kwargs):
        Window.bind(mouse_pos=self._on_mouse_pos)
        self.bind(size=self._on_size_changed)
        self.entered_figure = True
        self.figure = figure
        super(FigureCanvasKivy, self).__init__(figure=self.figure, **kwargs)
        self._isDrawn = False

    def draw(self):
        '''Draw the figure using the KivyRenderer
        '''
        self.clear_widgets()
        self.canvas.clear()
        self._renderer = RendererKivy(self)
        self.figure.draw(self._renderer)
        self._isDrawn = True

    def on_touch_down(self, touch):
        '''Kivy Event to trigger the following matplotlib events:
           `motion_notify_event`, `scroll_event`, `button_press_event`,
           `enter_notify_event` and `leave_notify_event`
        '''
        newcoord = self.to_widget(touch.x, touch.y, relative=True)
        x = newcoord[0]
        y = newcoord[1]

        if super(FigureCanvasKivy, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos):
            FigureCanvasBase.motion_notify_event(self, x,
                                y, guiEvent=None)

            touch.grab(self)
            if(touch.button == "scrollup" or touch.button == "scrolldown"):
                FigureCanvasBase.scroll_event(self, x,
                                              y, 5, guiEvent=None)
            else:
                FigureCanvasBase.button_press_event(self, x, y,
                                                self.get_mouse_button(touch),
                                                dblclick=False, guiEvent=None)
            if self.entered_figure:
                FigureCanvasBase.enter_notify_event(self, guiEvent=None,
                                                    xy=None)
        else:
            if not self.entered_figure:
                FigureCanvasBase.leave_notify_event(self, guiEvent=None)
        return False

    def on_touch_move(self, touch):
        '''Kivy Event to trigger the following matplotlib events:
           `motion_notify_event`, `enter_notify_event` and `leave_notify_event`
        '''
        newcoord = self.to_widget(touch.x, touch.y, relative=True)
        x = newcoord[0]
        y = newcoord[1]
        inside = self.collide_point(touch.x, touch.y)
        FigureCanvasBase.motion_notify_event(self, x, y,
                                             guiEvent=None)
        if inside and self.entered_figure:
            FigureCanvasBase.enter_notify_event(self, guiEvent=None, xy=None)
            self.entered_figure = False
        elif not inside and not self.entered_figure:
            FigureCanvasBase.leave_notify_event(self, guiEvent=None)
            self.entered_figure = True
        return False

    def get_mouse_button(self, touch):
        '''Translate kivy convention for left, right and middle click button
           into matplotlib int values: 1 for left, 2 for middle and 3 for
           right.
        '''
        if touch.button == "left":
            return 1
        elif touch.button == "middle":
            return 2
        elif touch.button == "right":
            return 3
        return -1

    def on_touch_up(self, touch):
        '''Kivy Event to trigger the following matplotlib events:
           `scroll_event` and `button_release_event`.
        '''
        newcoord = self.to_widget(touch.x, touch.y, relative=True)
        x = newcoord[0]
        y = newcoord[1]
        if touch.grab_current is self:
            if touch.button == "scrollup" or touch.button == "scrolldown":
                FigureCanvasBase.scroll_event(self, x, y,
                                              5, guiEvent=None)
            else:
                FigureCanvasBase.button_release_event(self, x, y,
                                                    touch.button, guiEvent=None)
            touch.ungrab(self)
        else:
            return super(FigureCanvasKivy, self).on_touch_up(touch)
        return False

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        '''Kivy event to trigger matplotlib `key_press_event`.
        '''
        FigureCanvasBase.key_press_event(self, keycode[1], guiEvent=None)
        return super(FigureCanvasKivy, self).keyboard_on_key_down(window,
                                                    keycode, text, modifiers)

    def keyboard_on_key_up(self, window, keycode):
        '''Kivy event to trigger matplotlib `key_release_event`.
        '''
        FigureCanvasBase.key_release_event(self, keycode[1], guiEvent=None)
        return super(FigureCanvasKivy, self).keyboard_on_key_up(window, keycode)

    def _on_mouse_pos(self, *args):
        '''Kivy Event to trigger the following matplotlib events:
           `motion_notify_event`, `leave_notify_event` and
           `enter_notify_event`.
        '''
        pos = args[1]
        newcoord = self.to_widget(pos[0], pos[1], relative=True)
        x = newcoord[0]
        y = newcoord[1]

        inside = self.collide_point(*pos)
        if inside:
            FigureCanvasBase.motion_notify_event(self, x, y,
                                            guiEvent=None)
        if not inside and not self.entered_figure:
            FigureCanvasBase.leave_notify_event(self, guiEvent=None)
            self.entered_figure = True
        elif inside and self.entered_figure:
            FigureCanvasBase.enter_notify_event(self, guiEvent=None, xy=None)
            self.entered_figure = False

    def _on_size_changed(self, *args):
        '''Changes the size of the matplotlib figure based on the size of the
           widget. The widget will change size according to the parent Layout
           size.
        '''
        w, h = self.size
        dpival = self.figure.dpi
        winch = w / dpival
        hinch = h / dpival
        self.figure.set_size_inches(winch, hinch)
        self.draw()

    def callback(self, *largs):
        self.draw()

    def close_event(self, guiEvent=None):
        FigureCanvasBase.close_event(self, guiEvent=guiEvent)

    def blit(self, bbox=None):
        '''If bbox is None, blit the entire canvas to the widget. Otherwise
           blit only the area defined by the bbox.
        '''
        self.blitbox = bbox

    filetypes = FigureCanvasBase.filetypes.copy()
    filetypes['png'] = 'Portable Network Graphics'

    def print_png(self, filename, *args, **kwargs):
        '''Call the widget function to make a png of the widget. It does a
           one second delay to allow the widget to be completed.
        '''
        Clock.schedule_once(partial(self._print_image, filename), 1)

    def get_default_filetype(self):
        return 'png'

    def _print_image(self, filename, *largs):
        self.export_to_png(filename)


class FigureManagerKivy(FigureManagerBase):
    '''The FigureManager main function is to instantiate the backend navigation
       toolbar and to call show to instantiate the App.
    '''

    def __init__(self, canvas, num):
        super(FigureManagerKivy, self).__init__(canvas, num)
        self.canvas = canvas
        self.toolbar = self._get_toolbar()

    def show(self):
        pass

    def get_window_title(self):
        return EventLoop.window.title

    def set_window_title(self, title):
        EventLoop.window.title = title

    def resize(self, w, h):
        Window.size(w, h)

    def _get_toolbar(self):
        if rcParams['toolbar'] == 'toolbar2':
            toolbar = NavigationToolbar2Kivy(self.canvas)
        else:
            toolbar = None
        return toolbar

    def destroy(self):
        app = App.get_running_app()
        if app is not None:
            app.stop()

'''Now just provide the standard names that backend.__init__ is expecting
'''
FigureCanvas = FigureCanvasKivy
FigureManager = FigureManagerKivy
