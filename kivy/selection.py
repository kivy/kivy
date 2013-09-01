'''
Selection
=========

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

    :Events:
        `on_selection_change`: (selectable_item, selectable_item list )
            Fired when selection changes, more generally, as when selection is
            set entirely, or when any operation is performed, per the gross
            dispatching done via ObservableList.

.. versionchanged:: 1.8.0

    Broke this code out of :class:`ListAdapter` into a separate mixin class
    that is used in Adapter. This way all adapters have selection available.

    Added convenience methods, get_selection() and get_first_selected_item().

    Changed the way select_list() and deselect_list() avoid uneeded
    dispatching, which allows the API to include the usual binding to
    selection, as compared to the original way, where only binding to
    on_selection_change was suggested.

    Added a batch_delete() to ObservableList in the selection list This method
    is for calling from revised select_list() and deselect_list() methods. This
    is part of a change to allow selection to be observed directly, to replace
    the on_selection_change event.  Now either of the following will work, but
    the first is preferred:

        1) ...adapter.bind(selection=some_method)

        2) ...adapter.bind(on_selection_change=some_method)

    Events are the normal type, where dispatches happen as a result of the
    list being set, or as a result of any change.

    Moved selection.py out of kivy/adapters to kivy/, to allow use in
    traditional controllers, which do not do item view creation and caching
    covered by adapters.

    Changed references to view, item_view, and view_list to selectable_item,
    item, and selectable_item_list, to make it clear that Selection work with
    non-view items, as are used in traditional controllers. Also, changed many
    references for data item to model data item, to make the distinction
    between selectable data items, the items for which selection is maintained,
    and associated model data. Selectable items are view instances for
    adapters, but they may be normal Python class instances for controllers.
    Model data can be anything, even Python class instances, but more typically
    consists of primitives such as integers, floats, strings, or dicts with
    those, etc.

    Removed propagate_selection_to_data, replacing it with a new system for
    selection_scheme and selection_update_method.

    Opened up selection to be passed as an initial argument, and to be modified
    externally. This required use of OpObservableList in the selection list, so
    that reactions can happen here on a detailed basis. These reactions are
    handled in a newly associated SelectionOpHandler, which works in concert
    with OpObservableList, in the manner this system works in list controllers
    and adapters. And the reactions entail checking that the values in the
    selection list qualify, that they also exist in data (or in sorted_keys,
    for the case of DictAdapter, one of the users of Selection).
'''

__all__ = ('Selection', 'SelectionTool', )

from kivy.enums import Enum
from kivy.enums import selection_update_methods
from kivy.enums import selection_schemes
from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty
from kivy.properties import ListOpHandler
from kivy.properties import ListOpInfo
from kivy.properties import ListProperty
from kivy.properties import NumericProperty
from kivy.properties import ObjectProperty
from kivy.properties import OpObservableList
from kivy.properties import OptionProperty


_selection_ops = Enum(['SELECT', 'DESELECT', 'DESELECT_AND_CHECK'])


class SelectionTool(EventDispatcher):
    '''A SelectionTool is a wrapper on a BooleanProperty, with convenience
    methods, supplanted with binding methods for binding with another ksel.

    .. versionadded:: 1.8

    '''

    selected = BooleanProperty(False)

    def __init__(self, value):
        super(SelectionTool, self).__init__(**{'selected': value})

    def select(self):
        self.selected = True

    def deselect(self):
        self.selected = False

    def is_selected(self):
        return self.selected

    def bind_to(self, func):
        self.bind(selected=func)

    def bind_to_ksel(self, ksel):
        self.bind(selected=ksel.setter('selected'))

    def bind_from_ksel(self, ksel):
        ksel.bind(selected=self.setter('selected'))


