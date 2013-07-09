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

from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import DictProperty
from kivy.properties import ListProperty
from kivy.properties import ObjectProperty
from kivy.properties import ObservableDict
from kivy.adapters.listadapter import ChangeMonitor
from kivy.adapters.listadapter import ListAdapter
from kivy.adapters.listadapter import ChangeRecordingObservableList


class ChangeRecordingObservableDict(ObservableDict):
    '''Adds range-observing and other intelligence to ObservableDict, storing
    change_info for use by an observer. The change_info is stored in an
    instance of ClassMonitor as an attr here (in this dict), so special
    handling in the overridden dict methods is needed, e.g. to keep
    class_monitor from being deleted, and to keep it out of keys() and
    iterators.
    '''

    def __init__(self, *largs):
        self.change_monitor = ChangeMonitor()
        super(ChangeRecordingObservableDict, self).__init__(*largs)

    def __len__(self, *largs):
        # We should always have our own change_monitor to remove from len
        # calculation. Our self.keys() takes care of that, so use it for len.
        return len(self.keys())

    def keys(self, *largs):
        # Do not include change_monitor.
        keys = super(ChangeRecordingObservableDict, self).keys(*largs)
        return list(set(keys) - set(['change_monitor', ]))

    # As for __len__() and keys(), omit our change_monitor instance in other
    # iterating methods. Use our own self.keys() in these:

    def __iter__(self, *largs):
        return iter(self.keys())

    def values(self):
        return [self[key] for key in self.keys()]

    def items(self):
        return [(key, self[key]) for key in self.keys()]

    def iterkeys(self):
        return iter(self.keys())

    def itervalues(self):
        return (self[key] for key in self.keys())

    def iteritems(self):
        for k in self.keys():
            yield (k, self[k])

    def __setattr__(self, attr, value):
        if attr in ('prop', 'obj', 'change_monitor'):
            super(ChangeRecordingObservableDict, self).__setattr__(attr, value)
            if not attr == 'change_monitor':
                self.change_monitor.change_info = ('crod_setattr', (attr, ))
            return
        super(ChangeRecordingObservableDict, self).__setitem__(attr, value)

    def __setitem__(self, key, value):
        if value is None:
            # ObservableDict will delete the item if value is None, so this is
            # like a delete op. __delitem__ gets called, so we will not set
            # self.change_monitor.change_info at the end of this method.
            change_info = ('crod_setitem_del', (key, ))
        else:
            if key in self:
                change_info = ('crod_setitem_set', (key, ))
            else:
                change_info = ('crod_setitem_add', (key, ))
        super(ChangeRecordingObservableDict, self).__setitem__(key, value)
        if change_info[0] in ['crod_setitem_set', 'crod_setitem_add', ]:
            self.change_monitor.change_info = change_info

    def __delitem__(self, key):
        # Protect change_monitor from deletion.
        if key == 'change_monitor':
            # TODO: Raise an exception?
            print 'tried to delete change_monitor'
            return
        super(ChangeRecordingObservableDict, self).__delitem__(key)
        self.change_monitor.change_info = ('crod_delitem', (key, ))

    def clear(self, *largs):
        # We have to call first on this one, because the clear() will remove
        # everything, including our self.change_monitor. The change_monitor
        # will be reset from the adapter after the clear().
        self.change_monitor.change_info = ('crod_clear', (None, ))
        super(ChangeRecordingObservableDict, self).clear(*largs)

    def pop(self, *largs):
        key = largs[0]

        # Protect change_monitor from deletion.
        if key == 'change_monitor':
            # TODO: Raise an exception?
            print 'tried to pop change_monitor'
            return

        # This is pop on a specific key. If that key is absent, the second arg
        # is returned. If there is no second arg in that case, a key error is
        # raised. But the key is always largs[0], so store that.
        # s.pop([i]) is same as x = s[i]; del s[i]; return x
        result = super(ChangeRecordingObservableDict, self).pop(*largs)
        self.change_monitor.change_info = ('crod_pop', (key, ))
        return result

    def popitem(self, *largs):
        # From python docs, "Remove and return an arbitrary (key, value) pair
        # from the dictionary." From other reading, arbitrary here effectively
        # means "random" in the loose sense, of removing on the basis of how
        # items are stored internally as links -- for truely random ops, use
        # the proper random module. Nevertheless, the item is deleted and
        # returned.  If the dict is empty, a key error is raised.

        last = None
        if len(largs):
            last = largs[0]

        if not self.keys():
            raise KeyError('dictionary is empty')

        key = next((self) if last else iter(self))

        if key == 'change_monitor':
            # TODO: Raise an exception?
            print 'tried to popitem change_monitor'
            return

        value = self[key]

        # NOTE: We have no set to self.change_monitor.change_info for
        # crod_popitem, because the following del self[key] will trigger a
        # crod_delitem, which should suffice for ListView to react as it would
        # for crod_popitem. If we set self.change_monitor.change_info with
        # crod_popitem here, we get a double-callback.
        del self[key]
        return key, value

    def setdefault(self, *largs):
        present_keys = super(ChangeRecordingObservableDict, self).keys()
        key = largs[0]
        change_info = None
        if not key in present_keys:
            change_info = ('crod_setdefault', (key, ))
        super(ChangeRecordingObservableDict, self).setdefault(*largs)
        if change_info:
            self.change_monitor.change_info = change_info

    def update(self, *largs):
        change_info = None
        present_keys = self.keys()
        if present_keys:
            change_info = ('crod_update', list(set(largs) - set(present_keys)))
        super(ChangeRecordingObservableDict, self).update(*largs)
        if change_info:
            self.change_monitor.change_info = change_info


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

    data = DictProperty({}, cls=ChangeRecordingObservableDict)
    '''A dict that indexes records by keys that are equivalent to the keys in
    sorted_keys, or they are a superset of the keys in sorted_keys.

    TODO: Is that last statement about "superset" correct?

    The values can be strings, class instances, dicts, etc.

    :data:`data` is a :class:`~kivy.properties.DictProperty` and defaults
    to None.
    '''

    __events__ = ('on_data_change', )

    def __init__(self, **kwargs):
        if 'sorted_keys' in kwargs:
            if type(kwargs['sorted_keys']) not in (tuple, list):
                msg = 'DictAdapter: sorted_keys must be tuple or list'
                raise Exception(msg)
            else:
                # Copy the provided sorted_keys, and maintain it internally.
                # The only function in the API for sorted_keys is to reset it
                # wholesale with a call to reset_sorted_keys().
                self.sorted_keys = list(kwargs.pop('sorted_keys'))
        else:
            self.sorted_keys = sorted(kwargs['data'].keys())

        super(DictAdapter, self).__init__(**kwargs)

        # Bind to the ChangeRecordingObservableDict's change_monitor.
        self.data.change_monitor.bind(on_change_info=self.crod_data_changed)

    def on_data_change(self, *args):
        '''Default data handler for on_data_change event.
        '''
        pass

    # TODO: If the desired action is inserting an item at a particular index,
    #       as in the typical case, it is too expensive to reset the entire
    #       sorted_keys. We could add a special method to DictAdapter that
    #       takes a key, value pair and an index, and in there do what is
    #       needed, as would happen for a crol_insert op.
    def reset_sorted_keys(self, sorted_keys):
        self.sorted_keys = sorted_keys
        # TODO: call update on dict to match?

    def crod_data_changed(self, *args):

        change_info = args[0].change_info

        # TODO: This is to solve a timing issue when running tests. Remove when
        #       no longer needed.
        if not change_info:
            Clock.schedule_once(lambda dt: self.crod_data_changed(*args))
            return

        data_op, keys = change_info

        if data_op == 'crod_clear':

            # Reset the change_monitor, because the clear() removed it and
            # everything else.
            self.data.change_monitor = ChangeMonitor()
            self.data.change_monitor.bind(on_change_info=self.crod_data_changed)

            # Empty all our things.
            self.sorted_keys = []
            self.selection = []
            self.delete_cache()

            # Set indices to full range (that was cleared).
            self.additional_change_info = (0, len(self.data) - 1)

            self.dispatch('on_data_change')
            return

        if data_op == 'crod_setitem_add':
            self.sorted_keys.append(keys[0])

        indices = [self.sorted_keys.index(k) for k in keys]

        start_index = min(indices)
        end_index = max(indices)

        # Add start_index and end_index to change_info, because by the time
        # data_changed() in ListView is called, we may have changed
        # sorted_keys, cached_views, and selection.
        self.additional_change_info = (start_index, end_index)

        print 'DICT ADAPTER crod_data_changed callback', change_info

        # TODO: -1 because change_monitor attr included in self.data!!!
        #       NOTE: This is not the case for CROL.
        len_self_data = len(self.data) - 1

        if len_self_data == 1 and data_op in ['crod_setitem_add',
                                              'crod_setdefault',
                                              'crod_update']:
            # Special case: deletion resulted in no data, leading up to the
            # present op, which adds one or more items. Cached views should
            # have already been treated.  Call check_for_empty_selection()
            # to re-establish selection if needed.
            self.check_for_empty_selection()

            # Dispatch for ListView.
            self.dispatch('on_data_change')

            return

        if data_op == 'crod_setattr':

            # TODO: If keys[0] is 'prop' or 'obj' the superclass of crod
            #       was called. Otherwise, it was the crod. What to do?
            pass

        elif data_op in ['crod_setitem_add', ]:

            # We have already added the key to sorted_keys, above.
            pass

        elif data_op in ['crod_setitem_set', ]:

            # Force a rebuild of the view for which data item has changed.
            # If the item was selected before, maintain the seletion.

            index = self.sorted_keys.index(keys[0])

            is_selected = False
            if hasattr(self.cached_views[index], 'is_selected'):
                is_selected = self.cached_views[index].is_selected

            del self.cached_views[index]

            item_view = self.get_view(index)
            if is_selected:
                self.handle_selection(item_view)

        elif data_op in ['crod_setitem_del',
                         'crod_delitem',
                         'crod_clear',
                         'crod_pop',
                         'crod_popitem']:

            deleted_indices = [self.sorted_keys.index(k) for k in keys]

            start_index = min(deleted_indices)

            # Delete keys from sorted_keys.
            # TODO: another way: del at min index * len(deleted_indices) ?
            for i in reversed(sorted(deleted_indices)):
                del self.sorted_keys[i]

            # Delete views from cache.
            new_cached_views = {}

            i = 0
            for k, v in self.cached_views.iteritems():
                if not k in deleted_indices:
                    new_cached_views[i] = self.cached_views[k]
                    if k >= start_index:
                        new_cached_views[i].index = i
                    i += 1

            self.cached_views = new_cached_views

            # Handle selection.
            for sel in self.selection:
                if sel.index in deleted_indices:
                    self.selection.remove(sel)

            # Do a check_for_empty_selection type step, if data remains.
            if (len_self_data > 0
                    and not self.selection
                    and not self.allow_empty_selection):
                # Find a good index to select, if the deletion results in
                # no selection, which is common, as the selected item is
                # often the one deleted.
                if start_index < len_self_data:
                    new_sel_index = start_index
                else:
                    new_sel_index = len_self_data - 1
                print 'new_sel_index', new_sel_index
                print 'len_self_data)', len_self_data
                print 'len(self.sorted_keys)', len(self.sorted_keys)
                v = self.get_view(new_sel_index)
                if v is not None:
                    print 'handling sel for', v.text
                    self.handle_selection(v)

        # Dispatch for ListView.
        self.dispatch('on_data_change')

    # TODO: No longer used. Backwards compatibility issue? At least provide
    #       migration instructions?
    def bind_triggers_to_view(self, func):
        self.bind(sorted_keys=func)
        self.bind(data=func)

    # self.data is paramount to self.sorted_keys. If sorted_keys is reset to
    # mismatch data, force a reset of sorted_keys to data.keys(). So, in order
    # to do a complete reset of data and sorted_keys, data must be reset
    # first, followed by a reset of sorted_keys, if needed.
    #
    # UPDATE: For crol and crod (data changed) development, the binding to this
    #         method has been removed, because sorted_keys needs to be updated
    #         and managed internally. For example if an item is deleted, its
    #         key in sorted_keys is removed, but other reactions, such as
    #         deleting cache items and updating selection are done in the crod
    #         code -- the code here would interfere.
    #
    #         TODO: Delete this method?
    #
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

    # TODO: It might be nice to return (key, data_item). Is this a good idea?
    #       There would be a backwards compatibility issue. If needed, make
    #       this the default function, and add a new one? Then later deprecate?
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
