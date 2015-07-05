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
    ObjectProperty, ListProperty, OptionProperty, BooleanProperty
from kivy.event import EventDispatcher
from kivy.factory import Factory
from kivy.clock import Clock
from collections import defaultdict
from functools import partial
from distutils.version import LooseVersion

_kivy_has_last_op = LooseVersion(kivy.__version__) >= LooseVersion('1.9.1')

_cached_views = defaultdict(list)


class RecycleViewLayout(Widget):
    '''We don't want the RecycleViewLayout children's size/pos changes to cause
    a re-layout because they should only be changed internally.
    '''
    pass


class RecycleAdapter(EventDispatcher):
    """
    Adapter provide a binding from data set to views that are displayed
    within a RecyclerView
    """

    data = ListProperty()
    viewclass = ObjectProperty()
    key_viewclass = StringProperty()

    # internals
    views = {}
    dirty_views = defaultdict(dict)
    recycleview = None

    __events__ = ("on_data_changed", )

    def __getitem__(self, index):
        """Return the data entry at `index`
        """
        return self.data[index]

    def attach_recycleview(self, rv):
        self.recycleview = rv

    def detach_recycleview(self):
        self.recycleview = None

    def create_view(self, index):
        """Create the view for the `index`
        """
        viewclass = self.get_viewclass(index)
        item = self[index]
        # FIXME: we could pass the data though the constructor, but that wont
        # work for kv-declared classes, and might lead the user to think it can
        # work for reloading as well.
        view = viewclass(**item)
        for key, value in item.items():
            setattr(view, key, value)
        return view

    def get_view(self, index):
        """Return a view instance for the `index`
        """
        if index in self.views:
            return self.views[index]

        dirty_views = self.dirty_views
        viewclass = self.get_viewclass(index)
        stale = False

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
        else:
            # create a fresh one
            view = self.create_view(index)

        if stale is True:
            item = self[index]
            for key, value in item.items():
                setattr(view, key, value)

        self.views[index] = view
        self.recycleview.refresh_view_layout(index, view)
        return view

    def get_viewclass(self, index):
        """Get the class needed to create the view `index`
        """
        viewclass = None
        if self.key_viewclass:
            viewclass = self[index].get(self.key_viewclass)
            viewclass = getattr(Factory, viewclass)
        if not viewclass:
            viewclass = self.viewclass
        return viewclass

    def make_view_dirty(self, view, index):
        """(internal) Used to flag the view as dirty, ready to be used for
        others. A dirty view can be reused by the same index by just changing
        the pos/size. So it's assumed that while in dirty view that index stays
        in sync with the data. Once the underlying data of this index changes,
        the view will be removed from the dirty views as well.
        """
        self.dirty_views[view.__class__][index] = view

    def invalidate(self):
        """Invalidate any state of the current adapter, to be ready for a fresh
        start.
        """
        views = self.views
        if not views:
            return
        for view in views.values():
            _cached_views[view.__class__].append(view)
        self.views = {}

    def get_views(self, i_start, i_end):
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

    def on_viewclass(self, instance, value):
        # resolve the real class if it was a string.
        if isinstance(value, string_types):
            self.viewclass = getattr(Factory, value)

    def on_data(self, instance, value):
        # data changed, if new list or list edited in unpredictable way, we'll
        # remove all the widgets. Otherwise if only append or extend, we don't
        # have to make everything dirty because the current items are good, we
        # just need to re-layout so pass on that info
        if not _kivy_has_last_op:
            self.dispatch('on_data_changed', extent='data')
            return

        last_op = value.last_op
        extent = 'data'
        if last_op in ('__delitem__', '__delslice__', 'remove', 'pop'):
            extent = 'data_size'
        elif last_op in ('__iadd__', '__imul__', 'append', 'extend'):
            extent = 'data_add'
        self.dispatch('on_data_changed', extent=extent)

    def on_data_changed(self, extent):
        pass


