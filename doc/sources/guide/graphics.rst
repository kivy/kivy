.. _graphics:

Graphics
========

Introduction to Canvas
----------------------

Widgets graphical representation is done using a canvas, which you can see both
as an unlimited drawing board, and as a set of drawing instructions, there are
numerous different instructions you can apply (add) to your canvas, but there
is two main kind of them:

- :mod:`context instructions <kivy.graphics.context_instructions>`
- :mod:`vertex instructions <kivy.graphics.vertex_instructions>`

Context instructions don't draw anything, but they change the results of the
vertex instructions.

Canvasses can contain two subsets of instructions. They are the
:mod:`canvas.before <kivy.graphics.Canvas.before>` and the :mod:`canvas.after
<kivy.graphics.Canvas.after>` instruction groups.  The instructions in these
groups will be executed before and after the :mod:`~kivy.graphics.canvas` group
respectively. This means that they will appear under (be executed before) and
above (be executed after) them.
Thoses groups are not created until the user accesses them.

To add a canvas instruction to a widget, you use the canvas context:

.. code-block:: python

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
and scale your canvas, attach a texture or change the drawing color, this one
is the most commonly used, but others are really useful too::

   with self.canvas.before:
       Color(1, 0, .4, mode='rgb')

Drawing instructions
--------------------

Drawing instructions are ranging from very simple ones, to draw a line or a
polygon, to more complex ones, like meshes or bezier curves::

    with self.canvas:
       # draw a line using the default color
       Line(points=(x1, y1, x2, y2, x3, y3))

       # lets draw a semi-transparent red square
       Color(1, 0, 0, .5, mode='rgba')
       Rect(pos=self.pos, size=self.size)

Manipulating instructions
-------------------------

Sometime, you want to update or remove the instructions you added to a canvas,
this can be done in various ways depending on your needs:

You can keep a reference to your instructions and update them::

    class MyWidget(Widget):
        def __init__(self, **kwargs):
            super(MyWidget, self).__init__(**kwargs)
            with self.canvas:
                self.rect = Rectangle(pos=self.pos, size=self.size)
    
            self.bind(pos=self.update_rect)
            self.bind(size=self.update_rect)
    
        def update_rect(self, *args):
            self.rect.pos = self.pos
            self.rect.size = self.size


Or you can clean your canvas and start fresh::

    class MyWidget(Widget):
        def __init__(self, **kwargs):
            super(MyWidget, self).__init__(**kwargs)
            self.draw_my_stuff()

            self.bind(pos=self.draw_my_stuff)
            self.bind(size=self.draw_my_stuff)

        def draw_my_stuff(self):
            self.canvas.clear()

            with self.canvas:
                self.rect = Rectangle(pos=self.pos, size=self.size)

