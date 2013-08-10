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

from kivy.properties import DictProperty
from kivy.properties import ListProperty
from kivy.properties import ObservableDict
from kivy.adapters.listadapter import ListAdapter
from kivy.adapters.listadapter import RangeObservingObservableList


class RangeObservingObservableDict(ObservableDict):

    # range_change is a normal python object consisting of the op name and
    # the keys involved:
    #
    #     (data_op, (keys))
    #
    # If the op does not cause a range change, range_change is set to None.
    #
    # Observers of data changes may consult range_change if needed, for
    # example, listview needs to know details for scrolling.
    #
    # DictAdapter itself, the owner of data, is the first observer of data
    # change that must react to delete ops, if the existing selection is
    # affected.
    #

    # TODO: Do something on this one?
    #def __setattr__(self, attr, value):
    #    if attr in ('prop', 'obj'):
    #        super(ObservableDict, self).__setattr__(attr, value)
    #        return
    #    self.__setitem__(attr, value)

    def __setitem__(self, key, value):
        if value is None:
            # ObservableDict will delete the item if value is None, so this is
            # like a delete op.
            self.range_change = ('delete', (key, ))
        else:
            self.range_change = ('add', (key, ))
        super(RangeObservingObservableDict, self).__setitem__(key, value)

    def __delitem__(self, key):
        self.range_change = ('delete', (key, ))
        super(RangeObservingObservableDict, self).__delitem__(key)

    def clear(self, *largs):
        # TODO: Should this, and other cases below, be (*largs)?
        self.range_change = ('delete', largs)
        super(RangeObservingObservableDict, self).clear(*largs)

    def remove(self, *largs):
        # remove(x) is same as del s[s.index(x)]
        self.range_change = ('delete', largs)
        super(RangeObservingObservableDict, self).remove(*largs)

    def pop(self, *largs):
        # This is pop on a specific key.
        # s.pop([i]) is same as x = s[i]; del s[i]; return x
        self.range_change = ('delete', largs)
        return super(RangeObservingObservableDict, self).pop(*largs)

    def popitem(self, *largs):
        # From python docs, "Remove and return an arbitrary (key, value) pair
        # from the dictionary." From other reading, arbitrary here effectively
        # means "random" in the loose sense -- for truely random ops, use the
        # proper random module. Nevertheless, the item is deleted and returned.
        self.range_change = ('delete', largs)
        return super(RangeObservingObservableDict, self).popitem(*largs)

    def setdefault(self, *largs):
        present_keys = super(RangeObservingObservableDict, self).keys()
        if not largs[0] in present_keys:
            self.range_change = ('add', largs)
        super(RangeObservingObservableDict, self).setdefault(*largs)

    def update(self, *largs):
        present_keys = super(RangeObservingObservableDict, self).keys()
        self.range_change = ('add', list(set(largs) - set(present_keys)))
        super(RangeObservingObservableDict, self).update(*largs)


class DictAdapter(ListAdapter):
    '''A :class:`~kivy.adapters.dictadapter.DictAdapter` is an adapter around a
    python dictionary of records. It extends the list-like capabilities of
    the :class:`~kivy.adapters.listadapter.ListAdapter`.
    '''

    sorted_keys = ListProperty([])
    '''The sorted_keys list property contains a list of hashable objects (can
    be strings) that will be used directly if no args_converter function is
    provided. If there is an args_converter, the record received from a
    lookup of the data, using keys from sorted_keys, will be passed
    to it for instantiation of list item view class instances.

    :data:`sorted_keys` is a :class:`~kivy.properties.ListProperty` and
    defaults to [].
    '''

    # TODO: This was initialized to None. Problem with setting to {} instead?
    data = DictProperty({}, RangeObservingObservableDict)
    '''A dict that indexes records by keys that are equivalent to the keys in
    sorted_keys, or they are a superset of the keys in sorted_keys.

    TODO: Is that last statement about "superset" correct?

    The values can be strings, class instances, dicts, etc.

    :data:`data` is a :class:`~kivy.properties.DictProperty` and defaults
    to None.
    '''

    def __init__(self, **kwargs):
        if 'sorted_keys' in kwargs:
            if type(kwargs['sorted_keys']) not in (tuple, list):
                msg = 'DictAdapter: sorted_keys must be tuple or list'
                raise Exception(msg)
            else:
                # Copy the provided sorted_keys, and maintain it internally.
                # The only function in the API for sorted_keys is to reset it
                # wholesale with a call to reset_sorted_keys().
                self.sorted_keys = list(kwargs['sorted_keys'])
                kwargs.remove('sorted_keys')
        else:
            self.sorted_keys = sorted(kwargs['data'].keys())

        super(DictAdapter, self).__init__(**kwargs)

        self.bind(sorted_keys=self.initialize_sorted_keys,
                  data=self.data_changed)

    def reset_sorted_keys(self, sorted_keys):
        self.sorted_keys = sorted_keys
        # call update on dict to match?

    def data_changed(self, *dt):

        print 'DICT ADAPTER data_changed callback', dt

        print self.data.range_change

        if self.adapter.data.range_change:

            data_op, keys = self.data.range_change

            if data_op == 'add':
                self.sorted_keys.extend(keys)
            elif data_op == 'delete':

                delete_affected_selection = False

                for selected_key in [sel.text for sel in self.selection]:
                    if selected_key in keys:
                        del self.selection[self.selection.index(selected_key)]
                        delete_affected_selection = True

                if delete_affected_selection:
                    self.dispatch('on_selection_change')

                self.check_for_empty_selection()

    def bind_triggers_to_view(self, func):
        self.bind(sorted_keys=func)
        self.bind(data=func)

    # self.data is paramount to self.sorted_keys. If sorted_keys is reset to
    # mismatch data, force a reset of sorted_keys to data.keys(). So, in order
    # to do a complete reset of data and sorted_keys, data must be reset
    # first, followed by a reset of sorted_keys, if needed.
    def initialize_sorted_keys(self, *args):
        stale_sorted_keys = False
        for key in self.sorted_keys:
            if not key in self.data:
                stale_sorted_keys = True
                break
        if stale_sorted_keys:
            self.sorted_keys = sorted(self.data.keys())
        self.delete_cache()
        self.initialize_selection()

    # Override ListAdapter.update_for_new_data().
    def update_for_new_data(self, *args):
        self.initialize_sorted_keys()

    # Note: this is not len(self.data).
    def get_count(self):
        return len(self.sorted_keys)

    def get_data_item(self, index):
        if index < 0 or index >= len(self.sorted_keys):
            return None
        return self.data[self.sorted_keys[index]]

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
