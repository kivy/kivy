'''
SelectableItem, SelectionSupport
================================

.. versionadded:: 1.4

Mixin classes for giving selection functionality to "collection-style" views.
'''

from kivy.properties import ObjectProperty, NumericProperty, \
                            ListProperty, BooleanProperty, OptionProperty


class SelectableItem(object):
    '''The :class:`SelectableItem` mixin is used in list item classes that are
    to be instantiated in a ListView, which uses a ListAdapter. The
    handle_selection() function interfaces to the ListView, via its
    ListAdapter, passing the selection_target, the object that is to be
    selected. select() and deselect() are to be overridden with display code
    to mark items as selected or not, if desired.
    '''

    # Usually selection_target would be self, but it could be self.parent
    # for an element of a composite list item.
    selection_target = ObjectProperty(None)

    is_selected = BooleanProperty(False)

    def __init__(self, **kwargs):
        # [TODO] list_adapter is not optional, and should be guaranteed,
        #        because list_adapter itself makes this __init__ call and
        #        passes self. OK to assume here? No, it could be set directly
        #        if a template is used, instead of a cls, in list_adapter.
        if 'list_adapter' in kwargs:
            self.list_adapter = kwargs['list_adapter']

        # For simple list items, selection_target will be the list item
        # itself, but for components of composite list items, the components
        # could "pass" selection up to their parent. [TODO] Does this usage
        # make sense?
        if hasattr(kwargs, 'selection_target'):
            self.selection_target = kwargs['selection_target']
        else:
            self.selection_target = self

        super(SelectableItem, self).__init__(**kwargs)

    # The list item is responsible for updating the display for
    # being selected, if desired.
    def select(self, *args):
        pass

    # The list item is responsible for updating the display for
    # being unselected, if desired.
    def deselect(self, *args):
        pass


class SelectionSupport(object):
    '''The :class:`SelectionSupport` mixin is the main one used for selection.
    Any "collection" view, such as ListView, that subclasses it will attain
    the selection ListProperty, a selection_mode OptionProperty, and an
    allow_empty_selection BooleanProperty, along with methods for the
    selection machinery tied to these properties.
    '''

    selection = ListProperty([])
    '''The selection list property is the main observable item for selection.
    '''

    selection_mode = OptionProperty('multiple',
            options=('none', 'single', 'multiple', 'filter'))
    '''Selection modes:

       none -- use the list as a simple list (no select action)

       single -- multi-touch/click ignored. single item selecting only

       multiple -- multi-touch / incremental clicks to select allowed

       filter -- [TODO] idea only now. Could pass in filtering function to
                 perform associated items selection
    '''

    allow_empty_selection = BooleanProperty(True)
    '''The allow_empty_selection may be used for cascading selection between
    several list views, or between a list view and an observing view. Such
    automatic maintainence of selection is important for all but simple
    list displays. Set allow_empty_selection = False, so that selection is
    auto-initialized, and always maintained, and so that any observing views
    may likewise be updated to stay in sync.
    '''

    def __init__(self, **kwargs):
        super(SelectionSupport, self).__init__(**kwargs)
        self.register_event_type('on_selection_change')

        self.bind(selection_mode=self.check_for_empty_selection,
                  allow_empty_selection=self.check_for_empty_selection)

    def handle_selection(self, obj):
        if obj.selection_target is obj:
            self._handle_selection(obj)
        else:
            self._handle_selection(obj.selection_target)

    def _handle_selection(self, obj):
        if obj not in self.selection:
            if self.selection_mode == 'single' and len(self.selection) > 0:
                for selected_obj in self.selection:
                    self.deselect_object(selected_obj)
            self.select_object(obj)
        else:
            self.deselect_object(obj)

        print 'selection is now', self.selection
        self.dispatch('on_selection_change')

    def select_object(self, obj):
        obj.select()
        obj.is_selected = True
        self.selection.append(obj)

    def select_list(self, obj_list, extend):
        '''Methods for selecting/deselecting a single item are
        straightforward, but here selection is handled for the items in the
        provided obj_list. Keyboard actions or multi-touch gestures may, if
        allowed, select multiple items, and may replace or add to an existing
        selection.

        Arguments:

            obj_list: the list of objects to become the new selection, or to
            add to the existing selection

            extend: boolean for whether or not to extend the existing list
        '''
        for obj in obj_list:
            self.select_object(obj)
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
            self.selection = []
            self.dispatch('on_selection_change')

        self.check_for_empty_selection(*args)
