"""
RecycleBoxLayout
================

.. versionadded:: 1.10.0

.. warning::
    This module is highly experimental, its API may change in the future and
    the documentation is not complete at this time.

The RecycleBoxLayout is designed to provide a
:class:`~kivy.uix.boxlayout.BoxLayout` type layout when used with the
:class:`~kivy.uix.recycleview.RecycleView` widget. Please refer to the
:mod:`~kivy.uix.recycleview` module documentation for more information.

"""

from itertools import accumulate, islice, chain
from kivy.uix.recyclelayout import RecycleLayout
from kivy.uix.boxlayout import BoxLayout

__all__ = ('RecycleBoxLayout', )


class RecycleBoxLayout(RecycleLayout, BoxLayout):

    _rv_positions = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.funbind('children', self._trigger_layout)

    def _update_sizes(self, changed):
        horizontal = self._is_horizontal
        padding_left, padding_top, padding_right, padding_bottom = self.padding
        padding_x = padding_left + padding_right
        padding_y = padding_top + padding_bottom
        selfw = self.width
        selfh = self.height
        layout_w = max(0, selfw - padding_x)
        layout_h = max(0, selfh - padding_y)
        cx = self.x + padding_left
        cy = self.y + padding_bottom
        view_opts = self.view_opts
        remove_view = self.remove_view

        for (index, widget, (w, h), (wn, hn), (shw, shh), (shnw, shnh),
             (shw_min, shh_min), (shwn_min, shhn_min), (shw_max, shh_max),
             (shwn_max, shhn_max), ph, phn) in changed:
            if (horizontal and
                (shw != shnw or w != wn or shw_min != shwn_min or
                 shw_max != shwn_max) or
                not horizontal and
                (shh != shnh or h != hn or shh_min != shhn_min or
                 shh_max != shhn_max)):
                return True

            remove_view(widget, index)
            opt = view_opts[index]
            if horizontal:
                wo, ho = opt['size']
                if shnh is not None:
                    _, h = opt['size'] = [wo, shnh * layout_h]
                else:
                    h = ho

                xo, yo = opt['pos']
                for key, value in phn.items():
                    posy = value * layout_h
                    if key == 'y':
                        yo = posy + cy
                    elif key == 'top':
                        yo = posy - h
                    elif key == 'center_y':
                        yo = posy - (h / 2.)
                opt['pos'] = [xo, yo]
            else:
                wo, ho = opt['size']
                if shnw is not None:
                    w, _ = opt['size'] = [shnw * layout_w, ho]
                else:
                    w = wo

                xo, yo = opt['pos']
                for key, value in phn.items():
                    posx = value * layout_w
                    if key == 'x':
                        xo = posx + cx
                    elif key == 'right':
                        xo = posx - w
                    elif key == 'center_x':
                        xo = posx - (w / 2.)
                opt['pos'] = [xo, yo]

        return False

    def compute_layout(self, data, flags):
        super().compute_layout(data, flags)

        changed = self._changed_views
        if (changed is None or
                changed and not self._update_sizes(changed)):
            return

        self.clear_layout()
        self._rv_positions = None
        if not data:
            l, t, r, b = self.padding
            self.minimum_size = l + r, t + b
            return

        view_opts = self.view_opts
        n_data = len(view_opts)
        for i, x, y, w, h in self._iterate_layout(
                [(opt['size'], opt['size_hint'], opt['pos_hint'],
                  opt['size_hint_min'], opt['size_hint_max']) for
                 opt in reversed(view_opts)]):
            opt = view_opts[n_data - i - 1]
            shw, shh = opt['size_hint']
            opt['pos'] = x, y
            wo, ho = opt['size']
            # layout won't/shouldn't change previous size if size_hint is None
            # which is what w/h being None means.
            opt['size'] = [(wo if shw is None else w),
                           (ho if shh is None else h)]

        spacing = self.spacing
        padding = self.padding
        is_horizontal = self._is_horizontal
        is_forward = self._is_forward_direction
        dim = not is_horizontal
        offset = ((self.x + padding[0]) if is_horizontal else
            (self.y + padding[3])) - spacing / 2.
        self._rv_positions = tuple(islice(
            accumulate(chain(
                (offset, ),
                (opt['size'][dim] + spacing for opt in (
                    view_opts if is_forward else reversed(view_opts))),
            )),
            1, n_data,
        ))

    def get_view_index_at(self, pos):
        calc_pos = self._rv_positions
        if not calc_pos:
            return 0
        pos = pos[not self._is_horizontal]
        idx = 0
        for v in calc_pos:
            if pos < v:
                break
            idx += 1
        return idx if (self._is_forward_direction) \
            else (len(self.view_opts) - idx - 1)

    def compute_visible_views(self, data, viewport):
        if self._rv_positions is None or not data:
            return []

        x, y, w, h = viewport
        at_idx = self.get_view_index_at
        a, b = at_idx((x, y)), at_idx((x + w, y + h))
        if not self._is_forward_direction:
            a, b = b, a
        return list(range(a, b + 1))