class RecycleLayoutManager(EventDispatcher):
    """A RecycleLayoutManager is responsible for measuring and positionning
    views within a RecycleView as determining the policy for when to recycle
    item views that are no longer visible to the user.
    """

    default_size = NumericProperty("48dp")
    key_size = StringProperty()
    recycleview = None
    container = None

    def attach_recycleview(self, rv):
        self.recycleview = rv

    def detach_recycleview(self):
        self.recycleview = None
        if self.container:
            self.container.clear_widgets()
        self.container = None

    def compute_positions_and_sizes(self, append):
        """(internal) Calculate all the views height according to
        default_size, key_size, and then calculate their future positions
        """
        pass

    def recycleview_setup(self):
        pass

    def compute_visible_views(self, container):
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
        """Return the view `index` for the `pos` position
        """
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

    def _compute_positions(self, sizes):
        pos = 0
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
            scroll_y = 1 - (min(1, max(recycleview.scroll_y, 0)))
            px_start = (container.height - recycleview.height) * scroll_y
            px_end = px_start + recycleview.height
        else:
            scroll_x = 1 - (min(1, max(recycleview.scroll_x, 0)))
            px_start = (container.width - recycleview.width) * scroll_x
            px_end = px_start + recycleview.width

        # now calculate the view indices we must show
        at_idx = self.get_view_index_at
        new, old = recycleview.get_views(at_idx(px_start), at_idx(px_end))

        rm = container.remove_widget
        for widget in old:
            rm(widget)

        refresh_view_layout = self.refresh_view_layout
        add = container.add_widget
        for widget, index in new:
            # add to the container if it's not already done
            if widget.parent is not None:
                refresh_view_layout(index, widget)
            else:
                add(widget)

    def refresh_view_layout(self, index, view):
        """(internal) Refresh the layout of a view. Size and pos are determine
        by the `RecycleView` according to the view `index` informations
        """
        container = self.recycleview.container
        view.size_hint = None, None
        if self.orientation == "vertical":
            view.width = container.width
            view.height = h = self.computed_sizes[index]
            view.y = self.computed_size - self.computed_positions[index] - h
        else:
            view.height = container.height
            view.width = w = self.computed_sizes[index]
            view.x = self.computed_size - self.computed_positions[index] - w

    def get_view_position(self, index):
        return self.computed_positions[index]

    def get_view_size(self, index):
        return self.computed_sizes[index]

    def get_view_index_at(self, pos):
        for index, c_pos in enumerate(self.computed_positions):
            if c_pos > pos:
                return index - 1
        return index


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

        fbind = self.fbind
        fbind('size', self.ask_refresh_from_data, extent=data_size)
        fbind('scroll_x', self.ask_refresh_viewport)
        fbind('scroll_y', self.ask_refresh_viewport)
        self._refresh_trigger()

    def refresh_views(self, *largs, **kwargs):
        flags = self._refresh_flags
        flags.update(kwargs)
        lm = self.layout_manager

        update = flags['all']
        if update:
            lm.recycleview_setup()
        else:
            update = flags['data']

        if update:
            self.container.clear_widgets()
            self.adapter.invalidate()
        else:
            update = flags['data_size'] or flags['data_add']

        if update:
            lm.compute_positions_and_sizes(flags['data_add'])

        if update or flags['viewport']:
            if self.data:
                lm.compute_visible_views()
            else:
                self.adapter.invalidate()

        flags['all'] = flags['data'] = flags['data_size'] = \
            flags['data_add'] = flags['viewport'] = False

    def ask_refresh_all(self, *largs):
        self._refresh_flags['all'] = True
        self._refresh_trigger()

    def ask_refresh_from_data(self, *largs, **kwargs):
        '''Accepts extent as a flag kwarg.
        '''
        flags = self._refresh_flags
        extent = kwargs.get('extent', 'data')
        if extent not in flags:
            raise ValueError('{} is not a valid value'.format(extent))

        flags[extent] = True
        self._refresh_trigger()

    def refresh_view_layout(self, index, view):
        self.layout_manager.refresh_view_layout(index, view)

    def get_views(self, i_start, i_end):
        return self.adapter.get_views(i_start, i_end)

    def _get_adapter(self):
        return self._adapter

    def _set_adapter(self, value):
        adapter = self._adapter
        if value is adapter:
            return
        if adapter is not None:
            adapter.detach_recycleview()
            adapter.funbind('on_data_changed', self.ask_refresh_from_data)

        if value is None:
            self._adapter = adapter = RecycleAdapter()
        else:
            if not isinstance(value, RecycleAdapter):
                raise ValueError(
                    'Expected object based on RecycleAdapter, got {}'.
                    format(value.__class__))
            self._adapter = adapter = value

        adapter.attach_recycleview(self)
        adapter.fbind('on_data_changed', self.ask_refresh_from_data)
        self.ask_refresh_from_data()
        return True

    adapter = AliasProperty(_get_adapter, _set_adapter, cache=False)
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

        if value is None:
            self._layout_manager = lm = LinearRecycleLayoutManager()
        else:
            if not isinstance(value, RecycleLayoutManager):
                raise ValueError(
                    'Expected object based on RecycleLayoutManager, got {}'.
                    format(value.__class__))
            self._layout_manager = lm = value

        lm.attach_recycleview(self)
        self.ask_refresh_from_data()
        return True

    layout_manager = AliasProperty(
        _get_layout_manager, _set_layout_manager, cache=False)
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

    container = AliasProperty(_get_container, _set_container, cache=False)
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
