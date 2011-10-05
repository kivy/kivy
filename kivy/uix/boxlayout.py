'''
Box Layout
==========

:class:`BoxLayout` arranges children in a vertical or horizontal box.

To position widgets above/below each other, use a vertical BoxLayout::

    layout = BoxLayout(orientation='vertical')
    btn1 = Button(text='Hello')
    btn2 = Button(text='World')
    layout.add_widget(btn1)
    layout.add_widget(btn2)

To position widgets next to each other, use a horizontal BoxLayout. In this 
example, we use 10 pixel spacing between children; the first button covers 
70% of the horizontal space, the second covers 30%::

    layout = BoxLayout(spacing=10)
    btn1 = Button(text='Hello', size_hint=(.7, 1))
    btn2 = Button(text='World', size_hint=(.3, 1))
    layout.add_widget(btn1)
    layout.add_widget(btn2)

.. note::

    The `size_hint` uses the available space after subtracting all the 
    fixed-size widgets. For example, if you have a layout that is 800px
    wide, and add three buttons like this:
    
    btn1 = Button(text='Hello', size=(200, 100), size_hint=(None, None))
    btn2 = Button(text='Kivy', size_hint=(.5, 1))
    btn3 = Button(text='World', size_hint=(.5, 1))
    
    The first button will be 200px wide as specified, the second and third 
    will be 300px each, ie (800-200)*0.5

'''

__all__ = ('BoxLayout', )

from kivy.clock import Clock
from kivy.uix.layout import Layout
from kivy.properties import NumericProperty, OptionProperty


class BoxLayout(Layout):
    '''Box layout class. See module documentation for more information.
    '''

    spacing = NumericProperty(0)
    '''Spacing between children, in pixels.

    :data:`spacing` is a :class:`~kivy.properties.NumericProperty`, default to
    0.
    '''

    padding = NumericProperty(0)
    '''Padding between layout box and children, in pixels.

    :data:`padding` is a :class:`~kivy.properties.NumericProperty`, default to
    0.
    '''

    orientation = OptionProperty('horizontal', options=(
        'horizontal', 'vertical'))
    '''Orientation of the layout.

    :data:`orientation` is an :class:`~kivy.properties.OptionProperty`, default
    to 'horizontal'. Can be 'vertical' or 'horizontal'.
    '''

    def __init__(self, **kwargs):
        kwargs.setdefault('size', (1, 1))
        self._trigger_layout = Clock.create_trigger(self._do_layout, -1)
        self._minimum_size = (0, 0)
        super(BoxLayout, self).__init__(**kwargs)
        self.bind(
            spacing = self._trigger_minimum_size,
            padding = self._trigger_minimum_size,
            orientation = self._trigger_minimum_size)
        self.bind(
            minimum_size = self._trigger_layout,
            spacing = self._trigger_layout,
            padding = self._trigger_layout,
            children = self._trigger_layout,
            orientation = self._trigger_layout,
            size = self._trigger_layout,
            pos = self._trigger_layout)

    def update_minimum_size(self, *largs):
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
