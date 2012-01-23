Introduction to the Kivy Language
=================================

In this part of the documentation, we'll see why the Kivy language was created,
and how it changes the way you code in Kivy.

Widget graphics
---------------

Per-frame drawing
~~~~~~~~~~~~~~~~~

Let's take a look at drawing widgets. By default, widgets contain an empty
``Canvas`` with no graphics instructions. Some widgets, like ``Button`` or
``Label``, come with some default graphics instructions to draw their background
and text. Consider a ``Button`` widget; how do we draw its background and text?
In some toolkits, you need to overload a ``draw()`` method and put your drawing
code in it, like::

    def draw(self):
        set_color(.5, .5, .5)
        draw_rectangle(x=self.x, y=self.y, width=self.width, height=self.height)
        set_color(1, 1, 1)
        draw_label(text=self.text, x=self.center_x, y=self.center_y, halign='center')

We think this way is obsolete because:

#. You don't know what you'll draw until you execute the method
#. You don't know if the drawing will change, or how it will change
#. And because of that, you cannot predict any optimizations.

Kivy's approach
~~~~~~~~~~~~~~~

In Kivy, you create graphics instructions and draw them to the
widget's ``Canvas``. A possible approach to drawing our ``Button``
could be::

    with self.canvas:
        Color(.5, .5, .5)
        Rectangle(pos=self.pos, size=self.size)
        Color(1, 1, 1)
        cx = self.center_x - self.texture_size[0] / 2.
        cy = self.center_y - self.texture_size[1] / 2.
        Rectangle(texture=self.texture, pos=(cx, cy), size=self.texture_size)

That will work... until the widget is moving or resizing itself. If a widget is
moving, ``self.pos`` is going to change, but we aren't updating the ``Rectangle``'s
position!

We know that ``pos`` and ``size`` are instances of the Kivy
:class:`~kivy.properties.Property` class, and so, we can bind callbacks to update
the graphics. In order to do that, we bind on both and update a method to clear and recreate
all the graphics::

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
recreating them. You can save the graphics and update them independently::

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

That's better. Graphics instructions are not deleted and recreated, we are just
updating their ``pos`` and ``size``. But the code is getting more complex, and
for the text rectangle, the update code is duplicated.

It can be complex to have the perfect graphics code in pure python. This
is where the Kivy language can be useful.

Usage of the Kivy language for graphics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Kivy language has a lot of benefits for this example ``Button``. You can
create a rule that will match your widget, create graphics instructions, and
update their properties according to a python expression. Here is the complete
example for our widget. This is the "yourwidget.kv" kivy language
part::

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

Yes, not a single line of graphics code has been written in Python. You'd like
to know how it's working, wouldn't you? Good.

The first line indicates a rule (like a CSS (Cascading Style Sheets) rule) that
will match all the classes named by the rule's name::

    <YourWidget>:

Then, you specify the canvas's graphics instruction::

    canvas:
        # ...
        Rectangle:
            pos: self.pos
            size: self.size

Inside the canvas, you put a Rectangle graphics instruction. The instruction's
``pos`` and ``size`` will be updated when the expression after the colon (":")
changes. That means, ``Rectangle.pos`` will change when ``YourWidget.pos``
changes.

More complex expressions can be used, like::

    pos: self.center_x - self.texture_size[0] / 2., self.center_y - self.texture_size[1] / 2.

This expression listens for a change in ``center_x``, ``center_y``, and
``texture_size``. If one of them is changing, the expression will be
re-evaluated, and update the ``Rectangle.pos`` field.
