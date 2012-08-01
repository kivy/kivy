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

from kivy.properties import ListProperty, DictProperty, ObjectProperty
from kivy.lang import Builder
from kivy.adapters.adapter import Adapter
from kivy.adapters.mixins.selection import SelectionSupport


class SimpleListAdapter(Adapter):
    '''ListAdapter is an adapter around a simple Python list.

    From Adapter, SimpleListAdapter gets these properties:

        - cls, for the list item class to use to instantiate row view
               instances

        - template, an optional kv template to use instead of a python class
                    (to use instead of cls)

        - args_converter, an optional function to transform data item argument
                          sets, in preparation for either a cls instantiation,
                          or a kv template invocation
    '''

    data = ListProperty([])
    '''The data list property contains a list of objects that will be used
    directly if no args_converter function is provided. If there is an
    args_converter, the data objects will be passed to it, for instantiation
    of item view class (cls) instances from the data.
    '''

    def __init__(self, **kwargs):
        if 'data' not in kwargs:
            raise Exception('list adapter: input must include data argument')
        if type(kwargs['data']) not in (tuple, list):
            raise Exception('list adapter: data must be a tuple or list')
        super(SimpleListAdapter, self).__init__(**kwargs)

    def get_count(self):
        return len(self.data)

    def get_item(self, index):
        if index < 0 or index >= len(self.data):
            return None
        return self.data[index]


class ListAdapter(SelectionSupport, SimpleListAdapter):
    '''From the SelectionSupport mixin, ListAdapter has these properties:

        - selection
        - selection_mode
        - allow_empty_selection

    and several methods used in selection operations.

    If you wish to have a bare-bones list adapter, without selection, use
    SimpleListAdapter.
    '''

    owning_view = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ListAdapter, self).__init__(**kwargs)

        # Reset and update selection, in SelectionSupport, if data changes.
        self.bind(data=self.initialize_selection)

    def get_view(self, index):
        '''This method is identical to the one in Adapter and
        SimpleListAdapter, but here we pass self to the list item class (cls)
        instantiation, so that the list item class, required to mix in
        SelectableItem, will have access to ListAdapter for calling to
        SelectionSupport methods.
        '''
        item = self.get_item(index)
        if item is None:
            return None

        item_args = None
        if self.args_converter:
            item_args = self.args_converter(item)
        else:
            item_args = item

        item_args['list_adapter'] = self
        item_args['data_index'] = index

        if self.cls:
            print 'CREATE VIEW FOR', index
            instance = self.cls(**item_args)
            return instance
        else:
            return Builder.template(self.template, **item_args)

    def on_selection_change(self, *args):
        '''on_selection_change() is the default handler for the
        on_selection_change event, which is registered in SelectionSupport.
        '''
        pass

    def check_for_empty_selection(self, *args):
        if self.allow_empty_selection is False:
            if len(self.selection) == 0:
                # Select the first item if we have it.
                v = self.owning_view.get_item_view(0)
                if v is not None:
                    print 'selecting first data item view', v, v.is_selected
                    self.handle_selection(v)

    def touch_selection(self, *args):
        self.dispatch('on_selection_change')


class ListsAdapter(ListAdapter):
    '''ListsAdapter is specialized for managing a dict of lists. It has wide
    application, because a list of lists is a common need. ListsAdapter may
    be used for chaining several list_adapters in a "cascade," where selection
    of the first, changes the selection of the next, and so on.
    '''

    lists_dict = DictProperty({})
    '''The selection of the observed_list_adapter, which must be single
    selection here, is the key into lists_dict, which is a dict
    of list item lists.
    '''

    observed_list_adapter = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ListsAdapter, self).__init__(**kwargs)
        self.observed_list_adapter.bind(
                on_selection_change=self.on_selection_change)

    def on_selection_change(self, *args):
        observed_selection = self.observed_list_adapter.selection

        if len(observed_selection) == 0:
            self.data = []
            return

        self.data = self.lists_dict[str(observed_selection[0])]


class AccumulatingListAdapter(ListAdapter):
    '''AccumulatingListAdapter is a list adapter whose
    data is formed by the selection of an observed list adapter.

    Selection will accumulate as either single or multiple selection
    events happen.
    '''

    observed_list_adapter = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(AccumulatingListAdapter, self).__init__(**kwargs)
        self.observed_list_adapter.bind(
                on_selection_change=self.on_selection_change)

    def on_selection_change(self, *args):
        observed_selection = self.observed_list_adapter.selection

        if len(observed_selection) == 0:
            self.data = []
            return

        self.data = [str(obj.text) for obj in observed_selection]
