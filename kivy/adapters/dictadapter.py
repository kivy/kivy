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

from kivy.logger import Logger
from kivy.event import EventDispatcher
from kivy.properties import DictProperty
from kivy.properties import ListProperty
from kivy.properties import ObjectProperty
from kivy.properties import ObservableDict
from kivy.adapters.adapter import Adapter
from kivy.adapters.listadapter import ChangeRecordingObservableList
from kivy.adapters.list_op_handler import ListOpHandler


class DictChangeMonitor(EventDispatcher):
    '''The ChangeRecordingObservableList/Dict instances need to store change
    info without triggering a data_changed() callback themselves. Use this
    intermediary to hold change info for CROL and CROD observers.
    '''

    change_info = ObjectProperty(None, allownone=True)

    def __init__(self, *largs):
        super(DictChangeMonitor, self).__init__(*largs)


class ChangeRecordingObservableDict(ObservableDict):
    '''Adds range-observing and other intelligence to ObservableDict, storing
    change_info for use by an observer. The change_info is stored in an
    instance of ClassMonitor as an attr here (in this dict), so special
    handling in the overridden dict methods is needed, e.g. to keep
    class_monitor from being deleted, and to keep it out of keys() and
    iterators.
    '''

    def __init__(self, *largs):
        super(ChangeRecordingObservableDict, self).__init__(*largs)
        self.change_monitor = DictChangeMonitor()

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
        if attr in ('prop', 'obj'):
            super(ChangeRecordingObservableDict, self).__setattr__(attr, value)
            return
        self.__setitem__(attr, value)

    def __setitem__(self, key, value):

        if value is None:
            # ObservableDict will delete the item if value is None, so this is
            # like a delete op. __delitem__ gets called, so we will not set
            # self.change_monitor.change_info at the end of this method.
            change_info = ('crod_setitem_del', (key, ))
        else:
            if key in self.keys():
                change_info = ('crod_setitem_set', (key, ))
            else:
                change_info = ('crod_setitem_add', (key, ))
        super(ChangeRecordingObservableDict, self).__setitem__(key, value)
        if change_info[0] in ['crod_setitem_set', 'crod_setitem_add', ]:
            # Ignore if it is change_monitor itself being set.
            if key != 'change_monitor':
                self.change_monitor.change_info = change_info

    def __delitem__(self, key):
        # Protect change_monitor from deletion.
        if key == 'change_monitor':
            # TODO: Raise an exception?
            Logger.info('CROD: tried to delete change_monitor')
            return
        super(ChangeRecordingObservableDict, self).__delitem__(key)
        self.change_monitor.change_info = ('crod_delitem', (key, ))

    def clear(self, *largs):
        # Store a local copy of self.change_monitor, because the clear() will
        # remove everything, including it. Restore it after the clear.
        change_monitor = self.change_monitor
        super(ChangeRecordingObservableDict, self).clear(*largs)
        self.change_monitor = change_monitor
        self.change_monitor.change_info = ('crod_clear', (None, ))

    def pop(self, *largs):
        key = largs[0]

        # Protect change_monitor from deletion.
        if key == 'change_monitor':
            # TODO: Raise an exception?
            Logger.info('CROD: tried to pop change_monitor')
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

        Logger.info('CROD: popitem, last = {0}'.format(last))

        if not self.keys():
            raise KeyError('dictionary is empty')

        key = next((self) if last else iter(self))

        Logger.info('CROD: popitem, key = {0}'.format(key))

        if key == 'change_monitor':
            # TODO: Raise an exception?
            Logger.info('CROD: tried to popitem change_monitor')
            return

        value = self[key]

        Logger.info('CROD: popitem, value = {0}'.format(value))

        # NOTE: We have no set to self.change_monitor.change_info for
        # crod_popitem, because the following del self[key] will trigger a
        # crod_delitem, which should suffice for ListView to react as it would
        # for crod_popitem. If we set self.change_monitor.change_info with
        # crod_popitem here, we get a double-callback.
        del self[key]
        return key, value

    def setdefault(self, *largs):
        present_keys = self.keys()
        key = largs[0]
        change_info = None
        if not key in present_keys:
            change_info = ('crod_setdefault', (key, ))
        result = super(ChangeRecordingObservableDict, self).setdefault(*largs)
        if change_info:
            self.change_monitor.change_info = change_info
        return result

    def update(self, *largs):
        change_info = None
        present_keys = self.keys()
        if present_keys:
            change_info = (
                    'crod_update',
                    list(set(largs[0].keys()) - set(present_keys)))
        super(ChangeRecordingObservableDict, self).update(*largs)
        if change_info:
            self.change_monitor.change_info = change_info

    # Expose this through the adapter.
    def insert(self, key, value):
        super(ChangeRecordingObservableDict, self).__setitem__(key, value)


