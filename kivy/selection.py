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
        `on_selection_change`: (selectable_item, selectable_item list )
            Fired when selection changes, more generally, as when selection is
            set entirely, or when any operation is performed, per the gross
            dispatching done via ObservableList.
        `on_selection`: (selectable_item, selectable_item list, op_info)
            Fired when selection changes, as when selection is set entirely, or
            specifically on a per-op basis. When any operation is performed,
            dispatching done via OpObservableList, which sends along an op_info
            argument containing details about what changed.

.. versionchanged:: 1.8.0

    Broke this code out of :class:`ListAdapter` into a separate mixin class
    that is used in Adapter. This way all adapters have selection available.

    Added a new bind_selection_to_children property to allow control of
    selection for composite widgets.

    Added convenience methods, get_selection() and get_first_selected_item().

    Changed the way select_list() and deselect_list() avoid uneeded
    dispatching, which allows the API to include the usual binding to
    selection, as compared to the original way, where only binding to
    on_selection_change was suggested.

    Added use of OpObservableList in the selection list, mainly to use a new
    batch_delete() method made for revised select_list() and deselect_list()
    methods. This is part of a change to allow selection to be observed
    directly, in addition to the already available on_selection_change event.
    Now either of the following will work, but have differing types of events
    associated:

        1) ...adapter.bind(selection=some_method)
             or
           ...adapter.bind(on_selection=some_method)

            Events are per-op dispatches, with an additional argument, op_info,
            available if an observer needs more detailed change info.

        2) ...adapter.bind(on_selection_change=some_method)

            Events are the regular type, where dispatches happen as a result of
            the list being set, or as a result of any change (There is no
            op_info detail available).

    Moved selection.py out of kivy/adapters to kivy/, to allow use in
    traditional controllers, which do not do item view creation and caching
    covered by adapters.

    Changed references to view, item_view, and view_list to selectable_item,
    item, and selectable_item_list, to make Selection work more easily with
    non-view items, as are used in traditional controllers. Also, changed many
    references to data item to model data item, to make the distinction between
    selectable data items, the items for which selection is maintained, and
    associated model data. Selectable items are view instances for adapters,
    but they may be normal Python class instances for controllers. Model data
    can be anything, even Python class instances, but more typically consists
    of primitives such as integers, floats, strings, and so on.

    Deprecated propagate_selection_to_data, in favor of sync_with_model_data.
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
from kivy.properties import OpObservableList
from kivy.properties import OptionProperty
from kivy.properties import StringProperty
from kivy.lang import Builder


