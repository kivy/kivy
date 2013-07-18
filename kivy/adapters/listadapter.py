'''
ListAdapter
=================

.. versionadded:: 1.5

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

A :class:`ListAdapter` is an adapter around a python list.

From an :class:`~kivy.adapters.adapter.Adapter`, a
:class:`~kivy.adapters.listadapter.ListAdapter` gets cls, template, and
args_converter properties.

From :class:`~kivy.adapters.selection.Selection` are properties that control
selection behaviour:

* *selection*, a list of selected items.

* *selection_mode*, 'single', 'multiple', 'none'

* *allow_empty_selection*, a boolean -- If False, a selection is forced. If
  True, and only user or programmatic action will change selection, it can
  be empty.

If you wish to have a bare-bones list adapter, without selection, use a
:class:`~kivy.adapters.simplelistadapter.SimpleListAdapter`.

A :class:`~kivy.adapters.dictadapter.DictAdapter` is a subclass of a
:class:`~kivy.adapters.adapter.Adapter`.

    :Events:

        `on_data_change`: (view, view list )
            Fired when data changes

.. versionchanged:: 1.6.0

    Added data = ListProperty([]), which was proably inadvertently deleted at
    some point. This means that whenever data changes an update will fire,
    instead of having to reset the data object (Adapter has data defined as
    an ObjectProperty, so we need to reset it here to ListProperty). See also
    DictAdapter and its set of data = DictProperty().

'''

__all__ = ('ListAdapter', )

import inspect
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.adapters.adapter import Adapter
from kivy.adapters.list_op_handler import ListOpHandler
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


class ListChangeMonitor(EventDispatcher):
    '''The ChangeRecordingObservableList/Dict instances need to store change
    info without triggering a data_changed() callback themselves. Use this
    intermediary to hold change info for CROL and CROD observers.
    '''

    op_started = BooleanProperty(False)
    change_info = ObjectProperty(None, allownone=True)
    crol_sort_started = BooleanProperty(False)
    sort_largs = ObjectProperty(None)
    sort_kwds = ObjectProperty(None)
    sort_op = StringProperty('')

    presort_indices_and_items = DictProperty({})
    '''This temporary association has keys as the indices of the adapter's
    cached_views and the adapter's data items, for use in post-sort widget
    reordering.  It is set by the adapter when needed.  It is cleared by the
    adapter at the end of its sort op callback.
    '''

    __events__ = ('on_crol_change_info', 'on_crol_sort_started', )

    def __init__(self, *largs):
        super(ListChangeMonitor, self).__init__(*largs)

        self.bind(change_info=self.dispatch_change,
                  crol_sort_started=self.dispatch_crol_sort_started)

    def dispatch_change(self, *args):
        self.dispatch('on_crol_change_info')

    def on_crol_change_info(self, *args):
        pass

    def dispatch_crol_sort_started(self, *args):
        if self.crol_sort_started:
            self.dispatch('on_crol_sort_started')

    def on_crol_sort_started(self, *args):
        pass

    def start(self):
        self.op_started = True

    def stop(self):
        self.op_started = False


