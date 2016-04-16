"""
RecycleLayout
=============

.. warning::
    This module is highly experimental, its API may change in the future and
    the documentation is not complete at this time.
"""

from kivy.uix.recycleview.layout import RecycleLayoutManagerBehavior
from kivy.uix.layout import Layout
from kivy.properties import ObjectProperty, StringProperty
from kivy.factory import Factory

__all__ = ('RecycleLayout', )


class RecycleLayout(RecycleLayoutManagerBehavior, Layout):

    default_size = ObjectProperty((100, 100))
    '''size as in w, h. They each can be None.
    '''
    key_size = StringProperty(None, allownone=True)
    default_size_hint = ObjectProperty((None, None))
    key_size_hint = StringProperty(None, allownone=True)
    default_pos_hint = ObjectProperty({})
    key_pos_hint = StringProperty(None, allownone=True)
    initial_size = ObjectProperty((100, 100))

    view_opts = []

    _size_needs_update = False
    _changed_views = []

    view_indices = {}

    def __init__(self, **kwargs):
        self.view_indices = {}
        self._updated_views = []
        self._trigger_layout = self._catch_layout_trigger
        super(RecycleLayout, self).__init__(**kwargs)

    def attach_recycleview(self, rv):
        super(RecycleLayout, self).attach_recycleview(rv)
        if rv:
            fbind = self.fbind
            fbind('default_size', rv.refresh_from_data)
            fbind('key_size', rv.refresh_from_data)
            fbind('default_size_hint', rv.refresh_from_data)
            fbind('key_size_hint', rv.refresh_from_data)
            fbind('default_pos_hint', rv.refresh_from_data)
            fbind('key_pos_hint', rv.refresh_from_data)

    def detach_recycleview(self):
        rv = self.recycleview
        if rv:
            funbind = self.funbind
            funbind('default_size', rv.refresh_from_data)
            funbind('key_size', rv.refresh_from_data)
            funbind('default_size_hint', rv.refresh_from_data)
            funbind('key_size_hint', rv.refresh_from_data)
            funbind('default_pos_hint', rv.refresh_from_data)
            funbind('key_pos_hint', rv.refresh_from_data)
        super(RecycleLayout, self).detach_recycleview()

    def _catch_layout_trigger(self, instance=None, value=None):
        rv = self.recycleview
        if rv is None:
            return

        idx = self.view_indices.get(instance)
        if idx is not None:
            if self._size_needs_update:
                return
            opt = self.view_opts[idx]
            if (instance.size == opt['size'] and
                instance.size_hint == opt['size_hint'] and
                instance.pos_hint == opt['pos_hint']):
                return
            self._size_needs_update = True
            rv.refresh_from_layout(view_size=True)
        else:
            rv.refresh_from_layout()

    def compute_sizes_from_data(self, data, flags):
        if [f for f in flags if not f]:
            # at least one changed data unpredictably
            self.clear_layout()
            opts = self.view_opts = [None for _ in data]
        else:
            opts = self.view_opts
            changed = False
            for flag in flags:
                for k, v in flag.items():
                    changed = True
                    if k == 'removed':
                        del opts[v]
                    elif k == 'appended':
                        opts.extend([None, ] * (v.stop - v.start))
                    elif k == 'inserted':
                        opts.insert(v, None)
                    elif k == 'modified':
                        start, stop, step = v.start, v.stop, v.step
                        r = range (start, stop) if step == None else \
                            range(start, stop, step)
                        for i in r:
                            opts[i] = None
                    else:
                        raise Exception('Unrecognized data flag {}'.format(k))

            if changed:
                self.clear_layout()

        assert len(data) == len(opts)
        ph_key = self.key_pos_hint
        ph_def = self.default_pos_hint
        sh_key = self.key_size_hint
        sh_def = self.default_size_hint
        s_key = self.key_size
        s_def = self.default_size
        viewcls_def = self.viewclass
        viewcls_key = self.key_viewclass
        iw, ih = self.initial_size

        sh = []
        for i, item in enumerate(data):
            if opts[i] is not None:
                continue

            ph = ph_def if ph_key is None else item.get(ph_key, ph_def)
            ph = item.get('pos_hint', ph)

            sh = sh_def if sh_key is None else item.get(sh_key, sh_def)
            sh = item.get('size_hint', sh)
            sh = [item.get('size_hint_x', sh[0]),
                  item.get('size_hint_y', sh[1])]

            s = s_def if s_key is None else item.get(s_key, s_def)
            s = item.get('size', s)
            w, h = s = item.get('width', s[0]), item.get('height', s[1])

            viewcls = None
            if viewcls_key is not None:
                viewcls = item.get(viewcls_key)
                if viewcls is not None:
                    viewcls = getattr(Factory, viewcls)
            if viewcls is None:
                viewcls = viewcls_def

            opts[i] = {
                'size': [(iw if w is None else w), (ih if h is None else h)],
                'size_hint': sh, 'pos': None, 'pos_hint': ph,
                'viewclass': viewcls, 'width_none': w is None,
                'height_none': h is None}

    def compute_layout(self, data, flags):
        self._size_needs_update = False

        opts = self.view_opts
        changed = []
        for widget, index in self.view_indices.items():
            opt = opts[index]
            s = opt['size']
            w, h = sn = widget.size
            sh = opt['size_hint']
            shnw, shnh = shn = widget.size_hint
            ph = opt['pos_hint']
            phn = widget.pos_hint
            if s != sn or sh != shn or ph != phn:
                changed.append((index, widget, s, sn, sh, shn, ph, phn))
                if shnw is None:
                    if shnh is None:
                        opt['size'] = sn
                    else:
                        opt['size'] = [w, s[1]]
                elif shnh is None:
                    opt['size'] = [s[0], h]
                opt['size_hint'] = shn
                opt['pos_hint'] = phn

        if [f for f in flags if not f]:  # need to redo everything
            self._changed_views = []
        else:
            self._changed_views = changed if changed else None

    def do_layout(self, *largs):
        assert False

    def set_visible_views(self, indices, data, viewport):
        view_opts = self.view_opts
        new, remaining, old = self.recycleview.view_adapter.set_visible_views(
            indices, data, view_opts)

        remove = self.remove_widget
        view_indices = self.view_indices
        for _, widget in old:
            remove(widget)
            del view_indices[widget]

        # first update the sizing info so that when we update the size
        # the widgets are not bound and won't trigger a re-layout
        refresh_view_layout = self.refresh_view_layout
        for index, widget in new:
            # make sure widget is added first so that any sizing updates
            # will be recorded
            opt = view_opts[index]
            refresh_view_layout(
                index, opt['pos'], opt['pos_hint'], opt['size'],
                opt['size_hint'], widget, viewport)

        # then add all the visible widgets, which binds size/size_hint
        add = self.add_widget
        for index, widget in new:
            # add to the container if it's not already done
            view_indices[widget] = index
            if widget.parent is None:
                add(widget)

        # finally, make sure if the size has changed to cause a re-layout
        changed = False
        for index, widget in new:
            opt = view_opts[index]
            if (changed or widget.size == opt['size'] and
                widget.size_hint == opt['size_hint'] and
                widget.pos_hint == opt['pos_hint']):
                continue
            changed = True

        if changed:
            # we could use LayoutChangeException here, but refresh_views in rv
            # needs to be updated to watch for it in the layout phase
            self._size_needs_update = True
            self.recycleview.refresh_from_layout(view_size=True)

    def refresh_view_layout(self, index, pos, pos_hint, size, size_hint, view,
                            viewport):
        opt = self.view_opts[index]
        w, h = size
        shw, shh = size_hint
        if shw is None and opt['width_none']:
            w = None
        if shh is None and opt['height_none']:
            h = None
        super(RecycleLayout, self).refresh_view_layout(
            index, pos, pos_hint, (w, h), size_hint, view, viewport)

    def remove_views(self):
        super(RecycleLayout, self).remove_views()
        self.clear_widgets()
        self.view_indices = {}

    def remove_view(self, view, index):
        super(RecycleLayout, self).remove_view(view, index)
        self.remove_widget(view)
        del self.view_indices[view]

    def clear_layout(self):
        super(RecycleLayout, self).clear_layout()
        self.clear_widgets()
        self.view_indices = {}
        self._size_needs_update = False
