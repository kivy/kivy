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

from kivy.properties import ListProperty, ObjectProperty, StringProperty, \
        DictProperty
from kivy.lang import Builder
from kivy.adapters.adapter import Adapter
from kivy.adapters.mixins.selection import SelectionSupport


class DictAdapter(SelectionSupport, Adapter):

    owning_view = ObjectProperty(None)
    '''Management of selection requires manipulation of key view instances,
    which are created here, but cached in the owning_view, such as a
    :class:`ListView` instance. In some operations at the adapter level,
    access is needed to the views.
    '''

    sorted_keys = ListProperty([])
    '''The sorted_keys list property contains a list of hashable objects (can
    be strings) that will be used directly if no args_converter function is
    provided. If there is an args_converter, the record received from a
    lookup in the data, using key from sorted_keys, will be passed
    to it, for instantiation of key view class (cls) instances from the
    sorted_keys.
    '''

    sort_on = StringProperty('')
    '''The sort_on string is the name of the property in the record to use for
    sorting records. This is used to maintain the sorted_keys list.
    '''

    data = DictProperty(None)
    '''A dict object indexes records by a key in sorted_keys.
    '''

    selected_keys = ListProperty([])
    '''The selected_keys list of keys mirrors the selection list of selected
    view instances. This is useful for binding the selection for a dict
    adaptor to another dict adaptor, or to some observer needing the keys, and
    not the view instances selected. The selection list is bound to
    update_selected_keys(), the method that updates selected_keys.

    [TODO] Evaluate for usefulness.
    '''

    def __init__(self, **kwargs):
        #if 'sort_on' not in kwargs:
            #raise Exception('data adapter: input must include sort_on')
        # sorted_keys can be passed in, but needs checking:
        if 'sorted_keys' in kwargs:
            if type(kwargs['sorted_keys']) not in (tuple, list):
                msg = 'DictAdapter: sorted_keys must be tuple or list'
                raise Exception(msg)
        else:
            self.sorted_keys = sorted(kwargs['data'].keys())

        super(DictAdapter, self).__init__(**kwargs)

        self.bind(data=self.initialize_data,
                  selection=self.update_selected_keys)

    def bind_primary_key_to_func(self, func):
        self.bind(sorted_keys=func)

    def sort_keys(self):
        self.sorted_keys = sorted(self.sorted_keys)

    def initialize_data(self, *args):
        self.sorted_keys = sorted(self.data.keys())
        self.initialize_selection()

    # [TODO] This update happens after selection has changed and the
    #        on_selection_change event has fired, so there will be a
    #        lag. Can selected_indices be used instead of this for
    #        known uses?
    #
    def update_selected_keys(self, *args):
        if len(self.selection) > 0 and len(self.selected_indices) > 0:
            self.selected_keys = \
                [self.sorted_keys[i] for i in self.selected_indices]
        else:
            self.selected_keys = []

    def get_count(self):
        return len(self.sorted_keys)

    def get_item(self, index):
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
            print 'CREATE VIEW FOR', index
            instance = self.cls(**item_args)
        else:
            print 'TEMPLATE item_args', item_args
            instance = Builder.template(self.template, **item_args)
            print 'TEMPLATE instance.index', instance.index

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
                    print 'selecting first list item view', v, v.is_selected
                    self.handle_selection(v)

    def touch_selection(self, *args):
        self.dispatch('on_selection_change')
