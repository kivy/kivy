'''
Box Layout
==========

.. only:: html

    .. image:: images/boxlayout.gif
        :align: right

.. only:: latex

    .. image:: images/boxlayout.png
        :align: right

:class:`BoxLayout` arranges children in a vertical or horizontal box.

To position widgets above/below each other, use a vertical BoxLayout::

    layout = BoxLayout(orientation='vertical')
    btn1 = Button(text='Hello')
    btn2 = Button(text='World')
    layout.add_widget(btn1)
    layout.add_widget(btn2)

To position widgets next to each other, use a horizontal BoxLayout. In this
example, we use 10 pixel spacing between children; the first button covers
70% of the horizontal space, the second covers 30%::

    layout = BoxLayout(spacing=10)
    btn1 = Button(text='Hello', size_hint=(.7, 1))
    btn2 = Button(text='World', size_hint=(.3, 1))
    layout.add_widget(btn1)
    layout.add_widget(btn2)

Position hints are partially working, depending on the orientation:

* If the orientation is `vertical`: `x`, `right` and `center_x` will be used.
* If the orientation is `horizontal`: `y`, `top` and `center_y` will be used.

You can check the `examples/widgets/boxlayout_poshint.py` for a live example.

.. note::

    The `size_hint` uses the available space after subtracting all the
    fixed-size widgets. For example, if you have a layout that is 800px
    wide, and add three buttons like this:

    btn1 = Button(text='Hello', size=(200, 100), size_hint=(None, None))
    btn2 = Button(text='Kivy', size_hint=(.5, 1))
    btn3 = Button(text='World', size_hint=(.5, 1))

    The first button will be 200px wide as specified, the second and third
    will be 300px each, e.g. (800-200) * 0.5


.. versionchanged:: 1.4.1
    Added support for `pos_hint`.

'''

__all__ = ('BoxLayout', )

from kivy.uix.layout import Layout
from kivy.properties import (NumericProperty, OptionProperty,
                             VariableListProperty)


class BoxLayout(Layout):
    '''Box layout class. See module documentation for more information.
    '''

    spacing = NumericProperty(0)
    '''Spacing between children, in pixels.

    :data:`spacing` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 0.
    '''

    padding = VariableListProperty([0, 0, 0, 0])
    '''Padding between layout box and children: [padding_left, padding_top,
    padding_right, padding_bottom].

    padding also accepts a two argument form [padding_horizontal,
    padding_vertical] and a one argument form [padding].

    .. versionchanged:: 1.7.0

    Replaced NumericProperty with VariableListProperty.

    :data:`padding` is a :class:`~kivy.properties.VariableListProperty` and
    defaults to [0, 0, 0, 0].
    '''

    orientation = OptionProperty('horizontal', options=(
        'horizontal', 'vertical'))
    '''Orientation of the layout.

    :data:`orientation` is an :class:`~kivy.properties.OptionProperty` and
    defaults to 'horizontal'. Can be 'vertical' or 'horizontal'.
    '''

    def __init__(self, **kwargs):
        super(BoxLayout, self).__init__(**kwargs)
        self.bind(
            spacing=self._trigger_layout,
            padding=self._trigger_layout,
            children=self._trigger_layout,
            orientation=self._trigger_layout,
            parent=self._trigger_layout,
            size=self._trigger_layout,
            pos=self._trigger_layout)

    def do_layout(self, *largs):
        # optimize layout by preventing looking at the same attribute in a loop
        len_children = len(self.children)
        if len_children == 0:
            return
        selfx = self.x
        selfy = self.y
        selfw = self.width
        selfh = self.height
        padding_left = self.padding[0]
        padding_top = self.padding[1]
        padding_right = self.padding[2]
        padding_bottom = self.padding[3]
        spacing = self.spacing
        orientation = self.orientation
        padding_x = padding_left + padding_right
        padding_y = padding_top + padding_bottom

        # calculate maximum space used by size_hint
        stretch_weight_x = 0.
        stretch_weight_y = 0.
        minimum_size_x = padding_x + spacing * (len_children - 1)
        minimum_size_y = padding_y + spacing * (len_children - 1)
        for w in self.children:
            shw = w.size_hint_x
            shh = w.size_hint_y
            if shw is None:
                minimum_size_x += w.width
            else:
                stretch_weight_x += shw
            if shh is None:
                minimum_size_y += w.height
            else:
                stretch_weight_y += shh

        if orientation == 'horizontal':
            x = padding_left
            stretch_space = max(0.0, selfw - minimum_size_x)
            for c in reversed(self.children):
                shw = c.size_hint_x
                shh = c.size_hint_y
                w = c.width
                h = c.height
                cx = selfx + x
                cy = selfy + padding_bottom

                if shw:
                    w = stretch_space * shw / stretch_weight_x
                if shh:
                    h = shh * (selfh - padding_y)

                for key, value in c.pos_hint.items():
                    posy = value * (selfh - padding_y)
                    if key == 'y':
                        cy += padding_bottom + posy
                    elif key == 'top':
                        cy += padding_bottom + posy - h
                    elif key == 'center_y':
                        cy += padding_bottom - h / 2. + posy

                c.x = cx
                c.y = cy
                c.width = w
                c.height = h
                x += w + spacing

        if orientation == 'vertical':
            y = padding_bottom
            stretch_space = max(0.0, selfh - minimum_size_y)
            for c in self.children:
                shw = c.size_hint_x
                shh = c.size_hint_y
                w = c.width
                h = c.height
                cx = selfx + padding_left
                cy = selfy + y

                if shh:
                    h = stretch_space * shh / stretch_weight_y
                if shw:
                    w = shw * (selfw - padding_x)

                for key, value in c.pos_hint.items():
                    posx = value * (selfw - padding_x)
                    if key == 'x':
                        cx += padding_left + posx
                    elif key == 'right':
                        cx += padding_left + posx - w
                    elif key == 'center_x':
                        cx += padding_left - w / 2. + posx

                c.x = cx
                c.y = cy
                c.width = w
                c.height = h
                y += h + spacing

    def add_widget(self, widget, index=0):
        widget.bind(
            pos_hint=self._trigger_layout)
        return super(BoxLayout, self).add_widget(widget, index)

    def remove_widget(self, widget):
        widget.unbind(
            pos_hint=self._trigger_layout)
        return super(BoxLayout, self).remove_widget(widget)