class ChangeRecordingObservableList(ObservableList):
    '''Adds range-observing and other intelligence to ObservableList, storing
    change_info for use by an observer.
    '''

    def __init__(self, *largs):
        super(ChangeRecordingObservableList, self).__init__(*largs)
        self.change_monitor = ListChangeMonitor()

    # TODO: setitem and delitem are supposed to handle slices, instead of the
    #       deprecated setslice() and delslice() methods.
    def __setitem__(self, key, value):
        self.change_monitor.start()
        super(ChangeRecordingObservableList, self).__setitem__(key, value)
        self.change_monitor.change_info = ('crol_setitem', (key, key))
        self.change_monitor.stop()

    def __delitem__(self, key):
        self.change_monitor.start()
        super(ChangeRecordingObservableList, self).__delitem__(key)
        self.change_monitor.change_info = ('crol_delitem', (key, key))
        self.change_monitor.stop()

    def __setslice__(self, *largs):
        self.change_monitor.start()
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
        self.change_monitor.stop()

    def __delslice__(self, *largs):
        self.change_monitor.start()
        # Delete the slice of a from index b to index c-1. del a[b:c],
        # where the args here are b and c.
        # Also deprecated.
        start_index = largs[0]
        end_index = largs[1] - 1
        super(ChangeRecordingObservableList, self).__delslice__(*largs)
        self.change_monitor.change_info = ('crol_delslice', (start_index, end_index))
        self.change_monitor.stop()

    def __iadd__(self, *largs):
        self.change_monitor.start()
        start_index = len(self)
        end_index = start_index + len(largs) - 1
        super(ChangeRecordingObservableList, self).__iadd__(*largs)
        self.change_monitor.change_info = ('crol_iadd', (start_index, end_index))
        self.change_monitor.stop()

    def __imul__(self, *largs):
        self.change_monitor.start()
        num = largs[0]
        start_index = len(self)
        end_index = start_index + (len(self) * num)
        super(ChangeRecordingObservableList, self).__imul__(*largs)
        self.change_monitor.change_info = ('crol_imul', (start_index, end_index))
        self.change_monitor.stop()

    def append(self, *largs):
        self.change_monitor.start()
        index = len(self)
        super(ChangeRecordingObservableList, self).append(*largs)
        self.change_monitor.change_info = ('crol_append', (index, index))
        self.change_monitor.stop()

    def remove(self, *largs):
        self.change_monitor.start()
        index = self.index(largs[0])
        super(ChangeRecordingObservableList, self).remove(*largs)
        self.change_monitor.change_info = ('crol_remove', (index, index))
        self.change_monitor.stop()

    def insert(self, *largs):
        self.change_monitor.start()
        index = largs[0]
        super(ChangeRecordingObservableList, self).insert(*largs)
        self.change_monitor.change_info = ('crol_insert', (index, index))
        self.change_monitor.stop()

    def pop(self, *largs):
        self.change_monitor.start()
        if largs:
            index = largs[0]
        else:
            index = len(self) - 1
        result = super(ChangeRecordingObservableList, self).pop(*largs)
        self.change_monitor.change_info = ('crol_pop', (index, index))
        return result
        self.change_monitor.stop()

    def extend(self, *largs):
        self.change_monitor.start()
        start_index = len(self)
        end_index = start_index + len(largs[0]) - 1
        super(ChangeRecordingObservableList, self).extend(*largs)
        self.change_monitor.change_info = \
                ('crol_extend', (start_index, end_index))
        self.change_monitor.stop()

    def start_sort_op(self, op, *largs, **kwds):
        self.change_monitor.start()

        self.change_monitor.sort_largs = largs
        self.change_monitor.sort_kwds = kwds
        self.change_monitor.sort_op = op

        # Trigger the "sort is starting" callback to the adapter, so it can do
        # pre-sort writing of the current arrangement of indices and data.
        self.change_monitor.crol_sort_started = True
        self.change_monitor.stop()

    def finish_sort_op(self):
        self.change_monitor.start()

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
        self.change_monitor.stop()

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

    list_op_handler = ObjectProperty(None)
    '''An instance of :class:`ListOpHandler`, containing methods that perform
    steps needed after the data (a :class:`ChangeRecordingObservableList`)
    has changed. The methods are responsible for updating cached_views and
    selection.

    :data:`list_op_handler` is a :class:`~kivy.properties.ObjectProperty` and
    defaults to None. It is instantiated and set on init.
    '''

    change_info = ObjectProperty(None, allownone=True)
    '''This is a copy of our data's change_monitor.change_info. We make a copy
    before dispatching the on_data_change event, so that observers can more
    conveniently access it.
    '''

    __events__ = ('on_data_change', )

    def __init__(self, **kwargs):
        super(ListAdapter, self).__init__(**kwargs)

        self.bind(selection_mode=self.selection_mode_changed,
                  allow_empty_selection=self.check_for_empty_selection,
                  data=self.data_changed)

        self.list_op_handler = ListOpHandler(adapter=self,
                                             source_list=self.data,
                                             duplicates_allowed=True)

        self.data.change_monitor.bind(
                on_crol_change_info=self.list_op_handler.data_changed,
                on_crol_sort_started=self.list_op_handler.sort_started)

        self.initialize_selection()

    def data_changed(self, *args):
        '''This callback happens as a result of the direct data binding set up
        in __init__(). It is needed for the direct set of data, as happens in
        ...data = [some new data list], which is not picked up by the CROL data
        change system. We check by looking for a valid change_monitor that is
        created when CROL has fired. If not present, we know this call is from
        a direct data set.
        '''
        if (hasattr(self.data, 'change_monitor')
               and not self.data.change_monitor.op_started):
            self.cached_views.clear()

            self.list_op_handler.source_list = self.data

            self.data.change_monitor.bind(
                on_crol_change_info=self.list_op_handler.data_changed,
                on_crol_sort_started=self.list_op_handler.sort_started)

            self.change_info = ('crol_reset', (0, 0))
            self.dispatch('on_data_change')

            self.initialize_selection()

    def on_data_change(self, *args):
        '''on_data_change() is the default handler for the
        on_data_change event.
        '''
        pass

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
