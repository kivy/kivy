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
        pad_left, pad_top, pad_right, pad_bottom = self.padding

        for c in self.children:
            x, y = _x, _y
            cw, ch = c.size
            shw, shh = c.size_hint
            shw_min, shh_min = c.size_hint_min
            shw_max, shh_max = c.size_hint_max

            if shw is not None:
                cw = shw * (width - pad_left - pad_right)
                if shw_min is not None and cw < shw_min:
                    cw = shw_min
                elif shw_max is not None and cw > shw_max:
                    cw = shw_max

            if shh is not None:
                ch = shh * (height - pad_top - pad_bottom)
                if shh_min is not None and ch < shh_min:
                    ch = shh_min
                elif shh_max is not None and ch > shh_max:
                    ch = shh_max

            if anchor_x == 'left':
                x = x + pad_left
            elif anchor_x == 'right':
                x = x + width - (cw + pad_right)
            else:
                x = x + (width - pad_right + pad_left - cw) / 2
            if anchor_y == 'bottom':
                y = y + pad_bottom
            elif anchor_y == 'top':
                y = y + height - (ch + pad_top)
            else:
                y = y + (height - pad_top + pad_bottom - ch) / 2

            c.pos = x, y
            c.size = cw, ch
