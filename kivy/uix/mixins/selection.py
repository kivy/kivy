'''
SelectableItem, SelectionObserver, SelectionSupport
===================================================

.. versionadded:: 1.4

Mixin classes for giving selection functionality to "collection-style" views.
'''

from kivy.properties import ObjectProperty, \
                            ListProperty, BooleanProperty, OptionProperty


class SelectableItem:
    '''The :class:`SelectableItem` mixin is used in list item classes that are
    to be instantiated in a ListView. The handle_selection() callback
    interfaces to the ListView. select() and deselect() are to be overridden
    with display code to mark items as selected or not.
    '''
    is_selected = BooleanProperty(False)
    selection_callback = ObjectProperty(None)

    # The list item must handle the selection AND call the list's
    # selection_callback.
    def handle_selection(self, *args):
        self.selection_callback(*args)

    # The list item is responsible for updating the display for
    # being selected.
    def select(self):
        raise NotImplementedError()

    # The list item is responsible for updating the display for
    # being unselected.
    def deselect(self):
        raise NotImplementedError()


class SelectionObserver(object):
    '''The :class:`SelectionObserver` mixin is used to mark classes that wish
    to observe a ListView -- to observe its selection. Such an observer class
    must override the observed_selection_changed() method.
    '''

    def observed_selection_changed(self, observed_selection):
        '''Override to take action on selection.
        '''
        raise NotImplementedError()


class SelectionSupport(object):
    '''The :class:`SelectionSupport` mixin is the main one used for selection.
    Any "collection" view, such as ListView, that subclasses it will attain
    the selection ListProperty, a selection_mode OptionProperty, and an
    allow_empty_selection BooleanProperty, along with methods for the
    selection machinery tied to these properties.
    '''

    selection = ListProperty([])
    '''The selection list property is the main observable item for selection.
    As the primary target for observation, the Kivy bindings system assures
    that any actions on this list property -- changing it wholesale, adding
    or removing items, and so on, trigger dispatching to bound observer
    methods.
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
        self.bind(selection_mode=self.initialize_selection,
                  allow_empty_selection=self.initialize_selection)
        self.initialize_selection()

    def handle_selection(self, obj):
        if obj not in self.selection:
            if self.selection_mode == 'single' and len(self.selection) > 0:
                for selected_obj in self.selection:
                    self.deselect_object(selected_obj)
            self.select_object(obj)
        else:
            self.deselect_object(obj)

        print 'selection is now', self.selection

    def select_object(self, obj):
        obj.select()
        obj.is_selected = True
        self.selection.append(obj)

    def select_list(self, l, extend):
        '''Methods for selecting/deselecting a single item are
        straightforward, but here selection is handled for the items in the
        provided list, l. Keyboard actions or multi-touch gestures may, if
        allowed, select multiple items, and may replace or add to an existing
        selction.

        Arguments:

            l: the list of objects to become the new selection, or to add to
               the existing selection

            extend: boolean for whether or not to extend the existing list
        '''
        for obj in l:
            self.select_object(obj)
        if extend:
            self.selection.extend(l)
        else:
            self.selection = l

    def deselect_object(self, obj):
        obj.deselect()
        obj.is_selected = False
        self.selection.remove(obj)

    def deselect_list(self, l):
        for obj in l:
            self.deselect_object(obj)

    def initialize_selection(self, *args):
        '''After emptying the selection list property, check the
        allow_empty_selection boolean, and maintain selection if required.
        '''
        print 'initialize_selection'
        self.selection = []

        if self.allow_empty_selection is False:
            v = self.get_view(0)
            if v is not None:
                print 'selecting first data item view', v, v.is_selected
                self.handle_selection(self.get_view(0))
            else:
                print 'ERROR: No data, so cannot initialize selection.'
