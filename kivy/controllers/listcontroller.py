'''
ListController
--------------

The ListController class defines data as a ListProperty that uses the
OpObservableList class internally.

List controllers are general purpose data containers that have the benefit of
Kivy properties and bindings.

Methods in list controllers can do filtering of the data for convenience and
efficiency. Using such methods, an API for the list data can be constructed.

List controllers can be used in combination, with bindings between their data
and/or selection properties. Another common use is to have an ObjectController
hold the single selection from a ListController.

.. versionadded:: 1.8

'''

from kivy.binding import DataBinding
from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty
from kivy.properties import OpObservableList
from kivy.properties import ListOpInfo
from kivy.properties import ListProperty
from kivy.selection import Selection

__all__ = ('ListController', )


class ListController(Selection, EventDispatcher):

    data = ListProperty([], cls=OpObservableList)

    data_binding = ObjectProperty(None, allownone=True)

    # TODO: Add arranged_data, as a proxy to data that honors the sort rules
    #       given in an order_by func that sorts on chosen properties and
    #       orders. Perhaps this can be:
    #
    #           order_by = ObjectProperty(None)
    #
    #           arranged_data = TransformProperty(
    #                   subject='data',
    #                   op=binding_transforms.TRANSFORM,
    #                   transform=order_by)
    #

    __events__ = ('on_data_change', )

    def __init__(self, **kwargs):

        if 'data_binding' not in kwargs:
            kwargs['data_binding'] = DataBinding()

        super(ListController, self).__init__(**kwargs)

        self.data_binding.bind_to(self, 'data')
        self.bind(data=self.data_changed)

    # TODO: Get rid of this event, and just relying on observing data?
    def on_data_change(self, *args):
        '''on_data_change() is the default handler for the on_data_change
        event.
        '''
        pass

    def get_count(self):
        return len(self.data)

    def get_selectable_item(self, index):

        if not self.data:
            return None

        if index < 0 or index > len(self.data) - 1:
            return None

        return self.data[index]

    def update(self, *args):
        # args:
        #
        #     controller args[0]
        #     value      args[1]
        #     op_info    args[2]

        value = args[1]

        if isinstance(value, list):
            self.data = value
        else:
            if value:
                self.data = [value]

    #################################
    # FILTERS and ALIAS PROPERTIES

    def all(self):
        return self.data

    def reversed(self):
        return reversed(self.data)

    def first(self):
        return self.data[0]

    def last(self):
        return self.data[-1]

    def add(self, item):
        self.data.append(item)

    def delete(self, item):
        self.data.remove(item)

    def sorted(self):
        return sorted(self.data)

    # TODO: There can also be an order_by or other aid for sorting.

    # TODO: Add examples of filtering and alias properties in
    #       examples/controllers/.

    def trim_left_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are less than the
        index of the first selected item if there is a selection.
        '''
        selection = self.selection
        if len(selection) > 0:
            first_sel_index = \
                    min([self.data.index(sel) for sel in selection])
            self.data = self.data[first_sel_index:]

    def trim_right_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are greater than
        the index of the last selected item if there is a selection.
        '''
        selection = self.selection
        if len(selection) > 0:
            last_sel_index = \
                    max([self.data.index(sel) for sel in selection])
            self.data = self.data[:last_sel_index + 1]

    def trim_to_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are les than or
        greater than the index of the last selected item if there is a
        selection. This preserves intervening list items within the selected
        range.
        '''
        selection = self.selection
        if len(selection) > 0:
            sel_indices = [self.data.index(sel) for sel in selection]
            first_sel_index = min(sel_indices)
            last_sel_index = max(sel_indices)
            self.data = self.data[first_sel_index:last_sel_index + 1]

    def cut_to_sel(self, *args):
        '''Same as trim_to_sel, but intervening list items within the selected
        range are also cut, leaving only list items that are selected.
        '''
        selection = self.selection
        if len(selection) > 0:
            self.data = selection

    def data_changed(self, *args):
        '''This method reacts following operations that are possible for an
        OpObservableList (OOL) instance in a controller:

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

        if not hasattr(self.data, 'op_change_info'):
            op_info = ListOpInfo('OOL_set', 0, 0)
        else:
            op_info = self.data.op_change_info

            if not op_info:
                op_info = ListOpInfo('OOL_set', 0, 0)

        # Make a copy in the controller for more convenient access by
        # observers.
        self.data_op_info = op_info

        op = op_info.op_name
        start_index = op_info.start_index
        end_index = op_info.end_index

        print 'ListController op', op

        if op == 'OOL_sort_start':

            self.sort_started(*args)

        if op == 'OOL_set':

            self.handle_set()

        elif (len(self.data) == 1
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

        self.dispatch('on_data_change')

    def handle_set(self):

        if not self.selection_binding:
            self.initialize_selection()

    def handle_add_first_item_op(self):
        '''Special case: deletion resulted in no data, leading up to the
        present op, which adds one or more items.  Call
        check_for_empty_selection() to re-establish selection if needed.
        '''

        if not self.selection_binding:
            self.check_for_empty_selection()

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

        self.check_for_empty_selection(initialize_selection=True)

    def handle_setslice_op(self, start_index, end_index):
        '''Although it is hard to guess what might be preferred, a "positional"
        priority for selection is observed here, where the indices of selected
        item views is maintained. We so something similar to
        check_for_empty_selection() if no selection remains after the op.
        '''

        if not self.selection_binding:
            #changed_indices = range(start_index, end_index + 1)

            sel_indices_for_removal = []
            for index, sel in enumerate(self.selection):
                if sel not in self.data:
                    sel_indices_for_removal.append(index)
            self.selection.batch_delete(reversed(sel_indices_for_removal))

            # Do a check_for_empty_selection type step, if data remains.
            data = self.data
            if (len(data) > 0
                    and not self.selection
                    and not self.allow_empty_selection):
                # Find a good index to select, if the deletion results in
                # no selection, which is common, as the selected item is
                # often the one deleted.
                if start_index < len(data):
                    new_sel_index = start_index
                else:
                    new_sel_index = start_index - 1
                item = self.get_selectable_item(new_sel_index)
                if item is not None:
                    self.handle_selection(item)

    def handle_delete_op(self, start_index, end_index):
        '''An item has been deleted. Reset selection.
        '''

        if not self.selection_binding:
            #deleted_indices = range(start_index, end_index + 1)

            sel_indices_for_removal = []
            for index, sel in enumerate(self.selection):
                if sel not in self.data:
                    sel_indices_for_removal.append(index)
            self.selection.batch_delete(reversed(sel_indices_for_removal))

            self.check_for_empty_selection()
#            # Do a check_for_empty_selection type step, if data remains.
#            if (len(self.data) > 0
#                    and not self.selection
#                    and not self.allow_empty_selection):
#                # Find a good index to select, if the deletion results in
#                # no selection, which is common, as the selected item is
#                # often the one deleted.
#                if start_index < len(self.data):
#                    new_sel_index = start_index
#                else:
#                    new_sel_index = start_index - 1
#                item = self.get_selectable_item(new_sel_index)
#                if item is not None:
#                    self.handle_selection(item)

    def sort_started(self, *args):
        pass

        # Save a pre-sort order, and position detail, if there are duplicates
        # of strings.
#        self.presort_indices_and_items = {}

        # Not yet implemented. See adapters/list_ops.py for inspiration.

#        self.data.finish_sort_op()

    def handle_sort_op(self):
        '''Data has been sorted or reversed. Use the pre-sort information about
        previous ordering, stored in the associated op_info instance.
        '''
        pass

#        presort_indices_and_items = self.presort_indices_and_items

        # We have an association of presort indices with data items.
        # Where is each data item after sort? Change the index of the
        # item to match present position.

        # Not yet implemented. See adapters/list_ops.py for inspiration.

        # Clear temporary storage.
#        self.presort_indices_and_items.clear()
