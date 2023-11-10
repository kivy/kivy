'''
Graphics
========

This package assembles many low level functions used for drawing. The whole
graphics package is compatible with OpenGL ES 2.0 and has many rendering
optimizations.

The basics
----------

For drawing on a screen, you will need :

    1. a :class:`~kivy.graphics.instructions.Canvas` object.
    2. :class:`~kivy.graphics.instructions.Instruction` objects.

Each :class:`~kivy.uix.widget.Widget`
in Kivy already has a :class:`Canvas` by default. When you create
a widget, you can create all the instructions needed for drawing. If
`self` is your current widget, you can do::

    from kivy.graphics import *
    with self.canvas:
        # Add a red color
        Color(1., 0, 0)

        # Add a rectangle
        Rectangle(pos=(10, 10), size=(500, 500))

The instructions :class:`Color` and :class:`Rectangle` are automatically added
to the canvas object and will be used when the window is drawn.

.. note::

    Kivy drawing instructions are not automatically relative to the position
    or size of the widget. You, therefore, need to consider these factors when
    drawing. In order to make your drawing instructions relative to the widget,
    the instructions need either to be
    declared in the :mod:`KvLang <kivy.lang>` or bound to pos and size changes.
    Please see :ref:`adding_widget_background` for more detail.

GL Reloading mechanism
----------------------

.. versionadded:: 1.2.0

During the lifetime of the application, the OpenGL context might be lost. This
happens:

- when the window is resized on OS X or the Windows platform and you're
  using pygame as a window provider. This is due to SDL 1.2. In the SDL 1.2
  design, it needs to recreate a GL context everytime the window is
  resized. This was fixed in SDL 1.3 but pygame is not yet available on it
  by default.

- when Android releases the app resources: when your application goes to the
  background, Android might reclaim your opengl context to give the
  resource to another app. When the user switches back to your application, a
  newly created gl context is given to your app.

Starting from 1.2.0, we have introduced a mechanism for reloading all the
graphics resources using the GPU: Canvas, FBO, Shader, Texture, VBO,
and VertexBatch:

- VBO and VertexBatch are constructed by our graphics instructions. We have all
  the data needed to reconstruct when reloading.

- Shader: same as VBO, we store the source and values used in the
  shader so we are able to recreate the vertex/fragment/program.

- Texture: if the texture has a source (an image file or atlas), the image
  is reloaded from the source and reuploaded to the GPU.

You should cover these cases yourself:

- Textures without a source: if you manually created a texture and manually
  blit data / a buffer to it, you must handle the reloading yourself. Check the
  :doc:`api-kivy.graphics.texture` to learn how to manage that case. (The text
  rendering already generates the texture and handles the reloading. You
  don't need to reload text yourself.)

- FBO: if you added / removed / drew things multiple times on the FBO, we
  can't reload it. We don't keep a history of the instructions put on it.
  As for textures without a source, check the :doc:`api-kivy.graphics.fbo` to
  learn how to manage that case.

'''

from kivy.graphics.instructions import Callback, Canvas, CanvasBase, \
    ContextInstruction, Instruction, InstructionGroup, RenderContext, \
    VertexInstruction
from kivy.graphics.context_instructions import BindTexture, Color, \
    PushState, ChangeState, PopState, MatrixInstruction, ApplyContextMatrix, \
    PopMatrix, PushMatrix, Rotate, Scale, Translate, LoadIdentity, \
    UpdateNormalMatrix, gl_init_resources
from kivy.graphics.vertex_instructions import Bezier, BorderImage, Ellipse, \
    GraphicException, Line, Mesh, Point, Quad, Rectangle, RoundedRectangle, \
    Triangle, SmoothLine, SmoothRectangle, SmoothEllipse, \
    SmoothRoundedRectangle, SmoothQuad, SmoothTriangle
from kivy.graphics.stencil_instructions import StencilPop, StencilPush, \
    StencilUse, StencilUnUse
from kivy.graphics.gl_instructions import ClearColor, ClearBuffers
from kivy.graphics.fbo import Fbo
from kivy.graphics.boxshadow import BoxShadow
from kivy.graphics.scissor_instructions import ScissorPush, ScissorPop

# very hacky way to avoid pyflakes warning...
__all__ = (Bezier.__name__, BindTexture.__name__, BorderImage.__name__,
           Callback.__name__, Canvas.__name__, CanvasBase.__name__,
           Color.__name__, ContextInstruction.__name__,
           Ellipse.__name__, Fbo.__name__, GraphicException.__name__,
           Instruction.__name__, InstructionGroup.__name__,
           Line.__name__, SmoothLine.__name__, MatrixInstruction.__name__,
           Mesh.__name__, Point.__name__, PopMatrix.__name__,
           PushMatrix.__name__, Quad.__name__, Rectangle.__name__,
           RenderContext.__name__, Rotate.__name__, Scale.__name__,
           StencilPop.__name__, StencilPush.__name__, StencilUse.__name__,
           StencilUnUse.__name__, Translate.__name__, Triangle.__name__,
           VertexInstruction.__name__, ClearColor.__name__,
           ClearBuffers.__name__, gl_init_resources.__name__,
           PushState.__name__, ChangeState.__name__, PopState.__name__,
           ApplyContextMatrix.__name__, UpdateNormalMatrix.__name__,
           LoadIdentity.__name__, BoxShadow.__name__, SmoothEllipse.__name__,
           SmoothRoundedRectangle.__name__, SmoothRectangle.__name__,
           SmoothQuad.__name__, SmoothTriangle.__name__,
           )
