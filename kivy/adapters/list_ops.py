from kivy.logger import Logger
from kivy.ops_properties import ListOpHandler


class AdapterListOpHandler(ListOpHandler):
    ''':class:`~kivy.adapters.list_ops.AdapterListOpHandler` is a helper class
    for :class:`~kivy.adapters.listadapter.ListAdapter`. It reacts to the
    following operations that are possible for a RecordingObservableList (ROL)
    instance in an adapter:

        handle_add_first_item_op()

            ROL_append
            ROL_extend
            ROL_insert

        handle_add_op()

            ROL_append
            ROL_extend
            ROL_iadd
            ROL_imul

        handle_insert_op()

            ROL_insert

        handle_setitem_op()

            ROL_setitem

        handle_setslice_op()

            ROL_setslice

        handle_delete_op()

            ROL_delitem
            ROL_delslice
            ROL_remove
            ROL_pop

        handle_sort_op()

            ROL_sort
            ROL_reverse

        These methods adjust cached_views and selection for the adapter.
    '''

    # TODO: Document that, e.g., self.adapter.sorted_keys = [] is not covered,
    #       and a call to, e.g., self.adapter.sorted_keys.set([]) is required.

    def __init__(self, adapter, source_list, duplicates_allowed):

        self.adapter = adapter
        self.source_list = source_list
        self.duplicates_allowed = duplicates_allowed

        super(AdapterListOpHandler, self).__init__()

    def data_changed(self, *args):

        op_info = args[0].op_info

        # TODO: This is to solve a timing issue when running tests. Remove when
        #       no longer needed.
        if not op_info:
            #Clock.schedule_once(lambda dt: self.data_changed(*args))
            return

        # Make a copy in the adapter for more convenient access by observers.
        self.adapter.op_info = op_info

        Logger.info(('ListAdapter: '
                     'ROL data_changed callback ') + str(op_info))

        op = op_info.op_name
        start_index = op_info.start_index
        end_index = op_info.end_index

        if op == 'ROL_set':

            self.handle_set()

        elif (len(self.source_list) == 1
                and op in ['ROL_append',
                           'ROL_insert',
                           'ROL_extend']):

            self.handle_add_first_item_op()

        else:

            if op in ['ROL_iadd',
                      'ROL_imul',
                      'ROL_append',
                      'ROL_extend']:

                self.handle_add_op()

            elif op in ['ROL_setitem']:

                self.handle_setitem_op(start_index)

            elif op in ['ROL_setslice']:

                self.handle_setslice_op(start_index, end_index)

            elif op in ['ROL_insert']:

                self.handle_insert_op(start_index)

            elif op in ['ROL_delitem',
                        'ROL_delslice',
                        'ROL_remove',
                        'ROL_pop']:

                self.handle_delete_op(start_index, end_index)

            elif op in ['ROL_sort',
                        'ROL_reverse']:

                self.handle_sort_op()

            else:

                Logger.info(('ListOpHandler: '
                             'ROL data_changed callback, uncovered op ')
                                 + str(op))

        self.adapter.dispatch('on_data_change')

    def handle_set(self):

        self.adapter.cached_views.clear()
        self.adapter.initialize_selection()

    def handle_add_first_item_op(self):
        '''Special case: deletion resulted in no data, leading up to the
        present op, which adds one or more items. Cached views should
        have already been treated.  Call check_for_empty_selection()
        to re-establish selection if needed.
        '''

        self.adapter.check_for_empty_selection()

    def handle_add_op(self):
        '''An item was added to the end of the list. This shouldn't affect
        anything here, as cached_views items can be built as needed through
        normal get_view() calls to build views for the added items.
        '''
        pass

    def handle_insert_op(self, index):
        '''An item was added at index. Adjust the indices of any cached_view
        items affected.
        '''

        new_cached_views = {}

        for k, v in self.adapter.cached_views.iteritems():

            if k < index:
                new_cached_views[k] = self.adapter.cached_views[k]
            else:
                new_cached_views[k + 1] = self.adapter.cached_views[k]
                new_cached_views[k + 1].index += 1

        self.adapter.cached_views = new_cached_views

    def handle_setitem_op(self, index):
        '''Force a rebuild of the item view for which the associated data item
        has changed.  If the item view was selected before, maintain the
        selection.
        '''

        is_selected = False
        if hasattr(self.adapter.cached_views[index], 'is_selected'):
            is_selected = self.adapter.cached_views[index].is_selected

        del self.adapter.cached_views[index]
        item_view = self.adapter.get_view(index)
        if is_selected:
            self.adapter.handle_selection(item_view)

    def handle_setslice_op(self, start_index, end_index):
        '''Force a rebuild of item views for which data items have changed.
        Although it is hard to guess what might be preferred, a "positional"
        priority for selection is observed here, where the indices of selected
        item views is maintained. We call check_for_empty_selection() if no
        selection remains after the op.
        '''

        changed_indices = range(start_index, end_index + 1)

        is_selected_indices = []
        for i in changed_indices:
            item_view = self.adapter.cached_views[i]
            if hasattr(item_view, 'is_selected'):
                if item_view.is_selected:
                    is_selected_indices.append(i)

        for i in changed_indices:
            del self.adapter.cached_views[i]

        for i in changed_indices:
            item_view = self.adapter.get_view(i)
            if item_view.index in is_selected_indices:
                self.adapter.handle_selection(item_view)

        # Remove deleted views from selection.
        #for selected_index in [item.index for item in self.adapter.selection]:
        for sel in self.adapter.selection:
            if sel.index in changed_indices:
                self.adapter.selection.remove(sel)

        # Do a check_for_empty_selection type step, if data remains.
        if (len(self.source_list) > 0
                and not self.adapter.selection
                and not self.adapter.allow_empty_selection):
            # Find a good index to select, if the deletion results in
            # no selection, which is common, as the selected item is
            # often the one deleted.
            if start_index < len(self.source_list):
                new_sel_index = start_index
            else:
                new_sel_index = start_index - 1
            v = self.adapter.get_view(new_sel_index)
            if v is not None:
                self.adapter.handle_selection(v)

    def handle_delete_op(self, start_index, end_index):
        '''An item has been deleted. Reset the index for item views affected.
        '''

        deleted_indices = range(start_index, end_index + 1)

        # Delete views from cache.
        new_cached_views = {}

        i = 0
        for k, v in self.adapter.cached_views.iteritems():
            if not k in deleted_indices:
                new_cached_views[i] = self.adapter.cached_views[k]
                if k >= start_index:
                    new_cached_views[i].index = i
                i += 1

        self.adapter.cached_views = new_cached_views

        # Remove deleted views from selection.
        #for selected_index in [item.index for item in self.adapter.selection]:
        for sel in self.adapter.selection:
            if sel.index in deleted_indices:
                self.adapter.selection.remove(sel)

        # Do a check_for_empty_selection type step, if data remains.
        if (len(self.source_list) > 0
                and not self.adapter.selection
                and not self.adapter.allow_empty_selection):
            # Find a good index to select, if the deletion results in
            # no selection, which is common, as the selected item is
            # often the one deleted.
            if start_index < len(self.source_list):
                new_sel_index = start_index
            else:
                new_sel_index = start_index - 1
            v = self.adapter.get_view(new_sel_index)
            if v is not None:
                self.adapter.handle_selection(v)

    def sort_started(self, *args):

        # Save a pre-sort order, and position detail, if there are duplicates
        # of strings.
        presort_indices_and_items = {}

        if self.duplicates_allowed:
            for i in self.adapter.cached_views:
                data_item = self.source_list[i]
                if isinstance(data_item, str):
                    duplicates = \
                            sorted([j for j, s in enumerate(self.source_list)
                                                 if s == data_item])
                    pos_in_instances = duplicates.index(i)
                else:
                    pos_in_instances = 0

                presort_indices_and_items[i] = \
                            {'data_item': data_item,
                             'pos_in_instances': pos_in_instances}
        else:
            for i in self.adapter.cached_views:
                data_item = self.source_list[i]
                pos_in_instances = 0
                presort_indices_and_items[i] = \
                            {'data_item': data_item,
                             'pos_in_instances': pos_in_instances}

        self.source_list.presort_indices_and_items = \
                presort_indices_and_items

        self.source_list.finish_sort_op()

    def handle_sort_op(self):
        '''Data has been sorted or reversed. Use the pre-sort information about
        previous ordering, stored in the associated ChangeMonitor instance, to
        reset the index of each cached item view, instead of deleting
        cached_views entirely.
        '''

        presort_indices_and_items = \
                self.source_list.presort_indices_and_items

        # We have an association of presort indices with data items.
        # Where is each data item after sort? Change the index of the
        # item_view to match present position.
        new_cached_views = {}

        if self.duplicates_allowed:
            for i in self.adapter.cached_views:
                item_view = self.adapter.cached_views[i]
                old_i = item_view.index
                data_item = presort_indices_and_items[old_i]['data_item']
                if isinstance(data_item, str):
                    duplicates = sorted(
                        [j for j, s in enumerate(self.source_list)
                                if s == data_item])
                    pos_in_instances = \
                        presort_indices_and_items[old_i]['pos_in_instances']
                    postsort_index = duplicates[pos_in_instances]
                else:
                    postsort_index = self.source_list.index(data_item)
                item_view.index = postsort_index
                new_cached_views[postsort_index] = item_view
        else:
            for i in self.adapter.cached_views:
                item_view = self.adapter.cached_views[i]
                old_i = item_view.index
                data_item = presort_indices_and_items[old_i]['data_item']
                postsort_index = self.source_list.index(data_item)
                item_view.index = postsort_index
                new_cached_views[postsort_index] = item_view

        self.adapter.cached_views = new_cached_views

        # Clear temporary storage.
        self.source_list.presort_indices_and_items.clear()
