'''
DictController
==============

.. versionadded:: 1.8

    Modified from the original DictAdapter.

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

A :class:`~kivy.controllers.dictcontroller.DictController` is an controller
around a python dictionary of records.
'''

__all__ = ('DictController', )

from kivy.controllers.listcontroller import ListController
from kivy.properties import DictProperty
from kivy.properties import DictOpInfo
from kivy.properties import OpObservableDict


class DictController(ListController):
    '''A :class:`~kivy.controllers.dictcontroller.DictController` is an
    controller around a python dictionary of records. It is an alternative to
    the list capabilities of
    :class:`~kivy.controllers.listcontroller.ListController`.

    This class supports a "collection" style view such as
    :class:`~kivy.uix.listview.ListView`.

    :class:`~kivy.controllers.dictcontroller.ListController` and
    :class:`~kivy.controllers.listcontroller.DictController` use special
    :class:`~kivy.properties.ListProperty` and
    :class:`~kivy.properties.DictProperty` variants,
    :class:`~kivy.properties.OpObservableList` and
    :class:`~kivy.properties.OpObservableDict`, which
    record op_info for use in the controller system.

    See :class:`~kivy.controllers.listcontroller.ListController` for how
    the system works for :class:`~kivy.properties.OpObservableList`.

    .. versionadded:: 1.5

        (As DictAdapter)

    .. versionchanged:: 1.8.0

        New classes, OpObserverableList and OpObservableDict, were added to
        kivy/properties.pyx as alternatives to ObservableList and
        ObservableDict, which only dispatch when data is set, or when any
        change occurs. The new ObObservableList and OpObservableDict dispatch
        on a fine-grained basis, after any individual op is performed.

        Just as ListController, the superclass, has its list_ops_handler,
        DictController delegates event handling to a dedicated DictOpHandler.

        The data_changed() method of the delegate DictOpHandler, and methods
        used there, do what is needed to cached_views and selection, then they
        dispatch, in turn, up to the owning collection type view, such as
        ListView. The collection type view then reacts with changes to its
        children and other parts of the user interface as needed.

        Changed to DictController, modifying from the original DictAdapter.
    '''

    data_dict = DictProperty({}, cls=OpObservableDict)
    '''A Python dict that uses :class:`~kivy.properties.OpObservableDict` as a
    "change-aware" wrapper that records op_info for dict ops.

    data_dict may contain more data items than are present in data (in the
    ListController superclass) -- data can be a subset of data_dict.keys().

    :data:`data_dict` is a :class:`~kivy.properties.DictProperty` and defaults
    to None.
    '''

    def __init__(self, **kwargs):

        super(DictController, self).__init__(**kwargs)

        self.bind(data_dict=self.data_dict_changed)

        print 'DictController, selection', self.selection

    def check_data(self, data, data_key_items):

        # Remove any key_items in data that are not found in
        # self.data_dict.keys(). This is the set intersection op (&).
        data_checked = list(set(data) & set(data_key_items))

        # Maintain sort order of incoming data.
        return [k for k in data if k in data_checked]

    def insert(self, index, key_item, value):
        '''A Python dict does not have an insert(), because keys are unordered.
        Here, with data, an insert() makes sense, but we put it as part of the
        controller API, not as a public method of the data dict.
        '''

        # This special insert() OOD call only does a dict set (it does not
        # write op_info). The data insert will trigger a data change event.
        print 'data_dict.setitem_for_insert', key_item, value
        self.data_dict.setitem_for_insert(key_item, value)
        print 'inserting', index, key_item
        self.data.insert(index, key_item)

    # NOTE: This is not len(self.data). (The data dict may contain more items
    #       than data -- data can be a subset.).
#    def get_count(self):
#        return len(self.data)

