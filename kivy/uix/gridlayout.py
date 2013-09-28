'''
Grid Layout
===========

.. only:: html

    .. image:: images/gridlayout.gif
        :align: right

.. only:: latex

    .. image:: images/gridlayout.png
        :align: right

.. versionadded:: 1.0.4

The :class:`GridLayout` arranges children in a matrix. It takes the available
space and divides it into columns and rows, then adds widgets to the resulting
"cells".

.. versionadded:: 1.0.7
    The implementation has changed to use the widget size_hint for calculating
    column/row sizes. `uniform_width` and `uniform_height` have been removed
    and other properties have added to give you more control.

Background
----------

Unlike many other toolkits, you cannot explicitly place a widget in a specific
column/row. Each child is automatically assigned a position determined by the
layout configuration and the child's index in the children list.

A GridLayout must always have at least one input constraint:
:data:`GridLayout.cols` or :data:`GridLayout.rows`. If you do not specify cols
or rows, the Layout will throw an exception.

Column Width and Row Height
---------------------------

The column width/row height are determined in 3 steps:

    - The initial size is given by the :data:`col_default_width` and
      :data:`row_default_height` properties. To customize the size of a single
      column or row, use :data:`cols_minimum` or :data:`rows_minimum`.
    - The `size_hint_x`/`size_hint_y` of the children are taken into account.
      If no widgets have a size hint, the maximum size is used for all children.
    - You can force the default size by setting the :data:`col_force_default`
      or :data:`row_force_default` property. This will force the layout to
      ignore the `width` and `size_hint` properties of children and use the
      default size.

Using a GridLayout
------------------

In the example below, all widgets will have an equal size. By default, the
`size_hint` is (1, 1), so a Widget will take the full size of the parent::

    layout = GridLayout(cols=2)
    layout.add_widget(Button(text='Hello 1'))
    layout.add_widget(Button(text='World 1'))
    layout.add_widget(Button(text='Hello 2'))
    layout.add_widget(Button(text='World 2'))

.. image:: images/gridlayout_1.jpg

Now, let's fix the size of Hello buttons to 100px instead of using
size_hint_x=1::

    layout = GridLayout(cols=2)
    layout.add_widget(Button(text='Hello 1', size_hint_x=None, width=100))
    layout.add_widget(Button(text='World 1'))
    layout.add_widget(Button(text='Hello 2', size_hint_x=None, width=100))
    layout.add_widget(Button(text='World 2'))

.. image:: images/gridlayout_2.jpg

Next, let's fix the row height to a specific size::

    layout = GridLayout(cols=2, row_force_default=True, row_default_height=40)
    layout.add_widget(Button(text='Hello 1', size_hint_x=None, width=100))
    layout.add_widget(Button(text='World 1'))
    layout.add_widget(Button(text='Hello 2', size_hint_x=None, width=100))
    layout.add_widget(Button(text='World 2'))

.. image:: images/gridlayout_3.jpg

'''

__all__ = ('GridLayout', 'GridLayoutException')

from kivy.logger import Logger
from kivy.uix.layout import Layout
from kivy.properties import NumericProperty, BooleanProperty, DictProperty, \
        BoundedNumericProperty, ReferenceListProperty, VariableListProperty
from math import ceil


def nmax(*args):
    '''(internal) Implementation of a max() function that supports None.
    '''
    # merge into one list
    args = [x for x in args if x is not None]
    return max(args)


class GridLayoutException(Exception):
    '''Exception for errors if the grid layout manipulation fails.
    '''
    pass


