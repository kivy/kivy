'''
ListAdapter
===========

.. versionadded:: 1.5

:class:`SimpleListAdapter` is for simple lists, such as for showing a
text-only display of strings, or a list of views of some type that have
no user interaction.

:class:`ListAdapter` is the main workhorse for broad use, because it adds
selection.

Several subclasses of :class:`ListAdapter` offer convenience for setting up
bindings required to connect a list adapter to another one, or to another
external object that changes selection in some way.

:class:`ListsAdapter` is for use when you have a list of lists, with one
showing at any given time.
'''

from kivy.properties import ListProperty, DictProperty, ObjectProperty
from kivy.lang import Builder
from kivy.adapters.adapter import Adapter
from kivy.adapters.mixins.selection import SelectionSupport

from inspect import isfunction, ismethod


class SimpleListAdapter(Adapter):
    ''':class:`SimpleListAdapter` is an adapter around a simple Python list.

    From :class:`Adapter`, :class:`SimpleListAdapter` gets these properties:

        Use only one:

            - cls, for a list item class to use to instantiate item view
                   instances

            - template, a kv template to use to instantiate item view
                        instances

        - args_converter, an optional function to transform data item argument
                          sets, in preparation for either a cls instantiation,
                          or a kv template invocation
    '''

    data = ListProperty([])
    '''The data list property contains a list of objects (can be strings) that
    will be used directly if no args_converter function is provided. If there
    is an args_converter, the data objects will be passed to it, for
    instantiation of item view class (cls) instances from the data.
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
    '''From the :class:`SelectionSupport` mixin, :class:`ListAdapter` has
    these properties:

        - selection
        - selection_mode
        - allow_empty_selection

    and several methods used in selection operations.

    If you wish to have a bare-bones list adapter, without selection, use
    SimpleListAdapter.
    '''

    owning_view = ObjectProperty(None)
    '''Management of selection requires manipulation of item view instances,
    which are created here, but cached in the owning_view, such as a
    :class:`ListView` instance. In some operations at the adapter level,
    access is needed to the views.
    '''

    datastore = ObjectProperty(None)
    '''A function that takes a str key, an item of data, as the single
    argument, and returns the value to the key stored in the underlying data
    structure or backing database. This is only used in the case that an item
    of data is a str.
    '''

    def __init__(self, **kwargs):
        # Check data for any str items. If found, check for datastore arg,
        # and if no datastore arg, raise exception. Otherwise break out.
        #
        for item in kwargs['data']:
            if type(item) == 'str':
                if 'datastore' not in kwargs:
                    msg = 'ListAdapter: data has str keys; need datastore.'
                    raise Exception(msg)
                break
        super(ListAdapter, self).__init__(**kwargs)

        # Reset and update selection, in SelectionSupport, if data changes.
        self.bind(data=self.initialize_selection)

    def get_view(self, index):
        '''This method is more complicated than the one in Adapter and
        SimpleListAdapter, because here we create bindings for the data item,
        and its children back to self.handle_selection(), in the mixed-in
        :class:`SelectionSupport` class, and do other selection-related tasks
        to keep item views in sync with the data.
        '''
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

        # If the data item is a string, it is assumed to be a key into the
        # datastore, so a lookup is done to check selection. Otherwise, the
        # data item must be a subclass of SelectableItem, or must have an
        # is_selected boolean or function, so it has is_selected available.
        # If is_selected is unavailable on the data item, an exception is
        # raised.
        #
        # A mixture of keys into the datastore and object instances
        # providing an is_selected() function or is_selected boolean
        # is allowed.
        #
        if type(item) == str:
            if self.datastore.get(item, 'is_selected'):
                self.handle_selection(instance)
        elif type(item) == dict and 'is_selected' in item:
            if item['is_selected']:
                self.handle_selection(instance)
        elif hasattr(item, 'is_selected'):
            if isfunction(item.is_selected) or ismethod(item.is_selected):
                if item.is_selected():
                    self.handle_selection(instance)
            else:
                if item.is_selected:
                    self.handle_selection(instance)
        else:
            msg = "ListAdapter: record for {0} unselectable".format(item)
            raise Exception(msg)

        # [TODO] if instance.handles_event('on_release'):       ?
        instance.bind(on_release=self.handle_selection)

        # [TODO] If the whole composite can't respond, should we try to see
        #        if the children can? No harm, no foul on setting this?
        for child in instance.children:
        #    if child.handles_event('on_release'):  [TODO] ?
            child.bind(on_release=self.handle_selection)

        return instance

    def on_selection_change(self, *args):
        '''on_selection_change() is the default handler for the
        on_selection_change event, which is registered in
        :class:`SelectionSupport`.
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
    ''':class:`ListsAdapter` is specialized for managing a list of lists,
    which is done internally with use of a dict of lists.
    :class:`ListsAdapter` may be used for chaining several list_adapters in a
    "cascade," where selection of the first, changes the selection of the
    next, and others.
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
