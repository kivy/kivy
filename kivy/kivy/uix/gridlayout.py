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

.. versionchanged:: 1.0.7
    The implementation has changed to use the widget size_hint for calculating
    column/row sizes. `uniform_width` and `uniform_height` have been removed
    and other properties have added to give you more control.

Background
----------

Unlike many other toolkits, you cannot explicitly place a widget in a specific
column/row. Each child is automatically assigned a position determined by the
layout configuration and the child's index in the children list.

A GridLayout must always have at least one input constraint:
:attr:`GridLayout.cols` or :attr:`GridLayout.rows`. If you do not specify cols
or rows, the Layout will throw an exception.

Column Width and Row Height
---------------------------

The column width/row height are determined in 3 steps:

    - The initial size is given by the :attr:`col_default_width` and
      :attr:`row_default_height` properties. To customize the size of a single
      column or row, use :attr:`cols_minimum` or :attr:`rows_minimum`.
    - The `size_hint_x`/`size_hint_y` of the children are taken into account.
      If no widgets have a size hint, the maximum size is used for all
      children.
    - You can force the default size by setting the :attr:`col_force_default`
      or :attr:`row_force_default` property. This will force the layout to
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
    BoundedNumericProperty, ReferenceListProperty, VariableListProperty, \
    ObjectProperty, StringProperty, OptionProperty
from math import ceil
from itertools import accumulate, product, chain, islice
from operator import sub


def nmax(*args):
    # merge into one list
    args = [x for x in args if x is not None]
    return max(args)


