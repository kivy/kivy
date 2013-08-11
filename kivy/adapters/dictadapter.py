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

import inspect

from kivy.adapters.adapter import Adapter
from kivy.adapters.dict_ops import AdapterDictOpHandler
from kivy.adapters.list_ops import AdapterListOpHandler

from kivy.models import SelectableDataItem

from kivy.properties import DictProperty
from kivy.properties import ListProperty
from kivy.properties import ObjectProperty

from kivy.properties import OpObservableList
from kivy.properties import OpObservableDict

from kivy.selection import Selection


class DictAdapter(Selection, Adapter):
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

    :Events:

        `on_data_change`: (view, view list )
            Fired when data changes

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
        self.dict_op_handler = AdapterDictOpHandler()

        self.bind(sorted_keys=self.list_op_handler.data_changed,
                  data=self.dict_op_handler.data_changed)

    def sorted_keys_checked(self, sorted_keys, data_keys):

        # Remove any keys in sorted_keys that are not found in
        # self.data.keys(). This is the set intersection op (&).
        sorted_keys_checked = list(set(sorted_keys) & set(data_keys))

        # Maintain sort order of incoming sorted_keys.
        return [k for k in sorted_keys if k in sorted_keys_checked]

    def bind_triggers_to_view(self, func):
        '''
        .. deprecated:: 1.8

             The data changed system was changed to use variants of
             ObservableList/Dict that dispatch after individual operations,
             passing information about what changed to a data_changed()
             handler, which should be implemented by observers of adapters.
        '''

        self.bind(sorted_keys=func)
        self.bind(data=func)

    def on_data_change(self, *args):
        pass

    def insert(self, index, key, value):
        '''A Python dict does not have an insert(), because keys are unordered.
        Here, with sorted_keys, an insert() makes sense, but we put it as part
        of the adapter API, not as a public method of the data dict.
        '''

        # This special insert() OOD call only does a dict set (it does not
        # write op_info). The sorted_keys insert will trigger a data change
        # event.
        self.data.setitem_for_insert(key, value)
        self.sorted_keys.insert(index, key)

    # NOTE: This is not len(self.data). (The data dict may contain more items
    #       than sorted_keys -- sorted_keys can be a subset.).
    def get_count(self):
        return len(self.sorted_keys)

    def get_data_item(self, index):
        '''args_converters for DictAdapter instances receive the index and the
        data value, along with the key at the index, as the last argument:

            data item at sorted_keys[index],
            the key (sorted_keys[index])

        So, an args_converter for DictAdapter will now get three arguments:

            index, data_item, key

        See the create_view() method of the Adapter base class, where argument
        parsing is done.
        '''

        key = self.sorted_keys[index]

        return self.data[key], key

    def create_view(self, index):
        '''This method first calls the Adapter superclass to get the data_item
        and new view_instance created from it. Then bindings are created for
        the view_instance and perhaps its children to self.handle_selection().
        Selection of view instances is optionally kept in sync with the
        selection of data items.
        '''

        if index < 0 or index > len(self.sorted_keys) -1:
            return None

        data_item, view_instance = super(DictAdapter, self).create_view(index)

        view_instance.bind(on_release=self.handle_selection)

        # Should the view instance reflect the state of selection in the
        # underlying data item?
        if self.sync_with_model_data:

            # The data item must be a subclass of SelectableDataItem, or must
            # have an is_selected boolean or function, so it has is_selected
            # available.  If is_selected is unavailable on the data item, an
            # exception is raised.

            if isinstance(data_item, SelectableDataItem):
                if data_item.is_selected:
                    self.handle_selection(view_instance)
            elif type(data_item) == dict and 'is_selected' in data_item:
                if data_item['is_selected']:
                    self.handle_selection(view_instance)
            elif hasattr(data_item, 'is_selected'):
                if (inspect.isfunction(data_item.is_selected)
                        or inspect.ismethod(data_item.is_selected)):
                    if data_item.is_selected():
                        self.handle_selection(view_instance)
                else:
                    if data_item.is_selected:
                        self.handle_selection(view_instance)
            else:
                msg = "ListAdapter: unselectable data item for {0}"
                raise Exception(msg.format(index))

        return view_instance

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
