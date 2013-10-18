'''
dict_ops
========

.. versionadded:: 1.8

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

An :class:`~kivy.adapters.dict_ops.DictOpHandler` and
:class:`~kivy.adapters.dict_ops.DictOpInfo` are used in association with an
adapter, controller, or other Kivy object that needs to manage its own
DictProperty instances that use an OpObservableDict. A DictProperty of this
type dispatches on a per-op basis, requiring the handling of individual op
reactions.
'''
__all__ = ('DictOpHandler', 'DictOpInfo')

from kivy.properties import DictOpHandler
from kivy.properties import DictOpInfo


class AdapterDictOpHandler(DictOpHandler):
    ''':class:`~kivy.adapters.dict_ops.AdapterDictOpHandler` is a helper class
    for :class:`~kivy.adapters.dictadapter.DictAdapter`. It reacts to the
    operations listed below that are possible for a OpObservableDict
    (OOD) instance in an adapter.

    For :class:`~kivy.adapters.dictadapter.DictAdapter` the ops that could be
    considered misssing from this coverage are handled by a companion handler
    for sorted_keys (OOL) changes. Sometimes the decision is made here to
    change sorted_keys, and let that trigger a data changed event.

    The following methods here react to some of the dict operations possible:

        handle_set()

            OOD_set

        handle_setitem_set_op()

            OOD_setitem_set

        handle_delete_op()

            OOD_delitem
            OOD_pop
            OOD_popitem

        handle_clear_op()

            OOD_clear

        These methods adjust cached_views and selection for the adapter.
    '''

    def __init__(self):

        super(AdapterDictOpHandler, self).__init__()

    def data_changed(self, *args):

        self.adapter = args[0]

        # NOTE: args[1] is the modified dict.

        if len(args) == 3:
            op_info = args[2]
        else:
            op_info = DictOpInfo('OOD_set', (None, ))

        # Make a copy for more convenient access by observers.
        self.adapter.op_info = op_info

        op = op_info.op_name
        keys = op_info.keys

        if op == 'OOD_set':

            self.handle_set()

        elif op in ['OOD_setitem_add', 'OOD_setdefault', ]:

            self.handle_add_op(keys[0])

        elif op == 'OOD_update':

            self.handle_update_op(keys)

        elif op == 'OOD_setitem_set':

            self.handle_setitem_set_op(keys[0])

        elif op in ['OOD_delitem',
                    'OOD_pop',
                    'OOD_popitem']:

            self.handle_delete_op(keys)

        elif op == 'OOD_clear':

            self.handle_clear_op()

    def handle_set(self):

        # Will trigger a data set callback in sorted_keys, which will clear
        # the cache and (re)initialize selection:
        self.adapter.sorted_keys = self.adapter.data.keys()

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

    def handle_add_op(self, key):

        # For add ops, OOD_setitem_add, OOD_setdefault, and OOD_update, we
        # only need to append or extend the sorted_keys (a OOL instance),
        # whose change will trigger a data changed callback.
        self.adapter.sorted_keys.append(key)

    def handle_update_op(self, keys):

        self.adapter.sorted_keys.extend(keys)

    def handle_delete_op(self, keys):

        indices = [self.adapter.sorted_keys.index(k) for k in keys]

        start_index = min(indices)
        end_index = max(indices)

        self.adapter.additional_op_info = (start_index, end_index)

        # Do not dispatch here. Trigger the data change callback. The event
        # will fire from the adapter, under control of the delegated
        # list_op_handler. The cache will be cleared and selection
        # reinitialized.
        del self.adapter.sorted_keys[start_index:end_index + 1]

    def handle_clear_op(self):

        # The data has been cleared, so there is no meaningful length to set
        # here (len(self.data) would give the new data length). So, set (0, 0).
        self.adapter.additional_op_info = (0, 0)

        # Trigger the data set callback, as above.
        self.adapter.sorted_keys = []
