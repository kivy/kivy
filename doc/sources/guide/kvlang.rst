Introduction to Kivy Language
=============================

In this part of the documentation, we'll see why Kivy language have been
introduced, and how it's changing the paradigm of the coding part.

Widget graphics
---------------

Per-frame drawing
~~~~~~~~~~~~~~~~~

In term of graphics, a widget by default doesn't contain any drawing. Some
widgets have defaults graphics instructions like Button, Label, etc. If we take
a Button, we need to draw the background and the text.  In some toolkits, you
need to overload a "draw()" method and put your drawing in it, like::

    def draw(self):
        set_color(.5, .5, .5)
        draw_rectangle(x=self.x, y=self.y, width=self.width, height=self.height)
        set_color(1, 1, 1)
        draw_label(text=self.text, x=self.center_x, y=self.center_y, halign='center')

We think this way is obsolete because:

#. You don't know what you'll draw until you execute the method
#. You don't know if the drawing will change, and how it will change
#. And because of that, you cannot predict any optimizations.

Kivy approach
~~~~~~~~~~~~~

In Kivy, you are creating graphics instructions one by one, and put them in the
widget Canvas. A possible approach would be::

    with self.canvas:
        Color(.5, .5, .5)
        Rectangle(pos=self.pos, size=self.size)
        Color(1, 1, 1)
        cx = self.center_x - self.texture_size[0] / 2.
        cy = self.center_y - self.texture_size[1] / 2.
        Rectangle(texture=self.texture, pos=(cx, cy), size=self.texture_size)

That will work... until the widget is moving or resizing itself. If a widget is
moving, self.pos is going to change. But we are not updating the Rectangle()
position !

We know that pos and size are Kivy :class:`~kivy.properties.Property` class,
and so, we can bind ourself to update the graphics. So we can bind on both and
update a method to clear and recreate all the graphics::

    class YourWidget(Widget):
        # ...
        def __init__(self, **kwargs):
            super(YourWidget, self).__init__(**kwargs)
            self.update_graphics()
            self.bind(pos=self.update_graphics,
                size=self.update_graphics)

        def update_graphics(self, *largs):
            self.canvas.clear()
            with self.canvas:
                Color(.5, .5, .5)
                Rectangle(pos=self.pos, size=self.size)
                Color(1, 1, 1)
                cx = self.center_x - self.texture_size[0] / 2.
                cy = self.center_y - self.texture_size[1] / 2.
                Rectangle(texture=self.texture, pos=(cx, cy), size=self.texture_size)

This method is still not perfect, because we are deleting all the graphics, and
recreate them. So you can save the graphics and update them independently::

    class YourWidget(Widget):
        # ...
        def __init__(self, **kwargs):
            super(YourWidget, self).__init__(**kwargs)

            # create the graphics
            with self.canvas:
                Color(.5, .5, .5)
                self.rect_bg = Rectangle(
                    pos=self.pos, size=self.size)
                Color(1, 1, 1)
                cx = self.center_x - self.texture_size[0] / 2.
                cy = self.center_y - self.texture_size[1] / 2.
                self.rect_text = Rectangle(
                    texture=self.texture, pos=(cx, cy), size=self.texture_size)

            self.bind(pos=self.update_graphics_pos,
                size=self.update_graphics_size)

        def update_graphics_pos(self, instance, value):
            self.rect_bg.pos = value
            cx = self.center_x - self.texture_size[0] / 2.
            cy = self.center_y - self.texture_size[1] / 2.
            self.rect_text.pos = cx, cy

        def update_graphics_size(self, instance, value):
            self.rect_bg.size = value
            cx = self.center_x - self.texture_size[0] / 2.
            cy = self.center_y - self.texture_size[1] / 2.
            self.rect_text.pos = cx, cy

It's better. Graphics instructions are not deleted and recreated, we are just
updating their pos and size. But the code is getting more complex, and for the
text rectangle, the update code is duplicated.

It can be complex to have the perfect code in pure python with graphics. This
is where Kivy language can be useful.

Usage of Kivy language for graphics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Kivy language have a lot of benefits for that example. You can create a rule
that will match your widget, create graphics instructions, and update their
properties according to a python expression.  Here is the complete example for
our widget. For example, this is the "yourwidget.kv" kivy language part::

    #:kivy 1.0

    <YourWidget>:
        canvas:
            Color:
                rgb: .5, .5, .5
            Rectangle:
                pos: self.pos
                size: self.size
            Color:
                rgb: 1, 1, 1
            Rectangle:
                texture: self.texture
                pos: self.center_x - self.texture_size[0] / 2., self.center_y - self.texture_size[1] / 2.
                size: self.texture_size

And here is your "yourwidget.py" python part::

    from kivy.lang import Builder
    from kivy.widget import Widget

    Builder.load_file('yourwidget.kv')

    class YourWidget(Widget):
        # ...
        pass

Yes, not a single graphics have been created in the Python part. You want to
understand how it's working ? Ok.

The first line is indicating a rule (like CSS rule) that will match all the
class named by the rule name::

    <YourWidget>:

Then said that you'll change the canvas instruction::

    canvas:
        # ...
        Rectangle:
            pos: self.pos
            size: self.size

Inside the canvas, you'll put a Rectangle graphics instruction. The instruction
pos/size will be updated when the right part of the expression will change.
That's mean: "Rectangle.pos" will change when "YourWidget.pos" will change.

More complex expression can be put like::

    pos: self.center_x - self.texture_size[0] / 2., self.center_y - self.texture_size[1] / 2.

This expression will listen for a change in "center_x", "center_y",
"texture_size". If one of them is changing, the expression will be reevaluated,
and update the Rectangle.pos.
