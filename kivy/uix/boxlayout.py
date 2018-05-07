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
    wide, and add three buttons like this::

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
                             VariableListProperty, ReferenceListProperty)


class BoxLayout(Layout):
    '''Box layout class. See module documentation for more information.
    '''

    spacing = NumericProperty(0)
    '''Spacing between children, in pixels.

    :attr:`spacing` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 0.
    '''

    padding = VariableListProperty([0, 0, 0, 0])
    '''Padding between layout box and children: [padding_left, padding_top,
    padding_right, padding_bottom].

    padding also accepts a two argument form [padding_horizontal,
    padding_vertical] and a one argument form [padding].

    .. versionchanged:: 1.7.0
        Replaced NumericProperty with VariableListProperty.

    :attr:`padding` is a :class:`~kivy.properties.VariableListProperty` and
    defaults to [0, 0, 0, 0].
    '''

    orientation = OptionProperty('horizontal', options=(
        'horizontal', 'vertical'))
    '''Orientation of the layout.

    :attr:`orientation` is an :class:`~kivy.properties.OptionProperty` and
    defaults to 'horizontal'. Can be 'vertical' or 'horizontal'.
    '''

    minimum_width = NumericProperty(0)
    '''Automatically computed minimum width needed to contain all children.

    .. versionadded:: 1.10.0

    :attr:`minimum_width` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0. It is read only.
    '''

    minimum_height = NumericProperty(0)
    '''Automatically computed minimum height needed to contain all children.

    .. versionadded:: 1.10.0

    :attr:`minimum_height` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0. It is read only.
    '''

    minimum_size = ReferenceListProperty(minimum_width, minimum_height)
    '''Automatically computed minimum size needed to contain all children.

    .. versionadded:: 1.10.0

    :attr:`minimum_size` is a
    :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`minimum_width`, :attr:`minimum_height`) properties. It is read
    only.
    '''

    def __init__(self, **kwargs):
        super(BoxLayout, self).__init__(**kwargs)
        update = self._trigger_layout
        fbind = self.fbind
        fbind('spacing', update)
        fbind('padding', update)
        fbind('children', update)
        fbind('orientation', update)
        fbind('parent', update)
        fbind('size', update)
        fbind('pos', update)

    def _iterate_layout(self, sizes):
        # optimize layout by preventing looking at the same attribute in a loop
        len_children = len(sizes)
        padding_left, padding_top, padding_right, padding_bottom = self.padding
        spacing = self.spacing
        orientation = self.orientation
        padding_x = padding_left + padding_right
        padding_y = padding_top + padding_bottom

        # calculate maximum space used by size_hint
        stretch_sum = 0.
        has_bound = False
        hint = [None] * len_children
        # min size from all the None hint, and from those with sh_min
        minimum_size_bounded = 0
        if orientation == 'horizontal':
            minimum_size_y = 0
            minimum_size_none = padding_x + spacing * (len_children - 1)

            for i, ((w, h), (shw, shh), _, (shw_min, shh_min),
                    (shw_max, _)) in enumerate(sizes):
                if shw is None:
                    minimum_size_none += w
                else:
                    hint[i] = shw
                    if shw_min:
                        has_bound = True
                        minimum_size_bounded += shw_min
                    elif shw_max is not None:
                        has_bound = True
                    stretch_sum += shw

                if shh is None:
                    minimum_size_y = max(minimum_size_y, h)
                elif shh_min:
                    minimum_size_y = max(minimum_size_y, shh_min)

            minimum_size_x = minimum_size_bounded + minimum_size_none
            minimum_size_y += padding_y
        else:
            minimum_size_x = 0
            minimum_size_none = padding_y + spacing * (len_children - 1)

            for i, ((w, h), (shw, shh), _, (shw_min, shh_min),
                    (_, shh_max)) in enumerate(sizes):
                if shh is None:
                    minimum_size_none += h
                else:
                    hint[i] = shh
                    if shh_min:
                        has_bound = True
                        minimum_size_bounded += shh_min
                    elif shh_max is not None:
                        has_bound = True
                    stretch_sum += shh

                if shw is None:
                    minimum_size_x = max(minimum_size_x, w)
                elif shw_min:
                    minimum_size_x = max(minimum_size_x, shw_min)

            minimum_size_y = minimum_size_bounded + minimum_size_none
            minimum_size_x += padding_x

        self.minimum_size = minimum_size_x, minimum_size_y
        # do not move the w/h get above, it's likely to change on above line
        selfx = self.x
        selfy = self.y

        if orientation == 'horizontal':
            stretch_space = max(0.0, self.width - minimum_size_none)
            dim = 0
        else:
            stretch_space = max(0.0, self.height - minimum_size_none)
            dim = 1

        if has_bound:
            # make sure the size_hint_min/max are not violated
            if stretch_space < 1e-9:
                # there's no space, so just set to min size or zero
                stretch_sum = stretch_space = 1.

                for i, val in enumerate(sizes):
                    sh = val[1][dim]
                    if sh is None:
                        continue

                    sh_min = val[3][dim]
                    if sh_min is not None:
                        hint[i] = sh_min
                    else:
                        hint[i] = 0.  # everything else is zero
            else:
                # hint gets updated in place
                self.layout_hint_with_bounds(
                    stretch_sum, stretch_space, minimum_size_bounded,
                    (val[3][dim] for val in sizes),
                    (elem[4][dim] for elem in sizes), hint)

        if orientation == 'horizontal':
            x = padding_left + selfx
            size_y = self.height - padding_y
            for i, (sh, ((w, h), (_, shh), pos_hint, _, _)) in enumerate(
                    zip(reversed(hint), reversed(sizes))):
                cy = selfy + padding_bottom

                if sh:
                    w = max(0., stretch_space * sh / stretch_sum)
                if shh:
                    h = max(0, shh * size_y)

                for key, value in pos_hint.items():
                    posy = value * size_y
                    if key == 'y':
                        cy += posy
                    elif key == 'top':
                        cy += posy - h
                    elif key == 'center_y':
                        cy += posy - (h / 2.)

                yield len_children - i - 1, x, cy, w, h
                x += w + spacing

        else:
            y = padding_bottom + selfy
            size_x = self.width - padding_x
            for i, (sh, ((w, h), (shw, _), pos_hint, _, _)) in enumerate(
                    zip(hint, sizes)):
                cx = selfx + padding_left

                if sh:
                    h = max(0., stretch_space * sh / stretch_sum)
                if shw:
                    w = max(0, shw * size_x)

                for key, value in pos_hint.items():
                    posx = value * size_x
                    if key == 'x':
                        cx += posx
                    elif key == 'right':
                        cx += posx - w
                    elif key == 'center_x':
                        cx += posx - (w / 2.)

                yield i, cx, y, w, h
                y += h + spacing

    def do_layout(self, *largs):
        children = self.children
        if not children:
            l, t, r, b = self.padding
            self.minimum_size = l + r, t + b
            return

        for i, x, y, w, h in self._iterate_layout(
                [(c.size, c.size_hint, c.pos_hint, c.size_hint_min,
                  c.size_hint_max) for c in children]):
            c = children[i]
            c.pos = x, y
            shw, shh = c.size_hint
            if shw is None:
                if shh is not None:
                    c.height = h
            else:
                if shh is None:
                    c.width = w
                else:
                    c.size = (w, h)

    def add_widget(self, widget, index=0, canvas=None):
        widget.fbind('pos_hint', self._trigger_layout)
        return super(BoxLayout, self).add_widget(widget, index, canvas)

    def remove_widget(self, widget):
        widget.funbind('pos_hint', self._trigger_layout)
        return super(BoxLayout, self).remove_widget(widget)
