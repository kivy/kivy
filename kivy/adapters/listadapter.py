'''
ListAdapter
===========

.. versionadded:: 1.5

:class:`ListAdapter` is an adapter around a python list.

From :class:`Adapter`, :class:`ListAdapter` gets these properties:

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

From the :class:`CollectionAdapter` mixin, :class:`ListAdapter` has
these properties:

    - selection
    - selection_mode
    - allow_empty_selection

and several methods used in selection operations.

If you wish to have a bare-bones list adapter, without selection, use
:class:`SimpleListAdapter`.
'''

from kivy.properties import ListProperty, DictProperty, ObjectProperty
from kivy.adapters.collectionadapter import CollectionAdapter
from kivy.adapters.models import SelectableDataItem

from inspect import isfunction, ismethod


class ListAdapter(CollectionAdapter):

    def __init__(self, **kwargs):
        super(ListAdapter, self).__init__(**kwargs)

    def get_count(self):
        return len(self.data)

    def get_data_item(self, index):
        if index < 0 or index >= len(self.data):
            return None
        return self.data[index]

    def bind_triggers_to_view(self, func):
        self.bind(data=func)

    def touch_selection(self, *args):
        self.dispatch('on_selection_change')

    # [TODO] Also make methods for scroll_to_sel_start, scroll_to_sel_end,
    #        scroll_to_sel_middle.

    def trim_left_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are less than the
        index of the first selected item, if there is selection.
        '''
        pass

    def trim_right_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are greater than
        the index of the last selected item, if there is selection.
        '''
        pass

    def trim_to_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are les than or
        greater than the index of the last selected item, if there is
        selection. This preserves intervening list items within the selected
        range.
        '''
        pass

    def cut_to_sel(self, *args):
        '''Same as trim_to_sel, but intervening list items within the selected
        range are cut also, leaving only list items that are selected.
        '''
        pass
