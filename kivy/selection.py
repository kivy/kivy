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
from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty
from kivy.properties import ListOpInfo
from kivy.properties import ListProperty
from kivy.properties import NumericProperty
from kivy.properties import ObjectProperty
from kivy.properties import OpObservableList
from kivy.properties import OptionProperty
from kivy.uix.widget import Widget


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

    _is_handling_selection = BooleanProperty(False)
    selection_binding = ObjectProperty(None, allownone=True)
    remove_on_deselect = BooleanProperty(False)

    __events__ = ('on_selection_change', )

    def __init__(self, **kwargs):

        super(Selection, self).__init__(**kwargs)

        self.bind(selection=self.selection_changed)

        self.bind(selection_mode=self.selection_mode_changed,
                  allow_empty_selection=self.initialize_selection)

        # NOTE: If selection is bound to an external controller or property,
        #       we do not initialize selection, but we do check it for
        #       agreement with allow_empty_selection and
        #       allow_multiple_selection.
        #
        #       Also, we do not call initialize_selection here if selection was
        #       passed in, but we do need to check_for_empty_selection() in
        #       this case. Otherwise, initialize_selection(), which calls
        #       check_for_empty_selection().
        if self.selection_binding:
            self.selection_binding.bind_to(self, 'selection')
            self.selection = getattr(self.selection_binding.source,
                                     self.selection_binding.prop)
        elif 'selection' in kwargs:
            self.check_for_empty_selection()
        else:
            self.initialize_selection()

    def selection_mode_changed(self, *args):
        if self.selection_mode == 'none':
            self.deselect_list(self.selection)
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

    def handle_selection(
            self, item, process_for_batch=False, initialize_selection=False):
        op_for_batch = None

        additions = []
        removals = []

        if isinstance(item, Widget) and hasattr(item, 'index'):
            item = self.data[item.index]

        if item not in self.selection:
            if (self.selection_mode in ['none', 'single']
                    and len(self.selection) > 0):
                for selected in self.selection:
                    if process_for_batch:
                        op_for_batch = _selection_ops.DESELECT
                    else:
                        self.deselect_item(selected,
                                           remove_from_selection=False)
                        if not initialize_selection:
                            removals.append(selected)
            if initialize_selection:
                len_selection = 0
            else:
                len_selection = len(self.selection)
            if self.selection_mode != 'none':
                if self.selection_mode == 'multiple':
                    if self.allow_empty_selection:
                        # If None, selection_limit is not active.
                        if self.selection_limit is None:
                            if process_for_batch:
                                op_for_batch = _selection_ops.SELECT
                            else:
                                self.select_item(item,
                                                 add_to_selection=False)
                                additions.append(item)
                        else:
                            if len_selection < self.selection_limit:
                                if process_for_batch:
                                    op_for_batch = _selection_ops.SELECT
                                else:
                                    self.select_item(item,
                                                     add_to_selection=False)
                                    additions.append(item)
                    else:
                        if process_for_batch:
                            op_for_batch = _selection_ops.SELECT
                        else:
                            self.select_item(item,
                                             add_to_selection=False)
                            additions.append(item)
                else:
                    if process_for_batch:
                        op_for_batch = _selection_ops.SELECT
                    else:
                        self.select_item(item, add_to_selection=False)
                        additions.append(item)
        else:

            if process_for_batch:
                op_for_batch = _selection_ops.DESELECT_AND_CHECK
            else:
                self.deselect_item(item, remove_from_selection=False)
                removals.append(item)

        if op_for_batch is not None:
            self._is_handling_selection = False
            return op_for_batch

        if initialize_selection:
            selection_copy = []
        else:
            selection_copy = list(self.selection)

            for r in removals:
                selection_copy.remove(r)

        for a in additions:
            selection_copy.append(a)

        self._is_handling_selection = True
        self.selection = selection_copy
        self._is_handling_selection = False

        # If the selection just done is a deselection, and
        # allow_empty_selection is False, then an item must be selected in a
        # second call.
        if self.selection_mode != 'none':
            self.check_for_empty_selection()

        if self.remove_on_deselect:
            indices_for_deletion = []
            for item in removals:
                indices_for_deletion.append(self.data.index(item))
            for index in reversed(indices_for_deletion):
                del self.data[index]

    def select_item(self, item, add_to_selection=True):

        ksel = None

        if isinstance(item, dict) and 'ksel' in item:
            ksel = item['ksel']
        elif hasattr(item, 'ksel'):
            ksel = item.ksel

        if ksel:
            ksel.select()

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
        # Use process_for_batch to keep handle_selection() from calling select
        # or deselect methods, which avoids changing selection. Collect the
        # select and deselect ops that handle_selection() reports are needed
        # (this way we use the same logic there), and then do the ops in a
        # quick loop, followed by a batch call for the actual selection list
        # changes.

        ops = []
        for item in selectable_items:
            ops.append(self.handle_selection(item))

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
            self.selection.batch_delete(
                    reversed([self.data.index(sd) for sd in sel_deletes]))
            self.is_handling_selection = False

        # Also, see the logic in handle_selection(), which includes calling
        # check_for_empty_selection() if the item is in selection and needs
        # deselection. We use that information to do the check and call here
        # after the batch ops.
        if check_for_empty_selection:
            if self.selection_mode != 'none':
                self.check_for_empty_selection()

