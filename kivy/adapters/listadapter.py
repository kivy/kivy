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

from kivy.event import EventDispatcher
from kivy.adapters.adapter import Adapter
from kivy.adapters.list_ops import ListOpHandler
from kivy.adapters.list_ops import RecordingObservableList
from kivy.properties import ListProperty
from kivy.properties import ObjectProperty


class ListAdapter(Adapter, EventDispatcher):
    '''A :class:`~kivy.adapters.listadapter.ListAdapter` is an adapter around a
    python list of items. It is an alternative to the dict capabilities of
    :class:`~kivy.adapters.dictadapter.DictAdapter`.

    :class:`~kivy.adapters.dictadapter.ListAdapter` and
    :class:`~kivy.adapters.listadapter.DictAdapter` use special
    :class:`~kivy.properties.ListProperty` and
    :class:`~kivy.properties.DictProperty` variants,
    :class:`~kivy.adapters.list_ops.RecordingObservableList` and
    :class:`~kivy.adapters.dict_ops.RecordingObservableDict`, which
    record op_info for use in the adapter system.

    This system endeavors to allow normal Python programming of the contained
    list or dict objects. For lists, this means normal operations (append,
    insert, pop, sort, etc.) and the ones for dicts (setitem, pop, popitem,
    setdefault, clear, etc.).

    :class:`~kivy.adapters.listadapter.ListAdapter` has data, a
    :class:`~kivy.adapters.list_ops.RecordingObservableList`. You can
    change the data list as you wish and the system will react accordingly.

    It may help you to understand how the system works, combining an adapter
    such as this one with a collection-style widget such as
    :class:`~kivy.uix.widgets.ListView`. When something happens in your program
    to change the list (here we are talking about the property called data),
    the op_info stored is a Python tuple containing the name of the data
    operation that occurred, along with a contained tuple with (start_index,
    end_index).  The system cannot know the details about operations
    beforehand, so it must react after-the-fact for which items were affected
    and how. The adapter has callbacks that handle specific operations, and
    make needed changes to the internal cached_views, selection, and related
    properties, in preparation for sending, in turn, a data-changed event to
    the collection-style widget that uses the adapter.  For example,
    :class:`~kivy.uix.widgets.ListView` observes its adapter for data-changed
    events and updates the user interface. When an item is deleted, it removes
    the item view widget from its container, or for an addition, it adds the
    item view widget to its container and scrolls the list, and so on.
    '''

    data = ListProperty([], cls=RecordingObservableList)
    '''A Python list that uses :class:`~kivy.properties.ObservableList` for
    storage, and uses :class:`~kivy.adapters.list_ops.RecordingObservableList`
    as a "change-aware" wrapper that records op_info for list ops.

    The data list property contains the normal items allowed in Python, but
    they need to be strings if no args_converter function is provided. If there
    is an args_converter, the record received from a lookup of the data will be
    passed to it for instantiation of item view class instances.

    :data:`data` is a :class:`~kivy.properties.ListProperty` and defaults
    to [].
    '''

    list_op_handler = ObjectProperty(None)
    '''An instance of :class:`ListOpHandler`, containing methods that perform
    steps needed after the data (a
    :class:`~kivy.adapters/list_ops.RecordingObservableList`) has changed. The
    methods are responsible for updating cached_views and selection.

    :data:`list_op_handler` is a :class:`~kivy.properties.ObjectProperty` and
    defaults to None. It is instantiated and set on init.
    '''

    op_info = ObjectProperty(None, allownone=True)
    '''This is a copy of our data's recorder.op_info. We make a copy
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

        self.data.recorder.bind(
                op_info=self.list_op_handler.data_changed,
                sort_started=self.list_op_handler.sort_started)

        self.initialize_selection()

    def data_changed(self, *args):
        '''This callback happens as a result of the direct data binding set up
        in __init__(). It is needed for the direct set of data, as happens in
        ...data = [some new data list], which is not picked up by the ROL data
        change system. We check by looking for a valid recorder that is created
        when a ROL event has fired. If not present, we know this call is from a
        direct data set.
        '''
        if (hasattr(self.data, 'recorder')
               and not self.data.recorder.op_started):
            self.cached_views.clear()

            self.list_op_handler.source_list = self.data

            self.data.recorder.bind(
                on_op_info=self.list_op_handler.data_changed,
                on_sort_started=self.list_op_handler.sort_started)

            self.op_info = ('ROL_reset', (0, 0))
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
