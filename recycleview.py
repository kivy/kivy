"""
RecycleView
===========

A flexible view for providing a limited window into a large data set.

Data accepted: list of dict.

TODO:
    - add custom function to get view height
    - add custom function to get view class
    - update view size when created
    - move all internals to adapter
    - selection
    - Method to clear cached class instances.
"""

import kivy
from kivy.compat import string_types
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.properties import NumericProperty, AliasProperty, StringProperty, \
    ObjectProperty, ListProperty, OptionProperty, BooleanProperty, \
    ObservableDict
from kivy.uix.behaviors import CompoundSelectionBehavior
from kivy.event import EventDispatcher
from kivy.factory import Factory
from kivy.clock import Clock
from collections import defaultdict
from functools import partial
from distutils.version import LooseVersion

_kivy_1_9_1 = LooseVersion(kivy.__version__) >= LooseVersion('1.9.1')

_view_base_cache = {}
'''Cache whose keys are classes and values is a boolean indicating whether the
class inherits from :class:`RecycleViewMixin`.
'''

_cached_views = defaultdict(list)
'''A size limited cache that contains old views (instances) that are not used.
Each key is a class whose value is the list of the instances of that class.
'''
# current number of unused classes in the class cache
_cache_count = 0
# maximum number of items in the class cache
_max_cache_size = 1000