def nmin(*args):
    # merge into one list
    args = [x for x in args if x is not None]
    return min(args)


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

    :attr:`spacing` is a
    :class:`~kivy.properties.VariableListProperty` and defaults to [0, 0].
    '''

    padding = VariableListProperty([0, 0, 0, 0])
    '''Padding between the layout box and its children: [padding_left,
    padding_top, padding_right, padding_bottom].

    padding also accepts a two argument form [padding_horizontal,
    padding_vertical] and a one argument form [padding].

    .. versionchanged:: 1.7.0
        Replaced NumericProperty with VariableListProperty.

    :attr:`padding` is a :class:`~kivy.properties.VariableListProperty` and
    defaults to [0, 0, 0, 0].
    '''

    cols = BoundedNumericProperty(None, min=0, allownone=True)
    '''Number of columns in the grid.

    .. versionchanged:: 1.0.8
        Changed from a NumericProperty to BoundedNumericProperty. You can no
        longer set this to a negative value.

    :attr:`cols` is a :class:`~kivy.properties.NumericProperty` and defaults to
    None.
    '''

    rows = BoundedNumericProperty(None, min=0, allownone=True)
    '''Number of rows in the grid.

    .. versionchanged:: 1.0.8
        Changed from a NumericProperty to a BoundedNumericProperty. You can no
        longer set this to a negative value.

    :attr:`rows` is a :class:`~kivy.properties.NumericProperty` and defaults to
    None.
    '''

    col_default_width = NumericProperty(0)
    '''Default minimum size to use for a column.

    .. versionadded:: 1.0.7

    :attr:`col_default_width` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0.
    '''

    row_default_height = NumericProperty(0)
    '''Default minimum size to use for row.

    .. versionadded:: 1.0.7

    :attr:`row_default_height` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0.
    '''

    col_force_default = BooleanProperty(False)
    '''If True, ignore the width and size_hint_x of the child and use the
    default column width.

    .. versionadded:: 1.0.7

    :attr:`col_force_default` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to False.
    '''

    row_force_default = BooleanProperty(False)
    '''If True, ignore the height and size_hint_y of the child and use the
    default row height.

    .. versionadded:: 1.0.7

    :attr:`row_force_default` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to False.
    '''

    cols_minimum = DictProperty({})
    '''Dict of minimum width for each column. The dictionary keys are the
    column numbers, e.g. 0, 1, 2...

    .. versionadded:: 1.0.7

    :attr:`cols_minimum` is a :class:`~kivy.properties.DictProperty` and
    defaults to {}.
    '''

    rows_minimum = DictProperty({})
    '''Dict of minimum height for each row. The dictionary keys are the
    row numbers, e.g. 0, 1, 2...

    .. versionadded:: 1.0.7

    :attr:`rows_minimum` is a :class:`~kivy.properties.DictProperty` and
    defaults to {}.
    '''

    minimum_width = NumericProperty(0)
    '''Automatically computed minimum width needed to contain all children.

    .. versionadded:: 1.0.8

    :attr:`minimum_width` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0. It is read only.
    '''

    minimum_height = NumericProperty(0)
    '''Automatically computed minimum height needed to contain all children.

    .. versionadded:: 1.0.8

    :attr:`minimum_height` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0. It is read only.
    '''

    minimum_size = ReferenceListProperty(minimum_width, minimum_height)
    '''Automatically computed minimum size needed to contain all children.

    .. versionadded:: 1.0.8

    :attr:`minimum_size` is a
    :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`minimum_width`, :attr:`minimum_height`) properties. It is read
    only.
    '''

    orientation = OptionProperty('lr-tb', options=(
        'lr-tb', 'tb-lr', 'rl-tb', 'tb-rl', 'lr-bt', 'bt-lr', 'rl-bt',
        'bt-rl'))
    '''Orientation of the layout.

    :attr:`orientation` is an :class:`~kivy.properties.OptionProperty` and
    defaults to 'lr-tb'.

    Valid orientations are 'lr-tb', 'tb-lr', 'rl-tb', 'tb-rl', 'lr-bt',
    'bt-lr', 'rl-bt' and 'bt-rl'.

    .. versionadded:: 2.0.0

    .. note::

        'lr' means Left to Right.
        'rl' means Right to Left.
        'tb' means Top to Bottom.
        'bt' means Bottom to Top.
    '''

    def __init__(self, **kwargs):
        self._cols = self._rows = None
        super(GridLayout, self).__init__(**kwargs)
        fbind = self.fbind
        update = self._trigger_layout
        fbind('col_default_width', update)
        fbind('row_default_height', update)
        fbind('col_force_default', update)
        fbind('row_force_default', update)
        fbind('cols', update)
        fbind('rows', update)
        fbind('parent', update)
        fbind('spacing', update)
        fbind('padding', update)
        fbind('children', update)
        fbind('size', update)
        fbind('pos', update)
        fbind('orientation', update)

    def get_max_widgets(self):
        if self.cols and self.rows:
            return self.rows * self.cols
        else:
            return None

    def on_children(self, instance, value):
        # if that makes impossible to construct things with deferred method,
        # migrate this test in do_layout, and/or issue a warning.
        smax = self.get_max_widgets()
        if smax and len(value) > smax:
            raise GridLayoutException(
                'Too many children in GridLayout. Increase rows/cols!')

    @property
    def _fills_row_first(self):
        return self.orientation[0] in 'lr'

    @property
    def _fills_from_left_to_right(self):
        return 'lr' in self.orientation

    @property
    def _fills_from_top_to_bottom(self):
        return 'tb' in self.orientation

    def _init_rows_cols_sizes(self, count):
        # the goal here is to calculate the minimum size of every cols/rows
        # and determine if they have stretch or not
        current_cols = self.cols
        current_rows = self.rows

        # if no cols or rows are set, we can't calculate minimum size.
        # the grid must be constrained at least on one side
        if not current_cols and not current_rows:
            Logger.warning('%r have no cols or rows set, '
                           'layout is not triggered.' % self)
            return

        if current_cols is None:
            current_cols = int(ceil(count / float(current_rows)))
        elif current_rows is None:
            current_rows = int(ceil(count / float(current_cols)))

        current_cols = max(1, current_cols)
        current_rows = max(1, current_rows)

        self._has_hint_bound_x = False
        self._has_hint_bound_y = False
        self._cols_min_size_none = 0.  # min size from all the None hint
        self._rows_min_size_none = 0.  # min size from all the None hint
        self._cols = cols = [self.col_default_width] * current_cols
        self._cols_sh = [None] * current_cols
        self._cols_sh_min = [None] * current_cols
        self._cols_sh_max = [None] * current_cols
        self._rows = rows = [self.row_default_height] * current_rows
        self._rows_sh = [None] * current_rows
        self._rows_sh_min = [None] * current_rows
        self._rows_sh_max = [None] * current_rows

        # update minimum size from the dicts
        items = (i for i in self.cols_minimum.items() if i[0] < len(cols))
        for index, value in items:
            cols[index] = max(value, cols[index])

        items = (i for i in self.rows_minimum.items() if i[0] < len(rows))
        for index, value in items:
            rows[index] = max(value, rows[index])
        return True

    def _fill_rows_cols_sizes(self):
        cols, rows = self._cols, self._rows
        cols_sh, rows_sh = self._cols_sh, self._rows_sh
        cols_sh_min, rows_sh_min = self._cols_sh_min, self._rows_sh_min
        cols_sh_max, rows_sh_max = self._cols_sh_max, self._rows_sh_max

        # calculate minimum size for each columns and rows
        has_bound_y = has_bound_x = False
        idx_iter = self._create_idx_iter(len(cols), len(rows))
        for child, (col, row) in zip(reversed(self.children), idx_iter):
            (shw, shh), (w, h) = child.size_hint, child.size
            shw_min, shh_min = child.size_hint_min
            shw_max, shh_max = child.size_hint_max

            # compute minimum size / maximum stretch needed
            if shw is None:
                cols[col] = nmax(cols[col], w)
            else:
                cols_sh[col] = nmax(cols_sh[col], shw)
                if shw_min is not None:
                    has_bound_x = True
                    cols_sh_min[col] = nmax(cols_sh_min[col], shw_min)
                if shw_max is not None:
                    has_bound_x = True
                    cols_sh_max[col] = nmin(cols_sh_max[col], shw_max)

            if shh is None:
                rows[row] = nmax(rows[row], h)
            else:
                rows_sh[row] = nmax(rows_sh[row], shh)
                if shh_min is not None:
                    has_bound_y = True
                    rows_sh_min[row] = nmax(rows_sh_min[row], shh_min)
                if shh_max is not None:
                    has_bound_y = True
                    rows_sh_max[row] = nmin(rows_sh_max[row], shh_max)
        self._has_hint_bound_x = has_bound_x
        self._has_hint_bound_y = has_bound_y

    def _update_minimum_size(self):
        # calculate minimum width/height needed, starting from padding +
        # spacing
        l, t, r, b = self.padding
        spacing_x, spacing_y = self.spacing
        cols, rows = self._cols, self._rows

        width = l + r + spacing_x * (len(cols) - 1)
        self._cols_min_size_none = sum(cols) + width
        # we need to subtract for the sh_max/min the already guaranteed size
        # due to having a None in the col. So sh_min gets smaller by that size
        # since it's already covered. Similarly for sh_max, because if we
        # already exceeded the max, the subtracted max will be zero, so
        # it won't get larger
        if self._has_hint_bound_x:
            cols_sh_min = self._cols_sh_min
            cols_sh_max = self._cols_sh_max

            for i, (c, sh_min, sh_max) in enumerate(
                    zip(cols, cols_sh_min, cols_sh_max)):
                if sh_min is not None:
                    width += max(c, sh_min)
                    cols_sh_min[i] = max(0., sh_min - c)
                else:
                    width += c

                if sh_max is not None:
                    cols_sh_max[i] = max(0., sh_max - c)
        else:
            width = self._cols_min_size_none

        height = t + b + spacing_y * (len(rows) - 1)
        self._rows_min_size_none = sum(rows) + height
        if self._has_hint_bound_y:
            rows_sh_min = self._rows_sh_min
            rows_sh_max = self._rows_sh_max

            for i, (r, sh_min, sh_max) in enumerate(
                    zip(rows, rows_sh_min, rows_sh_max)):
                if sh_min is not None:
                    height += max(r, sh_min)
                    rows_sh_min[i] = max(0., sh_min - r)
                else:
                    height += r

                if sh_max is not None:
                    rows_sh_max[i] = max(0., sh_max - r)
        else:
            height = self._rows_min_size_none

        # finally, set the minimum size
        self.minimum_size = (width, height)

    def _finalize_rows_cols_sizes(self):
        selfw = self.width
        selfh = self.height

        # resolve size for each column
        if self.col_force_default:
            cols = [self.col_default_width] * len(self._cols)
            for index, value in self.cols_minimum.items():
                cols[index] = value
            self._cols = cols
        else:
            cols = self._cols
            cols_sh = self._cols_sh
            cols_sh_min = self._cols_sh_min
            cols_weight = float(sum((x for x in cols_sh if x is not None)))
            stretch_w = max(0., selfw - self._cols_min_size_none)

            if stretch_w > 1e-9:
                if self._has_hint_bound_x:
                    # fix the hints to be within bounds
                    self.layout_hint_with_bounds(
                        cols_weight, stretch_w,
                        sum((c for c in cols_sh_min if c is not None)),
                        cols_sh_min, self._cols_sh_max, cols_sh)

                for index, col_stretch in enumerate(cols_sh):
                    # if the col don't have stretch information, nothing to do
                    if not col_stretch:
                        continue
                    # add to the min width whatever remains from size_hint
                    cols[index] += stretch_w * col_stretch / cols_weight

        # same algo for rows
        if self.row_force_default:
            rows = [self.row_default_height] * len(self._rows)
            for index, value in self.rows_minimum.items():
                rows[index] = value
            self._rows = rows
        else:
            rows = self._rows
            rows_sh = self._rows_sh
            rows_sh_min = self._rows_sh_min
            rows_weight = float(sum((x for x in rows_sh if x is not None)))
            stretch_h = max(0., selfh - self._rows_min_size_none)

            if stretch_h > 1e-9:
                if self._has_hint_bound_y:
                    # fix the hints to be within bounds
                    self.layout_hint_with_bounds(
                        rows_weight, stretch_h,
                        sum((r for r in rows_sh_min if r is not None)),
                        rows_sh_min, self._rows_sh_max, rows_sh)

                for index, row_stretch in enumerate(rows_sh):
                    # if the row don't have stretch information, nothing to do
                    if not row_stretch:
                        continue
                    # add to the min height whatever remains from size_hint
                    rows[index] += stretch_h * row_stretch / rows_weight

    def _iterate_layout(self, count):
        orientation = self.orientation
        padding = self.padding
        spacing_x, spacing_y = self.spacing

        cols = self._cols
        if self._fills_from_left_to_right:
            x_iter = accumulate(chain(
                (self.x + padding[0], ),
                (
                    col_width + spacing_x
                    for col_width in islice(cols, len(cols) - 1)
                ),
            ))
        else:
            x_iter = accumulate(chain(
                (self.right - padding[2] - cols[-1], ),
                (
                    col_width + spacing_x
                    for col_width in islice(reversed(cols), 1, None)
                ),
            ), sub)
            cols = reversed(cols)

        rows = self._rows
        if self._fills_from_top_to_bottom:
            y_iter = accumulate(chain(
                (self.top - padding[1] - rows[0], ),
                (
                    row_height + spacing_y
                    for row_height in islice(rows, 1, None)
                ),
            ), sub)
        else:
            y_iter = accumulate(chain(
                (self.y + padding[3], ),
                (
                    row_height + spacing_y
                    for row_height in islice(reversed(rows), len(rows) - 1)
                ),
            ))
            rows = reversed(rows)

        if self._fills_row_first:
            for i, (y, x), (row_height, col_width) in zip(
                    reversed(range(count)),
                    product(y_iter, x_iter),
                    product(rows, cols)):
                yield i, x, y, col_width, row_height
        else:
            for i, (x, y), (col_width, row_height) in zip(
                    reversed(range(count)),
                    product(x_iter, y_iter),
                    product(cols, rows)):
                yield i, x, y, col_width, row_height

    def do_layout(self, *largs):
        children = self.children
        if not children or not self._init_rows_cols_sizes(len(children)):
            l, t, r, b = self.padding
            self.minimum_size = l + r, t + b
            return
        self._fill_rows_cols_sizes()
        self._update_minimum_size()
        self._finalize_rows_cols_sizes()

        for i, x, y, w, h in self._iterate_layout(len(children)):
            c = children[i]
            c.pos = x, y
            shw, shh = c.size_hint
            shw_min, shh_min = c.size_hint_min
            shw_max, shh_max = c.size_hint_max

            if shw_min is not None:
                if shw_max is not None:
                    w = max(min(w, shw_max), shw_min)
                else:
                    w = max(w, shw_min)
            else:
                if shw_max is not None:
                    w = min(w, shw_max)

            if shh_min is not None:
                if shh_max is not None:
                    h = max(min(h, shh_max), shh_min)
                else:
                    h = max(h, shh_min)
            else:
                if shh_max is not None:
                    h = min(h, shh_max)

            if shw is None:
                if shh is not None:
                    c.height = h
            else:
                if shh is None:
                    c.width = w
                else:
                    c.size = (w, h)

    def _create_idx_iter(self, n_cols, n_rows):
        col_indices = range(n_cols) if self._fills_from_left_to_right \
            else range(n_cols - 1, -1, -1)
        row_indices = range(n_rows) if self._fills_from_top_to_bottom \
            else range(n_rows - 1, -1, -1)

        if self._fills_row_first:
            return (
                (col_index, row_index)
                for row_index, col_index in product(row_indices, col_indices))
        else:
            return product(col_indices, row_indices)
