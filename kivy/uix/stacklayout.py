'''
Stack Layout
============

.. versionadded:: 1.0.5

:class:`StackLayout` arranges children vertically or horizontally, as many
as the layout can fit.

.. warning:

    This is experimental and subject to change as long as this warning notice is
    present.

'''

__all__ = ('StackLayout', )

from kivy.uix.layout import Layout
from kivy.properties import NumericProperty, OptionProperty, \
    ReferenceListProperty


class StackLayout(Layout):
    '''Stack layout class. See module documentation for more information.
    '''

    spacing = NumericProperty(0)
    '''Spacing between children, in pixels.

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
    to 'lr-tb'. Only supports 'lr-tb' and 'tb-lr' at the moment.

    .. note::

        lr mean Left to Right.
        tb mean Top to Bottom.
    '''

    minimum_width = NumericProperty(0)
    '''Minimum width needed to contain all childrens.

    .. versionadded:: 1.0.8

    :data:`minimum_width` is a :class:`kivy.properties.NumericProperty`, default
    to 0.
    '''

    minimum_height = NumericProperty(0)
    '''Minimum height needed to contain all childrens.

    .. versionadded:: 1.0.8

    :data:`minimum_height` is a :class:`kivy.properties.NumericProperty`,
    default to 0.
    '''

    minimum_size = ReferenceListProperty(minimum_width, minimum_height)
    '''Minimum size needed to contain all childrens.

    .. versionadded:: 1.0.8

    :data:`minimum_size` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:data:`minimum_width`, :data:`minimum_height`) properties.
    '''

    def __init__(self, **kwargs):
        super(StackLayout, self).__init__(**kwargs)
        self.bind(
            padding = self._trigger_layout,
            spacing = self._trigger_layout,
            children = self._trigger_layout,
            orientation = self._trigger_layout,
            size = self._trigger_layout,
            pos = self._trigger_layout)

    def do_layout(self, *largs):
        # optimize layout by preventing looking at the same attribute in a loop
        reposition_child = self.reposition_child
        selfx, selfy = self.pos
        selfw, selfh = self.size
        orientation = self.orientation
        padding = self.padding
        padding2 = padding * 2
        spacing = self.spacing

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
                lw = self.width - padding2 - c.width - spacing
                x = self.x + padding

            if lc:
                y -= lh
                height += lh + padding
                for c2 in lc:
                    reposition_child(c2, pos=(x, y))
                    x += c2.width + spacing
            self.minimum_height = height

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
                lh = self.height - padding2 - c.height - spacing
                y = self.y + padding

            if lc:
                x -= lw
                width += lw
                for c2 in lc:
                    reposition_child(c2, pos=(x, y))
                    y += c2.height + spacing
            self.minimum_width = width
