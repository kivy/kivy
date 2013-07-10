'''
ListAdapter
=================

.. versionadded:: 1.5

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

A :class:`ListAdapter` is an adapter around a python list.

Selection operations are a main concern for the class.

From an :class:`Adapter`, a :class:`ListAdapter` gets cls, template, and
args_converter properties and adds others that control selection behaviour:

* *selection*, a list of selected items.

* *selection_mode*, 'single', 'multiple', 'none'

* *allow_empty_selection*, a boolean -- If False, a selection is forced. If
  True, and only user or programmatic action will change selection, it can
  be empty.

If you wish to have a bare-bones list adapter, without selection, use a
:class:`~kivy.adapters.simplelistadapter.SimpleListAdapter`.

A :class:`~kivy.adapters.dictadapter.DictAdapter` is a subclass of a
:class:`~kivy.adapters.listadapter.ListAdapter`. They both dispatch the
*on_selection_change* event.

    :Events:
        `on_selection_change`: (view, view list )
            Fired when selection changes

.. versionchanged:: 1.6.0

    Added data = ListProperty([]), which was proably inadvertently deleted at
    some point. This means that whenever data changes an update will fire,
    instead of having to reset the data object (Adapter has data defined as
    an ObjectProperty, so we need to reset it here to ListProperty). See also
    DictAdapter and its set of data = DictProperty().

'''

__all__ = ('ListAdapter', )

import inspect
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.adapters.adapter import Adapter
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


class ChangeMonitor(EventDispatcher):
    '''The ChangeRecordingObservableList/Dict instances need to store change
    info without triggering a data_changed() callback themselves. Use this
    intermediary to hold change info for CROL and CROD observers.
    '''

    change_info = ObjectProperty(None, allownone=True)
    crol_sort_started = BooleanProperty(False)
    sort_largs = ObjectProperty(None)
    sort_kwds = ObjectProperty(None)
    sort_op = StringProperty('')

    presort_indices_and_data = DictProperty({})
    '''This temporary association has keys as the indices of the adapter's
    cached_views and the adapter's data items, for use in post-sort widget
    reordering.  It is set by the adapter when needed.  It is cleared by the
    adapter at the end of its sort op callback.
    '''

    __events__ = ('on_change_info', 'on_crol_sort_started', )

    def __init__(self, *largs):
        super(ChangeMonitor, self).__init__(*largs)

        self.bind(change_info=self.dispatch_change,
                  crol_sort_started=self.dispatch_crol_sort_started)

    def dispatch_change(self, *args):
        self.dispatch('on_change_info')

    def on_change_info(self, *args):
        pass

    def dispatch_crol_sort_started(self, *args):
        if self.crol_sort_started:
            self.dispatch('on_crol_sort_started')

    def on_crol_sort_started(self, *args):
        pass