class GridLayout(Layout):
    '''Grid layout class. See module documentation for more information.
    '''

    spacing = VariableListProperty([0, 0], length=2)
    '''Spacing between children: [spacing_horizontal, spacing_vertical].

    spacing also accepts a one argument form [spacing].

    :data:`spacing` is a
    :class:`~kivy.properties.VariableListProperty`, default to [0, 0].
    '''

    padding = VariableListProperty([0, 0, 0, 0])
    '''Padding between the layout box and it's children: [padding_left,
    padding_top, padding_right, padding_bottom].

    padding also accepts a two argument form [padding_horizontal,
    padding_vertical] and a one argument form [padding].

    .. versionchanged:: 1.7.0

    Replaced NumericProperty with VariableListProperty.

    :data:`padding` is a :class:`~kivy.properties.VariableListProperty` and
    defaults to [0, 0, 0, 0].
    '''

    cols = BoundedNumericProperty(None, min=0, allow_none=True)
    '''Number of columns in the grid.

    .. versionadded:: 1.0.8

        Changed from a NumericProperty to BoundedNumericProperty. You can no
        longer set this to a negative value.

    :data:`cols` is a :class:`~kivy.properties.NumericProperty` and defaults to
    0.
    '''

    rows = BoundedNumericProperty(None, min=0, allow_none=True)
    '''Number of rows in the grid.

    .. versionadded:: 1.0.8

        Changed from a NumericProperty to a BoundedNumericProperty. You can no
        longer set this to a negative value.

    :data:`rows` is a :class:`~kivy.properties.NumericProperty` and defaults to
    0.
    '''

    col_default_width = NumericProperty(0)
    '''Default minimum size to use for a column.

    .. versionadded:: 1.0.7

    :data:`col_default_width` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0.
    '''

    row_default_height = NumericProperty(0)
    '''Default minimum size to use for row.

    .. versionadded:: 1.0.7

    :data:`row_default_height` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0.
    '''

    col_force_default = BooleanProperty(False)
    '''If True, ignore the width and size_hint_x of the child and use the
    default column width.

    .. versionadded:: 1.0.7

    :data:`col_force_default` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to False.
    '''

    row_force_default = BooleanProperty(False)
    '''If True, ignore the height and size_hint_y of the child and use the
    default row height.

    .. versionadded:: 1.0.7

    :data:`row_force_default` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to False.
    '''

    cols_minimum = DictProperty({})
    '''List of minimum sizes for each column.

    .. versionadded:: 1.0.7

    :data:`cols_minimum` is a :class:`~kivy.properties.DictProperty` and
    defaults to {}.
    '''

    rows_minimum = DictProperty({})
    '''List of minimum sizes for each row.

    .. versionadded:: 1.0.7

    :data:`rows_minimum` is a :class:`~kivy.properties.DictProperty` and
    defaults to {}.
    '''

    minimum_width = NumericProperty(0)
    '''Minimum width needed to contain all children.

    .. versionadded:: 1.0.8

    :data:`minimum_width` is a :class:`kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    minimum_height = NumericProperty(0)
    '''Minimum height needed to contain all children.

    .. versionadded:: 1.0.8

    :data:`minimum_height` is a :class:`kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    minimum_size = ReferenceListProperty(minimum_width, minimum_height)
    '''Minimum size needed to contain all children.

    .. versionadded:: 1.0.8

    :data:`minimum_size` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:data:`minimum_width`, :data:`minimum_height`) properties.
    '''

    def __init__(self, **kwargs):
        self._cols = self._rows = None
        super(GridLayout, self).__init__(**kwargs)

        self.bind(
            col_default_width=self._trigger_layout,
            row_default_height=self._trigger_layout,
            col_force_default=self._trigger_layout,
            row_force_default=self._trigger_layout,
            cols=self._trigger_layout,
            rows=self._trigger_layout,
            parent=self._trigger_layout,
            spacing=self._trigger_layout,
            padding=self._trigger_layout,
            children=self._trigger_layout,
            size=self._trigger_layout,
            pos=self._trigger_layout)

    def get_max_widgets(self):
        if self.cols and not self.rows:
            return None
        if self.rows and not self.cols:
            return None
        if not self.cols and not self.rows:
            return None
        return self.rows * self.cols

    def on_children(self, instance, value):
        # if that makes impossible to construct things with deffered method,
        # migrate this test in do_layout, and/or issue a warning.
        smax = self.get_max_widgets()
        if smax and len(value) > smax:
            raise GridLayoutException(
                    'Too many children in GridLayout. Increase rows/cols!')

    def update_minimum_size(self, *largs):
        # the goal here is to calculate the minimum size of every cols/rows
        # and determine if they have stretch or not
        current_cols = self.cols
        current_rows = self.rows
        children = self.children
        len_children = len(children)

        # if no cols or rows are set, we can't calculate minimum size.
        # the grid must be contrained at least on one side
        if not current_cols and not current_rows:
            Logger.warning('%r have no cols or rows set, '
                'layout is not triggered.' % self)
            return None
        if current_cols is None:
            current_cols = int(ceil(len_children / float(current_rows)))
        elif current_rows is None:
            current_rows = int(ceil(len_children / float(current_cols)))

        current_cols = max(1, current_cols)
        current_rows = max(1, current_rows)

        cols = [self.col_default_width] * current_cols
        cols_sh = [None] * current_cols
        rows = [self.row_default_height] * current_rows
        rows_sh = [None] * current_rows

        # update minimum size from the dicts
        # FIXME index might be outside the bounds ?
        for index, value in self.cols_minimum.items():
            cols[index] = value
        for index, value in self.rows_minimum.items():
            rows[index] = value

        # calculate minimum size for each columns and rows
        i = len_children - 1
        for row in range(current_rows):
            for col in range(current_cols):

                # don't go further is we don't have child left
                if i < 0:
                    break

                # get initial information from the child
                c = children[i]
                shw = c.size_hint_x
                shh = c.size_hint_y
                w = c.width
                h = c.height

                # compute minimum size / maximum stretch needed
                if shw is None:
                    cols[col] = nmax(cols[col], w)
                else:
                    cols_sh[col] = nmax(cols_sh[col], shw)
                if shh is None:
                    rows[row] = nmax(rows[row], h)
                else:
                    rows_sh[row] = nmax(rows_sh[row], shh)

                # next child
                i = i - 1

        # calculate minimum width/height needed, starting from padding + spacing
        padding_x = self.padding[0] + self.padding[2]
        padding_y = self.padding[1] + self.padding[3]
        spacing_x, spacing_y = self.spacing
        width = padding_x + spacing_x * (current_cols - 1)
        height = padding_y + spacing_y * (current_rows - 1)
        # then add the cell size
        width += sum(cols)
        height += sum(rows)

        # remember for layout
        self._cols = cols
        self._rows = rows
        self._cols_sh = cols_sh
        self._rows_sh = rows_sh

        # finally, set the minimum size
        self.minimum_size = (width, height)

    def do_layout(self, *largs):
        self.update_minimum_size()
        if self._cols is None:
            return
        if self.cols is None and self.rows is None:
            raise GridLayoutException('Need at least cols or rows constraint.')

        children = self.children
        len_children = len(children)
        if len_children == 0:
            return

        # speedup
        padding_left = self.padding[0]
        padding_top = self.padding[1]
        spacing_x, spacing_y = self.spacing
        selfx = self.x
        selfw = self.width
        selfh = self.height

        # resolve size for each column
        if self.col_force_default:
            cols = [self.col_default_width] * len(self._cols)
            for index, value in self.cols_minimum.items():
                cols[index] = value
        else:
            cols = self._cols[:]
            cols_sh = self._cols_sh
            cols_weigth = sum([x for x in cols_sh if x])
            strech_w = max(0, selfw - self.minimum_width)
            for index in range(len(cols)):
                # if the col don't have strech information, nothing to do
                col_stretch = cols_sh[index]
                if col_stretch is None:
                    continue
                # calculate the column stretch, and take the maximum from
                # minimum size and the calculated stretch
                col_width = cols[index]
                col_width = max(col_width, strech_w * col_stretch / cols_weigth)
                cols[index] = col_width

        # same algo for rows
        if self.row_force_default:
            rows = [self.row_default_height] * len(self._rows)
            for index, value in self.rows_minimum.items():
                rows[index] = value
        else:
            rows = self._rows[:]
            rows_sh = self._rows_sh
            rows_weigth = sum([x for x in rows_sh if x])
            strech_h = max(0, selfh - self.minimum_height)
            for index in range(len(rows)):
                # if the row don't have strech information, nothing to do
                row_stretch = rows_sh[index]
                if row_stretch is None:
                    continue
                # calculate the row stretch, and take the maximum from minimum
                # size and the calculated stretch
                row_height = rows[index]
                row_height = max(row_height,
                                 strech_h * row_stretch / rows_weigth)
                rows[index] = row_height

        # reposition every child
        i = len_children - 1
        y = self.top - padding_top
        for row_height in rows:
            x = selfx + padding_left
            for col_width in cols:
                if i < 0:
                    break
                c = children[i]
                c.x = x
                c.y = y - row_height
                c.width = col_width
                c.height = row_height
                i = i - 1
                x = x + col_width + spacing_x
            y -= row_height + spacing_y

