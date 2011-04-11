'''
Stack Layout
============

.. versionadded:: 1.0.5

.. warning:

    This is experimental and subject to change as long as this warning notice is
    present.

Arrange widgets in a vertical or horizontal mode, as much as the layout can.
'''

__all__ = ('StackLayout', )

from kivy.clock import Clock
from kivy.uix.layout import Layout
from kivy.properties import NumericProperty, OptionProperty


class StackLayout(Layout):
    '''Stack layout class. See module documentation for more informations.
    '''

    spacing = NumericProperty(0)
    '''Spacing is the space between each children, in pixels.

    :data:`spacing` is a :class:`~kivy.properties.NumericProperty`, default to
    0.
    '''

    padding = NumericProperty(0)
    '''Padding between widget box and children, in pixels.

    :data:`padding` is a :class:`~kivy.properties.NumericProperty`, default to
    0.
    '''

    orientation = OptionProperty('vertical', options=(
        'horizontal', 'vertical'))
    '''Orientation of the layout.

    :data:`orientation` is an :class:`~kivy.properties.OptionProperty`, default
    to 'horizontal'. Can take a value of 'vertical' or 'horizontal'.
    '''

    def __init__(self, **kwargs):
        kwargs.setdefault('size', (1, 1))
        self._minimum_size = (0, 0)
        super(StackLayout, self).__init__(**kwargs)
        self.bind(
            children = self._trigger_layout,
            orientation = self._trigger_layout,
            size = self._trigger_layout,
            pos = self._trigger_layout)

    def update_minimum_size(self, *largs):
        self._do_layout()
        super(StackLayout, self).update_minimum_size(*largs)

    def _trigger_layout(self, *largs):
        Clock.unschedule(self._do_layout)
        Clock.schedule_once(self._do_layout)

    def _do_layout(self, *largs):
        # optimize layout by preventing looking at the same attribute in a loop
        reposition_child = self.reposition_child
        selfx, selfy = self.pos
        selfw, selfh = self.size
        orientation = self.orientation
        padding = self.padding
        padding2 = padding * 2
        spacing = self.spacing
        spacing2 = spacing * 2

        x = self.x + padding
        y = self.top - padding
        lw = self.width - padding2
        lh = 0
        lc = []
        height = 0

        if orientation == 'vertical' or True:
            for c in reversed(self.children):
                if c.size_hint_x:
                    c.width = c.size_hint_x * (selfw - padding2)

                # is the widget fit in the line ?
                if lw - c.width >= 0:
                    lc.append(c)
                    lw -= c.width + spacing
                    lh = max(lh, c.height)
                    continue

                # push the line
                y -= lh
                height += lh + spacing
                for c2 in lc:
                    reposition_child(c2, pos=(x, y))
                    x += c2.width + spacing
                y -= spacing
                lc = [c]
                lh = c.height
                lw = self.width - padding2 - c.width
                x = self.x + padding

            if lc:
                y -= lh
                height += lh
                for c2 in lc:
                    reposition_child(c2, pos=(x, y))
                    x += c2.width + spacing
            self.height = height
