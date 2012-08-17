'''
ListAdapter
===========

.. versionadded:: 1.5

:class:`SimpleListAdapter` is for simple lists, such as for showing a
text-only display of strings, or a list of views of some type that have
no user interaction.

:class:`ListAdapter` is has broader application, because it adds selection.
Its data items cannot be simple strings; they must be objects conforming to
the model of selection, handling is_selected.
'''

from kivy.properties import ListProperty, DictProperty, ObjectProperty
from kivy.lang import Builder
from kivy.adapters.collectionadapter import CollectionAdapter
from kivy.adapters.mixins.selection import SelectionSupport, \
        SelectableDataItem

from inspect import isfunction, ismethod


class SimpleListAdapter(CollectionAdapter):
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
    :class:`SimpleListAdapter`.

    :class:`ListAdapter`, by adding selection, has the requirement that data
    items be instances of a subclass of :class:`SelectableView` (Do not use
    simple strings as data items).
    '''

    def __init__(self, **kwargs):
        super(ListAdapter, self).__init__(**kwargs)

        # Reset and update selection, in SelectionSupport, if data changes.
        self.bind(data=self.initialize_selection)

    def bind_primary_key_to_func(self, func):
        self.bind(data=func)

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

        # The data item must be a subclass of SelectableView, or must have an
        # is_selected boolean or function, so it has is_selected available.
        # If is_selected is unavailable on the data item, an exception is
        # raised.
        #
        # [TODO] Only tested boolean is_selected.
        #
        # [TODO] Wouldn't use of getattr help a lot here?
        #
        if issubclass(item.__class__, SelectableDataItem):
            if item.is_selected:
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
            msg = "ListAdapter: unselectable data item for {0}".format(item)
            raise Exception(msg)

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
                # Select the first item if we have it.
                v = self.owning_view.get_item_view(0)
                if v is not None:
                    print 'selecting first data item view', v, v.is_selected
                    self.handle_selection(v)

    def touch_selection(self, *args):
        self.dispatch('on_selection_change')

    # [TODO] Also make methods for scroll_to_sel_start, scroll_to_sel_end,
    #        scroll_to_sel_middle.

    def trim_left_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are less than the
        index of the first selected item, if there is selection.
        '''
        pass

    def trim_right_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are greater than
        the index of the last selected item, if there is selection.
        '''
        pass

    def trim_to_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are les than or
        greater than the index of the last selected item, if there is
        selection. This preserves intervening list items within the selected
        range.
        '''
        pass

    def cut_to_sel(self, *args):
        '''Same as trim_to_sel, but intervening list items within the selected
        range are cut also, leaving only list items that are selected.
        '''
        pass
