'''
ListAdapter
===========

.. versionadded:: 1.4

Notes:

    - Consider adding the functionality for locking changes to the associated
      data -- whether or not editing of item_view_instances is allowed.
      This could be controlled simply with an is_editable boolean, but would
      involve more work in the implementation, of course.
    
'''

from kivy.properties import ListProperty
from kivy.lang import Builder
from kivy.uix.mixins.selection import SelectionSupport
from kivy.adapters.adapter import Adapter


class ListAdapter(SelectionSupport, Adapter):
    '''ListAdapter is an adapter around a simple Python list.

    From the SelectionSupport mixin, ListAdapter has these properties:

        - selection
        - selection_mode
        - allow_empty_selection

    and several methods used in selection operations.

    From Adapter, ListAdapter gets these properties:

        - cls, for the list item class to use to instantiate row view
               instances
        - template, an optional kv template to use instead of a python class
                    (to use instead of cls)
        - args_converter, an optional function to transform data item argument
                          sets, in preparation for either a cls instantiation,
                          or a kv template invocation
    '''

    data = ListProperty([])
    '''The data list property contains dict argument sets for individual
    data items. If an args_converter function is provided, it will be used to
    instantiate view class (cls) instances for the row items.
    '''

    def __init__(self, data, **kwargs):
        if type(data) not in (tuple, list):
            raise Exception('ListAdapter: input must be a tuple or list')
        super(ListAdapter, self).__init__(**kwargs)

        # Reset and update selection, in SelectionSupport, if data changes.
        self.bind(data=self.initialize_selection)

        # Do the initial set -- triggers initialize_selection().
        self.data = data

    def get_count(self):
        return len(self.data)

    def get_item(self, index):
        if index < 0 or index >= len(self.data):
            return None
        return self.data[index]

    def get_view(self, index):
        '''This method is identical to the one in Adapter, but here we pass
        self to the list item class (cls) instantiation, so that the list
        item class, required to mix in SelectableItem, will have access to
        ListAdapter for calling to SelectionSupport methods.
        '''
        item = self.get_item(index)
        if item is None:
            return None

        item_args = None
        if self.args_converter:
            item_args = self.args_converter(item)
        else:
            item_args = item

        if self.cls:
            print 'CREATE VIEW FOR', index
            instance = self.cls(self, **item_args)
            return instance
        else:
            # [TODO] However this is done, document it.
            item_args['list_adapter'] = self

            return Builder.template(self.template, **item_args)
