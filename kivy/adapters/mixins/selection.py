'''
SelectableItem, SelectionSupport
================================

.. versionadded:: 1.4

Mixin classes for giving selection functionality to "collection-style" views,
such as :class:`ListView`, and their item views, via the intermediating
control of :class:`ListAdapter`, or one of its subclasses.
'''

from kivy.properties import ObjectProperty, ListProperty, BooleanProperty, \
        OptionProperty, NumericProperty
from kivy.event import EventDispatcher


class SelectableItem(object):
    '''The :class:`SelectableItem` mixin is used in list item classes that are
    to be instantiated in a ListView, which uses a list adapter. The
    handle_selection() function interfaces to :class:`ListView`, via its
    list adapter. select() and deselect() are to be overridden with display code
    to mark items as selected or not, if desired.
    '''

    index = NumericProperty(-1)
    '''The index into the underlying data list or the data item this view
    represents.
    '''

    is_selected = BooleanProperty(False)
    '''A SelectableItem instance carries this property, and is kept in
    sync with the equivalent property in the data item it represents.
    '''

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

    def select_data_item(self, item):
        self.set_data_item_selection(item, True)

    def deselect_data_item(self, item):
        self.set_data_item_selection(item, False)

    def set_data_item_selection(self, item, value):
        print 'set_data_item_selection', item, type(item)
        if type(item) is str:
            print 'set_data_item_selection', item, value
            self.datastore.set(item, 'is_selected', value)
        elif type(item) is dict and 'is_selected' in item:
            item['is_selected'] = value
        elif hasattr(item, 'is_selected'):
            item.is_selected = value

    def select_object(self, obj):
        obj.select()
        obj.is_selected = True
        self.selection.append(obj)

        # [TODO] sibling selection for composite items
        #        Needed? Or handled from parent?
        #        (avoid circular, redundant selection)
        #if hasattr(obj, 'parent') and hasattr(obj.parent, 'children'):
            #siblings = [child for child in obj.parent.children if child != obj]
            #for sibling in siblings:
                #if hasattr(sibling, 'select'):
                    #sibling.select()

        # child selection
        for child in obj.children:
            if hasattr(child, 'select'):
                child.select()

        print 'select_object, obj.index is:', obj.index
        item = self.data[obj.index]
        self.select_data_item(item)

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

        # [TODO] sibling deselection for composite items
        #        Needed? Or handled from parent?
        #        (avoid circular, redundant selection)
        #if hasattr(obj, 'parent') and hasattr(obj.parent, 'children'):
            #siblings = [child for child in obj.parent.children if child != obj]
            #for sibling in siblings:
                #if hasattr(sibling, 'deselect'):
                    #sibling.deselect()

        # child deselection
        for child in obj.children:
            if hasattr(child, 'deselect'):
                child.deselect()

        item = self.data[obj.index]
        self.deselect_data_item(item)

    def deselect_list(self, l):
        for obj in l:
            self.deselect_object(obj)
        self.dispatch('on_selection_change')

    def initialize_selection(self, *args):
        '''Called when data changes.
        '''
        if len(self.selection) > 0:
            self.selection = []
            self.dispatch('on_selection_change')

        # NOTE: self.check_for_empty_selection() now called at the end of
        #       listview.hard_populate(). If called here, it comes before
        #       the listview builds its new item views.
