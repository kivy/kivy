from kivy.logger import Logger
from kivy.properties import DictOpHandler


class AdapterDictOpHandler(DictOpHandler):
    ''':class:`~kivy.adapters.dict_ops.AdapterDictOpHandler` is a helper class
    for :class:`~kivy.adapters.dictadapter.DictAdapter`. It reacts to the
    operations listed below that are possible for a OpObservableDict
    (OOD) instance in an adapter.

    For :class:`~kivy.adapters.dictadapter.DictAdapter` the ops that could be
    considered misssing from this coverage are handled by a companion handler
    for sorted_keys (OOL) changes.

    The following methods here react to some of the dict operations possible:

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

    def __init__(self, source_dict):

        self.source_dict = source_dict

        super(AdapterDictOpHandler, self).__init__()

    def data_changed(self, *args):

        self.adapter = args[0]
        # TODO: args[1] is the modified dict -- utilize somehow?
        op_info = args[2]

        # Make a copy for more convenience access by observers.
        self.adapter.op_info = op_info

        op = op_info.op_name
        keys = op_info.keys

        # For add ops, OOD_setitem_add, OOD_setdefault, and OOD_update, we
        # only need to append or extend the sorted_keys (a OOL instance),
        # whose change will trigger a data changed callback.
        if op in ['OOD_setitem_add', 'OOD_setdefault', ]:
            self.adapter.sorted_keys.append(keys[0])
        if op == 'OOD_update':
            self.adapter.sorted_keys.extend(keys)

        Logger.info('DictAdapter: data_changed callback ' + str(op_info))

        if op in ['OOD_setitem_set', ]:

            # NOTE: handle_setitem_set_op() fires a data change dispatch.
            self.handle_setitem_set_op(keys[0])

        elif op in ['OOD_delitem',
                    'OOD_pop',
                    'OOD_popitem']:

            # NOTE: handle_delete_op() does not dispatch, because it changes
            #       self.adapter.sorted_keys, which will dispatch.
            self.handle_delete_op(keys)

        elif op == 'OOD_clear':

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
        self.adapter.sorted_keys = []
