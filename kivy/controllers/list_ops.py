'''
List Ops
--------

The ControllerListOpHandler class is a helper to ListController, serving to
handle adjustments to selection after operations on the data list happen.

Compare to AdapterListOpHandler, which performs a similar role for ListAdapter,
with the additional responsibility for managing cached_views.

.. versionadded 1.8

'''

from kivy.properties import ListOpHandler
from kivy.properties import ListOpInfo


class ControllerListOpHandler(ListOpHandler):
    '''This class is a helper class for
    :class:`~kivy.controllers.listcontroller.ListController`. It reacts to the
    following operations that are possible for an OpObservableList (OOL)
    instance in a controller:

        handle_add_first_item_op()

            OOL_append
            OOL_extend
            OOL_insert

        handle_add_op()

            OOL_append
            OOL_extend
            OOL_iadd
            OOL_imul

        handle_insert_op()

            OOL_insert

        handle_setitem_op()

            OOL_setitem

        handle_setslice_op()

            OOL_setslice

        handle_delete_op()

            OOL_delitem
            OOL_delslice
            OOL_remove
            OOL_pop

        handle_sort_op()

            OOL_sort
            OOL_reverse

        These methods adjust selection for the controller.
    '''

    def __init__(self, source_list, duplicates_allowed):

        self.source_list = source_list
        self.duplicates_allowed = duplicates_allowed

        super(ControllerListOpHandler, self).__init__()

    def data_changed(self, *args):

        self.controller = args[0]
        # TODO: args[1] is the modified list -- can utilize?
        if len(args) == 3:
            op_info = args[2]
        else:
            op_info = ListOpInfo('OOL_set', 0, 0)

        # Make a copy in the controller for more convenient access by
        # observers.
        self.controller.op_info = op_info

        op = op_info.op_name
        start_index = op_info.start_index
        end_index = op_info.end_index

        if op == 'OOL_sort_start':
            self.sort_started(*args)

        if op == 'OOL_set':

            self.handle_set()

        elif (len(self.source_list) == 1
                and op in ['OOL_append',
                           'OOL_insert',
                           'OOL_extend']):

            self.handle_add_first_item_op()

        else:

            if op in ['OOL_iadd',
                      'OOL_imul',
                      'OOL_append',
                      'OOL_extend']:

                self.handle_add_op()

            elif op in ['OOL_setitem']:

                self.handle_setitem_op(start_index)

            elif op in ['OOL_setslice']:

                self.handle_setslice_op(start_index, end_index)

            elif op in ['OOL_insert']:

                self.handle_insert_op(start_index)

            elif op in ['OOL_delitem',
                        'OOL_delslice',
                        'OOL_remove',
                        'OOL_pop']:

                self.handle_delete_op(start_index, end_index)

            elif op in ['OOL_sort',
                        'OOL_reverse']:

                self.handle_sort_op()

        self.controller.dispatch('on_data_change')

    def handle_set(self):

        self.controller.initialize_selection()

    def handle_add_first_item_op(self):
        '''Special case: deletion resulted in no data, leading up to the
        present op, which adds one or more items.  Call
        check_for_empty_selection() to re-establish selection if needed.
        '''

        self.controller.check_for_empty_selection()

    def handle_add_op(self):
        '''An item was added to the end of the list. This shouldn't affect
        anything here.
        '''
        pass

    def handle_insert_op(self, index):
        '''An item was added at index. No effect anticipated.
        '''
        pass

    def handle_setitem_op(self, index):
        '''If the item view was selected before, maintain the
        selection.
        '''

        self.controller.check_for_empty_selection()

    def handle_setslice_op(self, start_index, end_index):
        '''Although it is hard to guess what might be preferred, a "positional"
        priority for selection is observed here, where the indices of selected
        item views is maintained. We so something similar to
        check_for_empty_selection() if no selection remains after the op.
        '''

        changed_indices = range(start_index, end_index + 1)

        # Remove deleted views from selection.
        # for selected_index in
        #     [item.index for item in self.controller.selection]:
        for sel in self.controller.selection:
            if sel.index in changed_indices:
                self.controller.selection.remove(sel)

        # Do a check_for_empty_selection type step, if data remains.
        if (len(self.source_list) > 0
                and not self.controller.selection
                and not self.controller.allow_empty_selection):
            # Find a good index to select, if the deletion results in
            # no selection, which is common, as the selected item is
            # often the one deleted.
            if start_index < len(self.source_list):
                new_sel_index = start_index
            else:
                new_sel_index = start_index - 1
            item = self.controller.get_selectable_item(new_sel_index)
            if item is not None:
                self.controller.handle_selection(item)

    def handle_delete_op(self, start_index, end_index):
        '''An item has been deleted. Reset selection.
        '''

        deleted_indices = range(start_index, end_index + 1)

        # Remove deleted views from selection.
        # for selected_index in
        #     [item.index for item in self.controller.selection]:
        for sel in self.controller.selection:
            if sel.index in deleted_indices:
                self.controller.selection.remove(sel)

        # Do a check_for_empty_selection type step, if data remains.
        if (len(self.source_list) > 0
                and not self.controller.selection
                and not self.controller.allow_empty_selection):
            # Find a good index to select, if the deletion results in
            # no selection, which is common, as the selected item is
            # often the one deleted.
            if start_index < len(self.source_list):
                new_sel_index = start_index
            else:
                new_sel_index = start_index - 1
            item = self.controller.get_selectable_item(new_sel_index)
            if item is not None:
                self.controller.handle_selection(item)

    def sort_started(self, *args):

        # Save a pre-sort order, and position detail, if there are duplicates
        # of strings.
        self.presort_indices_and_items = {}

        # Not yet implemented. See adapters/list_ops.py for inspiration.

        self.source_list.finish_sort_op()

    def handle_sort_op(self):
        '''Data has been sorted or reversed. Use the pre-sort information about
        previous ordering, stored in the associated op_info instance.
        '''

        presort_indices_and_items = self.presort_indices_and_items

        # We have an association of presort indices with data items.
        # Where is each data item after sort? Change the index of the
        # item to match present position.

        # Not yet implemented. See adapters/list_ops.py for inspiration.

        # Clear temporary storage.
        self.presort_indices_and_items.clear()
