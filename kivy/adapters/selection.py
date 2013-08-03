'''
Selection
=================

.. versionadded:: 1.8

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

:class:`Selection` provides selection operations for adapters and controllers.

Elements that control selection behaviour:

* *selection*, a list of selected items.

* *selection_mode*, 'single', 'multiple', 'none'

* *allow_empty_selection*, a boolean -- If False, a selection is forced. If
  True, and only user or programmatic action will change selection, it can
  be empty.

Users of this class dispatch the *on_selection_change* event.

    :Events:
        `on_selection_change`: (view, view list )
            Fired when selection changes

.. versionchanged:: 1.8.0

    Broke this code out of :class:`ListAdapter` into a separate mixin class
    that is used in Adapter. This way all adapters have selection available.

    Added a new bind_selection_to_children property to allow control of
    selection for composite widgets.

    Added convenience methods, get_selection() and get_first_selected_item().
'''

__all__ = ('Selection', )

import inspect
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.adapters.models import SelectableDataItem
from kivy.properties import BooleanProperty
from kivy.properties import DictProperty
from kivy.properties import ListProperty
from kivy.properties import NumericProperty
from kivy.properties import ObjectProperty
from kivy.properties import ObservableList
from kivy.properties import OptionProperty
from kivy.properties import StringProperty
from kivy.lang import Builder


