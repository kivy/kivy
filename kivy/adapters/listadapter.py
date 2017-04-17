'''
ListAdapter
=================

.. versionadded:: 1.5

.. note::

    The feature has been deprecated.

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

A :class:`ListAdapter` is an adapter around a python list and adds support
for selection operations. If you wish to have a bare-bones list adapter,
without selection, use a
:class:`~kivy.adapters.simplelistadapter.SimpleListAdapter`.

From an :class:`~kivy.adapters.Adapter`, a :class:`ListAdapter` inherits cls,
template, and args_converter properties and adds others that control selection
behaviour:

* :attr:`~ListAdapter.selection`: a list of selected items.

* :attr:`~ListAdapter.selection_mode`: one of 'single', 'multiple' or 'none'.

* :attr:`~ListAdapter.allow_empty_selection`: a boolean. If False, a selection
  is forced. If True, and only user or programmatic action will change
  selection, it can be empty.

A :class:`~kivy.adapters.dictadapter.DictAdapter` is a subclass of a
:class:`~kivy.adapters.listadapter.ListAdapter`. They both dispatch the
:attr:`~ListAdapter.on_selection_change` event when selection changes.

.. versionchanged:: 1.6.0
    Added data = ListProperty([]), which was probably inadvertently deleted at
    some point. This means that whenever data changes an update will fire,
    instead of having to reset the data object (Adapter has data defined as
    an ObjectProperty, so we need to reset it here to ListProperty). See also
    DictAdapter and its set of data = DictProperty().

'''

__all__ = ('ListAdapter', )

import inspect
from kivy.event import EventDispatcher
from kivy.adapters.adapter import Adapter
from kivy.adapters.models import SelectableDataItem
from kivy.properties import ListProperty
from kivy.properties import DictProperty
from kivy.properties import BooleanProperty
from kivy.properties import OptionProperty
from kivy.properties import NumericProperty
from kivy.lang import Builder


