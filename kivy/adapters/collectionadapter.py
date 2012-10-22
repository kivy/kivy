'''
CollectionAdapter
=================

.. versionadded:: 1.5

:class:`CollectionAdapter` is a base class for adapters dedicated to lists or
dicts or other collections of data.

Provides selection and view creation and management functionality to 
"collection-style" views, such as :class:`ListView`, and their item views, via
the :class:`ListAdapter` and :class:`DictAdapter` subclasses.
'''

from kivy.event import EventDispatcher
from kivy.adapters.adapter import Adapter
from kivy.adapters.models import SelectableDataItem
from kivy.properties import ObjectProperty
from kivy.properties import ListProperty
from kivy.properties import DictProperty
from kivy.properties import BooleanProperty
from kivy.properties import OptionProperty
from kivy.properties import NumericProperty
from kivy.lang import Builder


class CollectionAdapter(Adapter, EventDispatcher):
    '''
    A base class for adapters interfacing with lists, dictionaries, or other
    collection type data, adding selection and view creation and management
    functonality.
    '''

    selection = ListProperty([])
    '''The selection list property is the container for selected items.
    '''

    selection_mode = OptionProperty('single',
            options=('none', 'single', 'multiple'))
    '''Selection modes:

       none -- use the list as a simple list (no select action). This option
               is here so that selection can be turned off, momentarily or
               permanently, for an existing list adapter. :class:`ListAdapter`
               is not meant to be used as a primary no-selection list adapter.
               Use :class:`SimpleListAdapter` for that.

       single -- multi-touch/click ignored. single item selecting only

       multiple -- multi-touch / incremental addition to selection allowed;
                   may be limited to a count by selection_limit
    '''

    propagate_selection_to_data = BooleanProperty(False)
    '''Normally, data items are not selected/deselected, because the data items
    might not have an is_selected boolean property -- only the item view for a
    given data item is selected/deselected, as part of the maintained selection
    list. However, if the data items do have an is_selected property, or if
    they mix in :class:`SelectableDataItem`, the selection machinery can
    propagate selection to data items. This can be useful for storing selection
    state in a local database or backend database for maintaining state in game
    play or other similar needs. It is a convenience function.

    To propagate selection or not?

    Consider a shopping list application for shopping for fruits at the
    market. The app allows selection of fruits to buy for each day of the
    week, presenting seven lists, one for each day of the week. Each list is
    loaded with all the available fruits, but the selection for each is a
    subset. There is only one set of fruit data shared between the lists, so
    it would not make sense to propagate selection to the data, because
    selection in any of the seven lists would clobber and mix with that of the
    others.

    However, consider a game that uses the same fruits data for selecting
    fruits available for fruit-tossing. A given round of play could have a
    full fruits list, with fruits available for tossing shown selected. If the
    game is saved and rerun, the full fruits list, with selection marked on
    each item, would be reloaded fine if selection is always propagated to the
    data. You could accomplish the same functionality by writing code to
    operate on list selection, but having selection stored on the data might
    prove convenient in some cases.
    '''

    allow_empty_selection = BooleanProperty(True)
    '''The allow_empty_selection may be used for cascading selection between
    several list views, or between a list view and an observing view. Such
    automatic maintainence of selection is important for all but simple
    list displays. Set allow_empty_selection False, so that selection is
    auto-initialized, and always maintained, and so that any observing views
    may likewise be updated to stay in sync.
    '''

    selection_limit = NumericProperty(0)
    '''When selection_mode is multiple, if selection_limit is non-zero, this
    number will limit the number of selected items. It can even be 1, which is
    equivalent to single selection. This is because a program could be
    programmatically changing selection_limit on the fly, and all possible
    values should be included.
    '''

    cached_views = DictProperty({})
    '''View instances for data items are instantiated and managed in the
    adapter. Here we maintain a dictionary containing the view
    instances keyed to the indices in the data.

    This dictionary works as a cache. get_view() only asks for a view from
    the adapter if one is not already stored for the requested index.
    '''

    def __init__(self, **kwargs):
        super(CollectionAdapter, self).__init__(**kwargs)
  
        self.register_event_type('on_selection_change')

        self.bind(selection_mode=self.check_for_empty_selection,
                  allow_empty_selection=self.check_for_empty_selection,
                  data=self.update_for_new_data)

        self.update_for_new_data()

    def set_item_view(self, index, item_view):
        pass

    def delete_cache(self, *args):
        self.cached_views = {}

    def get_view(self, index):
        if index in self.cached_views:
            return self.cached_views[index]
        item_view = self.create_view(index)
        if item_view:
            self.cached_views[index] = item_view
        return item_view

    def create_view(self, index):
        '''This method is more complicated than the one in Adapter and
        SimpleListAdapter, because here we create bindings for the data item,
        and its children back to self.handle_selection(), and do other
        selection-related tasks to keep item views in sync with the data.
        '''
        item = self.get_data_item(index)
        if item is None:
            return None

        item_args = None
        if self.args_converter:
            item_args = self.args_converter(item)
        else:
            item_args = item

        item_args['index'] = index

        if self.cls:
            view_instance = self.cls(**item_args)
        else:
            view_instance = Builder.template(self.template, **item_args)

        if self.propagate_selection_to_data:
            # The data item must be a subclass of SelectableDataItem, or must have
            # an is_selected boolean or function, so it has is_selected available.
            # If is_selected is unavailable on the data item, an exception is
            # raised.
            #
            # [TODO] Only tested boolean is_selected.
            #
            # [TODO] Wouldn't use of getattr help a lot here?
            #
            if issubclass(item.__class__, SelectableDataItem):
                if item.is_selected:
                    self.handle_selection(view_instance)
            elif type(item) == dict and 'is_selected' in item:
                if item['is_selected']:
                    self.handle_selection(view_instance)
            elif hasattr(item, 'is_selected'):
                if isfunction(item.is_selected) or ismethod(item.is_selected):
                    if item.is_selected():
                        self.handle_selection(view_instance)
                else:
                    if item.is_selected:
                        self.handle_selection(view_instance)
            else:
                msg = "CollectionAdapter: unselectable data item for {0}".format(item)
                raise Exception(msg)

        view_instance.bind(on_release=self.handle_selection)

        # [TODO] Tested?
        for child in view_instance.children:
            child.bind(on_release=self.handle_selection)

        return view_instance

    def on_selection_change(self, *args):
        '''on_selection_change() is the default handler for the
        on_selection_change event.
        '''
        pass

    def handle_selection(self, view, *args):
        if view not in self.selection:
            if self.selection_mode in ['none', 'single'] and \
                    len(self.selection) > 0:
                for selected_view in self.selection:
                    self.deselect_item_view(selected_view)
            if self.selection_mode != 'none':
                if self.selection_mode == 'multiple':
                    if self.allow_empty_selection:
                        if self.selection_limit > 0:
                            if len(self.selection) < self.selection_limit:
                                self.select_item_view(view)
                    else:
                        self.select_item_view(view)
                else:
                    self.select_item_view(view)
        else:
            if self.selection_mode == 'none':
                for selected_view in self.selection:
                    self.deselect_item_view(selected_view)
            else:
                self.deselect_item_view(view)
                # If the deselection makes selection empty, the following call
                # will check allows_empty_selection, and if False, will
                # select the first item. If view happens to be the first item,
                # this will be a reselection, and the user will notice no
                # change, except perhaps a flicker.
                #
                self.check_for_empty_selection()

        self.dispatch('on_selection_change')

    def select_data_item(self, item):
        self.set_data_item_selection(item, True)

    def deselect_data_item(self, item):
        self.set_data_item_selection(item, False)

    def set_data_item_selection(self, item, value):
        if issubclass(item.__class__, SelectableDataItem):
            item.is_selected = value
        elif type(item) is dict:
            item['is_selected'] = value
        elif hasattr(item, 'is_selected'):
            item.is_selected = value
        else:
            raise Exception('Selection: data item is not selectable')

    def select_item_view(self, view):
        view.select()
        view.is_selected = True
        self.selection.append(view)

        # [TODO] sibling selection for composite items
        #        Needed? Or handled from parent?
        #        (avoid circular, redundant selection)
        #if hasattr(view, 'parent') and hasattr(view.parent, 'children'):
         #siblings = [child for child in view.parent.children if child != view]
         #for sibling in siblings:
             #if hasattr(sibling, 'select'):
                 #sibling.select()

        # child selection
        for child in view.children:
            if hasattr(child, 'select'):
                child.select()

        if self.propagate_selection_to_data:
            data_item = self.get_data_item(view.index)
            self.select_data_item(data_item)

    def select_list(self, view_list, extend):
        '''The select call is made for the items in the provided view_list.

        Arguments:

            view_list: the list of item views to become the new selection, or
            to add to the existing selection

            extend: boolean for whether or not to extend the existing list
        '''

        # Select all the item views.
        for view in view_list:
            self.select_item_view(view)

        # Extend or set selection.
        if extend:
            self.selection.extend(view_list)
        else:
            self.selection = view_list

        self.dispatch('on_selection_change')

    def deselect_item_view(self, view):
        view.deselect()
        view.is_selected = False
        self.selection.remove(view)

        # [TODO] sibling deselection for composite items
        #        Needed? Or handled from parent?
        #        (avoid circular, redundant selection)
        #if hasattr(view, 'parent') and hasattr(view.parent, 'children'):
         #siblings = [child for child in view.parent.children if child != view]
         #for sibling in siblings:
             #if hasattr(sibling, 'deselect'):
                 #sibling.deselect()

        # child deselection
        for child in view.children:
            if hasattr(child, 'deselect'):
                child.deselect()

        if self.propagate_selection_to_data:
            item = self.get_data_item(view.index)
            self.deselect_data_item(item)

    def deselect_list(self, l):
        for view in l:
            self.deselect_item_view(view)
        self.dispatch('on_selection_change')

    def update_for_new_data(self, *args):
        self.delete_cache()
        self.initialize_selection()

    def initialize_selection(self, *args):
        if len(self.selection) > 0:
            self.selection = []
            self.dispatch('on_selection_change')

        self.check_for_empty_selection()

    def check_for_empty_selection(self, *args):
        if not self.allow_empty_selection:
            if len(self.selection) == 0:
                # Select the first item if we have it.
                v = self.get_view(0)
                if v is not None:
                    print 'selecting first data item view', v, v.is_selected
                    self.handle_selection(v)

    def trim_left_of_sel(self, *args):  #pragma: no cover
        '''Cut list items with indices in sorted_keys that are less than the
        index of the first selected item, if there is selection.
        '''
        raise NotImplementedError

    def trim_right_of_sel(self, *args):  #pragma: no cover
        '''Cut list items with indices in sorted_keys that are greater than
        the index of the last selected item, if there is selection.
        '''
        raise NotImplementedError

    def trim_to_sel(self, *args):  #pragma: no cover
        '''Cut list items with indices in sorted_keys that are les than or
        greater than the index of the last selected item, if there is
        selection. This preserves intervening list items within the selected
        range.
        '''
        raise NotImplementedError

    def cut_to_sel(self, *args):  #pragma: no cover
        '''Same as trim_to_sel, but intervening list items within the selected
        range are cut also, leaving only list items that are selected.
        '''
        raise NotImplementedError
