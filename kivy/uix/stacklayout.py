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

    orientation = OptionProperty('lr-tb', options=(
        'lr-tb', 'tb-lr'))
    '''Orientation of the layout.

    :data:`orientation` is an :class:`~kivy.properties.OptionProperty`, default
    to 'lr-tb'. Support only 'lr-tb' and 'tb-lr' for the moment.

    .. note::

        lr mean Left to Right.
        tb mean Top to Bottom.
    '''

    def __init__(self, **kwargs):
        kwargs.setdefault('size', (1, 1))
        self._minimum_size = (0, 0)
        self._trigger_layout = Clock.create_trigger(self._do_layout, -1)
        super(StackLayout, self).__init__(**kwargs)
        self.bind(
            children = self._trigger_layout,
            orientation = self._trigger_layout,
            size = self._trigger_layout,
            pos = self._trigger_layout)

    def update_minimum_size(self, *largs):
        self._do_layout()
        super(StackLayout, self).update_minimum_size(*largs)

    def _do_layout(self, *largs):
        # optimize layout by preventing looking at the same attribute in a loop
        reposition_child = self.reposition_child
        '''
        print '_do_layout===='
        def reposition_child(*l, **kw):
            print 'reposition_child', l, kw
            self.reposition_child(*l, **kw)
        '''
        selfx, selfy = self.pos
        selfw, selfh = self.size
        orientation = self.orientation
        padding = self.padding
        padding2 = padding * 2
        spacing = self.spacing
        spacing2 = spacing * 2

        lc = []
        height = padding2
        width = padding2

        if orientation == 'lr-tb':
            x = self.x + padding
            y = self.top - padding
            lw = self.width - padding2
            lh = 0
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
                height += lh + padding
                for c2 in lc:
                    reposition_child(c2, pos=(x, y))
                    x += c2.width + spacing
            self.height = height

        elif orientation == 'tb-lr':
            x = self.right - padding
            y = self.y + padding
            lw = 0
            lh = self.height - padding2
            for c in reversed(self.children):
                if c.size_hint_y:
                    c.height = c.size_hint_y * (selfh - padding2)

                # is the widget fit in the column ?
                if lh - c.height >= 0:
                    lc.append(c)
                    lh -= c.height + spacing
                    lw = max(lw, c.width)
                    continue

                # push the line
                x -= lw
                width += lw + spacing
                for c2 in lc:
                    reposition_child(c2, pos=(x, y))
                    y += c2.height + spacing
                x -= spacing
                lc = [c]
                lw = c.width
                lh = self.height - padding2 - c.height
                y = self.y + padding

            if lc:
                x -= lw
                width += lw
                for c2 in lc:
                    reposition_child(c2, pos=(x, y))
                    y += c2.height + spacing
            self.width = width
