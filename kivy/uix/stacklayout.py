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

The :class:`StackLayout` arranges children vertically or horizontally, as many
as the layout can fit. The size of the individual children widgets do not
have to be uniform.

For example, to display widgets that get progressively larger in width::

    root = StackLayout()
    for i in range(25):
        btn = Button(text=str(i), width=40 + i * 5, size_hint=(None, 0.15))
        root.add_widget(btn)

.. image:: images/stacklayout_sizing.png
    :align: left
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

    spacing also accepts a single argument form [spacing].

    :attr:`spacing` is a
    :class:`~kivy.properties.VariableListProperty` and defaults to [0, 0].

    '''

    padding = VariableListProperty([0, 0, 0, 0])
    '''Padding between the layout box and it's children: [padding_left,
    padding_top, padding_right, padding_bottom].

    padding also accepts a two argument form [padding_horizontal,
    padding_vertical] and a single argument form [padding].

    .. versionchanged:: 1.7.0
        Replaced the NumericProperty with a VariableListProperty.

    :attr:`padding` is a
    :class:`~kivy.properties.VariableListProperty` and defaults to
    [0, 0, 0, 0].

    '''

    orientation = OptionProperty('lr-tb', options=(
        'lr-tb', 'tb-lr', 'rl-tb', 'tb-rl', 'lr-bt', 'bt-lr', 'rl-bt',
        'bt-rl'))
    '''Orientation of the layout.

    :attr:`orientation` is an :class:`~kivy.properties.OptionProperty` and
    defaults to 'lr-tb'.

    Valid orientations are 'lr-tb', 'tb-lr', 'rl-tb', 'tb-rl', 'lr-bt',
    'bt-lr', 'rl-bt' and 'bt-rl'.

    .. versionchanged:: 1.5.0
        :attr:`orientation` now correctly handles all valid combinations of
        'lr','rl','tb','bt'. Before this version only 'lr-tb' and
        'tb-lr' were supported, and 'tb-lr' was misnamed and placed
        widgets from bottom to top and from right to left (reversed compared
        to what was expected).

    .. note::

        'lr' means Left to Right.
        'rl' means Right to Left.
        'tb' means Top to Bottom.
        'bt' means Bottom to Top.
    '''

    minimum_width = NumericProperty(0)
    '''Minimum width needed to contain all children. It is automatically set
    by the layout.

    .. versionadded:: 1.0.8

    :attr:`minimum_width` is a :class:`kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    minimum_height = NumericProperty(0)
    '''Minimum height needed to contain all children. It is automatically set
    by the layout.

    .. versionadded:: 1.0.8

    :attr:`minimum_height` is a :class:`kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    minimum_size = ReferenceListProperty(minimum_width, minimum_height)
    '''Minimum size needed to contain all children. It is automatically set
    by the layout.

    .. versionadded:: 1.0.8

    :attr:`minimum_size` is a
    :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`minimum_width`, :attr:`minimum_height`) properties.
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
        first_in_line = True # i assume last_in_line will always be computed
        usable_space = selfsize[innerattr] - su # replace lu to check last wgt
        n_child = len(self.children)
        i_child = n_child - 1
        while i_child >= 0:
            c = self.children[i_child]
            if c.size_hint[0] and orientation[0] in ('lr', 'rl'):
                space_used = c.size_hint[0] * (selfsize[0] - padding_x)
                if i_child > 0:
                    c2 = self.children[i_child - 1]
                    space_used2 = c2.size_hint[0] * (selfsize[0] - padding_x)
                    if usable_space - space_used >= space_used2:
                        last_in_line = False
                    else: last_in_line = True
                else: last_in_line = True
                
                if first_in_line and not last_in_line:
                    c.width = space_used - spacing_u / 2
                elif last_in_line and not first_in_line:
                    c.width = space_used - spacing_u / 2
                elif not first_in_line and not last_in_line:
                    c.width = space_used - spacing_u
                else: c.width = space_used

            if c.size_hint[1] and orientation[0] in ('bt', 'tb'):
                space_used = c.size_hint[1] * (selfsize[1] - padding_y)
                if i_child > 0:
                    c2 = self.children[i_child - 1]
                    space_used2 = c2.size_hint[1] * (selfsize[1] - padding_y)
                    if usable_space - space_used >= space_used2:
                        last_in_line = False
                    else: last_in_line = True
                else: last_in_line = True
                
                if first_in_line and not last_in_line:
                    c.height = space_used - spacing_u / 2
                elif last_in_line and not first_in_line:
                    c.height = space_used - spacing_u / 2
                elif not first_in_line and not last_in_line:
                    c.height = space_used - spacing_u
                else: c.height = space_used

            # does the widget fit in the row/column?
            if lu >= space_used:
                lc.append(c)
                lu -= space_used
                lv = max(lv, c.size[outerattr])
                first_in_line = last_in_line
                i_child -= 1
                if last_in_line:
                  usable_space = selfsize[innerattr] - su
                else: usable_space -= space_used
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
            lu = selfsize[innerattr] - su - space_used
            u = ustart
            first_in_line = last_in_line
            i_child -= 1

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