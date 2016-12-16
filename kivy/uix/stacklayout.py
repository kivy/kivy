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


def _compute_size(c, available_size, idx):
    sh_min = c.size_hint_min[idx]
    sh_max = c.size_hint_max[idx]
    val = c.size_hint[idx] * available_size

    if sh_min is not None:
        if sh_max is not None:
            return max(min(sh_max, val), sh_min)
        return max(val, sh_min)
    if sh_max is not None:
        return min(sh_max, val)
    return val


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
        trigger = self._trigger_layout
        fbind = self.fbind
        fbind('padding', trigger)
        fbind('spacing', trigger)
        fbind('children', trigger)
        fbind('orientation', trigger)
        fbind('size', trigger)
        fbind('pos', trigger)

    def do_layout(self, *largs):
        if not self.children:
            self.minimum_size = (0., 0.)
            return

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
            sv = padding_y  # size in v-direction, for minimum_size property
            su = padding_x  # size in h-direction
            spacing_u = spacing_x
            spacing_v = spacing_y
            padding_u = padding_x
            padding_v = padding_y
        else:
            sv = padding_x  # size in v-direction, for minimum_size property
            su = padding_y  # size in h-direction
            spacing_u = spacing_y
            spacing_v = spacing_x
            padding_u = padding_y
            padding_v = padding_x

        # space calculation, row height or column width, for arranging widgets
        lv = 0

        urev = (deltau < 0)
        vrev = (deltav < 0)
        firstchild = self.children[0]
        sizes = []
        lc = []
        for c in reversed(self.children):
            if c.size_hint[outerattr] is not None:
                c.size[outerattr] = max(
                    1, _compute_size(c, selfsize[outerattr] - padding_v,
                                     outerattr))

            # does the widget fit in the row/column?
            ccount = len(lc)
            totalsize = availsize = max(
                0, selfsize[innerattr] - padding_u - spacing_u * ccount)
            if not lc:
                if c.size_hint[innerattr] is not None:
                    childsize = max(1, _compute_size(c, totalsize, innerattr))
                else:
                    childsize = max(0, c.size[innerattr])
                availsize = selfsize[innerattr] - padding_u - childsize
                testsizes = [childsize]
            else:
                testsizes = [0] * (ccount + 1)
                for i, child in enumerate(lc):
                    if availsize <= 0:
                        # no space left but we're trying to add another widget.
                        availsize = -1
                        break
                    if child.size_hint[innerattr] is not None:
                        testsizes[i] = childsize = max(
                            1, _compute_size(child, totalsize, innerattr))
                    else:
                        childsize = max(0, child.size[innerattr])
                        testsizes[i] = childsize
                    availsize -= childsize
                if c.size_hint[innerattr] is not None:
                    testsizes[-1] = max(
                        1, _compute_size(c, totalsize, innerattr))
                else:
                    testsizes[-1] = max(0, c.size[innerattr])
                availsize -= testsizes[-1]

            # Tiny value added in order to avoid issues with float precision
            # causing unexpected children reordering when parent resizes.
            # e.g. if size is 101 and children size_hint_x is 1./5
            # 5 children would not fit in one line because 101*(1./5) > 101/5
            if (availsize + 1e-10) >= 0 or not lc:
                # even if there's no space, we always add one widget to a row
                lc.append(c)
                sizes = testsizes
                lv = max(lv, c.size[outerattr])
                continue

            # apply the sizes
            for i, child in enumerate(lc):
                if child.size_hint[innerattr] is not None:
                    child.size[innerattr] = sizes[i]

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
            if c.size_hint[innerattr] is not None:
                sizes = [
                    max(1, _compute_size(c, selfsize[innerattr] - padding_u,
                                         innerattr))]
            else:
                sizes = [max(0, c.size[innerattr])]
            u = ustart

        if lc:
            # apply the sizes
            for i, child in enumerate(lc):
                if child.size_hint[innerattr] is not None:
                    child.size[innerattr] = sizes[i]

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
