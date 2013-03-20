.. _graphics:

Graphics
========

Introduction to the Canvas
--------------------------

A widgets graphical representation is done using a canvas, which you can see both
as an unlimited drawing board and as a set of drawing instructions. There are
numerous instructions you can apply (add) to your canvas, but there
are two main kinds:

- :mod:`Context instructions <kivy.graphics.context_instructions>`
- :mod:`Vertex instructions <kivy.graphics.vertex_instructions>`

Context instructions don't draw anything, but they change the results of the
Vertex instructions.

Canvasses can contain two subsets of instructions. They are the
:mod:`canvas.before <kivy.graphics.Canvas.before>`
and the :mod:`canvas.after <kivy.graphics.Canvas.after>` instruction groups.
The instructions in these groups will be executed before and after the
:mod:`~kivy.graphics.canvas` group respectively. This  means that they will appear
under (be executed before) and above (be executed after) them.

To add a canvas instruction to a widget, you use the canvas context::

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

Context instructions manipulate the opengl context. You can rotate, translate,
scale, attach a texture or change the drawing color of the context. Changing the 
color is the most commonly used, but the others are really useful too::

   with self.canvas.before:
       Color(1, 0, .4, mode='rgb')

Drawing instructions
--------------------

Drawing instructions range from the very simple (drawing a line or a
polygon) to the more complex (like meshes or bezier curves)::

    with self.canvas:
       # draw a line using the default color
       Line(points=(x1, y1, x2, y2, x3, y3))

       # lets draw a semi-transparent red square
       Color(1, 0, 0, .5, mode='rgba')
       Rect(pos=self.pos, size=self.size)

Manipulating instructions
-------------------------

Sometimes you want to update or remove the instructions you have added to a canvas.
This can be done in various ways, depending on your needs.

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

