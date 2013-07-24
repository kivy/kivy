# TODO: In Python 3, UserDict.IterableUserDict class is
#       collections.UserDict. Conditional import needed?
from UserDict import IterableUserDict

from kivy.logger import Logger
from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty
from kivy.properties import ObservableDict


class DictOpInfo(object):

    def __init__(self, op_name, keys):
        self.op_name = op_name
        self.keys = keys


class RecordingObservableDict(EventDispatcher, IterableUserDict):
    '''This class is used as a cls argument to
    :class:`~kivy.properties.DictProperty` as an alternative to the default
    :class:`~kivy.properties.ObservableDict`.

    :class:`~kivy.adapters.list_ops.RecordingObservableDict` is used to record
    change info about a dict instance, in a more detailed, per-op manner than a
    :class:`~kivy.properties.ObservableDict` instance, which dispatches grossly
    for any change, but with no info about the change.

    Range-observing and granular (per op) data is stored in op_info for use by
    an observer.
    '''

    dp = ObjectProperty(None)
    owner = ObjectProperty(None)
    op_info = ObjectProperty(None)

    def __init__(self, *largs):
        # largs are:
        #
        #     DictProperty instance
        #     Owner instance (e.g., an adapter)
        #     value
        #
        super(RecordingObservableDict, self).__init__()
        self.dp = largs[0]
        self.owner = largs[1]
        self.data = largs[2]

    def __setitem__(self, key, value):

        if key in self.keys():
            op_info = DictOpInfo('ROD_setitem_set', (key, ))
        else:
            op_info = DictOpInfo('ROD_setitem_add', (key, ))
        self.data.__setitem__(key, value)
        self.op_info = op_info

    def __delitem__(self, key):
        self.data.__delitem__(key)
        self.op_info = DictOpInfo('ROD_delitem', (key, ))

    def clear(self, *largs):
        # Store a local copy of self, because the clear() will
        # remove everything, including it. Restore it after the clear.
        recorder = self
        self.data.clear(*largs)
        self = recorder
        self.op_info = DictOpInfo('ROD_clear', (None, ))

    def pop(self, *largs):
        key = largs[0]

        # This is pop on a specific key. If that key is absent, the second arg
        # is returned. If there is no second arg in that case, a key error is
        # raised. But the key is always largs[0], so store that.
        # s.pop([i]) is same as x = s[i]; del s[i]; return x
        result = self.data.pop(*largs)
        self.op_info = DictOpInfo('ROD_pop', (key, ))
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

        Logger.info('ROD: popitem, last = {0}'.format(last))

        if not self.keys():
            raise KeyError('dictionary is empty')

        key = next((self) if last else iter(self))

        Logger.info('ROD: popitem, key = {0}'.format(key))

        value = self[key]

        Logger.info('ROD: popitem, value = {0}'.format(value))

        # NOTE: We have no set to self.op_info for
        # ROD_popitem, because the following del self[key] will trigger a
        # ROD_delitem, which should suffice for the owning collection view
        # (e.g., ListView) to react as it would for ROD_popitem. If we set
        # self.op_info with ROD_popitem here, we get a
        # double-callback.
        del self[key]
        return key, value

    def setdefault(self, *largs):
        present_keys = self.keys()
        key = largs[0]
        op_info = None
        if not key in present_keys:
            op_info = DictOpInfo('ROD_setdefault', (key, ))
        result = self.data.setdefault(*largs)
        if op_info:
            self.op_info = op_info
        return result

    def update(self, *largs):
        op_info = None
        present_keys = self.keys()
        if present_keys:
            op_info = DictOpInfo(
                    'ROD_update',
                    list(set(largs[0].keys()) - set(present_keys)))
        self.data.update(*largs)
        if op_info:
            self.op_info = op_info

    # Expose this through the adapter.
    def insert(self, key, value):
        self.data.__setitem__(key, value)


class DictOpHandler(object):
    '''A :class:`DictOpHandler` reacts to the following operations that are
    possible for a RecordingObservableDict (ROD) instance in an adapter.

    Operations here are for a ROD dict, and also for a companion ROL list of
    keys.

    The following methods react to the dict operations possible:

        handle_setitem_set_op()

            ROD_setitem_set

        handle_delete_op()

            ROD_delitem
            ROD_pop
            ROD_popitem

        handle_clear_op()

            ROD_clear

        These methods adjust cached_views and selection for the adapter.
    '''

    def __init__(self, adapter, source_dict):

        self.adapter = adapter
        self.source_dict = source_dict

        super(DictOpHandler, self).__init__()

    def data_changed(self, *args):

        op_info = args[0].op_info

        # Do nothing on the reset by the owning collection view, such as
        # ListView, which happens at the conclusion of the op, after the user
        # interface adjustments are made by the collection view.
        if not op_info:
            return

        # Make a copy for more convenience access by observers.
        self.adapter.op_info = op_info

        op = op_info.op_name
        keys = op_info.keys

        # For add ops, ROD_setitem_add, ROD_setdefault, and ROD_update, we
        # only need to append or extend the sorted_keys (a ROL instance),
        # whose change will trigger a data changed callback.
        if op in ['ROD_setitem_add', 'ROD_setdefault', ]:
            self.adapter.sorted_keys.append(keys[0])
        if op == 'ROD_update':
            self.adapter.sorted_keys.extend(keys)

        Logger.info('DictAdapter: data_changed callback ' + str(op_info))

        if op in ['ROD_setitem_set', ]:

            # NOTE: handle_setitem_set_op() fires a data change dispatch.
            self.handle_setitem_set_op(keys[0])

        elif op in ['ROD_delitem',
                         'ROD_pop',
                         'ROD_popitem']:

            # NOTE: handle_delete_op() does not dispatch, because it changes
            #       self.adapter.sorted_keys, which will dispatch.
            self.handle_delete_op(keys)

        elif op == 'ROD_clear':

            # NOTE: handle_clear_op() does not dispatch, because it resets
            #       self.adapter.sorted_keys, which will dispatch.
            self.handle_clear_op()

    def handle_setitem_set_op(self, key):

        # Force a rebuild of the view for which data item has changed.
        # If the item was selected before, maintain the seletion.

        # We do not alter sorted_keys -- the key is the same, only the
        # value has changed. So, we must dispatch here.

        index = self.adapter.sorted_keys.index(key)

        is_selected = False
        if hasattr(self.adapter.cached_views[index], 'is_selected'):
            is_selected = self.adapter.cached_views[index].is_selected

        del self.adapter.cached_views[index]

        item_view = self.adapter.get_view(index)
        if is_selected:
            self.adapter.handle_selection(item_view)

        # Set start_index, end_index to the index.
        self.adapter.additional_op_info = (index, index)

        # Dispatch directly, because we did not change sorted_keys.
        self.adapter.dispatch('on_data_change')

    def handle_delete_op(self, keys):

        indices = [self.adapter.sorted_keys.index(k) for k in keys]

        start_index = min(indices)
        end_index = max(indices)

        self.adapter.additional_op_info = (start_index, end_index)

        # Trigger the data change callback (The event will fire from the
        # adapter, under control of the delegated list_op_handler).
        del self.adapter.sorted_keys[start_index:end_index + 1]

    def handle_clear_op(self):

        # Set start_index and end_index to full range (that was cleared).
        self.adapter.additional_op_info = (0, len(self.source_dict) - 1)

        self.adapter.cached_views.clear()
        self.adapter.selection = []

        # Trigger the data set callback, as above.
        self.adapter.sorted_keys.set([])