def _clean_cache():
    '''Trims _cached_views cache to half the size of `_max_cache_size`.
    '''
    # all keys will be reduced to max_size.
    max_size = (_max_cache_size // 2) // len(_cached_views)
    global _cache_count
    for cls, instances in _cached_views.items():
        _cache_count -= max(0, len(instances) - max_size)
        del instances[max_size:]


class LayoutChangeException(Exception):
    pass


class RecycleViewLayout(Widget):
    '''The default :attr:`RecycleView.container` class used by
    :class:`RecycleView` to contain the widgets that provide the views into
    the :attr:`RecycleView.data`.

    As the views' size is controlled by the layout managers, we don't want the
    :RecycleViewLayout children's size/pos changes to cause
    a re-layout, so it inherits from Widget rather than a layout.
    '''
    pass


class RecycleViewMixin(object):
    '''A optional base class for data views (:attr:`RecycleView`.viewclass).
    If a view inherits from this class, the class's functions will be called
    when the view needs to be updated due to a data change or layout update.
    '''

    def refresh_view_attrs(self, rv, data):
        '''Called by the :class:`RecycleAdapter` when the view is initially
        populated with the values from the `data` dictionary for this item.

        :Parameters:

            `rv`: :class:`RecycleView` instance
                The :class:`RecycleView` that caused the update.
            `data`: dict
                The data dict used to populate this view.
        '''
        for key, value in data.items():
            setattr(self, key, value)

    def refresh_view_layout(self, rv, index, pos, size, viewport):
        '''Called when the view's size is updated by the layout manager,
        :class:`RecycleLayoutManager`.

        :Parameters:

            `rv`: :class:`RecycleView` instance
                The :class:`RecycleView` that caused the update.
            `viewport`: 4-tuple
                The coordinates of the bottom left and top right corners of
                the current visible area of the :class:`RecycleView`.
                E.g. 0, 0, 100, 100 for a area of size 100x100 at position
                0, 0). This may be larger than this view item.
            `data`: dict
                The data dict used to populate this view.
            `width`: float/int
                The width to which this view should be set.
            `height`: float/int
                The height to which this view should be set.

        :raises:
            `LayoutChangeException`: If the sizing or data changed during a
            call to this method, raising a `LayoutChangeException` exception
            will force a refresh. Useful when data changed and we don't want
            to layout further since it'll be overwritten again soon.
        '''
        self.size = size
        self.pos = pos

    def apply_selection(self, rv, index, is_selected):
        pass


class RecycleAdapter(EventDispatcher):
    """
    Adapter provides a binding between the data and the view objects that
    visualize them within a :class:`RecyclerView`.

    :Events:
        `on_data_changed`:
            Fired when the :attr:`data` changes.
    """

    data = ListProperty()
    '''See :attr:`RecyclerView.data`. The data for a item at index `i` can
    also be accessed with :class:`RecycleAdapter` `[i]`.
    '''
    viewclass = ObjectProperty()
    '''See :attr:`RecyclerView.viewclass`.
    '''
    key_viewclass = StringProperty()
    '''See :attr:`RecyclerView.key_viewclass`.
    '''

    # internals
    views = {}  # current displayed items
    # items whose attrs, except for pos/size is still accurate
    dirty_views = defaultdict(dict)
    recycleview = None

    __events__ = ("on_data_changed", )

    def __getitem__(self, index):
        """Return the data entry at `index`
        """
        return self.data[index]

    @property
    def observable_dict(self):
        '''See :meth:`RecyclerView.observable_dict`.
        '''
        return partial(ObservableDict, self.__class__.data, self)

    def attach_recycleview(self, rv):
        self.recycleview = rv

    def detach_recycleview(self):
        self.recycleview = None

    def create_view(self, index, viewclass=None):
        """Creates and initializes the view for the data at `index`. The
        returned view is synced with the data, except for the pos/size
        properties.
        """
        if viewclass is None:
            viewclass = self.get_viewclass(index)
        if viewclass is None:
            return
        item = self[index]
        # FIXME: we could pass the data though the constructor, but that wont
        # work for kv-declared classes, and might lead the user to think it can
        # work for reloading as well.
        view = viewclass(**item)
        if viewclass not in _view_base_cache:
            _view_base_cache[viewclass] = isinstance(view, RecycleViewMixin)

        if _view_base_cache[viewclass]:
            view.refresh_view_attrs(self.recycleview, item)
        else:
            for key, value in item.items():
                setattr(view, key, value)
        return view

    def get_view(self, index):
        """Returns a view instance for the data at `index`. It looks through
        the various caches and finally creates a view if it doesn't exist.
        The returned view is synced with the data, except for the pos/size
        properties.
        """
        if index in self.views:
            return self.views[index]

        dirty_views = self.dirty_views
        viewclass = self.get_viewclass(index)
        if viewclass is None:
            return
        rv = self.recycleview
        stale = False
        view = None

        if viewclass in dirty_views:
            dirty_class = dirty_views[viewclass]
            if index in dirty_class:
                # we found ourself in the dirty list, no need to update data!
                view = dirty_class.pop(index)
            elif _cached_views[viewclass]:
                # global cache has this class, update data
                view, stale = _cached_views[viewclass].pop(), True
            elif dirty_class:
                # random any dirty view element - update data
                view, stale = dirty_class.popitem()[1], True
        elif _cached_views[viewclass]:
            # global cache has this class, update data
            view, stale = _cached_views[viewclass].pop(), True

        if view is None:
            # create a fresh one
            view = self.create_view(index, viewclass)

        if stale is True:
            item = self[index]
            if viewclass not in _view_base_cache:
                _view_base_cache[viewclass] = isinstance(view,
                                                         RecycleViewMixin)

            if _view_base_cache[viewclass]:
                view.refresh_view_attrs(rv, item)
            else:
                for key, value in item.items():
                    setattr(view, key, value)

        self.views[index] = view
        return view

    def get_viewclass(self, index):
        """Get the class type used to create the view from the data at `index`.
        """
        viewclass = None
        if self.key_viewclass:
            viewclass = self[index].get(self.key_viewclass)
            viewclass = getattr(Factory, viewclass)
        if viewclass is None:
            viewclass = self.viewclass
        return viewclass

    def make_view_dirty(self, view, index):
        """(internal) Used to flag the view as dirty, ready to be used for
        others. A dirty view can be reused by the same index by just changing
        the pos/size. So it's assumed that while in dirty cache the view stays
        in sync with the data. Once the underlying data of this index changes,
        the view will be removed from the dirty views as well and moved to the
        global cahce.
        """
        self.dirty_views[view.__class__][index] = view

    def make_views_dirty(self):
        '''Makes all the views dirty. See :attr:`make_view_dirty`.
        '''
        views = self.views
        if not views:
            return

        dirty_views = self.dirty_views
        for index, view in views.items():
            dirty_views[view.__class__][index] = view
        self.views = {}

    def invalidate(self):
        """Moves all the current views into the global cache. As opposed to
        making a view dirty, this will completely disconnect the view from the
        data, as it is assumed the data has gone out of sync with the view.
        """
        views = self.views
        if not views:
            return
        global _cache_count
        for view in views.values():
            _cached_views[view.__class__].append(view)
            _cache_count += 1

        if _cache_count >= _max_cache_size:
            _clean_cache()
        self.views = {}

    def get_views(self, i_start, i_end):
        '''Gets a 2-tuple of the new and old views for the current viewport.
        The new views are synced to the data except for the size/pos
        properties.
        The old views need to be removed from the layout, and the new views
        added.
        '''
        current_views = self.views
        visible_views = {}
        new_views = []
        dirty_views = self.dirty_views
        get_view = self.get_view
        make_view_dirty = self.make_view_dirty

        # iterate though the visible view
        # add them into the container if not already done
        for index in range(i_start, i_end + 1):
            view = get_view(index)
            if not view:
                continue

            visible_views[index] = view
            current_views.pop(index, None)
            new_views.append((view, index))

        # put all the hidden view as dirty views
        for index, view in current_views.items():
            make_view_dirty(view, index)
        # save the current visible views
        self.views = visible_views
        return new_views, current_views.values()

    def get_visible_view(self, index):
        return self.views.get(index)

    def on_viewclass(self, instance, value):
        # resolve the real class if it was a string.
        if isinstance(value, string_types):
            self.viewclass = getattr(Factory, value)

    def on_data(self, instance, value):
        # data changed, if new list or list edited in unpredictable way, we'll
        # remove all the widgets. Otherwise if only append or extend, we don't
        # have to make everything dirty because the current items are good, we
        # just need to re-layout so pass on that info
        if not _kivy_1_9_1:
            self.dispatch('on_data_changed', extent='data')
            return

        last_op = value.last_op
        if last_op in ('__iadd__', '__imul__', 'append', 'extend'):
            extent = 'data_add'
        else:
            extent = 'data'
        self.dispatch('on_data_changed', extent=extent)

    def on_data_changed(self, extent):
        '''Dispatched when the :attr:`data` changes.

        :Parameters:

            `extent`: str
                The extent of the changes in the data. Could be one of
                `'data'`, `'data_size'`, or `'data_add'`.

                `data`: means the data has changed and the views are out of
                    sync.
                `data_size`: means that the data has changed, but only such
                    that we have to re-layout the data. The other non-pos/size
                    attributes of the data is still in sync with the view.
                `data_size`: means that new elements has been added to the
                    data list, but the previously existing data has not been
                    changed.
        '''
        if extent == 'data':
            self.invalidate()


class LayoutSelectionMixIn(CompoundSelectionBehavior):

    key_selection = StringProperty('')
    '''The key used to decide whether a view of a data item can be selected
    with touch or the keyboard. All data items can be selected directly
    using `select_node`.
    '''

    _selectable_nodes = []
    _nodes_map = {}

    def __init__(self, **kwargs):
        self.nodes_order_reversed = False
        super(LayoutSelectionMixIn, self).__init__(**kwargs)

    def compute_positions_and_sizes(self, append):
        # overwrite this method so that when data changes we update
        # selectable nodes.
        key = self.key_selection
        nodes = self._selectable_nodes = [
            i for i, d in enumerate(self.recycleview.data) if d.get(key)]
        self._nodes_map = {v: k for k, v in enumerate((nodes))}
        return super(
            LayoutSelectionMixIn, self).compute_positions_and_sizes(append)

    def get_selectable_nodes(self):
        # the indices of the data is used as the nodes
        return self._selectable_nodes

    def get_index_of_node(self, node, selectable_nodes):
        # the indices of the data is used as the nodes, so node
        return self._nodes_map[node]

    def goto_node(self, key, last_node, last_node_idx):
        node, idx = super(LayoutSelectionMixIn, self).goto_node(
            key, last_node, last_node_idx)
        if node is not last_node:
            self.show_index_view(node)
        return node, idx

    def select_node(self, node):
        if super(LayoutSelectionMixIn, self).select_node(node):
            view = self.recycleview.adapter.get_visible_view(node)
            if view is not None:
                self.apply_selection(node, view, True)

    def deselect_node(self, node):
        if super(LayoutSelectionMixIn, self).deselect_node(node):
            view = self.recycleview.adapter.get_visible_view(node)
            if view is not None:
                self.apply_selection(node, view, False)

    def apply_selection(self, index, view, is_selected):
        viewclass = view.__class__
        if viewclass not in _view_base_cache:
            _view_base_cache[viewclass] = isinstance(view, RecycleViewMixin)

        if _view_base_cache[viewclass]:
            view.apply_selection(self.recycleview, index, is_selected)

    def refresh_view_layout(self, index, view, viewport):
        super(LayoutSelectionMixIn, self).refresh_view_layout(index, view,
                                                              viewport)
        self.apply_selection(index, view, index in self.selected_nodes)


class RecycleLayoutManager(EventDispatcher):
    """A RecycleLayoutManager is responsible for positioning views into the
    :attr:`RecycleView.data` within a :class:`RecycleView`. It adds new views
    into the data when it becomes visible to the user, and removes them when
    they leave the visible area.
    """

    default_size = NumericProperty("48dp")
    key_size = StringProperty()
    recycleview = None
    container = None

    def attach_recycleview(self, rv):
        self.recycleview = rv
        c = rv.container
        if c is not None:
            self.container = c

    def detach_recycleview(self):
        self.recycleview = None
        self.clear_layout()
        self.container = None

    def compute_positions_and_sizes(self, append):
        """(internal) Calculates the size and future positions of all the
        views.
        """
        pass

    def recycleview_setup(self):
        pass

    def compute_visible_views(self):
        pass

    def refresh_view_layout(self, index, view):
        pass

    def get_view_position(self, index):
        """Get the position for the view at `index`
        """
        pass

    def get_view_size(self, index):
        """Get the height for the view at `index`
        """
        pass

    def get_view_index_at(self, pos):
        """Return the view `index` on which position, `pos`, falls.
        """
        pass

    def clear_layout(self):
        if self.container is not None:
            self.container.clear_widgets()

    def show_index_view(self, index):
        '''Moves the views so that the view corresponding to `index` is
        visible.
        '''
        pass


class LinearRecycleLayoutManager(RecycleLayoutManager):
    """Implementation of a `RecycleLayoutManager` for a horizontal or vertical
    arrangment
    """
    orientation = OptionProperty("vertical",
                                 options=["horizontal", "vertical"])

    # internal
    computed_sizes = []
    computed_positions = []

    def compute_positions_and_sizes(self, append):
        recycleview = self.recycleview
        height = 0
        key_size = self.key_size
        default_size = self.default_size
        data = recycleview.adapter.data
        if append:
            sizes = self.computed_sizes
            pos = self.computed_positions
            n = len(sizes)

            sizes.extend(
                [item.get(key_size, default_size) for item in data[n:]]
            )
            self.computed_size += sum(sizes[n:])
            pos.extend(
                self._compute_positions(sizes[n:], pos[-1] + sizes[n - 1]))
        else:
            self.computed_sizes = [
                item.get(key_size, default_size)
                for item in data
            ]
            self.computed_size = sum(self.computed_sizes)
            self.computed_positions = list(
                self._compute_positions(self.computed_sizes))

        if self.orientation == "horizontal":
            recycleview.container.size = self.computed_size, recycleview.height
        else:
            recycleview.container.size = recycleview.width, self.computed_size

    def _compute_positions(self, sizes, pos=0):
        for size in sizes:
            yield pos
            pos += size

    def recycleview_setup(self):
        """(internal) Prepare the scrollview and container to receive widgets
        from this layout manager. Means the size of the container, as well as
        the allowed axis of the scrollview need to be set
        """
        recycleview = self.recycleview
        if self.orientation == "horizontal":
            recycleview.do_scroll_x = True
            recycleview.do_scroll_y = False
        else:
            recycleview.do_scroll_x = False
            recycleview.do_scroll_y = True

    def compute_visible_views(self):
        """(internal) Determine the views that need to be showed in the current
        scrollview. All the hidden views will be flagged as dirty, and might
        be resued for others views.
        """
        # determine the view to create for the scrollview y / height
        recycleview = self.recycleview
        container = recycleview.container
        if self.orientation == "vertical":
            h = container.height
            scroll_y = min(1, max(recycleview.scroll_y, 0))
            px_end = 0, max(0, (h - recycleview.height) * scroll_y)
            px_start = 0, px_end[1] + min(recycleview.height, h)
            viewport = 0, px_end[1], container.width, px_start[1]
        else:
            w = container.width
            scroll_x = min(1, max(recycleview.scroll_x, 0))
            px_start = max(0, (w - recycleview.width) * scroll_x), 0
            px_end = px_start[0] + min(recycleview.width, w), 0
            viewport = px_end[0], 0, px_start[0], container.height

        # now calculate the view indices we must show
        at_idx = self.get_view_index_at
        s, e, = at_idx(px_start), at_idx(px_end)
        data = recycleview.data
        if s is None:
            s = len(data) - 1
        if e is None:
            e = len(data) - 1
        new, old = recycleview.get_views(s, e)

        rm = container.remove_widget
        for widget in old:
            rm(widget)

        refresh_view_layout = self.refresh_view_layout
        add = container.add_widget
        for widget, index in new:
            # add to the container if it's not already done
            refresh_view_layout(index, widget, viewport)
            if widget.parent is None:
                add(widget)

    def refresh_view_layout(self, index, view, viewport):
        """(internal) Refresh the layout of a view. Size and pos are determine
        by the `RecycleView` according to the view `index` informations
        """
        rv = self.recycleview
        container = rv.container
        view.size_hint = None, None
        if view.__class__ not in _view_base_cache:
            _view_base_cache[view.__class__] = isinstance(view,
                                                          RecycleViewMixin)

        if self.orientation == "vertical":
            w = container.width
            h = self.computed_sizes[index]
            y = self.computed_size - self.computed_positions[index] - h
            x = 0
        else:
            h = container.height
            w = self.computed_sizes[index]
            x = self.computed_size - self.computed_positions[index] - w
            y = 0

        if _view_base_cache[view.__class__]:
            view.refresh_view_layout(rv, index, (x, y), (w, h), viewport)
        else:
            view.size = w, h
            view.pos = x, y

    def get_view_position(self, index):
        return self.computed_positions[index]

    def get_view_size(self, index):
        return self.computed_sizes[index]

    def get_view_index_at(self, pos):
        if self.orientation == 'vertical':
            pos = self.recycleview.container.height - pos[1]
        else:
            pos = pos[0]
        for index, c_pos in enumerate(self.computed_positions):
            if c_pos > pos:
                return max(index - 1, 0)
        if pos >= self.computed_positions[-1] + self.computed_sizes[-1]:
            return None
        return index

    def show_index_view(self, index):
        rv = self.recycleview
        if self.orientation == "vertical":
            h = rv.container.height
            if h <= rv.height:  # all views are visible
                return

            # convert everything to container coordinates
            top = h - self.computed_positions[index]
            bottom = top - self.computed_sizes[index]
            view_h = h - rv.height
            view_bot = view_h * min(1, max(rv.scroll_y, 0))
            view_top = view_bot + rv.height

            if top <= view_top:
                if bottom >= view_bot:  # it's fully in view
                    return
                rv.scroll_y = bottom / float(view_h)
            else:
                rv.scroll_y = (top - rv.height) / float(view_h)
        else:
            w = rv.container.width
            if w <= rv.width:  # all views are visible
                return

            # convert everything to container coordinates
            left = self.computed_positions[index]
            right = left + self.computed_sizes[index]
            view_w = w - rv.width
            view_left = view_w * min(1, max(rv.scroll_x, 0))
            view_right = view_left + rv.width

            if left >= view_left:
                if right <= view_right:  # it's fully in view
                    return
                rv.scroll_x = (right - rv.width) / float(view_w)
            else:
                rv.scroll_x = left / float(view_w)


class RecycleView(ScrollView):
    """RecycleView is a flexible view for providing a limited window into
    a large data set.

    See module documentation for more informations.
    """

    # internals
    _adapter = None
    _layout_manager = None
    _container = None
    _refresh_trigger = None
    _refresh_flags = {
        'all': True, 'data': True, 'data_size': True,
        'data_add': True, 'viewport': True
    }
    '''These flags indicate how much the view is out of sync and needs to
    be synchronized with the data. The goal is that the minimum amount
    of synchronization should be done. The flags are ordered such that for
    each flag, all the ops required for the proceeding flags are reduced by
    some known info about the change causing the refresh.

    Meaning of the flags:
    -all: Initial setup of the recycleview itself. E.g. do_scroll_x.
        Updates everything.
    -data: Signal that the data changed and all the attributes/size/pos
        may have changed so they need to be recomputed and all attrs
        re-applied. This
    -data_size: Signal that the pos/size attrs of the data may have changed,
        new data may have been added, and or old data was removed. However,
        no existing data attrs was changed, beyond the size/pos values. This
        means that we don't need to re-apply the data attrs, other than
        size/pos for existing data insatances because they did not change.
        Added data will get new class instances and will have their values
        applied.
    -data_add: Similar to `data_size`, except that data, if added, was added
        at the end. This will allow further possible optimizations, but may
        be implemented as `data_size`.
    -viewport: The items visible changed, so we have to move our viewport.
        Other than viewport, nothing is recalculated.
    '''

    def __init__(self, **kwargs):
        self._refresh_flags = dict(self._refresh_flags)
        self._refresh_trigger = Clock.create_trigger(self.refresh_views, -1)

        if self._layout_manager is None:
            self.layout_manager = LinearRecycleLayoutManager()
        if self._adapter is None:
            self.adapter = RecycleAdapter()
        super(RecycleView, self).__init__(**kwargs)
        if self._container is None:
            self.container = RecycleViewLayout(size_hint=(None, None))

        fbind = self.fbind if _kivy_1_9_1 else self.fast_bind
        fbind('size', self.ask_refresh_from_data, extent='data_size')
        fbind('scroll_x', self.ask_refresh_viewport)
        fbind('scroll_y', self.ask_refresh_viewport)
        self._refresh_trigger()

    def refresh_views(self, *largs, **kwargs):
        flags = self._refresh_flags
        flags.update(kwargs)
        lm = self.layout_manager

        try:
            append = False
            update = flags['all']
            if update:
                flags['all'] = False
                lm.recycleview_setup()
            else:
                update = flags['data']

            if update:
                flags['data'] = False
                self.layout_manager.clear_layout()
            else:
                append = flags['data_add'] and not flags['data_size']
                update = flags['data_size'] or flags['data_add']

            if update:
                flags['data_size'] = flags['data_add'] = False
                lm.compute_positions_and_sizes(append)

            if update or flags['viewport']:
                flags['viewport'] = False
                if self.data:
                    lm.compute_visible_views()
        except LayoutChangeException:
            # at a minimum we will have to recompute the size
            flags['data_size'] = True
            self.refresh_views()

    def ask_refresh_all(self, *largs):
        self._refresh_flags['all'] = True
        self._refresh_trigger()

    def ask_refresh_from_data(self, *largs, **kwargs):
        '''Accepts extent as a flag kwarg.
        '''
        extent = kwargs.get('extent', 'data')
        if extent not in ('data', 'data_size', 'data_add'):
            raise ValueError('{} is not a valid extent'.format(extent))
        self.adapter.dispatch('on_data_changed', extent=extent)

    def ask_refresh_viewport(self, *largs):
        self._refresh_flags['viewport'] = True
        self._refresh_trigger()

    def get_views(self, i_start, i_end):
        return self.adapter.get_views(i_start, i_end)

    @property
    def observable_dict(self):
        '''It's specific to the adapter present when called.
        '''
        return self.adapter.observable_dict

    def _dispatch_prop_on_source(self, prop_name, *largs):
        '''Dispatches the prop of this class when the adapter/layout_manager
        property changes.
        '''
        getattr(self.__class__, prop_name).dispatch(self)


    def _handle_ask_data_refresh(self, *largs, **kwargs):
        self._refresh_flags[kwargs['extent']] = True
        self._refresh_trigger()

    def _get_adapter(self):
        return self._adapter

    def _set_adapter(self, value):
        adapter = self._adapter
        if value is adapter:
            return
        if adapter is not None:
            adapter.detach_recycleview()
            funbind = adapter.funbind if _kivy_1_9_1 else adapter.fast_unbind
            funbind('on_data_changed', self._handle_ask_data_refresh)
            funbind('viewclass', self._dispatch_prop_on_source, 'viewclass')
            funbind('key_viewclass', self._dispatch_prop_on_source,
                    'key_viewclass')
            funbind('data', self._dispatch_prop_on_source, 'data')

        if value is None:
            self._adapter = adapter = RecycleAdapter()
        else:
            if not isinstance(value, RecycleAdapter):
                raise ValueError(
                    'Expected object based on RecycleAdapter, got {}'.
                    format(value.__class__))
            self._adapter = adapter = value

        adapter.attach_recycleview(self)
        fbind = adapter.fbind if _kivy_1_9_1 else adapter.fast_bind
        fbind('on_data_changed', self._handle_ask_data_refresh)
        fbind('viewclass', self._dispatch_prop_on_source, 'viewclass')
        fbind('key_viewclass', self._dispatch_prop_on_source, 'key_viewclass')
        fbind('data', self._dispatch_prop_on_source, 'data')
        self.ask_refresh_from_data()
        return True

    adapter = AliasProperty(_get_adapter, _set_adapter)
    """Adapter responsible for providing views that represent items in a data
    set."""

    def _get_layout_manager(self):
        return self._layout_manager

    def _set_layout_manager(self, value):
        lm = self._layout_manager
        if value is lm:
            return
        if lm is not None:
            lm.detach_recycleview()
            funbind = lm.funbind if _kivy_1_9_1 else lm.fast_unbind
            funbind('default_size', self._dispatch_prop_on_source,
                    'default_size')
            funbind('key_size', self._dispatch_prop_on_source, 'key_size')

        if value is None:
            self._layout_manager = lm = LinearRecycleLayoutManager()
        else:
            if not isinstance(value, RecycleLayoutManager):
                raise ValueError(
                    'Expected object based on RecycleLayoutManager, got {}'.
                    format(value.__class__))
            self._layout_manager = lm = value

        lm.attach_recycleview(self)
        fbind = lm.fbind if _kivy_1_9_1 else lm.fast_bind
        fbind('default_size', self._dispatch_prop_on_source, 'default_size')
        fbind('key_size', self._dispatch_prop_on_source, 'key_size')
        if self.adapter is not None:
            self.ask_refresh_from_data()
        return True

    layout_manager = AliasProperty(
        _get_layout_manager, _set_layout_manager)
    """Layout manager responsible to position views within the recycleview
    """

    def _get_container(self):
        return self._container

    def _set_container(self, value):
        container = self._container
        if value is container:
            return

        if container is not None:
            self.remove_widget(container)
        if value is None:
            c = self._container = RecycleViewLayout(size_hint=(None, None))
        else:
            c = self._container = value
        self.add_widget(c)
        self.ask_refresh_from_data(extent='data_size')
        return True

    container = AliasProperty(_get_container, _set_container)
    """Container.
    """

    # or easier way to use
    def _get_data(self):
        return self.adapter.data
    def _set_data(self, value):
        self.adapter.data = value
    data = AliasProperty(_get_data, _set_data, bind=["adapter"])
    """Set the data on the current adapter
    """

    def _get_viewclass(self):
        return self.adapter.viewclass
    def _set_viewclass(self, value):
        self.adapter.viewclass = value
    viewclass = AliasProperty(_get_viewclass, _set_viewclass,
        bind=["adapter"])
    """Set the viewclass on the current adapter
    """

    def _get_key_viewclass(self):
        return self.adapter.key_viewclass
    def _set_key_viewclass(self, value):
        self.adapter.key_viewclass = value
    key_viewclass = AliasProperty(_get_key_viewclass, _set_key_viewclass,
        bind=["adapter"])
    """Set the key viewclass on the current adapter
    """

    def _get_default_size(self):
        return self.layout_manager.default_size
    def _set_default_size(self, value):
        self.layout_manager.default_size = value
    default_size = AliasProperty(_get_default_size, _set_default_size,
                                 bind=["layout_manager"])
    """Set the default size on the current `layout_manager`
    """

    def _get_key_size(self):
        return self.layout_manager.key_size
    def _set_key_size(self, value):
        self.layout_manager.key_size = value
    key_size = AliasProperty(_get_key_size, _set_key_size,
                             bind=["layout_manager"])
    """Set the key to look for the size on the current `layout_manager`
    """
