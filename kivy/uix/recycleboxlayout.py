"""
RecycleBoxLayout
================

.. versionadded:: 1.9.2

.. warning::
    This module is highly experimental, its API may change in the future and
    the documentation is not complete at this time.

The RecycleBoxLayout is designed to provide a
:class:`~kivy.uix.boxlayout.BoxLayout` type layout when used with the
:class:`~kivy.uix.recycleview.RecycleView` widget. Please refer to the
:mod:`~kivy.uix.recycleview` module documentation for more information.

"""

from kivy.uix.recyclelayout import RecycleLayout
from kivy.uix.boxlayout import BoxLayout

__all__ = ('RecycleBoxLayout', )


class RecycleBoxLayout(RecycleLayout, BoxLayout):

    _rv_positions = None

    def __init__(self, **kwargs):
        super(RecycleBoxLayout, self).__init__(**kwargs)
        self.funbind('children', self._trigger_layout)

    def _update_sizes(self, changed):
        horizontal = self.orientation == 'horizontal'
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

        return relayout

    def compute_layout(self, data, flags):
        super(RecycleBoxLayout, self).compute_layout(data, flags)

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
        n = len(view_opts)
        for i, x, y, w, h in self._iterate_layout(
                [(opt['size'], opt['size_hint'], opt['pos_hint'],
                  opt['size_hint_min'], opt['size_hint_max']) for
                 opt in reversed(view_opts)]):
            opt = view_opts[n - i - 1]
            shw, shh = opt['size_hint']
            opt['pos'] = x, y
            wo, ho = opt['size']
            # layout won't/shouldn't change previous size if size_hint is None
            # which is what w/h being None means.
            opt['size'] = [(wo if shw is None else w),
                           (ho if shh is None else h)]

        spacing = self.spacing
        pos = self._rv_positions = [None, ] * len(data)

        if self.orientation == 'horizontal':
            pos[0] = self.x
            last = pos[0] + self.padding[0] + view_opts[0]['size'][0] + \
                spacing / 2.
            for i, val in enumerate(view_opts[1:], 1):
                pos[i] = last
                last += val['size'][0] + spacing
        else:
            last = pos[-1] = \
                self.y + self.height - self.padding[1] - \
                view_opts[0]['size'][1] - spacing / 2.
            n = len(view_opts)
            for i, val in enumerate(view_opts[1:], 1):
                last -= spacing + val['size'][1]
                pos[n - 1 - i] = last

    def get_view_index_at(self, pos):
        calc_pos = self._rv_positions
        if not calc_pos:
            return 0

        x, y = pos

        if self.orientation == 'horizontal':
            if x >= calc_pos[-1] or len(calc_pos) == 1:
                return len(calc_pos) - 1

            ix = 0
            for val in calc_pos[1:]:
                if x < val:
                    return ix
                ix += 1
        else:
            if y >= calc_pos[-1] or len(calc_pos) == 1:
                return 0

            iy = 0
            for val in calc_pos[1:]:
                if y < val:
                    return len(calc_pos) - iy - 1
                iy += 1

        assert False

    def compute_visible_views(self, data, viewport):
        if self._rv_positions is None or not data:
            return []

        x, y, w, h = viewport
        at_idx = self.get_view_index_at
        if self.orientation == 'horizontal':
            a, b = at_idx((x, y)), at_idx((x + w, y))
        else:
            a, b = at_idx((x, y + h)), at_idx((x, y))
        return list(range(a, b + 1))
