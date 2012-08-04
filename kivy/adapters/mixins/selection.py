'''
SelectableItem, SelectionSupport
================================

.. versionadded:: 1.4

Mixin classes for giving selection functionality to "collection-style" views,
such as :class:`ListView`, and their item views, via the intermediating
control of :class:`ListAdapter`, or one of its subclasses.
'''

from kivy.properties import ObjectProperty, ListProperty, BooleanProperty, \
        OptionProperty
from kivy.event import EventDispatcher


class SelectableItem(object):
    '''The :class:`SelectableItem` mixin is used in list item classes that are
    to be instantiated in a ListView, which uses a ListAdapter. The
    handle_selection() function interfaces to the ListView, via its
    ListAdapter select() and deselect() are to be overridden with display code
    to mark items as selected or not, if desired.
    '''

    is_selected = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(SelectableItem, self).__init__(**kwargs)

    def select(self, *args):
        '''The list item is responsible for updating the display for
        being selected, if desired.
        '''
        pass

    def deselect(self, *args):
        '''The list item is responsible for updating the display for
        being unselected, if desired.
        '''
        pass


class SelectionSupport(EventDispatcher):
    '''The :class:`SelectionSupport` mixin is used for selection. Any
    "collection" view, such as :class:`ListView`.
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

       multiple -- multi-touch / incremental clicks to select allowed
    '''

    allow_empty_selection = BooleanProperty(True)
    '''The allow_empty_selection may be used for cascading selection between
    several list views, or between a list view and an observing view. Such
    automatic maintainence of selection is important for all but simple
    list displays. Set allow_empty_selection False, so that selection is
    auto-initialized, and always maintained, and so that any observing views
    may likewise be updated to stay in sync.
    '''

    def __init__(self, **kwargs):
        super(SelectionSupport, self).__init__(**kwargs)
        self.register_event_type('on_selection_change')

        self.bind(selection_mode=self.check_for_empty_selection,
                  allow_empty_selection=self.check_for_empty_selection)

    def handle_selection(self, obj, *args):
        if obj not in self.selection:
            if self.selection_mode == 'single' and len(self.selection) > 0:
                for selected_obj in self.selection:
                    self.deselect_object(selected_obj)
            self.select_object(obj)
        else:
            self.deselect_object(obj)

        print 'selection for', self, 'is now', self.selection
        self.dispatch('on_selection_change')

    def select_object(self, obj):
        obj.select()
        obj.is_selected = True
        self.selection.append(obj)

    def select_list(self, obj_list, extend):
        '''The select call is made for the items in the provided obj_list.

        Arguments:

            obj_list: the list of objects to become the new selection, or to
            add to the existing selection

            extend: boolean for whether or not to extend the existing list
        '''

        # Select all the objects.
        for obj in obj_list:
            self.select_object(obj)

        # Extend or set selection.
        if extend:
            self.selection.extend(obj_list)
        else:
            self.selection = obj_list

        self.dispatch('on_selection_change')

    def deselect_object(self, obj):
        obj.deselect()
        obj.is_selected = False
        self.selection.remove(obj)

    def deselect_list(self, l):
        for obj in l:
            self.deselect_object(obj)
        self.dispatch('on_selection_change')

    def initialize_selection(self, *args):
        '''Called when data changes.
        '''
        if len(self.selection) > 0:
            # [TODO] What about the previous selection? Just blow it away?
            self.selection = []
            self.dispatch('on_selection_change')

        # NOTE: self.check_for_empty_selection() now called at the end of
        #       listview.hard_populate(). If called here, it comes before
        #       the listview builds its new item views.
