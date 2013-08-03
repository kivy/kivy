'''
DictAdapter
===========

.. versionadded:: 1.5

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

A :class:`~kivy.adapters.dictadapter.DictAdapter` is an adapter around a
python dictionary of records.
'''

__all__ = ('DictAdapter', )

from kivy.properties import DictProperty
from kivy.properties import ListProperty
from kivy.properties import ObjectProperty

from kivy.properties import OpObservableList
from kivy.properties import OpObservableDict

from kivy.adapters.adapter import Adapter
from kivy.adapters.dict_ops import AdapterDictOpHandler
from kivy.adapters.list_ops import AdapterListOpHandler


class DictAdapter(Adapter):
    '''A :class:`~kivy.adapters.dictadapter.DictAdapter` is an adapter around a
    python dictionary of records. It is an alternative to the list capabilities
    of :class:`~kivy.adapters.listadapter.ListAdapter`.

    This class supports a "collection" style view such as
    :class:`~kivy.uix.listview.ListView`.

    :class:`~kivy.adapters.dictadapter.ListAdapter` and
    :class:`~kivy.adapters.listadapter.DictAdapter` use special
    :class:`~kivy.properties.ListProperty` and
    :class:`~kivy.properties.DictProperty` variants,
    :class:`~kivy.properties.OpObservableList` and
    :class:`~kivy.properties.OpObservableDict`, which
    record op_info for use in the adapter system.

    :class:`~kivy.adapters.dictadapter.DictAdapter` has sorted_keys, a
    :class:`~kivy.properties.OpObservableList`, and data, a
    :class:`~kivy.properties.OpObservableDict`.  You can change
    these as you wish and the system will react accordingly (for the
    sorted_keys list: append, insert, pop, sort, etc.; for the data dict:
    setitem, pop, popitem, setdefault, clear, etc.).

    See :class:`~kivy.adapters.dictadapter.ListAdapter` for discussion of how
    the system works for :class:`~kivy.properties.OpObservableList`
    (sorted_keys here is one of those).

    Here we also have a data property, which is a
    :class:`~kivy.properties.OpObservableDict`, sending change info for
    possible ops to an associated helper op handler,
    :class:`~kivy.adapters.dict_ops.AdapterDictOpHandler`. The op handler
    responds to data changes by updating cached_views and selection, in support
    of the "collection" style view that uses this adapter.

    .. versionchanged:: 1.8.0

        New classes, OpObserverableList and OpObservableDict, were added to
        kivy/properties.pyx as alternatives to ObservableList and
        ObservableDict, which only dispatch when data is set, or when any
        change occurs. The new ObObservableList and OpObservableDict dispatch
        on a fine-grained basis, after any individual op is performed.

        These new classes are used in the ListProperty for sorted_keys and in
        the DictProperty for data.

        DictAdapter must react to the events that come for a change to
        sorted_keys or to data. It delegates handling of these events for
        sorted_keys to a ListOpHandler instance, defined in a new module,
        adapters/list_ops.py.  Likewise, for data, it delegates event handling
        to a dedicated DictOpHandler. This handling mainly involves adjusting
        cached_views and selection, in support of collection type widgets, such
        as ListView, that use DictAdapter.

        The data_changed() method of the delegate ListOpHandler and
        DictOpHandler modules, and methods used there, do what is needed to
        cached_views and selection, then they dispatch, in turn, up to the
        owning collection type view, such as ListView. The collection type view
        then reacts with changes to its children and other parts of the user
        interface as needed.
    '''

    sorted_keys = ListProperty([], cls=OpObservableList)
    '''A Python list that uses
    :class:`~kivy.properties.OpObservableList`
    as a "change-aware" wrapper that records op_info for list ops.

    :data:`sorted_keys` is a :class:`~kivy.properties.ListProperty` and
    defaults to [].
    '''

    data = DictProperty({}, cls=OpObservableDict)
    '''A Python dict that uses
    :class:`~kivy.properties.OpObservableDict` as a "change-aware"
    wrapper that records op_info for dict ops.

    The dict may contain more data items than are present in sorted_keys --
    sorted_keys can be a subset of data.keys().

    :data:`data` is a :class:`~kivy.properties.DictProperty` and defaults
    to None.
    '''

    dict_op_handler = ObjectProperty(None)
    '''An instance of :class:`~kivy.adapters.dict_ops.DictOpHandler`,
    containing methods that perform steps needed after the data (a
    :class:`~kivy.properties.OpObservableDict`) has changed. The
    methods are responsible for updating cached_views and selection.

    :data:`dict_op_handler` is a :class:`~kivy.properties.ObjectProperty` and
    defaults to None. It is instantiated and set on init.
    '''

    op_info = ObjectProperty(None)
    '''This is a copy of our data's op_info. We make a copy before dispatching
    the on_data_change event, so that observers can more conveniently access
    it.
    '''

    additional_op_info = ObjectProperty(None)
    '''Some ops need to store additional info, start_index and end_index.
    '''

    __events__ = ('on_data_change', )

    def __init__(self, **kwargs):

        if 'sorted_keys' in kwargs:
            if type(kwargs['sorted_keys']) not in (tuple, list):
                msg = 'DictAdapter: sorted_keys must be tuple or list'
                raise Exception(msg)
            else:
                self.sorted_keys = \
                        self.sorted_keys_checked(kwargs.pop('sorted_keys'),
                                                 kwargs['data'].keys())
        else:
            self.sorted_keys = sorted(kwargs['data'].keys())

        super(DictAdapter, self).__init__(**kwargs)

        # Delegate handling for sorted_keys changes to a ListOpHandler.
        self.list_op_handler = AdapterListOpHandler(
                source_list=self.sorted_keys, duplicates_allowed=False)

        # Delegate handling for data changes to a DictOpHandler.
        self.dict_op_handler = AdapterDictOpHandler(source_dict=self.data)

        self.bind(sorted_keys=self.list_op_handler.data_changed,
                  data=self.dict_op_handler.data_changed)

    def sorted_keys_checked(self, sorted_keys, data_keys):

        # Remove any keys in sorted_keys that are not found in
        # self.data.keys(). This is the set intersection op (&).
        sorted_keys_checked = list(set(sorted_keys) & set(data_keys))

        # Maintain sort order of incoming sorted_keys.
        return [k for k in sorted_keys if k in sorted_keys_checked]

    # TODO: bind_triggers_to_view() is no longer used. Leave, but mark as
    #       deprecated.
    def bind_triggers_to_view(self, func):
        self.bind(sorted_keys=func)
        self.bind(data=func)

    # NOTE: The reason for on_data_change and on_sorted_keys_change,
    #       instead of on_data and on_sorted_keys: These are peculiar to the
    #       adapters and their API (using and referring to op_info). This
    #       leaves on_data and on_sorted_keys still available for use in the
    #       "regular" manner, perhaps for some Kivy widgets, perhaps for
    #       custom widgets.
    # TODO: Remove this note, because the events are no longer used by the
    #       internal system. Keep the events?

    def on_data_change(self, *args):
        '''Default data handler for on_data_change event.
        '''
        pass

    def insert(self, index, key, value):

        # This special insert() OOD call only does a dict set (it does not
        # write op_info). We will let the sorted_keys insert trigger a
        # data change event.
        self.data.insert(key, value)

        self.sorted_keys.insert(index, key)

    # NOTE: This is not len(self.data). (The data dict may contain more items
    #       than sorted_keys -- sorted_keys can be a subset.).
    def get_count(self):
        return len(self.sorted_keys)

    # TODO: It might be nice to return (key, data_item). Is this a good idea?
    #       There would be a backwards compatibility issue. If needed, make
    #       this the default function, and add a new one? Then later deprecate?
    def get_data_item(self, index):
        if index < 0 or index >= len(self.sorted_keys):
            return None
        return self.data[self.sorted_keys[index]]

    # TODO: Also make methods for scroll_to_sel_start, scroll_to_sel_end,
    #       scroll_to_sel_middle.

    def trim_left_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are less than the
        index of the first selected item, if there is a selection.
        '''
        if len(self.selection) > 0:
            selected_keys = [sel.text for sel in self.selection]
            first_sel_index = self.sorted_keys.index(selected_keys[0])
            desired_keys = self.sorted_keys[first_sel_index:]
            self.data = dict([(key, self.data[key]) for key in desired_keys])

    def trim_right_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are greater than
        the index of the last selected item, if there is a selection.
        '''
        if len(self.selection) > 0:
            selected_keys = [sel.text for sel in self.selection]
            last_sel_index = self.sorted_keys.index(selected_keys[-1])
            desired_keys = self.sorted_keys[:last_sel_index + 1]
            self.data = dict([(key, self.data[key]) for key in desired_keys])

    def trim_to_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are les than or
        greater than the index of the last selected item, if there is a
        selection. This preserves intervening list items within the selected
        range.
        '''
        if len(self.selection) > 0:
            selected_keys = [sel.text for sel in self.selection]
            first_sel_index = self.sorted_keys.index(selected_keys[0])
            last_sel_index = self.sorted_keys.index(selected_keys[-1])
            desired_keys = self.sorted_keys[first_sel_index:last_sel_index + 1]
            self.data = dict([(key, self.data[key]) for key in desired_keys])

    def cut_to_sel(self, *args):
        '''Same as trim_to_sel, but intervening list items within the selected
        range are also cut, leaving only list items that are selected.
        '''
        if len(self.selection) > 0:
            selected_keys = [sel.text for sel in self.selection]
            self.data = dict([(key, self.data[key]) for key in selected_keys])
