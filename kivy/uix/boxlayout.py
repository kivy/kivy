'''
BoxLayout: 

'''

__all__ = ('BoxLayout', )

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.c_ext.properties import NumericProperty, OptionProperty

class Layout(Widget):
    def __init__(self, **kwargs):
        kwargs.setdefault('size', (1, 1))
        self._minimum_size = (0, 0)
        super(Layout, self).__init__(**kwargs)

    def _get_minimum_size(self):
        '''Returns minimum size of layout (based on size of fixed / minimum size
        of children).
        '''
        return self._minimum_size
    def _set_minimum_size(self, size):
        '''Sets the layout minimum size property (the layout calculates this in
        update_minimum_size and uses it to perform layout calculations). If the
        widgets size (width or height) is smaller than the minimum size, it is
        resized to be at least minimum size.
        '''
        self._minimum_size = size
        if self.width < size[0]:
            self.width = size[0]
        if self.height < size[1]:
            self.height = size[1]
    minimum_size = property(_get_minimum_size, _set_minimum_size)

    def reposition_child(self, child, **kwargs):
        for prop in kwargs:
            child.__setattr__(prop, kwargs[prop])

class BoxLayout(Layout):

    #: Spacing between widget box and children
    spacing = NumericProperty(0)

    #: Spacing between each widget
    padding = NumericProperty(0)

    #: Orientation of the layout
    orientation = OptionProperty('horizontal',
                                 options=('horizontal', 'vertical'))

    def __init__(self, **kwargs):
        kwargs.setdefault('size', (1, 1))
        self._minimum_size = (0, 0)
        super(BoxLayout, self).__init__(**kwargs)
        self.bind(
            spacing = self._trigger_layout,
            padding = self._trigger_layout,
            children = self._trigger_layout,
            orientation = self._trigger_layout
        )

    def _trigger_layout(self, *largs):
        Clock.unschedule(self._do_layout)
        Clock.schedule_once(self._do_layout)

    def _update_minimum_size(self):
        '''Calculates the minimum size of the layout.

        In calculation, there must be a space for child widgets that have fixed
        size (size_hint == (None, None)). There must also be at least enough
        space for every child layout's minimum size (cant be too small even if
        size_hint is set).
        '''
        padding = self.padding
        padding2 = padding * 2
        spacing = self.spacing
        width = height = padding2

        if self.orientation == 'horizontal':
            width += (len(self.children) - 1) * spacing
            for w in self.children:
                shw, shh = w.size_hint
                if shw is None:
                    width += w.width
                if shh is None:
                    height = max(w.height + padding2, height)
                if isinstance(w, Layout):
                    _w, _h = w.minimum_size
                    if shw is not None:
                        width += _w
                    if shh is not None:
                        height = max(_h + padding2, height)

        if self.orientation == 'vertical':
            height += (len(self.children) - 1) * spacing
            for w in self.children:
                shw, shh = w.size_hint
                if shw is None:
                    width = max(w.width + padding2, width)
                if shh is None:
                    height += w.height
                if isinstance(w, Layout):
                    _w, _h = w.minimum_size
                    if shw is not None:
                        width = max(_w + padding2, width)
                    if shh is not None:
                        height += _h

        self.minimum_size = (width, height)

    def _do_layout(self, *largs):
        # optimize layout by preventing looking at the same attribute in a loop
        reposition_child = self.reposition_child
        selfx, selfy = self.pos
        selfw, selfh = self.size
        padding = self.padding
        spacing = self.spacing
        orientation = self.orientation
        padding2 = padding * 2

        # calculate maximum space used by size_hint
        stretch_weight_x = 0.
        stretch_weight_y = 0.
        for w in self.children:
            stretch_weight_x += w.size_hint[0] or 0.0
            stretch_weight_y += w.size_hint[1] or 0.0

        if orientation == 'horizontal':
            x = y = padding
            stretch_space = max(0.0, selfw - self.minimum_size[0])
            for c in reversed(self.children):
                shw, shh = c.size_hint
                c_pos = selfx + x, selfy + y
                c_size = list(c.size)
                if shw:
                    #its sizehint * available space
                    c_size[0] = stretch_space * shw / stretch_weight_x
                    if isinstance(c, Layout):
                        c_size[0] += c.minimum_size[0]
                if shh:
                    c_size[1] = shh * (selfh - padding2)
                reposition_child(c, pos=c_pos, size=c_size)
                x += c_size[0] + spacing

        if orientation == 'vertical':
            x = y = padding
            stretch_space = max(0.0, selfh - self.minimum_size[1])
            for c in self.children:
                shw, shh = c.size_hint
                c_pos = selfx + x, selfy + y
                c_size = list(c.size)
                if shh:
                    c_size[1] = stretch_space * shh / stretch_weight_y
                    if isinstance(c, Layout):
                        c_size[1] += c.minimum_size[1]
                if shw:
                    c_size[0] = shw * (selfw - padding2)
                reposition_child(c, pos=c_pos, size=c_size)
                y += c_size[1] + spacing
