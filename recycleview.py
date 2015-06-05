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
"""

from kivy.compat import string_types
from kivy.uix.relativelayout import RelativeLayout
from kivy.lang import Builder
from kivy.properties import NumericProperty, AliasProperty, StringProperty, \
    ObjectProperty, ListProperty, OptionProperty, BooleanProperty
from kivy.event import EventDispatcher
from kivy.factory import Factory
from kivy.clock import Clock

Builder.load_string("""
<RecycleView>:
    ScrollView:
        id: sv
        on_scroll_y: root.refresh_from_scroll("y")
        on_scroll_x: root.refresh_from_scroll("x")
        on_size: root.request_layout(full=True)
        RecycleViewLayout:
            id: layout
            size_hint: None, None
""")


class RecycleViewLayout(RelativeLayout):
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
    dirty_views = {}
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
        refresh_view_layout = self.recycleview.refresh_view_layout
        if viewclass in dirty_views:

            # we found ourself in the dirty list, no need to update data!
            if index in dirty_views[viewclass]:
                view = dirty_views[viewclass].pop(index)
                refresh_view_layout(index, view)
                self.views[index] = view
                return view

            # we are not in the dirty list, just take one and reuse it.
            if dirty_views[viewclass]:
                previous_index = tuple(dirty_views[viewclass].keys())[-1]
                view = dirty_views[viewclass].pop(previous_index)
                # update view data
                item = self[index]
                for key, value in item.items():
                    setattr(view, key, value)
                refresh_view_layout(index, view)
                self.views[index] = view
                return view

        # create a fresh one
        self.views[index] = view = self.create_view(index)
        refresh_view_layout(index, view)
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
        others.
        """
        viewclass = view.__class__
        if viewclass not in self.dirty_views:
            self.dirty_views[viewclass] = {index: view}
        else:
            self.dirty_views[viewclass][index] = view

    def invalidate(self):
        """Invalidate any state of the current adapter, to be ready for a fresh
        start.
        """
        for index, view in self.views.items():
            self.make_view_dirty(view, index)
        self.views = {}

    def on_viewclass(self, instance, value):
        # resolve the real class if it was a string.
        if isinstance(value, string_types):
            self.viewclass = getattr(Factory, value)

    def on_data(self, instance, value):
        # data changed, right now, remove all the widgets.
        self.dirty_views = {}
        self.views = {}
        self.dispatch("on_data_changed")

    def on_data_changed(self):
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

    def can_scroll_horizontally(self):
        return False

    def can_scroll_vertically(self):
        return True

    def compute_container_size(self, container, scrollview):
        """(internal) Calculate the size of the container for the scrollview
        """
        pass

    def compute_positions_and_sizes(self, container):
        """(internal) Calculate all the views height according to
        default_size, key_size, and then calculate their future positions
        """
        pass

    def compute_visible_views(self, container, scrollview):
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

    def can_scroll_horizontally(self):
        return self.orientation == "horizontal"

    def can_scroll_vertically(self):
        return self.orientation == "vertical"

    def compute_positions_and_sizes(self, container):
        height = 0
        key_size = self.key_size
        default_size = self.default_size
        data = self.recycleview.current_adapter.data
        self.computed_sizes = [
            item.get(key_size, default_size)
            for item in data
        ]
        self.computed_size = sum(self.computed_sizes)
        self.computed_positions = list(
            self._compute_positions(self.computed_sizes))

    def _compute_positions(self, sizes):
        pos = 0
        for size in sizes:
            yield pos
            pos += size

    def setup(self, container, scrollview):
        """(internal) Prepare the scrollview and container to receive widgets
        from this layout manager. Means the size of the container, as well as
        the allowed axis of the scrollview need to be set
        """
        if self.orientation == "horizontal":
            scrollview.do_scroll_x = True
            scrollview.do_scroll_y = False
            container.size = self.computed_size, scrollview.height
        else:
            scrollview.do_scroll_x = False
            scrollview.do_scroll_y = True
            container.size = scrollview.width, self.computed_size

    def compute_visible_views(self, container, scrollview):
        """(internal) Determine the views that need to be showed in the current
        scrollview. All the hidden views will be flagged as dirty, and might
        be resued for others views.
        """
        # determine the view to create for the scrollview y / height
        if self.orientation == "vertical":
            scroll_y = 1 - (min(1, max(scrollview.scroll_y, 0)))
            px_start = (container.height - scrollview.height) * scroll_y
            px_end = px_start + scrollview.height
        else:
            scroll_x = 1 - (min(1, max(scrollview.scroll_x, 0)))
            px_start = (container.width - scrollview.width) * scroll_x
            px_end = px_start + scrollview.width

        # now calculate the view indices we must show
        i_start = self.get_view_index_at(px_start)
        i_end = self.get_view_index_at(px_end)

        adapter = self.recycleview.current_adapter
        current_views = adapter.views
        visible_views = {}
        dirty_views = adapter.dirty_views

        # iterate though the visible view
        # add them into the container if not already done
        for index in range(i_start, i_end + 1):
            view = adapter.get_view(index)
            if not view:
                continue

            visible_views[index] = view
            current_views.pop(index, None)

            # add to the container if it's not already done
            if view.parent:
                continue
            container.add_widget(view)

        # put all the hidden view as dirty views
        for index, view in current_views.items():
            container.remove_widget(view)
            adapter.make_view_dirty(view, index)

        # save the current visible views
        adapter.views = visible_views

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



