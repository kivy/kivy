'''
ListAdapter
=================

.. versionadded:: 1.5

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

A :class:`ListAdapter` is an adapter around a python list.

From :class:`~kivy.adapters.adapter.Adapter`, a
:class:`~kivy.adapters.listadapter.ListAdapter` gets cls, template, and
args_converter properties.

From :class:`~kivy.adapters.selection.Selection` are properties that control
selection behaviour:

* *selection*, a list of selected items.

* *selection_mode*, 'single', 'multiple', 'none'

* *allow_empty_selection*, a boolean -- If False, a selection is forced. If
  True, and only user or programmatic action will change selection, it can
  be empty.

    :Events:

        `on_data_change`: (view, view list )
            Fired when data changes

.. versionchanged:: 1.6.0

    Added data = ListProperty([]), which was proably inadvertently deleted at
    some point. This means that whenever data changes an update will fire,
    instead of having to reset the data object (Adapter has data defined as
    an ObjectProperty, so we need to reset it here to ListProperty). See also
    DictAdapter and its set of data = DictProperty().

.. versionchanged:: 1.8.0

    A new class, OpObservableList is passed to ListProperty to replace its
    internal use of ObservableList. OpObservableList dispatches change events
    on a per op basis, as compared to the gross dispatching done by
    ObservableList. This new functionality is paired with changeds in ListView,
    which now reacts in a more fine-grained way to data changes. See its new
    data_changed() method. See also new adapter modules, list_ops.py and
    dict_ops.py which contain code for the more detailed dispatching logic.

'''

__all__ = ('ListAdapter', )

from kivy.adapters.adapter import Adapter
from kivy.adapters.list_ops import AdapterListOpHandler
from kivy.properties import OpObservableList
from kivy.properties import ListProperty
from kivy.properties import ObjectProperty


class ListAdapter(Adapter):
    '''A :class:`~kivy.adapters.listadapter.ListAdapter` is an adapter around a
    python list of items. It is an alternative to the dict capabilities of
    :class:`~kivy.adapters.dictadapter.DictAdapter`.

    :class:`~kivy.adapters.dictadapter.ListAdapter` and
    :class:`~kivy.adapters.listadapter.DictAdapter` use special
    :class:`~kivy.properties.ListProperty` and
    :class:`~kivy.properties.DictProperty` variants,
    :class:`~kivy.properties.OpObservableList` and
    :class:`~kivy.properties.OpObservableDict`, which record
    op_info for use in the adapter system.

    The data property of :class:`~kivy.adapters.listadapter.ListAdapter` is a
    :class:`~kivy.properties.OpObservableList`.

    This system endeavors to allow normal Python programming of the contained
    data list object. When normal operations such as append, insert, pop,
    sort, are performed on the data list, and the system will notice those
    changes and react accordingly, adjusting its cached_views and selection in
    support of the "collection" style view that uses the adapter (e.g.,
    :class:`~kivy.uix.listview.ListView`).

    This adapter supports collection-style widgets such as
    :class:`~kivy.uix.widgets.ListView`. When something happens in your program
    to change the data list, the name of the data operation that occurred,
    along with start_index, end_index of the item(s) affected are stored.  The
    adapter, via its instance of a :class:`~kivy.properties.ListOpHandler`,
    has callbacks that handle specific operations, and make needed changes to
    the internal cached_views, selection, and related properties, in
    preparation for sending, in turn, a data-changed event to the
    collection-style widget that uses the adapter.  For example,
    :class:`~kivy.uix.widgets.ListView` observes its adapter for data-changed
    events and updates the user interface. When an item is deleted, it removes
    the item view widget from its container, or for an addition, it adds the
    item view widget to its container and scrolls the list, and so on.

    .. versionchanged:: 1.8.0

        A new class, OpObserverableList, was added to kivy/properties.pyx as an
        alternative to ObservableList, which only dispatches when data is
        set, or when any change occurs. The new ObObservableList dispatches on
        a fine-grained basis, after any individual op is performed.

        This new class is used in the ListProperty for data.

        ListAdapter must react to the events that come for a change to data.
        It delegates handling of these events to a ListOpHandler
        instance, defined in a new module, adapters/list_ops.py. This handling
        mainly involves adjusting cached_views and selection, in support of
        collection type widgets, such as ListView, that use ListAdapter.

        The data_changed() method of the delegate ListOpHandler and methods
        called there do what is needed to cached_views and selection, then they
        dispatch, in turn, up to the owning collection type view, such as
        ListView. The collection type view then reacts with changes to its
        children and other parts of the user interface as needed.
    '''

    data = ListProperty([], cls=OpObservableList)
    '''A Python list that uses
    :class:`~kivy.properties.OpObservableList` for storage, as a
    "change-aware" wrapper that records change info for list ops.

    :data:`data` is a :class:`~kivy.properties.ListProperty` and defaults
    to [].
    '''

    list_op_handler = ObjectProperty(None)
    '''An instance of :class:`~kivy.adapters.list_ops.AdapterListOpHandler`,
    containing methods that perform steps needed after the data has changed.
    The methods are responsible for updating cached_views and selection.

    :data:`list_op_handler` is a :class:`~kivy.properties.ObjectProperty` and
    defaults to None. It is instantiated and set on init.
    '''

    op_info = ObjectProperty(None)
    '''This is a copy of our data's op_info. We make a copy before dispatching
    the on_data_change event, so that observers can more conveniently access
    it.
    '''

    __events__ = ('on_data_change', )

    def __init__(self, **kwargs):
        super(ListAdapter, self).__init__(**kwargs)

        self.list_op_handler = AdapterListOpHandler(
                source_list=self.data, duplicates_allowed=True)

        self.bind(selection_mode=self.selection_mode_changed,
                  allow_empty_selection=self.check_for_empty_selection,
                  data=self.list_op_handler.data_changed)

        self.initialize_selection()

    def on_data_change(self, *args):
        '''on_data_change() is the default handler for the
        on_data_change event.
        '''
        pass

    # [TODO] Also make methods for scroll_to_sel_start, scroll_to_sel_end,
    #        scroll_to_sel_middle.

    def trim_left_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are less than the
        index of the first selected item if there is a selection.
        '''
        if len(self.selection) > 0:
            first_sel_index = min([sel.index for sel in self.selection])
            self.data = self.data[first_sel_index:]

    def trim_right_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are greater than
        the index of the last selected item if there is a selection.
        '''
        if len(self.selection) > 0:
            last_sel_index = max([sel.index for sel in self.selection])
            self.data = self.data[:last_sel_index + 1]

    def trim_to_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are les than or
        greater than the index of the last selected item if there is a
        selection. This preserves intervening list items within the selected
        range.
        '''
        if len(self.selection) > 0:
            sel_indices = [sel.index for sel in self.selection]
            first_sel_index = min(sel_indices)
            last_sel_index = max(sel_indices)
            self.data = self.data[first_sel_index:last_sel_index + 1]

    def cut_to_sel(self, *args):
        '''Same as trim_to_sel, but intervening list items within the selected
        range are also cut, leaving only list items that are selected.
        '''
        if len(self.selection) > 0:
            self.data = self.selection