class Selection(EventDispatcher):
    '''
    A base class for adapters and controllers interfacing with lists,
    dictionaries or other collection type data, adding selection, view creation
    and management functonality.
    '''

    selection = ListProperty([])
    '''The selection list property is the container for selected items.

    :data:`selection` is a :class:`~kivy.properties.ListProperty` and defaults
    to [].
    '''

    selection_mode = OptionProperty('single',
            options=('none', 'single', 'multiple'))
    '''Selection modes:

       * *none*, use the list as a simple list (no select action). This option
         is here so that selection can be turned off, momentarily or
         permanently, for an existing list adapter.
         A :class:`~kivy.adapters.listadapter.ListAdapter` is not meant to be
         used as a primary no-selection list adapter.  Use a
         :class:`~kivy.adapters.simplelistadapter.SimpleListAdapter` for that.

       * *single*, multi-touch/click ignored. Single item selection only.

       * *multiple*, multi-touch / incremental addition to selection allowed;
         may be limited to a count by selection_limit

    :data:`selection_mode` is an :class:`~kivy.properties.OptionProperty` and
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

    NOTE: This would probably be better named as sync_selection_with_data().

    To propagate selection or not?

    Consider a shopping list application for shopping for fruits at the
    market. The app allows for the selection of fruits to buy for each day of
    the week, presenting seven lists: one for each day of the week. Each list is
    loaded with all the available fruits, but the selection for each is a
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

    :data:`propagate_selection_to_data` is a
    :class:`~kivy.properties.BooleanProperty` and defaults to False.
    '''

    allow_empty_selection = BooleanProperty(True)
    '''The allow_empty_selection may be used for cascading selection between
    several list views, or between a list view and an observing view. Such
    automatic maintenance of the selection is important for all but simple
    list displays. Set allow_empty_selection to False and the selection is
    auto-initialized and always maintained, so any observing views
    may likewise be updated to stay in sync.

    :data:`allow_empty_selection` is a
    :class:`~kivy.properties.BooleanProperty` and defaults to True.
    '''

    selection_limit = NumericProperty(-1)
    '''When the selection_mode is multiple and the selection_limit is
    non-negative, this number will limit the number of selected items. It can
    be set to 1, which is equivalent to single selection. If selection_limit is
    not set, the default value is -1, meaning that no limit will be enforced.

    :data:`selection_limit` is a :class:`~kivy.properties.NumericProperty` and
    defaults to -1 (no limit).
    '''

    bind_selection_to_children = BooleanProperty(True)
    '''Should the children of selectable list items have their selection follow
    that of their parent (if they are themselves selectable)?

    :data:`bind_selection_to_children` is a
    :class:`~kivy.properties.BooleanProperty` and defaults to True (There will
    be a call to select/deselect children of any list item when that item is
    itself selected/deselected.).
    '''

    # TODO: Evaluate the need for this. If this is added, how will the bind
    #       call work? (on_release here is not a string, but an arg):
    #
    #           view_instance.bind(on_release=self.handle_selection)
    #
    # selection_triggering_event = StringProperty('on_release')
    # '''What is the name of the event fired from list items to affect
    # selection?
    #
    # :data:`selection_triggering_event` is a
    # :class:`~kivy.properties.StringProperty` and defaults to the Kivy event
    # on_release, which is the typical case for buttons.
    # '''

    __events__ = ('on_selection_change', )

    def __init__(self, **kwargs):
        super(Selection, self).__init__(**kwargs)

        self.bind(selection_mode=self.selection_mode_changed,
                  allow_empty_selection=self.check_for_empty_selection)

        self.initialize_selection()

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

    def on_selection_change(self, *args):
        '''on_selection_change() is the default handler for the
        on_selection_change event.
        '''
        pass

    def get_selection(self):
        '''A convenience method.
        '''
        return self.selection

    def get_first_selected_item(self):
        '''A convenience method.
        '''
        return self.selection[0] if self.selection else None

    # TODO: The change event here is called on_selection_change. This is not
    # consistent with general use, because there is no selection_change
    # property, to which the on_ prefix has been added. The reason why doing
    # selection this way, by making the API for binding as:
    #
    #     ...list.adapter.bind(on_selection_change=self.some_func) ...
    #
    # was related to batch updating of selection for the select_list() and
    # deselect_list() methods, which call here with hold_dispatch=True. This
    # can be changed to pass in a temporary selection list, tmp_selection. If
    # tmp_selection is not None, work off a copy somehow and return it. Then,
    # the select_list() and deselect_list() methods will set to selection on
    # return. This way, we can simplify the API to:
    #
    #     ...list.adapter.bind(selection=self.some_func) ...
    #
    # and, we will be better prepared to make a simpler usage in kv also.
    #
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
            self.deselect_item_view(view)
            if self.selection_mode != 'none':
                #
                # If the deselection makes selection empty, the following call
                # will check allows_empty_selection, and if False, will
                # select the first item. If view happens to be the first item,
                # this will be a reselection, and the user will notice no
                # change, except perhaps a flicker.
                #
                # TODO: Does the above paragraph describe a timing issue that
                #       is hard to predict? If so, clarify. Otherwise, clarify.
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
            if 'is_selected' in item:
                item['is_selected'] = value
        elif hasattr(item, 'is_selected'):
            # TODO: Change this to use callable().
            if (inspect.isfunction(item.is_selected)
                    or inspect.ismethod(item.is_selected)):
                item.is_selected()
            else:
                item.is_selected = value

    def select_item_view(self, view):

        has_selection = False

        if hasattr(view, 'select'):
            # TODO: Change this to use callable().
            if (inspect.isfunction(view.select)
                    or inspect.ismethod(view.select)):
                view.select()
                has_selection = True

        # TODO: The handling of is_selected is not put here as an else clause,
        #       so if calling select() has already set an is_selected property
        #       this will be an unneccessary (redundant) reset.

        if hasattr(view, 'is_selected'):
            # TODO: Change this to use callable().
            if (inspect.isfunction(view.is_selected)
                    or inspect.ismethod(view.is_selected)):
                view.is_selected()
            else:
                view.is_selected = True
            has_selection = True

        if has_selection:
            self.selection.append(view)

        # [TODO] sibling selection for composite items
        #        Needed? Or handled from parent?
        #        (avoid circular, redundant selection)
        #if hasattr(view, 'parent') and hasattr(view.parent, 'children'):
         #siblings = [child for child in view.parent.children if child != view]
         #for sibling in siblings:
             #if hasattr(sibling, 'select'):
                 #sibling.select()

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
        #if hasattr(view, 'parent') and hasattr(view.parent, 'children'):
         #siblings = [child for child in view.parent.children if child != view]
         #for sibling in siblings:
             #if hasattr(sibling, 'deselect'):
                 #sibling.deselect()

        if self.propagate_selection_to_data:
            item = self.get_data_item(view.index)
            self.deselect_data_item(item)

    def deselect_list(self, l):
        for view in l:
            self.handle_selection(view, hold_dispatch=True)

        self.dispatch('on_selection_change')

    # [TODO] Could easily add select_all() and deselect_all().

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
