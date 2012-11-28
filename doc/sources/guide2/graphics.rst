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

Sometime, you want to update or remove the instructions you added to an canvas,
this can be done in various ways depending on your needs:

You can keep a reference to your instruction and update them::

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


Or you can clean your canva and start fresh::

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

