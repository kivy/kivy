'''
Anchor Layout
=============

.. only:: html

    .. image:: images/anchorlayout.gif
        :align: right

.. only:: latex

    .. image:: images/anchorlayout.png
        :align: right

The :class:`AnchorLayout` aligns its children to a border (top, bottom,
left, right) or center.


To draw a button in the lower-right corner::

    layout = AnchorLayout(
        anchor_x='right', anchor_y='bottom')
    btn = Button(text='Hello World')
    layout.add_widget(btn)

'''

__all__ = ('AnchorLayout', )

from kivy.uix.layout import Layout
from kivy.properties import OptionProperty, VariableListProperty


class AnchorLayout(Layout):
    '''Anchor layout class. See the module documentation for more information.
    '''

    padding = VariableListProperty([0, 0, 0, 0])
    '''Padding between the widget box and its children, in pixels:
    [padding_left, padding_top, padding_right, padding_bottom].

    padding also accepts a two argument form [padding_horizontal,
    padding_vertical] and a one argument form [padding].

    :attr:`padding` is a :class:`~kivy.properties.VariableListProperty` and
    defaults to [0, 0, 0, 0].
    '''

    anchor_x = OptionProperty('center', options=(
        'left', 'center', 'right'))
    '''Horizontal anchor.

    :attr:`anchor_x` is an :class:`~kivy.properties.OptionProperty` and
    defaults to 'center'. It accepts values of 'left', 'center' or
    'right'.
    '''

    anchor_y = OptionProperty('center', options=(
        'top', 'center', 'bottom'))
    '''Vertical anchor.

    :attr:`anchor_y` is an :class:`~kivy.properties.OptionProperty` and
    defaults to 'center'. It accepts values of 'top', 'center' or
    'bottom'.
    '''

    def __init__(self, **kwargs):
        super(AnchorLayout, self).__init__(**kwargs)
        fbind = self.fbind
        update = self._trigger_layout
        fbind('children', update)
        fbind('parent', update)
        fbind('padding', update)
        fbind('anchor_x', update)
        fbind('anchor_y', update)
        fbind('size', update)
        fbind('pos', update)

    def do_layout(self, *largs):
        _x, _y = self.pos
        width = self.width
        height = self.height
        anchor_x = self.anchor_x
        anchor_y = self.anchor_y
        padding = self.padding

        for c in self.children:
            x, y = _x, _y
            w, h = c.size
            if c.size_hint[0] is not None:
                w = c.size_hint[0] * width - (padding[0] + padding[2])
            if c.size_hint[1] is not None:
                h = c.size_hint[1] * height - (padding[1] + padding[3])

            if anchor_x == 'left':
                x = x + padding[0]
            if anchor_x == 'right':
                x = x + width - (w + padding[2])
            if self.anchor_x == 'center':
                x = x + (width / 2) - (w / 2)
            if anchor_y == 'bottom':
                y = y + padding[1]
            if anchor_y == 'top':
                y = y + height - (h + padding[3])
            if anchor_y == 'center':
                y = y + (height / 2) - (h / 2)

            c.x = x
            c.y = y
            c.width = w
            c.height = h
