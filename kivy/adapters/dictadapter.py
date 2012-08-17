'''
DictAdapter
===========

.. versionadded:: 1.5

:class:`DictAdapter` is an adapter around a python dictionary of records.

From :class:`Adapter`, :class:`SimpleListAdapter` gets these properties:

    Use only one:

        - cls, for a list key class to use to instantiate key view
               instances

        - template, a kv template to use to instantiate key view
                    instances

    - args_converter, an optional function to transform data item argument
                      sets, in preparation for either a cls instantiation,
                      or a kv template invocation

From the :class:`SelectionSupport` mixin, :class:`DictAdapter` has
these properties:

    - selection
    - selection_mode
    - allow_empty_selection

and several methods used in selection operations.

If you wish to have a bare-bones list adapter, without selection, use
:class:`SimpleListAdapter`.

'''

from kivy.properties import ListProperty, DictProperty
from kivy.lang import Builder
from kivy.adapters.collectionadapter import CollectionAdapter
from kivy.adapters.mixins.selection import SelectionSupport


class DictAdapter(SelectionSupport, CollectionAdapter):

    sorted_keys = ListProperty([])
    '''The sorted_keys list property contains a list of hashable objects (can
    be strings) that will be used directly if no args_converter function is
    provided. If there is an args_converter, the record received from a
    lookup in the data, using key from sorted_keys, will be passed
    to it, for instantiation of key view class (cls) instances from the
    sorted_keys.
    '''

    data = DictProperty(None)
    '''A dict that indexes records by keys that are equivalent in content
    to the keys in sorted_keys.
    '''

    def __init__(self, **kwargs):
        if 'sorted_keys' in kwargs:
            if type(kwargs['sorted_keys']) not in (tuple, list):
                msg = 'DictAdapter: sorted_keys must be tuple or list'
                raise Exception(msg)
        else:
            self.sorted_keys = sorted(kwargs['data'].keys())

        super(DictAdapter, self).__init__(**kwargs)

        self.bind(sorted_keys=self.initialize_sorted_keys,
                  data=self.initialize_data)

    def bind_primary_key_to_func(self, func):
        self.bind(sorted_keys=func)

    def sort_keys(self):
        self.sorted_keys = sorted(self.sorted_keys)

    def initialize_sorted_keys(self, *args):
        self.initialize_selection()

    def initialize_data(self, *args):
        self.sorted_keys = sorted(self.data.keys())
        self.initialize_selection()

    def get_count(self):
        return len(self.sorted_keys)

    def get_item(self, index):
        #print 'DictAdapter, get_item', index
        #print 'DictAdapter, get_item, sorted_keys', self.sorted_keys
        if index < 0 or index >= len(self.sorted_keys):
            return None
        return self.data[self.sorted_keys[index]]

    def get_view(self, index):
        item = self.get_item(index)
        if item is None:
            return None

        item_args = None
        if self.args_converter:
            item_args = self.args_converter(item)
        else:
            item_args = item

        item_args['index'] = index

        if self.cls:
            #print 'CREATE VIEW FOR', index
            instance = self.cls(**item_args)
        else:
            #print 'TEMPLATE item_args', item_args
            instance = Builder.template(self.template, **item_args)
            #print 'TEMPLATE instance.index', instance.index

        if item['is_selected']:
            self.handle_selection(instance)

        # [TODO] if instance.handles_event('on_release'):       ?
        instance.bind(on_release=self.handle_selection)

        # [TODO] If the whole composite can't respond, should we try to see
        #        if the children can? No harm, no foul on setting this?
        for child in instance.children:
        #    if child.handles_event('on_release'):  [TODO] ?
            child.bind(on_release=self.handle_selection)

        return instance

    def check_for_empty_selection(self, *args):
        if not self.allow_empty_selection:
            if len(self.selection) == 0:
                # Select the first key if we have it.
                v = self.owning_view.get_item_view(0)
                if v is not None:
                    #print 'selecting first list item view', v, v.is_selected
                    self.handle_selection(v)

    def touch_selection(self, *args):
        self.dispatch('on_selection_change')

    # [TODO] Also make methods for scroll_to_sel_start, scroll_to_sel_end,
    #        scroll_to_sel_middle.

    def trim_left_of_sel(self, *args):
        if len(self.selection) > 0:
            selected_keys = [sel.text for sel in self.selection]
            first_sel_index = self.sorted_keys.index(selected_keys[0])
            desired_keys = self.sorted_keys[first_sel_index:]
            self.data = {key: self.data[key] for key in desired_keys}

    def trim_right_of_sel(self, *args):
        if len(self.selection) > 0:
            selected_keys = [sel.text for sel in self.selection]
            last_sel_index = self.sorted_keys.index(selected_keys[-1])
            desired_keys = self.sorted_keys[:last_sel_index + 1]
            self.data = {key: self.data[key] for key in desired_keys}

    def trim_to_sel(self, *args):
        if len(self.selection) > 0:
            selected_keys = [sel.text for sel in self.selection]
            first_sel_index = self.sorted_keys.index(selected_keys[0])
            last_sel_index = self.sorted_keys.index(selected_keys[-1])
            desired_keys = self.sorted_keys[first_sel_index:last_sel_index + 1]
            self.data = {key: self.data[key] for key in desired_keys}

    def cut_to_sel(self, *args):
        if len(self.selection) > 0:
            selected_keys = [sel.text for sel in self.selection]
            self.data = {key: self.data[key] for key in selected_keys}
