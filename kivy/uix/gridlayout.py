'''
Grid layout
===========

Arrange widgets in a matrix

Example of a GridLayout::

layout = GridLayout(cols=3, rows=3)
for i in range(9):
layout.add_widget(Label(text=str(i)))

another example using two different widgets and some spacing::

layout = GridLayout(cols=3, rows=5, spacing=10)
for i in range(9):
layout.add_widget(Label(text=str(i)))
for i in range(10,16):
layout.add_widget(Button(text=str(i)))


.. note::

The `size_hint` represent the size available after substracting all the
fixed size. For example, if you have 3 widgets (width is 200px,
50%, 50%), and if the layout have a width of 600px :

- the first widget width will be 200px
- the second widget width will be 300px
- the third widget width will be 300px
'''

__all__ = ('GridLayout', 'GridLayoutException')

from kivy.clock import Clock
from kivy.uix.layout import Layout
from kivy.properties import NumericProperty
from kivy.properties import BooleanProperty


class GridLayoutException(Exception):
    '''Exception for errors in the grid layout manipulation
    '''
    pass


class GridLayout(Layout):
    '''Grid layout class. See module documentation for more informations.
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
    cols = NumericProperty(None)
    '''Number of columns in the grid

:data:`cols` is a :class:`~kivy.properties.NumericProperty`, default to 0.
'''

    rows = NumericProperty(None)
    '''Number of rows in the grid

:data:`rows` is a :class:`~kivy.properties.NumericProperty`, default to 0.
'''

    uniform_width = BooleanProperty(False)
    '''Define if the width of all the columns must be identical

:data:`uniform_width` is a :class:`~kivy.properties.BooleanProperty`,
default to False.
'''

    uniform_height = BooleanProperty(False)
    '''Define if the height of all the lines must be identical

:data:`uniform_height` is a :class:`~kivy.properties.BooleanProperty`,
default to False.
'''

    def __init__(self, **kwargs):
        super(GridLayout, self).__init__(**kwargs)

        self.bind(
            spacing = self.update_minimum_size,
            padding = self.update_minimum_size,
            children = self.update_minimum_size,
            cols = self.update_minimum_size,
            rows = self.update_minimum_size)

        self.bind(
            spacing = self._trigger_layout,
            padding = self._trigger_layout,
            children = self._trigger_layout,
            size = self._trigger_layout,
            pos = self._trigger_layout)

    def get_max_widgets(self):
        if self.cols and not self.rows:
            return None
        if self.rows and not self.cols:
            return None
        return self.rows * self.cols

    def on_children(self, instance, value):
        # if that makes impossible to construct things with deffered method,
        # migrate this test in do_layout, and/or issue a warning.
        smax = self.get_max_widgets()
        if smax and len(value) > smax:
            raise GridLayoutException(
                    'Too much children in GridLayout. Increase your rows/cols!')

    def update_minimum_size(self, *largs):
        current_cols = self.cols
        current_rows = self.rows
        if current_cols is None:
            current_cols = 1 + (len(self.children) / current_rows)
        elif current_rows is None:
            current_rows = 1 + (len(self.children) / current_cols)

        cols = dict(zip(xrange(current_cols), [0] * current_cols))
        rows = dict(zip(xrange(current_rows), [0] * current_rows))

        # calculate maximum size for each columns and rows
        i = 0
        max_width = max_height = 0
        for row in range(current_rows):
            for col in range(current_cols):
                if i >= len(self.children):
                    break

                #get needed size for that child
                c = self.children[i]
                w, h = c.size
                if isinstance(c, Layout):
                    w, h = c.minimum_size

                cols[col] = max(cols[col], w)
                self.max_col_width = max(max_width, cols[col])

                rows[row] = max(rows[row], h)
                self.max_row_height = max(max_height, rows[row])

                i = i + 1

        # consider uniform sizeing
        if self.uniform_width:
            for col in range(current_cols):
                cols[col] = self.max_col_width
        if self.uniform_height:
            for row in range(current_rows):
                rows[row] = self.max_row_height


        # calculate minimum width/height for this widget
        width = self.spacing * (len(cols) + 1)
        height = self.spacing * (len(rows) + 1)
        for i in cols:
            width += cols[i]
        for i in rows:
            height += rows[i]

        #remeber for layout
        self.col_widths = cols
        self.row_heights = rows

        self.minimum_size = (width, height)

    def _trigger_layout(self, *largs):
        Clock.unschedule(self._do_layout)
        Clock.schedule_once(self._do_layout)

    def _do_layout(self, *largs):
        if self.cols is None and self.rows is None:
            raise GridLayoutException('Need at least cols or rows restriction.')

        if len(self.children) == 0:
            return

        spacing = self.spacing
        _x, _y = self.pos
        # reposition every child
        i = 0
        y = _y + spacing
        for row_height in self.row_heights.itervalues():
            x = _x + spacing
            for col_width in self.col_widths.itervalues():
                if i >= len(self.children):
                    break
                c = self.children[i]
                # special y, we inverse order of children at reposition
                c_pos = (x, self.top - row_height - (y - _y))
                c_size = list(self.children[i].size)
                if self.uniform_width or c.size_hint[0]:
                    c_size[0] = col_width * (c.size_hint[0] or 1.0)
                if self.uniform_height or c.size_hint[1]:
                    c_size[1] = row_height * (c.size_hint[1] or 1.0)
                self.reposition_child(c, pos=c_pos, size=c_size)
                i = i + 1
                x = x + col_width + spacing
            y = y + row_height + spacing



