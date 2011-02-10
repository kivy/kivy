'''
Anchor layout
=============

This layout align his children to a border or a center: top, left, center,
right...
'''

__all__ = ('AnchorLayout', )

from kivy.clock import Clock
from kivy.uix.layout import Layout
from kivy.properties import NumericProperty, OptionProperty


class AnchorLayout(Layout):
    '''Anchor layout class. See module documentation for more informations.
    '''

    padding = NumericProperty(0)
    '''Padding between widget box and children, in pixels.

    :data:`padding` is a :class:`~kivy.properties.NumericProperty`, default to
    0.
    '''

    anchor_x = OptionProperty('center', options=(
        'left', 'center', 'right'))
    '''Horizontal anchor.

    :data:`anchor_x` is an :class:`~kivy.properties.OptionProperty`, default
    to 'center'. Can take a value of 'left', 'center' or 'right'
    '''

    anchor_y = OptionProperty('center', options=(
        'top', 'center', 'bottom'))
    '''Vertical anchor.

    :data:`anchor_y` is an :class:`~kivy.properties.OptionProperty`, default
    to 'center'. Can take a value of 'top', 'center' or 'bottom'
    '''

    def __init__(self, **kwargs):
        super(AnchorLayout, self).__init__(**kwargs)
        self.bind(
            padding = self._trigger_layout,
            anchor_x = self._trigger_layout,
            anchor_y = self._trigger_layout,
            size = self._trigger_layout,
            pos = self._trigger_layout)

    def _trigger_layout(self, *largs):
        Clock.unschedule(self._do_layout)
        Clock.schedule_once(self._do_layout)

    def _do_layout(self, *largs):
        _x, _y = self.pos
        width = self.width
        height = self.height
        anchor_x = self.anchor_x
        anchor_y = self.anchor_y
        padding = self.padding
        reposition_child = self.reposition_child

        for c in self.children:
            x, y = _x, _y
            w, h = c.size
            if c.size_hint[0]:
                w = c.size_hint[0] * width
            elif not self.size_hint[0]:
                width = max(width, c.width)
            if c.size_hint[1]:
                h = c.size_hint[1]*height
            elif not self.size_hint[1]:
                height = max(height, c.height)

            if anchor_x == 'left':
                x = x + padding
            if anchor_x == 'right':
                x = x + width - (w + padding)
            if self.anchor_x == 'center':
                x = x + (width / 2) - (w / 2)
            if anchor_y == 'bottom':
                y = y + padding
            if anchor_y == 'top':
                y = y + height - (h + padding)
            if anchor_y == 'center':
                y = y + (height / 2) - (h / 2)

            reposition_child(c, pos=(x, y), size=(w, h))

        self.size = (width, height) # might have changed inside loop
