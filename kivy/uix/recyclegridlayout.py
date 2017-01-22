"""
RecycleGridLayout
=================

.. versionadded:: 1.9.2

.. warning::
    This module is highly experimental, its API may change in the future and
    the documentation is not complete at this time.

The RecycleGridLayout is designed to provide a
:class:`~kivy.uix.gridlayout.GridLayout` type layout when used with the
:class:`~kivy.uix.recycleview.RecycleView` widget. Please refer to the
:mod:`~kivy.uix.recycleview` module documentation for more information.
"""

from kivy.uix.recyclelayout import RecycleLayout
from kivy.uix.gridlayout import GridLayout, GridLayoutException, nmax, nmin
from collections import defaultdict

__all__ = ('RecycleGridLayout', )


class RecycleGridLayout(RecycleLayout, GridLayout):

    _cols_pos = None
    _rows_pos = None

    def __init__(self, **kwargs):
        super(RecycleGridLayout, self).__init__(**kwargs)
        self.funbind('children', self._trigger_layout)

    def on_children(self, instance, value):
        pass

    def _fill_rows_cols_sizes(self):
        cols, rows = self._cols, self._rows
        cols_sh, rows_sh = self._cols_sh, self._rows_sh
        cols_sh_min, rows_sh_min = self._cols_sh_min, self._rows_sh_min
        cols_sh_max, rows_sh_max = self._cols_sh_max, self._rows_sh_max
        self._cols_count = cols_count = [defaultdict(int) for _ in cols]
        self._rows_count = rows_count = [defaultdict(int) for _ in rows]

        # calculate minimum size for each columns and rows
        n_cols = len(cols)
        has_bound_y = has_bound_x = False
        for i, opt in enumerate(self.view_opts):
            (shw, shh), (w, h) = opt['size_hint'], opt['size']
            shw_min, shh_min = opt['size_hint_min']
            shw_max, shh_max = opt['size_hint_max']
            row, col = divmod(i, n_cols)

            if shw is None:
                cols_count[col][w] += 1
            if shh is None:
                rows_count[row][h] += 1

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

    def _update_rows_cols_sizes(self, changed):
        cols_count, rows_count = self._cols_count, self._rows_count
        cols, rows = self._cols, self._rows
        remove_view = self.remove_view
        n_cols = len(cols_count)

        # this can be further improved to reduce re-comp, but whatever...
        for index, widget, (w, h), (wn, hn), sh, shn, sh_min, shn_min, \
                sh_max, shn_max, _, _ in changed:
            if sh != shn or sh_min != shn_min or sh_max != shn_max:
                return True
            elif (sh[0] is not None and w != wn and
                  (h == hn or sh[1] is not None) or
                  sh[1] is not None and h != hn and
                  (w == wn or sh[0] is not None)):
                remove_view(widget, index)
            else:  # size hint is None, so check if it can be resized inplace
                row, col = divmod(index, n_cols)

                if w != wn:
                    col_w = cols[col]
                    cols_count[col][w] -= 1
                    cols_count[col][wn] += 1
                    was_last_w = cols_count[col][w] <= 0
                    if was_last_w and col_w == w or wn > col_w:
                        return True
                    if was_last_w:
                        del cols_count[col][w]

                if h != hn:
                    row_h = rows[row]
                    rows_count[row][h] -= 1
                    rows_count[row][hn] += 1
                    was_last_h = rows_count[row][h] <= 0
                    if was_last_h and row_h == h or hn > row_h:
                        return True
                    if was_last_h:
                        del rows_count[row][h]

        return False

    def compute_layout(self, data, flags):
        super(RecycleGridLayout, self).compute_layout(data, flags)

        n = len(data)
        smax = self.get_max_widgets()
        if smax and n > smax:
            raise GridLayoutException(
                'Too many children ({}) in GridLayout. Increase rows/cols!'.
                format(n))

        changed = self._changed_views
        if (changed is None or
                changed and not self._update_rows_cols_sizes(changed)):
            return

        self.clear_layout()
        if not self._init_rows_cols_sizes(n):
            self._cols_pos = None
            l, t, r, b = self.padding
            self.minimum_size = l + r, t + b
            return
        self._fill_rows_cols_sizes()
        self._update_minimum_size()
        self._finalize_rows_cols_sizes()

        view_opts = self.view_opts
        for widget, x, y, w, h in self._iterate_layout(n):
            opt = view_opts[n - widget - 1]
            shw, shh = opt['size_hint']
            opt['pos'] = x, y
            wo, ho = opt['size']
            # layout won't/shouldn't change previous size if size_hint is None
            # which is what w/h being None means.
            opt['size'] = [(wo if shw is None else w),
                           (ho if shh is None else h)]

        spacing_x, spacing_y = self.spacing
        cols, rows = self._cols, self._rows

        cols_pos = self._cols_pos = [None, ] * len(cols)
        rows_pos = self._rows_pos = [None, ] * len(rows)

        cols_pos[0] = self.x
        last = cols_pos[0] + self.padding[0] + cols[0] + spacing_x / 2.
        for i, val in enumerate(cols[1:], 1):
            cols_pos[i] = last
            last += val + spacing_x

        last = rows_pos[-1] = \
            self.y + self.height - self.padding[1] - rows[0] - spacing_y / 2.
        n = len(rows)
        for i, val in enumerate(rows[1:], 1):
            last -= spacing_y + val
            rows_pos[n - 1 - i] = last

    def get_view_index_at(self, pos):
        if self._cols_pos is None:
            return 0

        x, y = pos
        col_pos = self._cols_pos
        row_pos = self._rows_pos
        cols, rows = self._cols, self._rows
        if not col_pos or not row_pos:
            return 0

        if x >= col_pos[-1]:
            ix = len(cols) - 1
        else:
            ix = 0
            for val in col_pos[1:]:
                if x < val:
                    break
                ix += 1

        if y >= row_pos[-1]:
            iy = len(rows) - 1
        else:
            iy = 0
            for val in row_pos[1:]:
                if y < val:
                    break
                iy += 1

        # gridlayout counts from left to right, top to down
        iy = len(rows) - iy - 1
        return iy * len(cols) + ix

    def compute_visible_views(self, data, viewport):
        if self._cols_pos is None:
            return []
        x, y, w, h = viewport
        # gridlayout counts from left to right, top to down
        at_idx = self.get_view_index_at
        bl = at_idx((x, y))
        br = at_idx((x + w, y))
        tl = at_idx((x, y + h))
        n = len(data)

        indices = []
        row = len(self._cols)
        if row:
            x_slice = br - bl + 1
            for s in range(tl, bl + 1, row):
                indices.extend(range(min(s, n), min(n, s + x_slice)))

        return indices
