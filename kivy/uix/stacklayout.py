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
    ReferenceListProperty, VariableListProperty


class StackLayout(Layout):
    '''Stack layout class. See module documentation for more information.
    '''

    spacing = VariableListProperty([0, 0], length=2)
    '''Spacing between children: [spacing_horizontal, spacing_vertical].

    spacing also accepts a one argument form [spacing].

    :data:`spacing` is a
    :class:`~kivy.properties.VariableListProperty`, default to [0, 0].

    '''

    padding = VariableListProperty([0, 0, 0, 0])
    '''Padding between layout box and children: [padding_left, padding_top,
    padding_right, padding_bottom].

    padding also accepts a two argument form [padding_horizontal,
    padding_vertical] and a one argument form [padding].

    .. versionchanged:: 1.7.0

    Replaced NumericProperty with VariableListProperty.

    :data:`padding` is a
    :class:`~kivy.properties.VariableListProperty`, default to [0, 0,
    0, 0].

    '''

    orientation = OptionProperty('lr-tb', options=(
        'lr-tb', 'tb-lr', 'rl-tb', 'tb-rl', 'lr-bt', 'bt-lr', 'rl-bt', 'bt-rl'))
    '''Orientation of the layout.

    :data:`orientation` is an :class:`~kivy.properties.OptionProperty`, default
    to 'lr-tb'.

    Valid orientations are: 'lr-tb', 'tb-lr', 'rl-tb', 'tb-rl', 'lr-bt',
    'bt-lr', 'rl-bt', 'bt-rl'

    .. versionchanged:: 1.5.0

        :data:`orientation` now correctly handles all valid combinations of
        'lr','rl','tb','bt'. Before this version only 'lr-tb' and
        'tb-lr' were supported, and 'tb-lr' was misnamed and placed
        widgets from bottom to top and from right to left (reversed compared
        to what was expected).

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
        padding_left = self.padding[0]
        padding_top = self.padding[1]
        padding_right = self.padding[2]
        padding_bottom = self.padding[3]

        padding_x = padding_left + padding_right
        padding_y = padding_top + padding_bottom
        spacing_x, spacing_y = self.spacing

        lc = []

        # Determine which direction and in what order to place the widgets
        posattr = [0] * 2
        posdelta = [0] * 2
        posstart = [0] * 2
        for i in (0, 1):
            posattr[i] = 1 * (orientation[i] in ('tb', 'bt'))
            k = posattr[i]
            if orientation[i] == 'lr':
                # left to right
                posdelta[i] = 1
                posstart[i] = selfpos[k] + padding_left
            elif orientation[i] == 'bt':
                # bottom to top
                posdelta[i] = 1
                posstart[i] = selfpos[k] + padding_bottom
            elif orientation[i] == 'rl':
                # right to left
                posdelta[i] = -1
                posstart[i] = selfpos[k] + selfsize[k] - padding_right
            else:
                # top to bottom
                posdelta[i] = -1
                posstart[i] = selfpos[k] + selfsize[k] - padding_top

        innerattr, outerattr = posattr
        ustart, vstart = posstart
        deltau, deltav = posdelta
        del posattr, posdelta, posstart

        u = ustart  # inner loop position variable
        v = vstart  # outer loop position variable

        # space calculation, used for determining when a row or column is full

        if orientation[0] in ('lr', 'rl'):
            lu = self.size[innerattr] - padding_x
            sv = padding_y  # size in v-direction, for minimum_size property
            su = padding_x  # size in h-direction
            spacing_u = spacing_x
            spacing_v = spacing_y
        else:
            lu = self.size[innerattr] - padding_y
            sv = padding_x  # size in v-direction, for minimum_size property
            su = padding_y  # size in h-direction
            spacing_u = spacing_y
            spacing_v = spacing_x

        # space calculation, row height or column width, for arranging widgets
        lv = 0

        urev = (deltau < 0)
        vrev = (deltav < 0)
        for c in reversed(self.children):
            if c.size_hint[0]:
                c.width = c.size_hint[0] * (selfsize[0] - padding_x)
            if c.size_hint[1]:
                c.height = c.size_hint[1] * (selfsize[1] - padding_y)

            # does the widget fit in the row/column?
            if lu - c.size[innerattr] >= 0:
                lc.append(c)
                lu -= c.size[innerattr] + spacing_u
                lv = max(lv, c.size[outerattr])
                continue

            # push the line
            sv += lv + spacing_v
            for c2 in lc:
                if urev:
                    u -= c2.size[innerattr]
                c2.pos[innerattr] = u
                pos_outer = v
                if vrev:
                    # v position is actually the top/right side of the widget
                    # when going from high to low coordinate values,
                    # we need to subtract the height/width from the position.
                    pos_outer -= c2.size[outerattr]
                c2.pos[outerattr] = pos_outer
                if urev:
                    u -= spacing_u
                else:
                    u += c2.size[innerattr] + spacing_u

            v += deltav * lv
            v += deltav * spacing_v
            lc = [c]
            lv = c.size[outerattr]
            lu = selfsize[innerattr] - su - c.size[innerattr] - spacing_u
            u = ustart

        if lc:
            # push the last (incomplete) line
            sv += lv + spacing_v
            for c2 in lc:
                if urev:
                    u -= c2.size[innerattr]
                c2.pos[innerattr] = u
                pos_outer = v
                if vrev:
                    pos_outer -= c2.size[outerattr]
                c2.pos[outerattr] = pos_outer
                if urev:
                    u -= spacing_u
                else:
                    u += c2.size[innerattr] + spacing_u

        self.minimum_size[outerattr] = sv