class ChangeRecordingObservableList(ObservableList):
    '''Adds range-observing and other intelligence to ObservableList, storing
    change_info for use by an observer.
    '''

    def __init__(self, *largs):
        super(ChangeRecordingObservableList, self).__init__(*largs)
        self.change_monitor = ChangeMonitor()

    # TODO: How do we see a full set (...adapter.data = [new list]) ?

    # TODO: setitem and delitem are supposed to handle slices.
    def __setitem__(self, key, value):
        super(ChangeRecordingObservableList, self).__setitem__(key, value)
        self.change_monitor.change_info = ('crol_setitem', (key, key))

    def __delitem__(self, key):
        super(ChangeRecordingObservableList, self).__delitem__(key)
        self.change_monitor.change_info = ('crol_delitem', (key, key))

    def __setslice__(self, *largs):
        #
        # Python docs:
        #
        #     operator.__setslice__(a, b, c, v)
        #
        #     Set the slice of a from index b to index c-1 to the sequence v.
        #
        #     Deprecated since version 2.6: This function is removed in Python
        #     3.x. Use setitem() with a slice index.
        #
        start_index = largs[0]
        end_index = largs[1] - 1
        super(ChangeRecordingObservableList, self).__setslice__(*largs)
        self.change_monitor.change_info = ('crol_setslice', (start_index, end_index))

    def __delslice__(self, *largs):
        # Delete the slice of a from index b to index c-1. del a[b:c],
        # where the args here are b and c.
        # Also deprecated.
        start_index = largs[0]
        end_index = largs[1] - 1
        super(ChangeRecordingObservableList, self).__delslice__(*largs)
        self.change_monitor.change_info = ('crol_delslice', (start_index, end_index))

    def __iadd__(self, *largs):
        start_index = len(self)
        end_index = start_index + len(largs) - 1
        super(ChangeRecordingObservableList, self).__iadd__(*largs)
        self.change_monitor.change_info = ('crol_iadd', (start_index, end_index))

    def __imul__(self, *largs):
        num = largs[0]
        start_index = len(self)
        end_index = start_index + (len(self) * num)
        super(ChangeRecordingObservableList, self).__imul__(*largs)
        self.change_monitor.change_info = ('crol_imul', (start_index, end_index))

    def append(self, *largs):
        index = len(self)
        super(ChangeRecordingObservableList, self).append(*largs)
        self.change_monitor.change_info = ('crol_append', (index, index))

    def remove(self, *largs):
        index = self.index(largs[0])
        super(ChangeRecordingObservableList, self).remove(*largs)
        self.change_monitor.change_info = ('crol_remove', (index, index))

    def insert(self, *largs):
        index = largs[0]
        super(ChangeRecordingObservableList, self).insert(*largs)
        self.change_monitor.change_info = ('crol_insert', (index, index))

    def pop(self, *largs):
        if largs:
            index = largs[0]
        else:
            index = len(self) - 1
        result = super(ChangeRecordingObservableList, self).pop(*largs)
        self.change_monitor.change_info = ('crol_pop', (index, index))
        return result

    def extend(self, *largs):
        start_index = len(self)
        end_index = start_index + len(largs[0]) - 1
        super(ChangeRecordingObservableList, self).extend(*largs)
        self.change_monitor.change_info = \
                ('crol_extend', (start_index, end_index))

    def start_sort_op(self, op, *largs, **kwds):

        self.change_monitor.sort_largs = largs
        self.change_monitor.sort_kwds = kwds
        self.change_monitor.sort_op = op

        # Trigger the "sort is starting" callback to the adapter, so it can do
        # pre-sort writing of the current arrangement of indices and data.
        self.change_monitor.crol_sort_started = True

    def finish_sort_op(self):

        largs = self.change_monitor.sort_largs
        kwds = self.change_monitor.sort_kwds
        sort_op = self.change_monitor.sort_op

        # Perform the sort.
        if sort_op == 'crol_sort':
            super(ChangeRecordingObservableList, self).sort(*largs, **kwds)
        else:
            super(ChangeRecordingObservableList, self).reverse(*largs)

        # Finalize. Will go back to adapter for handling cached_views,
        # selection, and prep for triggering data_changed on ListView.
        self.change_monitor.change_info = (sort_op, (0, len(self) - 1))

    def sort(self, *largs, **kwds):
        self.start_sort_op('crol_sort', *largs, **kwds)

    def reverse(self, *largs):
        self.start_sort_op('crol_reverse', *largs)