class DictAdapter(Adapter, EventDispatcher):
    '''A :class:`~kivy.adapters.dictadapter.DictAdapter` is an adapter around a
    python dictionary of records. It extends the list-like capabilities of
    the :class:`~kivy.adapters.listadapter.ListAdapter`.
    '''

    # TODO: Adapt to Python's OrderedDict?

    sorted_keys = ListProperty([], cls=ChangeRecordingObservableList)
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
        self.sorted_keys.change_monitor.bind(
                on_crol_change_info=self.list_op_handler.data_changed,
                on_crol_sort_started=self.list_op_handler.sort_started)

        # We handle data (ChangeRecordingObservableDict) changes here.
        self.data.change_monitor.bind(
                change_info=self.crod_data_changed)

    def sorted_keys_checked(self, sorted_keys, data_keys):

        # Remove any keys in sorted_keys that are not found in
        # self.data.keys(). This is the set intersection op (&).
        sorted_keys_checked = list(set(sorted_keys) & set(data_keys))

        # Maintain sort order of incoming sorted_keys.
        return [k for k in sorted_keys if k in sorted_keys_checked]

    # TODO: Document the reason for on_data_change and on_sorted_keys_change,
    #       instead of on_data and on_sorted_keys: These are peculiar to the
    #       adapters and their API (using and referring to change_info). This
    #       leaves on_data and on_sorted_keys still available for use in the
    #       "regular" manner, perhaps for some Kivy widgets, perhaps for
    #       custom widgets.

    def on_data_change(self, *args):
        '''Default data handler for on_data_change event.
        '''
        pass

    def insert(self, index, key, value):

        # This special insert() crod call only does a dict set (it does not
        # write change_info). We will let the sorted_keys insert trigger a
        # data change event.
        self.data.insert(key, value)

        self.sorted_keys.insert(index, key)

    def sorted_keys_changed(self, *args):
        '''This callback happens as a result of the direct sorted_keys binding
        set up in __init__(). It is needed for the direct set of sorted_keys,
        as happens in ...sorted_keys = [some new list], which is not picked up
        by the CROL data change system. We check by looking for a valid
        change_monitor that is created when CROL has fired. If not present, we
        know this call is from a direct sorted_keys set.
        '''

        if (hasattr(self.sorted_keys, 'change_monitor')
               and not self.sorted_keys.change_monitor.op_started):

            self.cached_views.clear()

            self.list_op_handler.source_list = self.sorted_keys

            self.sorted_keys.change_monitor.bind(
                on_crol_change_info=self.list_op_handler.data_changed,
                on_crol_sort_started=self.list_op_handler.sort_started)

            self.change_info = ('crol_reset', (0, 0))
            self.dispatch('on_data_change')

            self.initialize_selection()

    def crod_data_changed(self, *args):

        change_info = args[0].change_info

        # TODO: This is to solve a timing issue when running tests. Remove when
        #       no longer needed.
        if not change_info:
            #Clock.schedule_once(lambda dt: self.crod_data_changed(*args))
            return

        # Make a copy for more convenience access by observers.
        self.change_info = change_info

        data_op, keys = change_info

        # For add ops, crod_setitem_add, crod_setdefault, and crod_update, we
        # only need to append or extend sorted_keys, whose change will trigger
        # a data changed callback.
        if data_op in ['crod_setitem_add', 'crod_setdefault', ]:
            self.sorted_keys.append(keys[0])
        if data_op == 'crod_update':
            self.sorted_keys.extend(keys)

        Logger.info('DictAdapter: data_changed callback ' + str(change_info))

        if data_op in ['crod_setitem_set', ]:

            # Force a rebuild of the view for which data item has changed.
            # If the item was selected before, maintain the seletion.

            # We do not alter sorted_keys -- the key is the same, only the
            # value has changed. So, we must dispatch here.

            index = self.sorted_keys.index(keys[0])

            is_selected = False
            if hasattr(self.cached_views[index], 'is_selected'):
                is_selected = self.cached_views[index].is_selected

            del self.cached_views[index]

            item_view = self.get_view(index)
            if is_selected:
                self.handle_selection(item_view)

            # Set start_index, end_index to the index.
            self.additional_change_info = (index, index)

            # Dispatch directly, because we did not change sorted_keys.
            self.dispatch('on_data_change')

        elif data_op in ['crod_setitem_del',
                         'crod_delitem',
                         'crod_pop',
                         'crod_popitem']:

            indices = [self.sorted_keys.index(k) for k in keys]

            start_index = min(indices)
            end_index = max(indices)

            self.additional_change_info = (start_index, end_index)

            # Trigger the data change callback.
            del self.sorted_keys[start_index:end_index + 1]

        elif data_op == 'crod_clear':

            # Set start_index and end_index to full range (that was cleared).
            self.additional_change_info = (0, len(self.data) - 1)

            self.cached_views.clear()
            self.selection = []

            # Trigger the data reset callback.
            self.sorted_keys = []

    # NOTE: This is not len(self.data).
    # TODO: Recheck this in light of new approach with crol, crod.
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