class Selection(EventDispatcher):
    '''
    A base class for adapters and controllers interfacing with lists,
    dictionaries or other collections.

    .. versionchanged:: 1.8

        Substantial changes were made to the selection system.

    '''

    selection = ListProperty([], cls=OpObservableList)
    '''The selection list property is the container for selected items.

    :data:`selection` is a :class:`~kivy.properties.ListProperty` and defaults
    to [].

    .. versionadded:: 1.5

    .. versionchanged:: 1.8

        Made selection use OpObservableList, which is associated with the use
        of a new SelectionOpHandler.
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

    .. versionadded:: 1.5

    '''

    allow_empty_selection = BooleanProperty(True)
    '''The allow_empty_selection may be used for cascading selection between
    several list views, or between a list view and an observing view. Such
    automatic maintenance of the selection is important for all but simple
    list displays. Set allow_empty_selection to False and the selection is
    auto-initialized and always maintained, so any observing views
    may likewise be updated to stay in sync.

    .. versionadded:: 1.5

    :data:`allow_empty_selection` is a
    :class:`~kivy.properties.BooleanProperty` and defaults to True.

    '''

    selection_limit = NumericProperty(None)
    '''When the selection_mode is multiple and the selection_limit is
    non-negative, this number will limit the number of selected items. It can
    be set to 1, which is equivalent to single selection. If selection_limit is
    None, no limit will be enforced.

    .. versionadded:: 1.5

    :data:`selection_limit` is a :class:`~kivy.properties.NumericProperty` and
    defaults to None (no limit).

    '''

    selection_update_method = OptionProperty(
            selection_update_methods.NOTIFY,
            options=tuple(selection_update_methods))
    '''
    Selection update methods:

        * *NOTIFY*, Use Kivy's events system to notify observers of selectable
          items for changes,

        * *SET*, When selection of either data or view item happens, propagate
          to the associated item by direct call.

    Consider a use of scheme = VIEW_DRIVEN, wherein anytime a view
    item's selection changes, its associated data item is to be selected also.
    In such a scheme, for a select, selection_update_method is either NOTIFY or
    SET, for which one of the following would be done:

        NOTIFY:

            view_instance.ksel.select()
            view_instance.dispatch('selection_changed')

        SET:

            view_instance.ksel.select()

    So, set selection_update_method in combination with setting
    scheme.

    .. versionadded:: 1.8

    :data:`selection_update_method` is an
    :class:`~kivy.properties.OptionProperty` that defaults to NOTIFY.

    '''

    selection_scheme = OptionProperty(
            selection_schemes.VIEW_ON_DATA, options=tuple(selection_schemes))
    '''
    Selection schemes:

        * *VIEW-ON-DATA*, in which selection is confined to views (data items
          are read for parameter values used to create views for them, but they
          are not selected, and their selection state is not read).

        * *VIEW-DRIVEN*, a one-way arrangement, in which selection of view
          items drives the selection of associated data items,

        * *DATA-DRIVEN*, vice-versa, a one-way arrangement, in which
          selection of data items drives the selection of associated view
          items, in addition to UI selection of views,

        * *DATA-VIEW-COUPLED*, a two-way arrangement, in which selection of
          either will be reflected in the other,

        * *OBJECT*, for use on a set of objects that can be anything, from list
          items, dictionary values, objects, event to views, but views for
          which no data items are associated.

    The class that uses selection will always have data, but may or may not
    have views based on that data.

    Examples that use selection and have both views and data include:

        * an adapter, a view-caching and view-creating system,

        * a controller, which does not create views, but may manage them,

        * a state of a statechart, which is most often functioning as a kind of
          controller.

    Examples that use selection on data only include:

        * a list controller of shapes

        * a list controller of searchable items

    For VIEW-DRIVEN, DATA-DRIVEN, and DAVA-VIEW-COUPLED schemes, bindings are
    set up in one or more directions between data items and the views that
    represent them.

    For the OBJECT selection scheme, no bindings are needed, and selection is
    simply set.

    The OBJECT selection scheme is used when there is only one set of items for
    which selection is to be managed. These data can be anything, objects,
    dicts, views, but they are not associated, at least in the context of
    selection, with another set of data.

    The VIEW_ON_DATA scheme is probably more common. Consider a shopping list
    application for shopping for fruits at the market.  Using a ListView, with
    its adapter and selection, the app allows for the selection of fruits to
    buy for each day of the week, presenting seven lists: one for each day of
    the week. Each list is loaded with all the available fruits, but the
    selection for each is a subset.  There is only one set of fruit model data
    shared between the lists, so it would not make sense to sync selection with
    the model data because selection in any of the seven lists would clash and
    mix with that of the others.

    The VIEW_DRIVEN and DATA_VIEW_COUPLED schemes can be used for storing
    selection state in a local database or backend database for maintaining
    state in game play or other similar scenarios.  Consider a game that uses
    the same fruits model data for selecting fruits available for
    fruit-tossing. A given round of play could have a full fruits list, with
    fruits available for tossing shown selected. If the game is saved and
    rerun, the full fruits list, with selection marked on each item, would be
    reloaded correctly if selection is always synced to the model data. You
    could accomplish the same functionality by writing code to operate on list
    selection, but having selection stored in the data might prove to be
    convenient or more efficient.

    The DATA_DRIVEN scheme is appropriate for situations where some external
    source updates selection of the data, and the user interface is to reflect
    that. This is similar to DATA_VIEW_COUPLED. For example, consider a user
    interface tied to some piece of machinery that analyses available tools for
    a task in an assembly plant, based on physical conditions and throughput
    values that limit which tools are viable in realtime. An operator views a
    screen to see what tools are currently available, and selects one for the
    next task.

    .. versionadded:: 1.8

    :data:`selection_scheme` is an :class:`~kivy.properties.OptionProperty`
    that defaults to VIEW_ON_DATA.
    '''

    _is_handling_selection = BooleanProperty(False)

    _selection_source_list = ObjectProperty(None)
    _selection_source_dict = ObjectProperty(None)

    # TODO: Now that selection works as it should as an observable property (in
    #       1.8), the on_selection_change event is perhaps no longer needed?
    __events__ = ('on_selection_change', )

    def __init__(self, **kwargs):

        super(Selection, self).__init__(**kwargs)

        # Selection is used in three different classes. Set the source list
        # based on this info. Compare how the source_list works in
        # ListOpHandler and DictOpHandler.
        # TODO: This deferred import is OK?
        from kivy.adapters.dictadapter import DictAdapter

        if isinstance(self, DictAdapter):
            self._selection_source_list = self.sorted_keys
            self._selection_source_dict = self.data
        else:
            self._selection_source_list = self.data

        self.bind(selection=self.selection_changed)

        self.bind(selection_mode=self.selection_mode_changed,
                  allow_empty_selection=self.check_for_empty_selection)

        # NOTE: We do not call initialize_selection here, as once occurred,
        #       because as of 1.8 selection can be passed in on creation, and
        #       it may be modified externally. We do need to check if an empty
        #       selection list was provided, but that selection is not allowed
        #       to be empty.
        self.check_for_empty_selection()

    def selection_mode_changed(self, *args):
        if self.selection_mode == 'none':
            for selected in self.selection:
                self.deselect_item(selected)
        else:
            self.check_for_empty_selection()

    def on_selection_change(self, *args):
        pass

    def get_selection(self):
        '''A convenience method.
        '''
        return self.selection

    def get_first_selected(self):
        '''A convenience method.
        '''
        return self.selection[0] if self.selection else None

    def get_last_selected(self):
        '''A convenience method.
        '''
        return self.selection[-1] if self.selection else None

    def handle_selection(self, item, hold_dispatch=False, *args):
        return_op = None

        additions = []
        removals = []

        if item not in self.selection:
            if self.selection_mode in ['none', 'single'] and \
                    len(self.selection) > 0:
                for selected in self.selection:
                    if hold_dispatch:
                        return_op = _selection_ops.DESELECT
                    else:
                        self.deselect_item(selected,
                                           remove_from_selection=False)
                        removals.append(selected)
            if self.selection_mode != 'none':
                if self.selection_mode == 'multiple':
                    if self.allow_empty_selection:
                        # If None, selection_limit is not active.
                        if self.selection_limit is None:
                            if hold_dispatch:
                                return_op = _selection_ops.SELECT
                            else:
                                self.select_item(item,
                                                 add_to_selection=False)
                                additions.append(item)
                        else:
                            if len(self.selection) < self.selection_limit:
                                if hold_dispatch:
                                    return_op = _selection_ops.SELECT
                                else:
                                    self.select_item(item,
                                                     add_to_selection=False)
                                    additions.append(item)
                    else:
                        if hold_dispatch:
                            return_op = _selection_ops.SELECT
                        else:
                            self.select_item(item,
                                             add_to_selection=False)
                            additions.append(item)
                else:
                    if hold_dispatch:
                        return_op = _selection_ops.SELECT
                    else:
                        self.select_item(item, add_to_selection=False)
                        additions.append(item)
        else:

            if hold_dispatch:
                return_op = _selection_ops.DESELECT_AND_CHECK
            else:
                self.deselect_item(item, remove_from_selection=False)
                removals.append(item)

        if return_op is not None:
            self._is_handling_selection = False
            return return_op

        selection_copy = list(self.selection)

        for r in removals:
            selection_copy.remove(r)

        for a in additions:
            selection_copy.append(a)

        self._is_handling_selection = True
        self.selection = selection_copy
        self._is_handling_selection = False

        if self.selection_mode != 'none':
            self.check_for_empty_selection()

        if not hold_dispatch:
            self.dispatch('on_selection_change')

    def select_item(self, item, add_to_selection=True):

        ksel = None

        if isinstance(item, dict) and 'ksel' in item:
            ksel = item['ksel']
        elif hasattr(item, 'ksel'):
            ksel = item.ksel

        if ksel:

            ksel.select()

            if (self.selection_scheme in [selection_schemes.VIEW_DRIVEN,
                                          selection_schemes.DATA_VIEW_COUPLED]
                and
                self.selection_update_method == selection_update_methods.SET):

                data_item = self.get_data_item(item.index)

                if isinstance(data_item, dict) and 'ksel' in data_item:
                    data_item['ksel'].select()
                elif hasattr(data_item, 'ksel'):
                    data_item.ksel.select()

        if add_to_selection:
            self.selection.append(item)

    def select_list(self, selectable_items, extend=True):
        '''The select call is made for the items in the provided
        selectable_items.

        Arguments:

            selectable_items: the list of items to become the new selection, or
            to add to the existing selection

            extend: boolean for whether or not to extend the existing list
        '''

        if not extend:
            self._is_handling_selection = True
            self.selection = []
            self._is_handling_selection = False

        # Make sure the items are deselected first.
        for sel in selectable_items:
            self.deselect_item(sel, remove_from_selection=False)

        self._handle_batch(selectable_items)

    def deselect_list(self, selectable_items):

        # Make sure the items are selected first.
        for sel in selectable_items:
            self.select_item(sel, add_to_selection=False)

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
            if op == _selection_ops.SELECT:
                self.select_item(item, add_to_selection=False)
                sel_adds.append(item)
            elif op == _selection_ops.DESELECT:
                self.deselect_item(item, remove_from_selection=False)
                sel_deletes.append(item)
            elif op == _selection_ops.DESELECT_AND_CHECK:
                self.deselect_item(item, remove_from_selection=False)
                sel_deletes.append(self.selection.index(item))
                check_for_empty_selection = True

        # Now do the ops as a batch call:
        if sel_adds:
            self.is_handling_selection = True
            self.selection.extend(sel_adds)
            self.is_handling_selection = False
        elif sel_deletes:
            self.is_handling_selection = True
            # sel_deletes contains indices.
            self.selection.batch_delete(reversed(sel_deletes))
            self.is_handling_selection = False

        # Also, see the logic in handle_selection(), which includes calling
        # check_for_empty_selection() if the item is in selection and needs
        # deselection. We use that information to do the check and call here
        # after the batch ops.
        if check_for_empty_selection:
            if self.selection_mode != 'none':
                self.check_for_empty_selection()

        self.dispatch('on_selection_change')

    def deselect_item(self, item, remove_from_selection=True):

        ksel = None

        if isinstance(item, dict) and 'ksel' in item:
            ksel = item['ksel']
        elif hasattr(item, 'ksel'):
            ksel = item.ksel

        if ksel:

            ksel.deselect()

            if (self.selection_scheme in [selection_schemes.VIEW_DRIVEN,
                                          selection_schemes.DATA_VIEW_COUPLED]
                and
                self.selection_update_method == selection_update_methods.SET):

                data_item = self.get_data_item(item.index)

                if isinstance(data_item, dict) and 'ksel' in data_item:
                    data_item['ksel'].deselect()
                elif hasattr(data_item, 'ksel'):
                    data_item.ksel.deselect()

        if remove_from_selection:
            self.selection.remove(item)

    def initialize_selection(self, *args):
        if len(self.selection) > 0:
            self._is_handling_selection = True
            self.selection = []
            self._is_handling_selection = False
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

    def selection_changed(self, *args):
        '''This method handles adjustments after operations on the selection
        list happen.

        Compare to code in ControllerListOpHandler and AdapterListOpHandler,
        which perform a similar role, except those have to manage cached_views.

        A main difference here is that the primary function is to channel selection
        changes through the system, not to adjust associated values, and to assure
        that selection items conform to the current selection parameters.

        .. versionadded 1.8

        This class reacts to the following operations that are possible for an
        OpObservableList (OOL) instance in a controller:

            handle_add_first_item_op()

                OOL_append
                OOL_extend
                OOL_insert

            handle_add_op()

                OOL_append
                OOL_extend
                OOL_iadd
                OOL_imul

            handle_insert_op()

                OOL_insert

            handle_setitem_op()

                OOL_setitem

            handle_setslice_op()

                OOL_setslice

            handle_delete_op()

                OOL_delitem
                OOL_delslice
                OOL_remove
                OOL_pop

            handle_sort_op()

                OOL_sort
                OOL_reverse

        '''

        if self._is_handling_selection:
            return

        # TODO: args[1] is the modified list -- can utilize?
        if len(args) == 3:
            op_info = args[2]
        else:
            op_info = ListOpInfo('OOL_set', 0, 0)

        # NOTE: At this point in the op handlers for list controller and
        #       adapters, there is a set that here would be:
        #
        #           self.op_info = op_info
        #
        #       This is not done here, because for one thing, it would
        #       overwrite the op_info added by the other systems (they mix in
        #       Selection). If a user of Selection needs op_info, they will get
        #       it in dispatches.

        # The reactions below do the following:
        #
        #     1) Delect the new items (change ksel to show False, which may
        #        cause whatever UI changes this entails, but only momentarily).
        #
        #     2) Select the item or items using the system. This will cause a
        #        change in the normal expected user interface change for
        #        selection, whatever that is for the items.

        op = op_info.op_name
        start_index = op_info.start_index
        end_index = op_info.end_index

        if op == 'OOL_sort_start':
            self.sort_started(*args)

        if op == 'OOL_set':

            self.handle_set()

        elif (len(self.selection) == 1
                and op in ['OOL_append',
                           'OOL_insert',
                           'OOL_extend']):

            self.handle_add_first_item_op()

        else:

            if op in ['OOL_iadd',
                      'OOL_imul',
                      'OOL_append',
                      'OOL_extend']:

                self.handle_add_op()

            elif op in ['OOL_setitem']:

                self.handle_setitem_op(start_index)

            elif op in ['OOL_setslice']:

                self.handle_setslice_op(start_index, end_index)

            elif op in ['OOL_insert']:

                self.handle_insert_op(start_index)

            elif op in ['OOL_delitem',
                        'OOL_delslice',
                        'OOL_remove',
                        'OOL_pop']:

                self.handle_delete_op(start_index, end_index)

            elif op in ['OOL_sort',
                        'OOL_reverse']:

                self.handle_sort_op()

    # NOTE: We do not dispatch here, because handle_selection does dispatching.

    def do_ksel_op(self, op, items):
        # We could be servicing selection for a DictAdapter, in which case
        # items are keys in sorted_keys, with which we must look up the
        # selectable item in the self.data dict. Otherwise, the items are
        # selectables.
        if self._selection_source_dict:
            if op == 'select':
                for key in items:
                    sel = self._selection_source_dict[key]
                    if not sel['ksel'].is_selected():
                        sel['ksel'].select()
            else:
                for key in items:
                    sel = self._selection_source_dict[key]
                    if sel['ksel'].is_selected():
                        sel['ksel'].deselect()
        else:
            for item in items:
                if isinstance(item, dict):
                    ksel = item['ksel']
                else:
                    ksel = item.ksel
                if op == 'select':
                    if not ksel.is_selected():
                        ksel.select()
                else:
                    if ksel.is_selected():
                        ksel.deselect()

    def handle_set(self):

        # Selection has been set externally, so the items in the
        # _selection_source_list which were previously part of selection are
        # still selected. Find them and unselect them.
        self.do_ksel_op('deselect', self._selection_source_list)

        # Now we can treat it as an add op.
        self.handle_add_op()

    def handle_add_first_item_op(self):
        '''Special case: deletion resulted in no data, leading up to the
        present op, which adds one or more items.
        '''

        self.handle_add_op()

    def handle_add_op(self):

        if self.selection_mode == 'none' and self.selection:
            self.selection = []

        if (self.selection_mode == 'single'
                and len(self.selection) > 1):
            self.selection = self.selection[:1]

        if (self.selection_mode == 'multiple'
                and self.selection_limit
                and len(self.selection) > self.selection_limit):
            self.selection = \
                    self.selection[:self.selection_limit]

        self.do_ksel_op('select', self.selection)

    def handle_insert_op(self, index):

        self.handle_add_op()

    def handle_setitem_op(self, index):

        # Find the item formerly at that index in selection and deselect it.
        self.do_ksel_op('deselect', self._selection_source_list)

        sel = self.selection[index]
        if isinstance(sel, dict):
            ksel = sel['ksel']
        else:
            ksel = sel.ksel
        ksel.select()

    def handle_setslice_op(self, start_index, end_index):

        # Find the items formerly at these indices in selection, within the
        # source list, and deselect them.
        self.do_ksel_op('deselect', self._selection_source_list)

        changed_indices = range(start_index, end_index + 1)

        self.do_ksel_op(
            'select',
            [sel for sel in self.selection if sel.index in changed_indices])

    def handle_delete_op(self, start_index, end_index):

        # Find the items formerly at these indices in selection, within the
        # source list, and deselect them.
        self.do_ksel_op('deselect', self._selection_source_list)

    def sort_started(self, *args):

        # TODO: We don't care about a sort, but go through the motions?

        # Save a pre-sort order, and position detail, if there are duplicates
        # of strings.
        self.presort_indices_and_items = {}

        # Not yet implemented. See adapters/list_ops.py for inspiration.

        self.selection.finish_sort_op()

    def handle_sort_op(self):

        # TODO: We don't care about a sort, but go through the motions?

        presort_indices_and_items = self.presort_indices_and_items

        # We have an association of presort indices with data items.
        # Where is each data item after sort? Change the index of the
        # item to match present position.

        # Not yet implemented. See adapters/list_ops.py for inspiration.

        # Clear temporary storage.
        self.presort_indices_and_items.clear()