#        self.dispatch('on_selection_change')

    def deselect_item(self, item, remove_from_selection=True):

        ksel = None

        if isinstance(item, dict) and 'ksel' in item:
            ksel = item['ksel']
        elif hasattr(item, 'ksel'):
            ksel = item.ksel

        if ksel:

            ksel.deselect()

        if remove_from_selection:
            self.selection.remove(item)

    def initialize_selection(self, *args):

        self.check_for_empty_selection(initialize_selection=True)

    def check_for_empty_selection(self, initialize_selection=False):

        if not self.allow_empty_selection:
            if len(self.selection) == 0 or initialize_selection:
                # Select the first item if we have it.
                if hasattr(self, 'get_data_item'):
                    item = self.get_data_item(0)
                    if item is not None:
                        self.handle_selection(
                            item, initialize_selection=initialize_selection)
                elif hasattr(self, 'get_selectable_item'):
                    item = self.get_selectable_item(0)
                    if item is not None:
                        self.handle_selection(
                            item, initialize_selection=initialize_selection)

    def selection_changed(self, *args):

        if self.selection is None:
            return

        '''This method handles adjustments after operations on the selection
        list happen.

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

        # Make a copy in the controller for more convenient access by
        # observers.
        self.selection_op_info = op_info

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

        self.dispatch('on_selection_change')

    def do_ksel_op(self, op, items):

        if not items:
            return

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

        self.do_ksel_op('deselect', self.selection)

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
        self.do_ksel_op('deselect', self.selection)

        sel = self.selection[index]
        if isinstance(sel, dict):
            ksel = sel['ksel']
        else:
            ksel = sel.ksel
        ksel.select()

    def handle_setslice_op(self, start_index, end_index):

        # Find the items formerly at these indices in selection, within the
        # source list, and deselect them.
        self.do_ksel_op('deselect', self.selection)

        changed_indices = range(start_index, end_index + 1)

        self.do_ksel_op(
            'select',
            [sel for sel in self.selection if sel.index in changed_indices])

    def handle_delete_op(self, start_index, end_index):

        # Find the items formerly at these indices in selection, within the
        # source list, and deselect them.
        self.do_ksel_op('deselect', self.selection)

    def sort_started(self, *args):

        # TODO: We don't care about a sort, but go through the motions?

        # Save a pre-sort order, and position detail, if there are duplicates
        # of strings.
        self.presort_indices_and_items = {}

        # Not yet implemented. See adapters/list_ops.py for inspiration.

        self.selection.finish_sort_op()

    def handle_sort_op(self):

        # TODO: We don't care about a sort, but go through the motions?

        # We have an association of presort indices with data items.
        # Where is each data item after sort? Change the index of the
        # item to match present position.

        # Not yet implemented. See adapters/list_ops.py for inspiration.

        # Clear temporary storage.
        self.presort_indices_and_items.clear()
