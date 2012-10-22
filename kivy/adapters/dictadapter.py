'''
DictAdapter
===========

.. versionadded:: 1.5

:class:`DictAdapter` is an adapter around a python dictionary of records.

From :class:`Adapter`, :class:`DictAdapter` gets these properties:

    Use only one:

        - cls, for a list key class to use to instantiate key view
               instances

        - template, a kv template to use to instantiate key view
                    instances

    - args_converter, an optional function to transform data item argument
                      sets, in preparation for either a cls instantiation,
                      or a kv template invocation. If no args_converter is
                      provided, a default one is set, that assumes that the
                      data items are strings.

From the :class:`CollectionAdapter` mixin, :class:`DictAdapter` has
these properties:

    - selection
    - selection_mode
    - allow_empty_selection

and several methods used in selection operations.

If you wish to have a bare-bones list adapter, without selection, use
:class:`SimpleListAdapter`.

'''

from kivy.properties import ListProperty, DictProperty
from kivy.lang import Builder
from kivy.adapters.collectionadapter import CollectionAdapter
from kivy.adapters.models import SelectableDataItem


class DictAdapter(CollectionAdapter):

    sorted_keys = ListProperty([])
    '''The sorted_keys list property contains a list of hashable objects (can
    be strings) that will be used directly if no args_converter function is
    provided. If there is an args_converter, the record received from a
    lookup in the data, using key from sorted_keys, will be passed
    to it, for instantiation of list item view class instances.
    '''

    data = DictProperty(None)
    '''A dict that indexes records by keys that are equivalent to the keys in
    sorted_keys, or they are a superset of the keys in sorted_keys.

    The values can be strings, class instances, dicts, etc.
    '''

    def __init__(self, **kwargs):
        if 'sorted_keys' in kwargs:
            if type(kwargs['sorted_keys']) not in (tuple, list):
                msg = 'DictAdapter: sorted_keys must be tuple or list'
                raise Exception(msg)
        else:
            self.sorted_keys = sorted(kwargs['data'].keys())

        super(DictAdapter, self).__init__(**kwargs)

        self.bind(sorted_keys=self.initialize_sorted_keys)

    def bind_triggers_to_view(self, func):
        self.bind(sorted_keys=func)
        self.bind(data=func)

    def initialize_sorted_keys(self, *args):
        self.delete_cache()
        self.initialize_selection()

    def get_count(self):
        return len(self.sorted_keys)

    def get_data_item(self, index):
        if index < 0 or index >= len(self.sorted_keys):
            return None
        return self.data[self.sorted_keys[index]]

    def select_data_item(self, item):
        # The data item must be a subclass of SelectableDataItem, or must have
        # an is_selected boolean or function, so it has is_selected available.
        # If is_selected is unavailable on the data item, an exception is
        # raised.
        #
        if issubclass(item.__class__, SelectableDataItem):
            item.is_selected = True
        elif type(item) == dict and 'is_selected' in item:
            item['is_selected'] = True
        elif hasattr(item, 'is_selected'):
            if isfunction(item.is_selected) or ismethod(item.is_selected):
                item.is_selected()
            else:
                item.is_selected = True
        else:
            msg = "ListAdapter: unselectable data item for {0}".format(item)
            raise Exception(msg)

    def touch_selection(self, *args):
        self.dispatch('on_selection_change')
                  

    # [TODO] Also make methods for scroll_to_sel_start, scroll_to_sel_end,
    #        scroll_to_sel_middle.

    def trim_left_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are less than the
        index of the first selected item, if there is selection.
        '''
        if len(self.selection) > 0:
            selected_keys = [sel.text for sel in self.selection]
            first_sel_index = self.sorted_keys.index(selected_keys[0])
            desired_keys = self.sorted_keys[first_sel_index:]
            self.data = {key: self.data[key] for key in desired_keys}

    def trim_right_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are greater than
        the index of the last selected item, if there is selection.
        '''
        if len(self.selection) > 0:
            selected_keys = [sel.text for sel in self.selection]
            last_sel_index = self.sorted_keys.index(selected_keys[-1])
            desired_keys = self.sorted_keys[:last_sel_index + 1]
            self.data = {key: self.data[key] for key in desired_keys}

    def trim_to_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are les than or
        greater than the index of the last selected item, if there is
        selection. This preserves intervening list items within the selected
        range.
        '''
        if len(self.selection) > 0:
            selected_keys = [sel.text for sel in self.selection]
            first_sel_index = self.sorted_keys.index(selected_keys[0])
            last_sel_index = self.sorted_keys.index(selected_keys[-1])
            desired_keys = self.sorted_keys[first_sel_index:last_sel_index + 1]
            self.data = {key: self.data[key] for key in desired_keys}

    def cut_to_sel(self, *args):
        '''Same as trim_to_sel, but intervening list items within the selected
        range are cut also, leaving only list items that are selected.
        '''
        if len(self.selection) > 0:
            selected_keys = [sel.text for sel in self.selection]
            self.data = {key: self.data[key] for key in selected_keys}
