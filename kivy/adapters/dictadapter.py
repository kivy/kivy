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

.. versionchanged:: 1.8.0

    Changed sorted_keys to an :class:`~kivy.properties.AliasProperty`. 
    Since it's solely dependent on :attr:`data`, 
    an :class:`~kivy.properties.AliasProperty` simplifies things.
    Did not allow setting of :attr:`sorted_keys` in the interest of
    consolidation.
    
    Changed :attr:`get_data_item` for readability.
    
    Changed :attr:`data` to initialize to an empty dictionary, `{}`.
    
    Removed `initialize_sorted_keys` and `update_for_new_data`.
    
    Removed mention of "if no args_converter".

'''

__all__ = ('DictAdapter', )

from kivy.properties import AliasProperty, DictProperty
from kivy.adapters.listadapter import ListAdapter


class DictAdapter(ListAdapter):
    '''A :class:`~kivy.adapters.dictadapter.DictAdapter` is an adapter around a
    python dictionary of records. It extends the list-like capabilities of
    the :class:`~kivy.adapters.listadapter.ListAdapter`.
    '''

    data = DictProperty({})
    '''A dict that indexes records by keys that are equivalent to the keys in
    sorted_keys, or they are a superset of the keys in sorted_keys.

    The values can be strings, class instances, dicts, etc.

    :attr:`data` is a :class:`~kivy.properties.DictProperty` and defaults
    to {}.
    '''
    
    def _get_sorted_keys(self):
        return sorted(self.data, key=self.data.get)
        
    sorted_keys = AliasProperty(_get_sorted_keys, None, bind=('data',))
    '''The sorted_keys list property contains a list of hashable objects (can
    be strings). If there is an args_converter, the record received from a
    lookup of the data, using keys from sorted_keys, will be passed
    to it for instantiation of list item view class instances.

    :attr:`sorted_keys` is a :class:`~kivy.properties.AliasProperty`.
    '''

    def bind_triggers_to_view(self, func):
        self.bind(sorted_keys=func)
        self.bind(data=func)

    # Note: this is not len(self.data).
    def get_count(self):
        return len(self.sorted_keys)

    def get_data_item(self, index):
        sorted_keys = self.sorted_keys

        if (0 <= index < len(sorted_keys)):
            return self.data[sorted_keys[index]]
        else:
            return None

    # [TODO] Also make methods for scroll_to_sel_start, scroll_to_sel_end,
    #        scroll_to_sel_middle.

    def trim_left_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are less than the
        index of the first selected item, if there is a selection.

        sorted_keys will be updated by update_for_new_data().
        '''
        if len(self.selection) > 0:
            selected_keys = [sel.text for sel in self.selection]
            first_sel_index = self.sorted_keys.index(selected_keys[0])
            desired_keys = self.sorted_keys[first_sel_index:]
            self.data = dict([(key, self.data[key]) for key in desired_keys])

    def trim_right_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are greater than
        the index of the last selected item, if there is a selection.

        sorted_keys will be updated by update_for_new_data().
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

        sorted_keys will be updated by update_for_new_data().
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

        sorted_keys will be updated by update_for_new_data().
        '''
        if len(self.selection) > 0:
            selected_keys = [sel.text for sel in self.selection]
            self.data = dict([(key, self.data[key]) for key in selected_keys])