class RecycleView(RelativeLayout):
    """RecycleView is a flexible view for providing a limited window into
    a large data set.

    See module documentation for more informations.
    """

    adapter = ObjectProperty(None, baseclass=RecycleAdapter)
    """Adapter responsible for providing views that represent items in a data
    set."""

    layout_manager = ObjectProperty(None, baseclass=RecycleLayoutManager)
    """Layout manager responsible to position views within the recycleview
    """


    # internals
    _previous_adapter = None
    _previous_layout_manager = None
    can_scroll_x = BooleanProperty(False)
    can_scroll_y = BooleanProperty(True)
    layout_size = ListProperty([1, 1])
    need_setup = True

    def __init__(self, **kwargs):
        self.default_adapter = RecycleAdapter()
        self.default_adapter.attach_recycleview(self)
        self.default_adapter.bind(
            on_data_changed=self.on_adapter_data_changed,
            on_view_refresh_layout=self.on_adapter_view_refresh_layout)
        self.default_layout_manager = LinearRecycleLayoutManager()
        self.default_layout_manager.attach_recycleview(self)
        self.can_scroll_x = self.default_layout_manager.can_scroll_horizontally()
        self.can_scroll_y = self.default_layout_manager.can_scroll_vertically()
        super(RecycleView, self).__init__(**kwargs)

    def do_layout(self, *args):
        super(RecycleView, self).do_layout(*args)
        if self.data:
            self.refresh_from_data(True)

    def refresh_from_data(self, force=False):
        """The data has changed, update the RecycleView internals
        """
        if force:
            self.current_adapter.invalidate()
            self.current_layout_manager.compute_positions_and_sizes(self.container)
        if self.need_setup:
            self.current_layout_manager.setup(self.container, self.ids.sv)
            self.need_setup = False
        self.current_layout_manager.compute_visible_views(self.container, self.ids.sv)

    def refresh_from_scroll(self, axis):
        self.current_layout_manager.compute_visible_views(self.container, self.ids.sv)

    def refresh_view_layout(self, index, view):
        self.current_layout_manager.refresh_view_layout(index, view)

    def refresh_setup(self):
        self.need_setup = True
        self._trigger_layout()

    @property
    def container(self):
        return self.ids.layout

    @property
    def current_layout_manager(self):
        return self.layout_manager or self.default_layout_manager

    def on_layout_manager(self, instance, value):
        if self._previous_layout_manager is not None:
            self._previous_layout_manager.detach_recycleview()
        lm = self.current_layout_manager
        lm.attach_recycleview(self)
        self._previous_layout_manager = lm
        self.can_scroll_x = lm.can_scroll_horizontally()
        self.can_scroll_y = lm.can_scroll_vertically()
        self.request_layout()

    @property
    def current_adapter(self):
        return self.adapter or self.default_adapter

    def on_adapter(self, instance, value):
        if self._previous_adapter is not None:
            self._previous_adapter.detach_recycleview()
        self.current_adapter.attach_recycleview(self)
        self._previous_adapter = self.current_adapter

    def on_adapter_data_changed(self, instance):
        if self.current_adapter != instance:
            return
        self.ids.layout.clear_widgets()
        self.request_layout(full=True)

    def on_adapter_view_refresh_layout(self, instance, index, view):
        self.current_layout_manager.refresh_view_layout(index, view)

    def request_layout(self, full=False):
        """Invalidate the layout manager state and recalculate the views sizes
        and positions.
        """
        if full:
            self.need_setup = True
        self._trigger_layout()

    # or easier way to use
    def _get_data(self):
        return self.current_adapter.data
    def _set_data(self, value):
        self.current_adapter.data = value
    data = AliasProperty(_get_data, _set_data, bind=["adapter"])
    """Set the data on the current adapter
    """

    def _get_viewclass(self):
        return self.current_adapter.viewclass
    def _set_viewclass(self, value):
        self.current_adapter.viewclass = value
    viewclass = AliasProperty(_get_viewclass, _set_viewclass,
        bind=["adapter"])
    """Set the viewclass on the current adapter
    """

    def _get_key_viewclass(self):
        return self.current_adapter.key_viewclass
    def _set_key_viewclass(self, value):
        self.current_adapter.key_viewclass = value
    key_viewclass = AliasProperty(_get_key_viewclass, _set_key_viewclass,
        bind=["adapter"])
    """Set the key viewclass on the current adapter
    """

    def _get_default_size(self):
        return self.current_layout_manager.default_size
    def _set_default_size(self, value):
        self.current_layout_manager.default_size = value
    default_size = AliasProperty(_get_default_size, _set_default_size,
                                 bind=["layout_manager"])
    """Set the default size on the current `layout_manager`
    """

    def _get_key_size(self):
        return self.current_layout_manager.key_size
    def _set_key_size(self, value):
        self.current_layout_manager.key_size = value
    key_size = AliasProperty(_get_key_size, _set_key_size,
                             bind=["layout_manager"])
    """Set the key to look for the size on the current `layout_manager`
    """