class ListAdapter(Adapter, EventDispatcher):
    '''
    A base class for adapters interfacing with lists, dictionaries or other
    collection type data, adding selection, view creation and management
    functonality.
    '''

    data = ListProperty([], cls=ChangeRecordingObservableList)
    '''The data list property is redefined here, overriding its definition as
    an ObjectProperty in the Adapter class. We bind to data so that any
    changes will trigger updates. See also how the
    :class:`~kivy.adapters.DictAdapter` redefines data as a
    :class:`~kivy.properties.DictProperty`.

    :data:`data` is a :class:`~kivy.properties.ListProperty` and defaults
    to [].
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
    # '''What is the name of the event fired from list items to effect selection?
    #
    # :data:`selection_triggering_event` is a
    # :class:`~kivy.properties.StringProperty` and defaults to the Kivy event
    # on_release, which is the typical case for buttons.
    # '''

    cached_views = DictProperty({})
    '''View instances for data items are instantiated and managed by the
    adapter. Here we maintain a dictionary containing the view
    instances keyed to the indices in the data.

    This dictionary works as a cache. get_view() only asks for a view from
    the adapter if one is not already stored for the requested index.

    :data:`cached_views` is a :class:`~kivy.properties.DictProperty` and
    defaults to {}.
    '''

    __events__ = ('on_selection_change', 'on_data_change')

    def __init__(self, **kwargs):
        super(ListAdapter, self).__init__(**kwargs)

        self.bind(selection_mode=self.selection_mode_changed,
                  allow_empty_selection=self.check_for_empty_selection)

        self.data.change_monitor.bind(on_change_info=self.crol_data_changed,
                                      on_crol_sort_started=self.crol_sort_started)

        self.delete_cache()
        self.initialize_selection()

    def crol_sort_started(self, *args):

        # Save a pre-sort order, and position detail, if there are duplicates
        # of strings.
        self.data.change_monitor.presort_indices_and_data = {}

        for i in self.cached_views:
            data_item = self.data[i]
            if isinstance(data_item, str):
                duplicates = sorted(
                        [j for j, s in enumerate(self.data) if s == data_item])
                pos_in_instances = duplicates.index(i)
            else:
                pos_in_instances = 0

            self.data.change_monitor.presort_indices_and_data[i] = \
                        {'data_item': data_item,
                         'pos_in_instances': pos_in_instances}

        self.data.finish_sort_op()

    def crol_data_changed(self, *args):

        change_info = args[0].change_info

        # TODO: This is to solve a timing issue when running tests. Remove when
        #       no longer needed.
        if not change_info:
            Clock.schedule_once(lambda dt: self.crol_data_changed(*args))
            return

        if change_info[0].startswith('crod'):
            return

        # crol_setitem
        # crol_delitem
        # crol_setslice
        # crol_delslice
        # crol_iadd
        # crol_imul
        # crol_append
        # crol_remove
        # crol_insert
        # crol_pop
        # crol_extend
        # crol_sort
        # crol_reverse

        print 'LIST ADAPTER data_changed callback', change_info

        data_op, (start_index, end_index) = change_info

        if len(self.data) == 1 and data_op in ['crol_append',
                                               'crol_insert',
                                               'crol_extend']:
            # Special case: deletion resulted in no data, leading up to the
            # present op, which adds one or more items. Cached views should
            # have already been treated.  Call check_for_empty_selection()
            # to re-establish selection if needed.
            self.check_for_empty_selection()
            self.dispatch('on_data_change')
            return

        if data_op in ['crol_iadd',
                       'crol_imul',
                       'crol_append',
                       'crol_extend']:
            # This shouldn't affect anything here, as cached_views items
            # can be built as needed through normal get_view() calls to
            # build views for the added items.
            pass

        elif data_op in ['crol_setitem']:

            # Force a rebuild of the view for which data item has changed.
            # If the item was selected before, maintain the seletion.

            is_selected = False
            if hasattr(self.cached_views[start_index], 'is_selected'):
                is_selected = self.cached_views[start_index].is_selected

            del self.cached_views[start_index]
            item_view = self.get_view(start_index)
            if is_selected:
                self.handle_selection(item_view)

        elif data_op in ['crol_setslice']:

            # Force a rebuild of views for which data items have changed.
            # Although it is hard to guess what might be preferred, a
            # "positional" priority for selection is observed here, where the
            # indices of selected item views is maintained. In contrast, we
            # could call check_for_empty_selection() if there no selection
            # remains after the op.

            changed_indices = range(start_index, end_index + 1)

            is_selected_indices = []
            for i in changed_indices:
                item_view = self.cached_views[i]
                if hasattr(item_view, 'is_selected'):
                    if item_view.is_selected:
                        is_selected_indices.append(i)

            for i in changed_indices:
                del self.cached_views[i]

            for i in changed_indices:
                item_view = self.get_view(i)
                if item_view.index in is_selected_indices:
                    self.handle_selection(item_view)

        elif data_op in ['crol_insert']:

            new_cached_views = {}

            for k, v in self.cached_views.iteritems():

                if k < start_index:
                    new_cached_views[k] = self.cached_views[k]
                else:
                    new_cached_views[k+1] = self.cached_views[k]
                    new_cached_views[k+1].index += 1

            self.cached_views = new_cached_views

        elif data_op in ['crol_delitem',
                         'crol_delslice',
                         'crol_remove',
                         'crol_pop']:

            deleted_indices = range(start_index, end_index + 1)

            # Delete views from cache.
            new_cached_views = {}

            i = 0
            for k, v in self.cached_views.iteritems():
                if not k in deleted_indices:
                    new_cached_views[i] = self.cached_views[k]
                    if k >= start_index:
                        new_cached_views[i].index = i
                    i += 1

            self.cached_views = new_cached_views

            # Remove deleted views from selection.
            #for selected_index in [item.index for item in self.selection]:
            for sel in self.selection:
                if sel.index in deleted_indices:
                    self.selection.remove(sel)

            # Do a check_for_empty_selection type step, if data remains.
            if (len(self.data) > 0
                    and not self.selection
                    and not self.allow_empty_selection):
                # Find a good index to select, if the deletion results in
                # no selection, which is common, as the selected item is
                # often the one deleted.
                if start_index < len(self.data):
                    new_sel_index = start_index
                else:
                    new_sel_index = start_index - 1
                v = self.get_view(new_sel_index)
                if v is not None:
                    self.handle_selection(v)

        elif data_op in ['crol_sort',
                         'crol_reverse']:

            presort_indices_and_data = \
                    self.data.change_monitor.presort_indices_and_data

            # We have an association of presort indices with data items.
            # Where is each data item after sort? Change the index of the
            # item_view to match present position.
            new_cached_views = {}
            for i in self.cached_views:
                item_view = self.cached_views[i]
                old_index = item_view.index
                data_item = presort_indices_and_data[old_index]['data_item']
                if isinstance(data_item, str):
                    duplicates = sorted(
                        [j for j, s in enumerate(self.data) if s == data_item])
                    pos_in_instances = \
                        presort_indices_and_data[old_index]['pos_in_instances']
                    postsort_index = duplicates[pos_in_instances]
                else:
                    postsort_index = self.data.index(data_item)
                item_view.index = postsort_index
                new_cached_views[postsort_index] = item_view

            self.cached_views = new_cached_views

            # Reset flags and temporary storage.
            self.data.change_monitor.crol_sort_started = False
            self.data.change_monitor.presort_indices_and_data.clear()

        self.dispatch('on_data_change')

    def delete_cache(self, maintain_selection=False):

        selected_indices_and_data = {}

        if self.selection and maintain_selection:
            for i in self.cached_views:
                item_view = self.cached_views[i]
                if item_view.is_selected:
                    selected_indices_and_data[i] = self.data[item_view.index]

        print 'saved selection', selected_indices_and_data

        self.cached_views.clear()

        for i in selected_indices_and_data:
            new_index = self.data.index(selected_indices_and_data[i])
            v = self.get_view(new_index)
            if v:
                self.handle_selection(v)

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
        '''This method is more complicated than the one in
        :class:`kivy.adapters.adapter.Adapter` and
        :class:`kivy.adapters.simplelistadapter.SimpleListAdapter`, because
        here we create bindings for the data item and its children back to
        self.handle_selection(), and do other selection-related tasks to keep
        item views in sync with the data.
        '''
        item = self.get_data_item(index)
        if item is None:
            return None

        item_args = self.args_converter(index, item)

        item_args['index'] = index

        if self.cls:
            view_instance = self.cls(**item_args)
        else:
            view_instance = Builder.template(self.template, **item_args)

        if self.propagate_selection_to_data:
            # The data item must be a subclass of SelectableDataItem, or must
            # have an is_selected boolean or function, so it has is_selected
            # available.  If is_selected is unavailable on the data item, an
            # exception is raised.
            #
            if isinstance(item, SelectableDataItem):
                if item.is_selected:
                    self.handle_selection(view_instance)
            elif type(item) == dict and 'is_selected' in item:
                if item['is_selected']:
                    self.handle_selection(view_instance)
            elif hasattr(item, 'is_selected'):
                # TODO: Change this to use callable().
                if (inspect.isfunction(item.is_selected)
                        or inspect.ismethod(item.is_selected)):
                    if item.is_selected():
                        self.handle_selection(view_instance)
                else:
                    if item.is_selected:
                        self.handle_selection(view_instance)
            else:
                msg = "ListAdapter: unselectable data item for {0}"
                raise Exception(msg.format(index))

        view_instance.bind(on_release=self.handle_selection)

        if self.bind_selection_to_children:
            for child in view_instance.children:
                child.bind(on_release=self.handle_selection)

        return view_instance

    def on_selection_change(self, *args):
        '''on_selection_change() is the default handler for the
        on_selection_change event.
        '''
        pass

    def on_data_change(self, *args):
        '''on_data_change() is the default handler for the
        on_data_change event.
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
            self.data = self.data[:last_sel_index + 1]

    def trim_to_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are les than or
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
