from kivy.logger import Logger


class DictOpHandler(object):
    '''A :class:`DictOpHandler` reacts to the following operations that are
    possible for a ChangeRecordingObservableDict (crod) instance in an adapter.

    Operations here are for a CROD dict, and also for a companion CROL list of
    keys.

    The following methods react to the dict operations possible:

        handle_setitem_set_op()

            crod_setitem_set

        handle_delete_op()

            crod_setitem_del
            crod_delitem
            crod_pop
            crod_popitem

        handle_clear_op()

            crod_clear

        These methods adjust cached_views and selection for the adapter.
    '''

    def __init__(self, adapter, source_dict):

        self.adapter = adapter
        self.source_dict = source_dict

        super(DictOpHandler, self).__init__()

    def data_changed(self, *args):

        change_info = args[0].change_info

        # Do nothing on the reset by the owning collection view, such as
        # ListView, which happens at the conclusion of the op, after the user
        # interface adjustments are made by the collection view.
        if not change_info:
            return

        # Make a copy for more convenience access by observers.
        self.adapter.change_info = change_info

        data_op, keys = change_info

        # For add ops, crod_setitem_add, crod_setdefault, and crod_update, we
        # only need to append or extend the sorted_keys (a crol instance),
        # whose change will trigger a data changed callback.
        if data_op in ['crod_setitem_add', 'crod_setdefault', ]:
            self.adapter.sorted_keys.append(keys[0])
        if data_op == 'crod_update':
            self.adapter.sorted_keys.extend(keys)

        Logger.info('DictAdapter: data_changed callback ' + str(change_info))

        if data_op in ['crod_setitem_set', ]:

            # NOTE: handle_setitem_set_op() fires a data change dispatch.
            self.handle_setitem_set_op(keys[0])

        elif data_op in ['crod_setitem_del',
                         'crod_delitem',
                         'crod_pop',
                         'crod_popitem']:

            # NOTE: handle_delete_op() does not dispatch, because it changes
            #       self.adapter.sorted_keys, which will dispatch.
            self.handle_delete_op(keys)

        elif data_op == 'crod_clear':

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
        self.adapter.additional_change_info = (index, index)

        # Dispatch directly, because we did not change sorted_keys.
        self.adapter.dispatch('on_data_change')

    def handle_delete_op(self, keys):

        indices = [self.adapter.sorted_keys.index(k) for k in keys]

        start_index = min(indices)
        end_index = max(indices)

        self.adapter.additional_change_info = (start_index, end_index)

        # Trigger the data change callback (The event will fire from the
        # adapter, under control of the delegated list_op_handler).
        del self.adapter.sorted_keys[start_index:end_index + 1]

    def handle_clear_op(self):

        # Set start_index and end_index to full range (that was cleared).
        self.adapter.additional_change_info = (0, len(self.source_dict) - 1)

        self.adapter.cached_views.clear()
        self.adapter.selection = []

        # Trigger the data reset callback, as above.
        self.adapter.sorted_keys = []
