'''
Stack Layout
============

.. only:: html

    .. image:: images/stacklayout.gif
        :align: right

.. only:: latex

    .. image:: images/stacklayout.png
        :align: right

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
        'lr-tb', 'tb-lr', 'rl-tb', 'tb-rl', 'lr-bt', 'bt-lr', 'rl-bt', 'bt-rl'))
    '''Orientation of the layout.

    :data:`orientation` is an :class:`~kivy.properties.OptionProperty`, default
    to 'lr-tb'.

    .. note::

        lr mean Left to Right.
        rl mean Right to Left.
        tb mean Top to Bottom.
        bt mean Bottom to Top.
    '''

    minimum_width = NumericProperty(0)
    '''Minimum width needed to contain all children.

    .. versionadded:: 1.0.8

    :data:`minimum_width` is a :class:`kivy.properties.NumericProperty`, default
    to 0.
    '''

    minimum_height = NumericProperty(0)
    '''Minimum height needed to contain all children.

    .. versionadded:: 1.0.8

    :data:`minimum_height` is a :class:`kivy.properties.NumericProperty`,
    default to 0.
    '''

    minimum_size = ReferenceListProperty(minimum_width, minimum_height)
    '''Minimum size needed to contain all children.

    .. versionadded:: 1.0.8

    :data:`minimum_size` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:data:`minimum_width`, :data:`minimum_height`) properties.
    '''

    def __init__(self, **kwargs):
        super(StackLayout, self).__init__(**kwargs)
        self.bind(
            padding=self._trigger_layout,
            spacing=self._trigger_layout,
            children=self._trigger_layout,
            orientation=self._trigger_layout,
            size=self._trigger_layout,
            pos=self._trigger_layout)

    def do_layout(self, *largs):
        # optimize layout by preventing looking at the same attribute in a loop
        selfpos = self.pos
        selfsize = self.size
        orientation = self.orientation.split('-')
        padding = self.padding
        padding2 = padding * 2
        spacing = self.spacing

        lc = []

        # Determine which direction and in what order to place the widgets
        posattr = [0] * 2
        posdelta = [0] * 2
        posstart = [0] * 2
        for i in (0, 1):
            posattr[i] = 1 * (orientation[i] in ('tb', 'bt'))
            k = posattr[i]
            if orientation[i] in ('lr', 'bt'):
                # left to right or bottom to top
                posdelta[i] = 1
                posstart[i] = selfpos[k] + padding
            else:
                # right to left or top to bottom
                posdelta[i] = -1
                posstart[i] = selfpos[k] + selfsize[k] - padding

        innerattr, outerattr = posattr
        ustart, vstart = posstart
        deltau, deltav = posdelta
        del posattr, posdelta, posstart

        u = ustart  # inner loop position variable
        v = vstart  # outer loop position variable

        # space calculation, used for determining when a row or column is full
        lu = self.size[innerattr] - padding2

        # space calculation, row height or column width, for arranging widgets
        lv = 0

        sv = padding2  # size in v-direction, for minimum_size property
        urev = (deltau < 0)
        vrev = (deltav < 0)
        for c in reversed(self.children):
            # Issue#823: ReferenceListProperty doesn't allow changing
            # individual properties.
            # when the above issue is fixed we can remove csize from below and
            # access c.size[i] directly
            csize = c.size[:]  # we need to update the whole tuple at once.
            for i in (0, 1):
                if c.size_hint[i]:
                    # calculate size
                    csize[i] = c.size_hint[i] * (selfsize[i] - padding2)
            c.size = tuple(csize)

            # does the widget fit in the row/column?
            if lu - c.size[innerattr] >= 0:
                lc.append(c)
                lu -= c.size[innerattr] + spacing
                lv = max(lv, c.size[outerattr])
                continue

            # push the line
            sv += lv + spacing
            for c2 in lc:
                if urev:
                    u -= c2.size[innerattr] + spacing
                p = [0, 0]  # issue #823
                p[innerattr] = u
                p[outerattr] = v
                if vrev:
                    # v position is actually the top/right side of the widget
                    # when going from high to low coordinate values,
                    # we need to subtract the height/width from the position.
                    p[outerattr] -= c2.size[outerattr]
                c2.pos = tuple(p)  # issue #823
                if not urev:
                    u += c2.size[innerattr] + spacing

            v += deltav * lv
            v += deltav * spacing
            lc = [c]
            lv = c.size[outerattr]
            lu = selfsize[innerattr] - padding2 - c.size[innerattr] - spacing
            u = ustart

        if lc:
            # push the last (incomplete) line
            sv += lv + spacing
            for c2 in lc:
                if urev:
                    u -= c2.size[innerattr] + spacing
                p = [0, 0]  # issue #823
                p[innerattr] = u
                p[outerattr] = v
                if vrev:
                    p[outerattr] -= c2.size[outerattr]
                c2.pos = tuple(p)  # issue #823
                if not urev:
                    u += c2.size[innerattr] + spacing

        minsize = self.minimum_size[:]  # issue #823
        minsize[outerattr] = sv
        self.minimum_size = tuple(minsize)
