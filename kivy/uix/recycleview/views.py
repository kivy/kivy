'''
RecycleView Views
=================

.. versionadded:: 1.10.0

The adapter part of the RecycleView which together with the layout is the
view part of the model-view-controller pattern.

The view module handles converting the data to a view using the adapter class
which is then displayed by the layout. A view can be any Widget based class.
However, inheriting from RecycleDataViewBehavior adds methods for converting
the data to a view.

TODO:
    * Make view caches specific to each view class type.

'''

from kivy.properties import StringProperty, ObjectProperty
from kivy.event import EventDispatcher
from kivy.factory import Factory
from collections import defaultdict

_view_base_cache = {}
'''Cache whose keys are classes and values is a boolean indicating whether the
class inherits from :class:`RecycleDataViewBehavior`.
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


class RecycleDataViewBehavior(object):
    '''A optional base class for data views (:attr:`RecycleView`.viewclass).
    If a view inherits from this class, the class's functions will be called
    when the view needs to be updated due to a data change or layout update.
    '''

    def refresh_view_attrs(self, rv, index, data):
        '''Called by the :class:`RecycleAdapter` when the view is initially
        populated with the values from the `data` dictionary for this item.

        Any pos or size info should be removed because they are set
        subsequently with :attr:`refresh_view_layout`.

        :Parameters:

            `rv`: :class:`RecycleView` instance
                The :class:`RecycleView` that caused the update.
            `data`: dict
                The data dict used to populate this view.
        '''
        sizing_attrs = RecycleDataAdapter._sizing_attrs
        for key, value in data.items():
            if key not in sizing_attrs:
                setattr(self, key, value)

    def refresh_view_layout(self, rv, index, layout, viewport):
        '''Called when the view's size is updated by the layout manager,
        :class:`RecycleLayoutManagerBehavior`.

        :Parameters:

            `rv`: :class:`RecycleView` instance
                The :class:`RecycleView` that caused the update.
            `viewport`: 4-tuple
                The coordinates of the bottom left and width height in layout
                manager coordinates. This may be larger than this view item.

        :raises:
            `LayoutChangeException`: If the sizing or data changed during a
            call to this method, raising a `LayoutChangeException` exception
            will force a refresh. Useful when data changed and we don't want
            to layout further since it'll be overwritten again soon.
        '''
        w, h = layout.pop('size')
        if w is None:
            if h is not None:
                self.height = h
        else:
            if h is None:
                self.width = w
            else:
                self.size = w, h

        for name, value in layout.items():
            setattr(self, name, value)

    def apply_selection(self, rv, index, is_selected):
        pass


class RecycleDataAdapter(EventDispatcher):
    '''The class that converts data to a view.

    --- Internal details ---
    A view can have 3 states.

        * It can be completely in sync with the data, which
          occurs when the view is displayed. These are stored in :attr:`views`.
        * It can be dirty, which occurs when the view is in sync with the data,
          except for the size/pos parameters which is controlled by the layout.
          This occurs when the view is not currently displayed but the data has
          not changed. These views are stored in :attr:`dirty_views`.
        * Finally the view can be dead which occurs when the data changes and
          the view was not updated or when a view is just created. Such views
          are typically added to the internal cache.

    Typically what happens is that the layout manager lays out the data
    and then asks for views, using :meth:`set_visible_views,` for some specific
    data items that it displays.

    These views are gotten from the current views, dirty or global cache. Then
    depending on the view state :meth:`refresh_view_attrs` is called to bring
    the view up to date with the data (except for sizing parameters). Finally,
    the layout manager gets these views, updates their size and displays them.
    '''

    recycleview = ObjectProperty(None, allownone=True)
    '''The :class:`~kivy.uix.recycleview.RecycleViewBehavior` associated
    with this instance.
    '''

    # internals
    views = {}  # current displayed items
    # items whose attrs, except for pos/size is still accurate
    dirty_views = defaultdict(dict)

    _sizing_attrs = {
        'size', 'width', 'height', 'size_hint', 'size_hint_x', 'size_hint_y',
        'pos', 'x', 'y', 'center', 'center_x', 'center_y', 'pos_hint',
        'size_hint_min', 'size_hint_min_x', 'size_hint_min_y', 'size_hint_max',
        'size_hint_max_x', 'size_hint_max_y'}

    def __init__(self, **kwargs):
        """
        Fix for issue https://github.com/kivy/kivy/issues/5913:
        Scrolling RV A, then Scrolling RV B, content of A and B seemed
        to be getting mixed up
        """
        self.views = {}
        self.dirty_views = defaultdict(dict)
        super(RecycleDataAdapter, self).__init__(**kwargs)

    def attach_recycleview(self, rv):
        '''Associates a :class:`~kivy.uix.recycleview.RecycleViewBehavior`
        with this instance. It is stored in :attr:`recycleview`.
        '''
        self.recycleview = rv

    def detach_recycleview(self):
        '''Removes the :class:`~kivy.uix.recycleview.RecycleViewBehavior`
        associated with this instance and clears :attr:`recycleview`.
        '''
        self.recycleview = None

    def create_view(self, index, data_item, viewclass):
        '''(internal) Creates and initializes the view for the data at `index`.

        The returned view is synced with the data, except for the pos/size
        information.
        '''
        if viewclass is None:
            return

        view = viewclass()
        self.refresh_view_attrs(index, data_item, view)
        return view

    def get_view(self, index, data_item, viewclass):
        '''(internal) Returns a view instance for the data at `index`

        It looks through the various caches and finally creates a view if it
        doesn't exist. The returned view is synced with the data, except for
        the pos/size information.

        If found in the cache it's removed from the source
        before returning. It doesn't check the current views.
        '''
        # is it in the dirtied views?
        dirty_views = self.dirty_views
        if viewclass is None:
            return
        stale = False
        view = None

        if viewclass in dirty_views:  # get it first from dirty list
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
        elif _cached_views[viewclass]:  # otherwise go directly to cache
            # global cache has this class, update data
            view, stale = _cached_views[viewclass].pop(), True

        if view is None:
            view = self.create_view(index, data_item, viewclass)
            if view is None:
                return

        if stale:
            self.refresh_view_attrs(index, data_item, view)
        return view

    def refresh_view_attrs(self, index, data_item, view):
        '''(internal) Syncs the view and brings it up to date with the data.

        This method calls :meth:`RecycleDataViewBehavior.refresh_view_attrs`
        if the view inherits from :class:`RecycleDataViewBehavior`. See that
        method for more details.

        .. note::
            Any sizing and position info is skipped when syncing with the data.
        '''
        viewclass = view.__class__
        if viewclass not in _view_base_cache:
            _view_base_cache[viewclass] = isinstance(view,
                                                     RecycleDataViewBehavior)

        if _view_base_cache[viewclass]:
            view.refresh_view_attrs(self.recycleview, index, data_item)
        else:
            sizing_attrs = RecycleDataAdapter._sizing_attrs
            for key, value in data_item.items():
                if key not in sizing_attrs:
                    setattr(view, key, value)

    def refresh_view_layout(self, index, layout, view, viewport):
        '''Updates the sizing information of the view.

        viewport is in coordinates of the layout manager.

        This method calls :meth:`RecycleDataViewBehavior.refresh_view_attrs`
        if the view inherits from :class:`RecycleDataViewBehavior`. See that
        method for more details.

        .. note::
            Any sizing and position info is skipped when syncing with the data.
        '''
        if view.__class__ not in _view_base_cache:
            _view_base_cache[view.__class__] = isinstance(
                view, RecycleDataViewBehavior)

        if _view_base_cache[view.__class__]:
            view.refresh_view_layout(
                self.recycleview, index, layout, viewport)
        else:
            w, h = layout.pop('size')
            if w is None:
                if h is not None:
                    view.height = h
            else:
                if h is None:
                    view.width = w
                else:
                    view.size = w, h

            for name, value in layout.items():
                setattr(view, name, value)

    def make_view_dirty(self, view, index):
        '''(internal) Used to flag this view as dirty, ready to be used for
        others. See :meth:`make_views_dirty`.
        '''
        del self.views[index]
        self.dirty_views[view.__class__][index] = view

    def make_views_dirty(self):
        '''Makes all the current views dirty.

        Dirty views are still in sync with the corresponding data. However, the
        size information may go out of sync. Therefore a dirty view can be
        reused by the same index by just updating the sizing information.

        Once the underlying data of this index changes, the view should be
        removed from the dirty views and moved to the global cache with
        :meth:`invalidate`.

        This is typically called when the layout manager needs to re-layout all
        the data.
        '''
        views = self.views
        if not views:
            return

        dirty_views = self.dirty_views
        for index, view in views.items():
            dirty_views[view.__class__][index] = view
        self.views = {}

    def invalidate(self):
        '''Moves all the current views into the global cache.

        As opposed to making a view dirty where the view is in sync with the
        data except for sizing information, this will completely disconnect the
        view from the data, as it is assumed the data has gone out of sync with
        the view.

        This is typically called when the data changes.
        '''
        global _cache_count
        for view in self.views.values():
            _cached_views[view.__class__].append(view)
            _cache_count += 1

        for cls, views in self.dirty_views.items():
            _cached_views[cls].extend(views.values())
            _cache_count += len(views)

        if _cache_count >= _max_cache_size:
            _clean_cache()
        self.views = {}
        self.dirty_views.clear()

    def set_visible_views(self, indices, data, viewclasses):
        '''Gets a 3-tuple of the new, remaining, and old views for the current
        viewport.

        The new views are synced to the data except for the size/pos
        properties.
        The old views need to be removed from the layout, and the new views
        added.

        The new views are not necessarily *new*, but are all the currently
        visible views.
        '''
        visible_views = {}
        previous_views = self.views
        ret_new = []
        ret_remain = []
        get_view = self.get_view

        # iterate though the visible view
        # add them into the container if not already done
        for index in indices:
            view = previous_views.pop(index, None)
            if view is not None:  # was current view
                visible_views[index] = view
                ret_remain.append((index, view))
            else:
                view = get_view(index, data[index],
                                viewclasses[index]['viewclass'])
                if view is None:
                    continue
                visible_views[index] = view
                ret_new.append((index, view))

        old_views = previous_views.items()
        self.make_views_dirty()
        self.views = visible_views
        return ret_new, ret_remain, old_views

    def get_visible_view(self, index):
        '''Returns the currently visible view associated with ``index``.

        If no view is currently displayed for ``index`` it returns ``None``.
        '''
        return self.views.get(index)