class Selection(EventDispatcher):
    '''
    A base class for adapters and controllers interfacing with lists,
    dictionaries or other collections.
    '''

    selection = ListProperty([], cls=OpObservableList)
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
    '''Deprecated, in favor of sync_with_model_data.
    '''

    sync_with_model_data = BooleanProperty(False)
    '''Normally, model data items are not selected/deselected because the model
    data items might not have an is_selected boolean property -- only the
    selectable_item for a given model data item is selected/deselected as part
    of the maintained selection list. However, if the model data items do have
    an is_selected property, or if they mix in
    :class:`~kivy.adapters.models.SelectableDataItem`, the selection machinery
    can propagate selection to model data items. This can be useful for storing
    selection state in a local database or backend database for maintaining
    state in game play or other similar scenarios. It is a convenience
    function.

    To propagate selection or not?

    Consider a shopping list application for shopping for fruits at the market.
    The app allows for the selection of fruits to buy for each day of the week,
    presenting seven lists: one for each day of the week. Each list is loaded
    with all the available fruits, but the selection for each is a subset.
    There is only one set of fruit model data shared between the lists, so it
    would not make sense to propagate selection to the model data because
    selection in any of the seven lists would clash and mix with that of the
    others.

    However, consider a game that uses the same fruits model data for selecting
    fruits available for fruit-tossing. A given round of play could have a full
    fruits list, with fruits available for tossing shown selected. If the game
    is saved and rerun, the full fruits list, with selection marked on each
    item, would be reloaded correctly if selection is always propagated to the
    model data. You could accomplish the same functionality by writing code to
    operate on list selection, but having selection stored in the data
    ListProperty might prove convenient in some cases.

    :data:`sync_with_model_data` is a
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
        # Cover propagate_selection_to_data deprecation.
        if 'propagate_selection_to_data' in kwargs:
            kwargs['sync_with_model_data'] = \
                    kwargs['propagate_selection_to_data']
        super(Selection, self).__init__(**kwargs)

        # Check for required methods:
        if not hasattr(self, 'get_data_item'):
            raise Exception(('Selection: mixing in Selection requires '
                             'get_data_item().'))

        if (not hasattr(self, 'get_view')
                and not hasattr(self, 'get_selectable_item')):
            raise Exception(('Selection: mixing in Selection requires '
                             'get_view() or get_selectable_item().'))

        if (hasattr(self, 'get_view')
                and hasattr(self, 'get_selectable_item')):
            raise Exception(('Selection: mixing in Selection requires '
                             'choosing between get_view() and '
                             'get_selectable_item().'))

        self.bind(selection_mode=self.selection_mode_changed,
                  allow_empty_selection=self.check_for_empty_selection)

        self.initialize_selection()

    def selection_mode_changed(self, *args):
        if self.selection_mode == 'none':
            for selected in self.selection:
                self.deselect_item(selected)
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

    def handle_selection(self, item, hold_dispatch=False, *args):
        if item not in self.selection:
            if self.selection_mode in ['none', 'single'] and \
                    len(self.selection) > 0:
                for selected in self.selection:
                    if hold_dispatch:
                        return 'DESELECT'
                    else:
                        self.deselect_item(selected)
            if self.selection_mode != 'none':
                if self.selection_mode == 'multiple':
                    if self.allow_empty_selection:
                        # If < 0, selection_limit is not active.
                        if self.selection_limit < 0:
                            if hold_dispatch:
                                return 'SELECT'
                            else:
                                self.select_item(item)
                        else:
                            if len(self.selection) < self.selection_limit:
                                if hold_dispatch:
                                    return 'SELECT'
                                else:
                                    self.select_item(item)
                    else:
                        if hold_dispatch:
                            return 'SELECT'
                        else:
                            self.select_item(item)
                else:
                    if hold_dispatch:
                        return 'SELECT'
                    else:
                        self.select_item(item)
        else:
            if hold_dispatch:
                return 'DESELECT-AND-CHECK'
            else:
                self.deselect_item(item)
            if self.selection_mode != 'none':
                #
                # If the deselection makes selection empty, the following call
                # will check allows_empty_selection, and if False, will
                # select the first item. If item happens to be the first item,
                # this will be a reselection, and the user will notice no
                # change, except perhaps a flicker.
                #
                # TODO: Does the above paragraph describe a timing issue that
                #       is hard to predict? If so, clarify. Otherwise, clarify.
                #
                self.check_for_empty_selection()

        if not hold_dispatch:
            self.dispatch('on_selection_change')

    def select_model_data_item(self, item):
        self.set_model_data_item_selection(item, True)

    def deselect_model_data_item(self, item):
        self.set_model_data_item_selection(item, False)

    def set_model_data_item_selection(self, item, value):
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

    def select_item(self, item, add_to_selection=True):

        has_selection = False

        if hasattr(item, 'select'):
            # TODO: Change this to use callable().
            if (inspect.isfunction(item.select)
                    or inspect.ismethod(item.select)):
                item.select()
                has_selection = True

        # TODO: The check for is_selected is not put here as an else clause of
        #       the if above, which could lead to redundant or unwanted
        #       behavior, unless the API is made clear that select() and
        #       deselect() are used for the UI changes only, and not for
        #       setting is_selected. This can be cleared up with a more
        #       explicit was_selected() and was_deselected() or something
        #       similiar, which is a style more common for UI reacting method
        #       names. There is another TODO that suggests a "selection
        #       effects" enum to be used in a system of predefined, and
        #       customizable selection effects.

        if hasattr(item, 'is_selected'):
            # TODO: Change this to use callable().
            item.is_selected = True
            has_selection = True

        # [TODO] sibling selection for composite items
        #        Needed? Or handled from parent?
        #        (avoid circular, redundant selection)
        #if hasattr(item, 'parent') and hasattr(item.parent, 'children'):
         #siblings = [child for child in item.parent.children if child != item]
         #for sibling in siblings:
             #if hasattr(sibling, 'select'):
                 #sibling.select()

        if self.sync_with_model_data:
            self.select_model_data_item(self.get_data_item(item.index))

        if has_selection and add_to_selection:
            self.selection.append(item)

    def select_list(self, selectable_items, extend=True):
        '''The select call is made for the items in the provided selectable_items.

        Arguments:

            selectable_items: the list of items to become the new selection, or
            to add to the existing selection

            extend: boolean for whether or not to extend the existing list
        '''

        if not extend:
            self.selection = []

        self._handle_batch(selectable_items)

    def deselect_list(self, selectable_items):
        self._handle_batch(selectable_items)

    def _handle_batch(self, selectable_items):
        # Use hold_dispatch to keep handle_selection() from calling select or
        # deselect methods, which avoids changing selection. Collect the select
        # and deselect ops that handle_selection() reports are needed (this way
        # we use the same logic there), and then do the ops in a quick loop,
        # followed by a batch call for the actual selection list changes.

        ops = []
        for item in selectable_items:
            ops.append(self.handle_selection(item, hold_dispatch=True))

        check_for_empty_selection = False

        # When we call the select and deselect methods, have them do everything
        # except actually changing selection -- we'll do a batch op instead.
        #
        # Accumulate the adds and deletes for the batch calls.
        #
        sel_adds = []
        sel_deletes = []
        for op, item in zip(ops, selectable_items):
            if op == 'SELECT':
                self.select_item(item, add_to_selection=False)
                sel_adds.append(item)
            elif op == 'DESELECT':
                self.deselect_item(item, remove_from_selection=False)
                sel_deletes.append(item)
            else:  # DESELECT-CHECK == deselect and check_for_empty_selection()
                self.deselect_item(item, remove_from_selection=False)
                sel_deletes.append(self.selection.index(item))
                check_for_empty_selection = True

        # Now do the ops as batch calls:
        if sel_adds:
            self.selection.extend(sel_adds)
        elif sel_deletes:
            # sel_deletes contains indices.
            self.selection.batch_delete(reversed(sel_deletes))

        # Also, see the logic in handle_selection(), which includes calling
        # check_for_empty_selection() if the item is in selection and needs
        # deselection. We use that information to do the check and call here
        # after the batch ops.
        if check_for_empty_selection:
            if self.selection_mode != 'none':
                self.check_for_empty_selection()

        self.dispatch('on_selection_change')

    def deselect_item(self, item, remove_from_selection=True):

        if hasattr(item, 'deselect'):
            # TODO: Change this to use callable().
            if (inspect.isfunction(item.deselect)
                    or inspect.ismethod(item.deselect)):
                item.deselect()
                has_selection = True

        # TODO: See note in same place within select_item(), above.

        if hasattr(item, 'is_selected'):
            # TODO: Change this to use callable().
            item.is_selected = False
            has_selection = True

        # [TODO] sibling deselection for composite items
        #        Needed? Or handled from parent?
        #        (avoid circular, redundant selection)
        #if hasattr(item, 'parent') and hasattr(item.parent, 'children'):
         #siblings = [child for child in item.parent.children if child != item]
         #for sibling in siblings:
             #if hasattr(sibling, 'deselect'):
                 #sibling.deselect()

        if self.sync_with_model_data:
            self.deselect_model_data_item(self.get_data_item(item.index))

        if has_selection and remove_from_selection:
            self.selection.remove(item)

    def initialize_selection(self, *args):
        if len(self.selection) > 0:
            self.selection = []
            self.dispatch('on_selection_change')

        self.check_for_empty_selection()

    def check_for_empty_selection(self, *args):
        if not self.allow_empty_selection:
            if len(self.selection) == 0:
                # Select the first item if we have it.
                if hasattr(self, 'get_view'):
                    view = self.get_view(0)
                    if view is not None:
                        self.handle_selection(view)
                elif hasattr(self, 'get_selectable_item'):
                    item = self.get_selectable_item(0)
                    self.handle_selection(item)
