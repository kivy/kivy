'''
SelectableView, SelectionSupport
================================

.. versionadded:: 1.5

Mixin classes for giving selection functionality to "collection-style" views,
such as :class:`ListView`, and their item views, via the intermediating
control of :class:`ListAdapter`, or one of its subclasses.
'''

from kivy.properties import ListProperty, BooleanProperty, \
        OptionProperty, NumericProperty
from kivy.event import EventDispatcher


class SelectableDataItem(object):

    def __init__(self, **kwargs):
        super(SelectableDataItem, self).__init__()
        if 'is_selected' in kwargs:
            self.is_selected = kwargs['is_selected']
        else:
            self.is_selected = False


class SelectableView(object):
    '''The :class:`SelectableView` mixin is used in list item classes that are
    to be instantiated in a list view, which uses a list adapter.  select()
    and deselect() are to be overridden with display code to mark items as
    selected or not, if desired.
    '''

    index = NumericProperty(-1)
    '''The index into the underlying data list or the data item this view
    represents.
    '''

    is_selected = BooleanProperty(False)
    '''A SelectableView instance carries this property, and is kept in
    sync with the equivalent property in the data item it represents.
    '''

    def __init__(self, **kwargs):
        super(SelectableView, self).__init__(**kwargs)

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

    selected_indices = ListProperty([])
    '''The selected_indices property is maintained in parallel with the
    selection list.
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

       multiple -- multi-touch / incremental addition to selection allowed;
                   may be limited to a count by selection_limit
    '''

    allow_empty_selection = BooleanProperty(True)
    '''The allow_empty_selection may be used for cascading selection between
    several list views, or between a list view and an observing view. Such
    automatic maintainence of selection is important for all but simple
    list displays. Set allow_empty_selection False, so that selection is
    auto-initialized, and always maintained, and so that any observing views
    may likewise be updated to stay in sync.
    '''

    selection_limit = NumericProperty(0)
    '''When selection_mode is multiple, if selection_limit is non-zero, this
    number will limit the number of selected items. It can even be 1, which is
    equivalent to single selection. This is because a program could be
    programmatically changing selection_limit on the fly, and all possible
    values should be included.
    '''

    def __init__(self, **kwargs):
        super(SelectionSupport, self).__init__(**kwargs)
        self.register_event_type('on_selection_change')

        self.bind(selection_mode=self.check_for_empty_selection,
                  allow_empty_selection=self.check_for_empty_selection)

    def on_selection_change(self, *args):
        '''on_selection_change() is the default handler for the
        on_selection_change event.
        '''
        pass

    def handle_selection(self, view, *args):
        print 'handle_selection for', view
        if view not in self.selection:
            print 'view', view, 'is not in selection'
            if self.selection_mode in ['none', 'single'] and \
                    len(self.selection) > 0:
                for selected_view in self.selection:
                    self.deselect_item_view(selected_view)
            if self.selection_mode != 'none':
                if self.selection_mode == 'multiple':
                    if self.allow_empty_selection:
                        if self.selection_limit > 0:
                            if len(self.selection) < self.selection_limit:
                                print 'selecting', view
                                self.select_item_view(view)
                    else:
                        print 'selecting', view
                        self.select_item_view(view)
                else:
                    print 'selecting', view
                    self.select_item_view(view)
        else:
            if self.selection_mode == 'none':
                for selected_view in self.selection:
                    self.deselect_item_view(selected_view)
            else:
                self.deselect_item_view(view)
                # If the deselection makes selection empty, the following call
                # will check allows_empty_selection, and if False, will
                # select the first item. If view happens to be the first item,
                # this will be a reselection, and the user will notice no
                # change, except perhaps a flicker.
                #
                # [TODO] Is this approach OK?
                #
                self.check_for_empty_selection()

        print 'selection for', self, 'is now', self.selection
        self.dispatch('on_selection_change')

    def select_data_item(self, item):
        self.set_data_item_selection(item, True)

    def deselect_data_item(self, item):
        self.set_data_item_selection(item, False)

    def set_data_item_selection(self, item, value):
        if issubclass(item.__class__, SelectableDataItem):
            item.is_selected = value
        elif type(item) is dict:
            item['is_selected'] = value
        elif hasattr(item, 'is_selected'):
            item.is_selected = value
        else:
            raise Exception('Selection: data item is not selectable')

    def select_item_view(self, view):
        view.select()
        view.is_selected = True
        print 'selected', view, view.is_selected
        self.selection.append(view)
        self.selected_indices.append(view.index)

        # [TODO] sibling selection for composite items
        #        Needed? Or handled from parent?
        #        (avoid circular, redundant selection)
        #if hasattr(view, 'parent') and hasattr(view.parent, 'children'):
         #siblings = [child for child in view.parent.children if child != view]
         #for sibling in siblings:
             #if hasattr(sibling, 'select'):
                 #sibling.select()

        # child selection
        for child in view.children:
            if hasattr(child, 'select'):
                child.select()

        data_item = self.get_item(view.index)
        self.select_data_item(data_item)

    def select_list(self, view_list, extend):
        '''The select call is made for the items in the provided view_list.

        Arguments:

            view_list: the list of item views to become the new selection, or
            to add to the existing selection

            extend: boolean for whether or not to extend the existing list
        '''

        # Select all the item views.
        for view in view_list:
            self.select_item_view(view)

        # Extend or set selection.
        if extend:
            self.selection.extend(view_list)
        else:
            self.selection = view_list

        self.dispatch('on_selection_change')

    def deselect_item_view(self, view):
        view.deselect()
        view.is_selected = False
        self.selection.remove(view)
        self.selected_indices.remove(view.index)

        # [TODO] sibling deselection for composite items
        #        Needed? Or handled from parent?
        #        (avoid circular, redundant selection)
        #if hasattr(view, 'parent') and hasattr(view.parent, 'children'):
         #siblings = [child for child in view.parent.children if child != view]
         #for sibling in siblings:
             #if hasattr(sibling, 'deselect'):
                 #sibling.deselect()

        # child deselection
        for child in view.children:
            if hasattr(child, 'deselect'):
                child.deselect()

        item = self.get_item(view.index)
        self.deselect_data_item(item)

    def deselect_list(self, l):
        for view in l:
            self.deselect_item_view(view)
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
