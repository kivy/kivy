'''
Graphics
========

This package assemble all low level function to draw object. The whole graphics
package is compatible OpenGL ES 2.0, and have a lot of rendering optimizations.

The basics
----------

For drawing on a screen, you will need :

    1. a :class:`~kivy.graphics.instructions.Canvas` object.
    2. :class:`~kivy.graphics.instructions.Instruction` objects.

Each widget in Kivy already have by default their :class:`Canvas`. When you are
creating a widget, you can create all the instructions needed for drawing. If
`self` is your current widget, you can do::

    from kivy.graphics import *
    with self.canvas:
        # Add a red color
        Color(1., 0, 0)

        # Add a rectangle
        Rectangle(pos=(10, 10), size=(500, 500))

The instructions :class:`Color` and :class:`Rectangle` are automaticly added to
the canvas object, and will be used when the window drawing will happen.

'''

from kivy.graphics.instructions import Callback, Canvas, CanvasBase, \
    ContextInstruction, Instruction, InstructionGroup, RenderContext, \
    VertexInstruction # pyflakes.ignore
from kivy.graphics.context_instructions import BindTexture, Color, \
    MatrixInstruction, PopMatrix, PushMatrix, Rotate, Scale, \
    Translate, gl_init_resources
from kivy.graphics.vertex_instructions import Bezier, BorderImage, Ellipse, \
    GraphicException, Line, Mesh, Point, Quad, Rectangle, Triangle
from kivy.graphics.stencil_instructions import StencilPop, StencilPush, \
    StencilUse
from kivy.graphics.fbo import Fbo

# very hacky way to avoid pyflakes warning...
__all__ = (Bezier.__name__, BindTexture.__name__, BorderImage.__name__,
    Callback.__name__, Canvas.__name__, CanvasBase.__name__, Color.__name__,
    ContextInstruction.__name__, Ellipse.__name__, Fbo.__name__,
    GraphicException.__name__, Instruction.__name__,
    InstructionGroup.__name__, Line.__name__, MatrixInstruction.__name__,
    Mesh.__name__, Point.__name__, PopMatrix.__name__, PushMatrix.__name__,
    Quad.__name__, Rectangle.__name__, RenderContext.__name__,
    Rotate.__name__, Scale.__name__, StencilPop.__name__,
    StencilPush.__name__, StencilUse.__name__, Translate.__name__,
    Triangle.__name__, VertexInstruction.__name__,
    gl_init_resources.__name__)