class ListAdapter(Adapter, EventDispatcher):
    '''
    A base class for adapters interfacing with lists, dictionaries or other
    collection type data, adding selection, view creation and management
    functionality.
    '''

    data = ListProperty([])
    '''The data list property is redefined here, overriding its definition as
    an ObjectProperty in the Adapter class. We bind to data so that any
    changes will trigger updates. See also how the
    :class:`~kivy.adapters.DictAdapter` redefines data as a
    :class:`~kivy.properties.DictProperty`.

    :attr:`data` is a :class:`~kivy.properties.ListProperty` and defaults
    to [].
    '''

    selection = ListProperty([])
    '''The selection list property is the container for selected items.

    :attr:`selection` is a :class:`~kivy.properties.ListProperty` and defaults
    to [].
    '''

    selection_mode = OptionProperty('single',
            options=('none', 'single', 'multiple'))
    '''The selection_mode is a string and can be set to one of the following
    values:

       * 'none': use the list as a simple list (no select action). This option
         is here so that selection can be turned off, momentarily or
         permanently, for an existing list adapter.
         A :class:`~kivy.adapters.listadapter.ListAdapter` is not meant to be
         used as a primary no-selection list adapter. Use a
         :class:`~kivy.adapters.simplelistadapter.SimpleListAdapter` for that.

       * 'single': multi-touch/click ignored. Single item selection only.

       * 'multiple': multi-touch / incremental addition to selection allowed;
         may be limited to a count by setting the
         :attr:`~ListAdapter.selection_limit`.

    :attr:`selection_mode` is an :class:`~kivy.properties.OptionProperty` and
    defaults to 'single'.
    '''

    propagate_selection_to_data = BooleanProperty(False)
    '''Normally, data items are not selected/deselected because the data items
    might not have an is_selected boolean property -- only the item view for a
    given data item is selected/deselected as part of the maintained selection
    list. However, if the data items do have an is_selected property, or if
    they mix in :class:`~kivy.adapters.models.SelectableDataItem`, the
    selection machinery can propagate selection to data items. This can be
    useful for storing selection state in a local database or backend database
    for maintaining state in game play or other similar scenarios. It is a
    convenience function.

    To propagate selection or not?

    Consider a shopping list application for shopping for fruits at the
    market. The app allows for the selection of fruits to buy for each day of
    the week, presenting seven lists: one for each day of the week. Each list
    is loaded with all the available fruits, but the selection for each is a
    subset. There is only one set of fruit data shared between the lists, so
    it would not make sense to propagate selection to the data because
    selection in any of the seven lists would clash and mix with that of the
    others.

    However, consider a game that uses the same fruits data for selecting
    fruits available for fruit-tossing. A given round of play could have a
    full fruits list, with fruits available for tossing shown selected. If the
    game is saved and rerun, the full fruits list, with selection marked on
    each item, would be reloaded correctly if selection is always propagated to
    the data. You could accomplish the same functionality by writing code to
    operate on list selection, but having selection stored in the data
    ListProperty might prove convenient in some cases.

    .. note::

        This setting should be set to True if you wish to initialize the view
        with item views already selected.

    :attr:`propagate_selection_to_data` is a
    :class:`~kivy.properties.BooleanProperty` and defaults to False.
    '''

    allow_empty_selection = BooleanProperty(True)
    '''The allow_empty_selection may be used for cascading selection between
    several list views, or between a list view and an observing view. Such
    automatic maintenance of the selection is important for all but simple
    list displays. Set allow_empty_selection to False and the selection is
    auto-initialized and always maintained, so any observing views
    may likewise be updated to stay in sync.

    :attr:`allow_empty_selection` is a
    :class:`~kivy.properties.BooleanProperty` and defaults to True.
    '''

    selection_limit = NumericProperty(-1)
    '''When the :attr:`~ListAdapter.selection_mode` is 'multiple' and the
    selection_limit is
    non-negative, this number will limit the number of selected items. It can
    be set to 1, which is equivalent to single selection. If selection_limit is
    not set, the default value is -1, meaning that no limit will be enforced.

    :attr:`selection_limit` is a :class:`~kivy.properties.NumericProperty` and
    defaults to -1 (no limit).
    '''

    cached_views = DictProperty({})
    '''View instances for data items are instantiated and managed by the
    adapter. Here we maintain a dictionary containing the view
    instances keyed to the indices in the data.

    This dictionary works as a cache. get_view() only asks for a view from
    the adapter if one is not already stored for the requested index.

    :attr:`cached_views` is a :class:`~kivy.properties.DictProperty` and
    defaults to {}.
    '''

    __events__ = ('on_selection_change', )

    def __init__(self, **kwargs):
        super(ListAdapter, self).__init__(**kwargs)

        fbind = self.fbind
        fbind('selection_mode', self.selection_mode_changed)
        fbind('allow_empty_selection', self.check_for_empty_selection)
        fbind('data', self.update_for_new_data)

        self.update_for_new_data()

    def delete_cache(self, *args):
        self.cached_views = {}

    def get_count(self):
        return len(self.data)

    def get_data_item(self, index):
        if index < 0 or index >= len(self.data):
            return None
        return self.data[index]

    def selection_mode_changed(self, *args):
        if self.selection_mode == 'none':
            for selected_view in self.selection:
                self.deselect_item_view(selected_view)
        else:
            self.check_for_empty_selection()

    def get_view(self, index):
        if index in self.cached_views:
            return self.cached_views[index]
        item_view = self.create_view(index)
        if item_view:
            self.cached_views[index] = item_view
        return item_view

    def create_view(self, index):
        '''This method is more complicated than the ones in the
        :class:`~kivy.adapters.adapter.Adapter` and
        :class:`~kivy.adapters.simplelistadapter.SimpleListAdapter` classes
        because here we create bindings for the data items and their children
        back to the *self.handle_selection()* event. We also perform
        other selection-related tasks to keep item views in sync with the data.
        '''
        item = self.get_data_item(index)
        if item is None:
            return None

        item_args = self.args_converter(index, item)

        item_args['index'] = index

        cls = self.get_cls()
        if cls:
            view_instance = cls(**item_args)
        else:
            view_instance = Builder.template(self.template, **item_args)

        if self.propagate_selection_to_data:
            # The data item must be a subclass of SelectableDataItem, or must
            # have an is_selected boolean or function, so it has is_selected
            # available. If is_selected is unavailable on the data item, an
            # exception is raised.
            #
            if isinstance(item, SelectableDataItem):
                if item.is_selected:
                    self.handle_selection(view_instance)
            elif type(item) == dict and 'is_selected' in item:
                if item['is_selected']:
                    self.handle_selection(view_instance)
            elif hasattr(item, 'is_selected'):
                if (inspect.isfunction(item.is_selected) or
                        inspect.ismethod(item.is_selected)):
                    if item.is_selected():
                        self.handle_selection(view_instance)
                else:
                    if item.is_selected:
                        self.handle_selection(view_instance)
            else:
                msg = "ListAdapter: unselectable data item for {0}"
                raise Exception(msg.format(index))

        view_instance.bind(on_release=self.handle_selection)

        for child in view_instance.children:
            child.bind(on_release=self.handle_selection)

        return view_instance

    def on_selection_change(self, *args):
        '''on_selection_change() is the default handler for the
        on_selection_change event. You can bind to this event to get notified
        of selection changes.

        :Parameters:
            adapter: :class:`~ListAdapter` or subclass
                The instance of the list adapter where the selection changed.
                Use the adapters :attr:`selection` property to see what has
                been selected.
        '''
        pass

    def handle_selection(self, view, hold_dispatch=False, *args):
        if view not in self.selection:
            if self.selection_mode in ['none', 'single'] and \
                    len(self.selection) > 0:
                for selected_view in self.selection:
                    self.deselect_item_view(selected_view)
            if self.selection_mode != 'none':
                if self.selection_mode == 'multiple':
                    if self.allow_empty_selection:
                        # If < 0, selection_limit is not active.
                        if self.selection_limit < 0:
                            self.select_item_view(view)
                        else:
                            if len(self.selection) < self.selection_limit:
                                self.select_item_view(view)
                    else:
                        self.select_item_view(view)
                else:
                    self.select_item_view(view)
        else:
            if len(self.selection) == 1 and not self.allow_empty_selection:
                # Maintain selection rather than always defaulting to first
                # item. This probably invalidates the next if section, but I
                # am unable to test all corner cases out, and leaving it in
                # does not hurt anything.
                pass
            else:
                self.deselect_item_view(view)
            if self.selection_mode != 'none':
                # If the deselection makes selection empty, the following call
                # will check allows_empty_selection, and if False, will
                # select the first item. If view happens to be the first item,
                # this will be a reselection, and the user will notice no
                # change, except perhaps a flicker.
                #
                self.check_for_empty_selection()

        if not hold_dispatch:
            self.dispatch('on_selection_change')

    def select_data_item(self, item):
        self.set_data_item_selection(item, True)

    def deselect_data_item(self, item):
        self.set_data_item_selection(item, False)

    def set_data_item_selection(self, item, value):
        if isinstance(item, SelectableDataItem):
            item.is_selected = value
        elif type(item) == dict:
            item['is_selected'] = value
        elif hasattr(item, 'is_selected'):
            if (inspect.isfunction(item.is_selected) or
                    inspect.ismethod(item.is_selected)):
                item.is_selected()
            else:
                item.is_selected = value

    def select_item_view(self, view):
        view.select()
        view.is_selected = True
        self.selection.append(view)

        # [TODO] sibling selection for composite items
        #        Needed? Or handled from parent?
        #        (avoid circular, redundant selection)
        # if hasattr(view, 'parent') and hasattr(view.parent, 'children'):
        #     siblings = [child for child in view.parent.children \
        #                 if child != view]
        #     for sibling in siblings:
        #         if hasattr(sibling, 'select'):
        #             sibling.select()

        if self.propagate_selection_to_data:
            data_item = self.get_data_item(view.index)
            self.select_data_item(data_item)

    def select_list(self, view_list, extend=True):
        '''The select call is made for the items in the provided view_list.

        Arguments:

            view_list: the list of item views to become the new selection, or
            to add to the existing selection

            extend: boolean for whether or not to extend the existing list
        '''
        if not extend:
            self.selection = []

        for view in view_list:
            self.handle_selection(view, hold_dispatch=True)

        self.dispatch('on_selection_change')

    def deselect_item_view(self, view):
        view.deselect()
        view.is_selected = False
        self.selection.remove(view)

        # [TODO] sibling deselection for composite items
        #        Needed? Or handled from parent?
        #        (avoid circular, redundant selection)
        # if hasattr(view, 'parent') and hasattr(view.parent, 'children'):
        #     siblings = [child for child in view.parent.children \
        #                 if child != view]
        #     for sibling in siblings:
        #         if hasattr(sibling, 'deselect'):
        #             sibling.deselect()

        if self.propagate_selection_to_data:
            item = self.get_data_item(view.index)
            self.deselect_data_item(item)

    def deselect_list(self, l):
        for view in l:
            self.handle_selection(view, hold_dispatch=True)

        self.dispatch('on_selection_change')

    # [TODO] Could easily add select_all() and deselect_all().

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
                    self.handle_selection(v)

    # [TODO] Also make methods for scroll_to_sel_start, scroll_to_sel_end,
    #        scroll_to_sel_middle.

    def trim_left_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are less than the
        index of the first selected item if there is a selection.
        '''
        if len(self.selection) > 0:
            first_sel_index = min([sel.index for sel in self.selection])
            self.data = self.data[first_sel_index:]

    def trim_right_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are greater than
        the index of the last selected item if there is a selection.
        '''
        if len(self.selection) > 0:
            last_sel_index = max([sel.index for sel in self.selection])
            print('last_sel_index', last_sel_index)
            self.data = self.data[:last_sel_index + 1]

    def trim_to_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are less than or
        greater than the index of the last selected item if there is a
        selection. This preserves intervening list items within the selected
        range.
        '''
        if len(self.selection) > 0:
            sel_indices = [sel.index for sel in self.selection]
            first_sel_index = min(sel_indices)
            last_sel_index = max(sel_indices)
            self.data = self.data[first_sel_index:last_sel_index + 1]

    def cut_to_sel(self, *args):
        '''Same as trim_to_sel, but intervening list items within the selected
        range are also cut, leaving only list items that are selected.
        '''
        if len(self.selection) > 0:
            self.data = self.selection
