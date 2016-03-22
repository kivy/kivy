'''
Layout
======

Layouts are used to calculate and assign widget positions.

The :class:`Layout` class itself cannot be used directly.
You should use one of the following layout classes:

- Anchor layout: :class:`kivy.uix.anchorlayout.AnchorLayout`
- Box layout: :class:`kivy.uix.boxlayout.BoxLayout`
- Float layout: :class:`kivy.uix.floatlayout.FloatLayout`
- Grid layout: :class:`kivy.uix.gridlayout.GridLayout`
- Page Layout: :class:`kivy.uix.pagelayout.PageLayout`
- Relative layout: :class:`kivy.uix.relativelayout.RelativeLayout`
- Scatter layout: :class:`kivy.uix.scatterlayout.ScatterLayout`
- Stack layout: :class:`kivy.uix.stacklayout.StackLayout`


Understanding the `size_hint` Property in `Widget`
--------------------------------------------------

The :attr:`~kivy.uix.Widget.size_hint` is a tuple of values used by
layouts to manage the sizes of their children. It indicates the size
relative to the layout's size instead of an absolute size (in
pixels/points/cm/etc). The format is::

    widget.size_hint = (width_percent, height_percent)

The percent is specified as a floating point number in the range 0-1. For
example, 0.5 is 50%, 1 is 100%.

If you want a widget's width to be half of the parent's width and the
height to be identical to the parent's height, you would do::

    widget.size_hint = (0.5, 1.0)

If you don't want to use a size_hint for either the width or height, set the
value to None. For example, to make a widget that is 250px wide and 30%
of the parent's height, do::

    widget.size_hint = (None, 0.3)
    widget.width = 250

Being :class:`Kivy properties <kivy.properties>`, these can also be set via
constructor arguments::

    widget = Widget(size_hint=(None, 0.3), width=250)

.. versionchanged:: 1.4.1
    The `reposition_child` internal method (made public by mistake) has
    been removed.

'''

__all__ = ('Layout', )

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.recycleview.layout import RecycleLayoutManagerBehavior


class Layout(Widget):
    '''Layout interface class, used to implement every layout. See module
    documentation for more information.
    '''

    _trigger_layout = None

    def __init__(self, **kwargs):
        if self.__class__ == Layout:
            raise Exception('The Layout class is abstract and \
                cannot be used directly.')
        if self._trigger_layout is None:
            self._trigger_layout = Clock.create_trigger(self.do_layout, -1)
        super(Layout, self).__init__(**kwargs)

    def do_layout(self, *largs):
        '''This function is called when a layout is needed by a trigger.
        If you are writing a new Layout subclass, don't call this function
        directly but use :meth:`_trigger_layout` instead.
        .. versionadded:: 1.0.8
        '''
        raise NotImplementedError('Must be implemented in subclasses.')

    def add_widget(self, widget, index=0):
        fbind = widget.fbind
        fbind('size', self._trigger_layout)
        fbind('size_hint', self._trigger_layout)
        return super(Layout, self).add_widget(widget, index)

    def remove_widget(self, widget):
        funbind = widget.funbind
        funbind('size', self._trigger_layout)
        funbind('size_hint', self._trigger_layout)
        return super(Layout, self).remove_widget(widget)


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

        if self._size_needs_update:
            return
        idx = self.view_indices.get(instance)
        if idx is not None:
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
        if [f for f in flags if not f]:  # need to redo everything
            self._changed_views = []
        else:
            opts = self.view_opts
            changed = []
            for widget, index in self.view_indices.items():
                opt = opts[index]
                s = opt['size']
                sn = widget.size
                sh = opt['size_hint']
                shn = widget.size_hint
                ph = opt['pos_hint']
                phn = widget.pos_hint
                if s != sn or sh != shn or ph != phn:
                    changed.append((index, widget, s, sn, sh, shn, ph, phn))
                    opt['size'] = sn
                    opt['size_hint'] = shn
                    opt['pos_hint'] = phn

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
        if opt['width_none']:
            w = None
        if opt['height_none']:
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
