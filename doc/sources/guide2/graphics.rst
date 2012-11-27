.. _graphics:

Graphics
========

Introduction to Canvas
----------------------

Widgets graphical representation is done using a canvas, which you can see both
as an unlimited drawing board, and as a set of drawing instructions, there are
numerous different instructions you can apply (add) to your canvas, but there
is two main kind of them:

- :mod:`kivy.graphics.context_instructions` Context instructions
- :mod:`kivy.graphics.vertex_instructions` Vertex Instructions

Context instructions don't draw anything, but they change the results of the
Vertex instructions.

Canvas can contains subsets of instructions, to treat them specially. There are
two default subsets of this kind, that you can access as `canvas.before` and
`canvas.after`, the instructions in these groups will be executed respectively
before and after the main ones, which mean they will be respectively under and
above them.

to add a canvas instruction to a widget, you use the canvas context::

    class MyWidget(Widget):
        def __init__(self, **kwargs):
            super(MyWidget, self).__init__(**kwargs)
            with self.canvas:
                # add your instruction for main canvas here

            with self.canvas.before:
                # you can use this to add instructions rendered before

            with self.canvas.after:
                # you can use this to add instructions rendered after

Context instructions
--------------------

Context instructions manipulate the opengl context, you can rotate, translate,
and scale your canvas and attach a texture or change the drawing color, this
one is the most commonly used, but others are really useful too::

   with self.canvas.before:
       Color(1, 0, .4, mode='rgb')

Drawing instructions
--------------------

Manipulating instructions
-------------------------