#    def get_data_item(self, index):
#        if index < 0 or index > len(self.data) - 1:
#            return None
#        key_item = self.data[index]
#        return self.data_dict[key_item]

    def additional_args_converter_args(self, index):
        '''args_converters for DictController instances receive the index and
        the data value, along with the key_item at the index, as the last
        argument:

        So, an args_converter for DictController gets three arguments:

            index, data_item, key_item

        The first two are already available to Controller.create_view(), but we
        must supply the third, the key_item for the index.
        '''

        return (self.data[index], )

    def trim_left_of_sel(self, *args):
        '''Cut list items with indices in data that are less than the
        index of the first selected item, if there is a selection.
        '''
        if len(self.selection) > 0:
            selected_key_items = [sel.text for sel in self.selection]
            first_sel_index = self.data.index(selected_key_items[0])
            desired_key_items = self.data[first_sel_index:]
            self.data_dict = \
                    dict([(key_item, self.data_dict[key_item])
                                  for key_item in desired_key_items])

    def trim_right_of_sel(self, *args):
        '''Cut list items with indices in data that are greater than
        the index of the last selected item, if there is a selection.
        '''
        if len(self.selection) > 0:
            selected_key_items = [sel.text for sel in self.selection]
            last_sel_index = self.data.index(selected_key_items[-1])
            desired_key_items = self.data[:last_sel_index + 1]
            self.data_dict = \
                    dict([(key_item, self.data_dict[key_item])
                                  for key_item in desired_key_items])

    def trim_to_sel(self, *args):
        '''Cut list items with indices in data that are les than or
        greater than the index of the last selected item, if there is a
        selection. This preserves intervening list items within the selected
        range.
        '''
        if len(self.selection) > 0:
            selected_key_items = [sel.text for sel in self.selection]
            first_sel_index = self.data.index(selected_key_items[0])
            last_sel_index = self.data.index(selected_key_items[-1])
            desired_key_items = self.data[first_sel_index:last_sel_index + 1]
            self.data_dict = \
                    dict([(key_item, self.data_dict[key_item])
                                  for key_item in desired_key_items])

    def cut_to_sel(self, *args):
        '''Same as trim_to_sel, but intervening list items within the selected
        range are also cut, leaving only list items that are selected.
        '''
        if len(self.selection) > 0:
            selected_key_items = [sel.text for sel in self.selection]
            self.data_dict = \
                    dict([(key_item, self.data_dict[key_item])
                                   for key_item in selected_key_items])

    def data_dict_changed(self, *args):
        '''
        data_changed() reacts to the operations listed below that are possible
        for a OpObservableDict (OOD).

        The following methods here react to some of the dict operations
        possible:

            handle_dict_set()

                OOD_set

            handle_dict_setitem_set_op()

                OOD_setitem_set

            handle_dict_delete_op()

                OOD_delitem
                OOD_pop
                OOD_popitem

            handle_dict_clear_op()

                OOD_clear

            These methods adjust cached_views and selection.
        '''

        # NOTE: args[1] is the modified dict.

        if len(args) == 3:
            op_info = args[2]
        else:
            op_info = DictOpInfo('OOD_set', (None, ))

        # Make a copy for more convenient access by observers.
        self.data_op_info = op_info

        op = op_info.op_name
        key_items = op_info.keys

        if op == 'OOD_set':

            self.handle_dict_set()

        elif op in ['OOD_setitem_add', 'OOD_setdefault', ]:

            self.handle_dict_add_op(key_items[0])

        elif op == 'OOD_update':

            self.handle_dict_update_op(key_items)

        elif op == 'OOD_setitem_set':

            self.handle_dict_setitem_set_op(key_items[0])

        elif op in ['OOD_delitem',
                    'OOD_pop',
                    'OOD_popitem']:

            self.handle_dict_delete_op(key_items)

        elif op == 'OOD_clear':

            self.handle_dict_clear_op()

    def handle_dict_set(self):

        # Will trigger a data set callback in data, which will clear
        # the cache and (re)initialize selection:
        self.data = self.data_dict.keys()

    def handle_dict_setitem_set_op(self, key_item):

        # Force a rebuild of the view for which data item has changed.
        # If the item was selected before, maintain the seletion.

        # We do not alter data -- the key_item is the same, only the
        # value has changed. So, we must dispatch here.

        print 'handle_dict_setitem_set_op', key_item, key_item.text
        index = self.data.index(key_item)

        print 'this is the index', index
        # Set start_index, end_index to the index.
        self.additional_op_info = (index, index)

        # Force a dispatch by resetting the same data item.
        self.data[index] = self.data_dict[key_item]

    def handle_dict_add_op(self, key_item):

        # For add ops, OOD_setitem_add, OOD_setdefault, and OOD_update, we only
        # need to append or extend the data (a OOL instance), whose change will
        # trigger a data changed callback.
        self.data.append(key_item)

    def handle_dict_update_op(self, key_items):

        self.data.extend(key_items)

    def handle_dict_delete_op(self, key_items):

        indices = [self.data.index(k) for k in key_items]

        start_index = min(indices)
        end_index = max(indices)

        self.additional_op_info = (start_index, end_index)

        # Do not dispatch here. Trigger the data change callback. The event
        # will fire under control of the delegated list_op_handler of the
        # ListController superclass. The cache will be cleared and selection
        # reinitialized.
        del self.data[start_index:end_index + 1]

    def handle_dict_clear_op(self):

        # The data has been cleared, so there is no meaningful length to set
        # here (len(self.data) would give the new data length). So, set (0, 0).
        self.additional_op_info = (0, 0)

        # Trigger the data set callback, as above.
        self.data = []
