'''
DictAdapter
===========

.. versionadded:: 1.5

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

A :class:`~kivy.adapters.dictadapter.DictAdapter` is an adapter around a
python dictionary of records. It extends the list-like capabilities of the
:class:`~kivy.adapters.listadapter.ListAdapter`.

If you wish to have a bare-bones list adapter, without selection, use the
:class:`~kivy.adapters.simplelistadapter.SimpleListAdapter`.

'''

__all__ = ('DictAdapter', )

from kivy.event import EventDispatcher
from kivy.properties import DictProperty
from kivy.properties import ListProperty
from kivy.properties import ObjectProperty
from kivy.adapters.adapter import Adapter
from kivy.adapters.dict_ops import DictOpHandler
from kivy.adapters.dict_ops import RecordingObservableDict
from kivy.adapters.list_ops import ListOpHandler
from kivy.adapters.list_ops import RecordingObservableList


class DictAdapter(Adapter, EventDispatcher):
    '''A :class:`~kivy.adapters.dictadapter.DictAdapter` is an adapter around a
    python dictionary of records. It is an alternative to the list capabilities
    of :class:`~kivy.adapters.listadapter.ListAdapter`.

    :class:`~kivy.adapters.dictadapter.ListAdapter` and
    :class:`~kivy.adapters.listadapter.DictAdapter` use special
    :class:`~kivy.properties.ListProperty` and
    :class:`~kivy.properties.DictProperty` variants,
    :class:`~kivy.adapters.list_ops.RecordingObservableList` and
    :class:`~kivy.adapters.dict_ops.RecordingObservableDict`, which
    record op_info for use in the adapter system.

    This system endeavors to allow normal Python programming of the contained
    list or dict objects. For lists, this means normal operations (append,
    insert, pop, sort, etc.) and the ones for dicts (setitem, pop, popitem,
    setdefault, clear, etc.).

    :class:`~kivy.adapters.dictadapter.DictAdapter` has sorted_keys, a
    :class:`~kivy.adapters.list_ops.RecordingObservableList`, and
    data, :class:`~kivy.adapters.dict_ops.RecordingObservableDict`.
    You can change these as you wish and the system will react accordingly.

    It may help you to understand how the system works, combining an adapter
    such as this one with a collection-style widget such as
    :class:`~kivy.uix.widgets.ListView`. When something happens in your program
    to change the list or dict in the aforementioned special properties (here
    we are talking about sorted_keys and data), the op_info stored is a
    Python tuple containing the name of the data operation that occurred, along
    with a contained tuple with (start_index, end_index) for lists or (keys,)
    for dicts. The system cannot know the details about operations beforehand,
    so it must react after-the-fact for which items were affected and how. The
    adapters have callbacks that handle specific operations, and make needed
    changes to their internal cached_views, selection, and related properties,
    in preparation for sending, in turn, a data-changed event to the
    collection-style widget that uses the adapter. For example,
    :class:`~kivy.uix.widgets.ListView` observes its adapter for data-changed
    events and updates the user interface. When an item is deleted, it removes
    the item view widget from its container, or for an addition, it adds the
    item view widget to its container and scrolls the list, and so on.
    '''

    # TODO: Adapt to Python's OrderedDict?

    sorted_keys = ListProperty([], cls=RecordingObservableList)
    '''A Python list that uses :class:`~kivy.properties.ObservableList` for
    storage, and uses :class:`~kivy.adapters.list_ops.RecordingObservableList` as a
    "change-aware" wrapper that records op_info for list ops.

    The sorted_keys list property contains hashable objects that need to be
    strings if no args_converter function is provided. If there is an
    args_converter, the record received from a lookup of the data, using keys
    from sorted_keys, will be passed to it for instantiation of item view class
    instances.

    :data:`sorted_keys` is a :class:`~kivy.properties.ListProperty` and
    defaults to [].
    '''

    data = DictProperty({}, cls=RecordingObservableDict)
    '''A Python dict that uses :class:`~kivy.properties.ObservableDict` for
    storage, and uses :class:`~kivy.adapters.dict_ops.RecordingObservableDict`
    as a "change-aware" wrapper that records op_info for dict ops.

    The dict may contain more data items than are present in sorted_keys --
    sorted_keys can be a subset of data.keys().

    :data:`data` is a :class:`~kivy.properties.DictProperty` and defaults
    to None.
    '''

    dict_op_handler = ObjectProperty(None)
    '''An instance of :class:`DictOpHandler`, containing methods that perform
    steps needed after the data (a
    :class:`~kivy.adapters.dict_ops.RecordingObservableDict`) has changed. The
    methods are responsible for updating cached_views and selection.

    :data:`dict_op_handler` is a :class:`~kivy.properties.ObjectProperty` and
    defaults to None. It is instantiated and set on init.
    '''

    op_info = ObjectProperty(None, allownone=True)
    '''This is a copy of our data's recorder.op_info. We make a copy
    before dispatching the on_data_change event, so that observers can more
    conveniently access it.
    '''

    additional_op_info = ObjectProperty(None)
    '''Some ops need to store additional info, such as start_index and
    end_index.
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

        self.bind(sorted_keys=self.sorted_keys_changed)

        # Delegate handling for sorted_keys changes to a ListOpHandler.
        self.list_op_handler = ListOpHandler(adapter=self,
                                             source_list=self.sorted_keys,
                                             duplicates_allowed=False)
        self.sorted_keys.recorder.bind(
                on_op_info=self.list_op_handler.data_changed,
                on_sort_started=self.list_op_handler.sort_started)

        # Delegate handling for data changes to a DictOpHandler.
        self.dict_op_handler = DictOpHandler(adapter=self,
                                             source_dict=self.data)
        self.data.recorder.bind(
                op_info=self.dict_op_handler.data_changed)

    def sorted_keys_checked(self, sorted_keys, data_keys):

        # Remove any keys in sorted_keys that are not found in
        # self.data.keys(). This is the set intersection op (&).
        sorted_keys_checked = list(set(sorted_keys) & set(data_keys))

        # Maintain sort order of incoming sorted_keys.
        return [k for k in sorted_keys if k in sorted_keys_checked]

    # NOTE: The reason for on_data_change and on_sorted_keys_change,
    #       instead of on_data and on_sorted_keys: These are peculiar to the
    #       adapters and their API (using and referring to op_info). This
    #       leaves on_data and on_sorted_keys still available for use in the
    #       "regular" manner, perhaps for some Kivy widgets, perhaps for
    #       custom widgets.

    def on_data_change(self, *args):
        '''Default data handler for on_data_change event.
        '''
        pass

    def insert(self, index, key, value):

        # This special insert() ROD call only does a dict set (it does not
        # write op_info). We will let the sorted_keys insert trigger a
        # data change event.
        self.data.insert(key, value)

        self.sorted_keys.insert(index, key)

    def sorted_keys_changed(self, *args):
        '''This callback happens as a result of the direct sorted_keys binding
        set up in __init__(). It is needed for the direct set of sorted_keys,
        as happens in ...sorted_keys = [some new list], which is not picked up
        by the ROL data change system. We check by looking for a valid recorder
        that is created when a ROL event has fired. If not present, we know
        this call is from a direct sorted_keys set.
        '''

        if (hasattr(self.sorted_keys, 'recorder')
               and not self.sorted_keys.recorder.op_started):

            self.cached_views.clear()

            self.list_op_handler.source_list = self.sorted_keys

            self.sorted_keys.recorder.bind(
                on_op_info=self.list_op_handler.data_changed,
                on_sort_started=self.list_op_handler.sort_started)

            self.op_info = ('ROL_reset', (0, 0))
            self.dispatch('on_data_change')

            self.initialize_selection()

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
