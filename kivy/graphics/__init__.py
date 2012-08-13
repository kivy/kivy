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

GL Reloading mechanism
----------------------

.. versionadded:: 1.2.0

During the lifetime of the application, the OpenGL context might be lost. This
is happening:

- When window is resized, on MacOSX and Windows platform, if you're using pygame
  as window provider, cause of SDL 1.2. In the SDL 1.2 design, it need to
  recreate a GL context everytime the window is resized. This is fixed in SDL
  1.3, but pygame is not available on it by default yet.

- when Android release the app resources: when your application goes to
  background, android system might reclaim your opengl context to give the
  resource to another app. When the user switch back to your application, a
  newly gl context is given to you.

Starting from 1.2.0, we introduced a mechanism for reloading all the graphics
resources using the GPU: Canvas, FBO, Shader, Texture, VBO, VertexBatch:

- VBO and VertexBatch are constructed by our graphics instructions. We have all
  the data to reconstruct when reloading.

- Shader: same as VBO, we store the source and values used in the shader, we are
  able to recreate the vertex/fragment/program.

- Texture: if the texture have a source (an image file, an atlas...), the image
  is reloaded from the source, and reuploaded to the GPU.

You should cover theses cases yourself:

- Texture without source: if you manually created a texture, and manually blit
  data / buffer to it, you must handle the reloading yourself. Check the
  :doc:`api-kivy.graphics.texture` to learn how to manage that case.  (The text
  rendering is generating the texture, and handle already the reloading. You
  don't need to reload text yourself.)

- FBO: if you added / removed / drawed things multiple times on the FBO, we
  can't reload it. We don't keep a history of the instruction put on it. As
  texture without source, Check the :doc:`api-kivy.graphics.fbo` to learn how to
  manage that case.

'''

from kivy.graphics.instructions import Callback, Canvas, CanvasBase, \
    ContextInstruction, Instruction, InstructionGroup, RenderContext, \
    VertexInstruction
from kivy.graphics.context_instructions import BindTexture, Color, \
    MatrixInstruction, PopMatrix, PushMatrix, Rotate, Scale, \
    Translate, gl_init_resources
from kivy.graphics.vertex_instructions import Bezier, BorderImage, Ellipse, \
    GraphicException, Line, Mesh, Point, Quad, Rectangle, Triangle
from kivy.graphics.stencil_instructions import StencilPop, StencilPush, \
    StencilUse, StencilUnUse
from kivy.graphics.gl_instructions import ClearColor, ClearBuffers
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
    StencilPush.__name__, StencilUse.__name__, StencilUnUse.__name__,
    Translate.__name__, Triangle.__name__, VertexInstruction.__name__,
    ClearColor.__name__, ClearBuffers.__name__,
    gl_init_resources.__name__)

