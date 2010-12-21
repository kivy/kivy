'''
Graphics
========

This package assemble all low level function to draw object. The whole graphics
package is compatible OpenGL ES 2.0, and have a lot of rendering optimizations.

The basics
----------

For drawing on a screen, you will need :

    1. a :class:`Canvas` object.
    2. :class:`CanvasInstructions` objects.

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


Compilation
-----------

.. todo::

    Write more about the compilation.

'''

from kivy.graphics.instructions import *
from kivy.graphics.context_instructions import *
from kivy.graphics.vertex_instructions import *
