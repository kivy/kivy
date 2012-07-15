from kivy.properties import ObjectProperty, \
                            ListProperty, BooleanProperty, OptionProperty

# selection.py contains several "mixin" classes relating to selection, either
# for view to implement a list of items, for the items themselves, or for a
# view to observe selection.

# The idea for SelectionSupport as mixin, comes from SproutCore's mixin of the
# same name. It exists as a mixin toward the idea of reuse in other
# "collection" type views that need to implement selection.

# The allow_empty_selection property is important. If you have a list of items,
# to which a view is bound to the selection of that list, set
# allow_empty_selection = False, so that the observing view is
# auto-initialized. This sets up a "cascade" on this basis.

class SelectableItem:
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
    # Override to take action on selection.
    def observed_selection_changed(self, observed_selection):
        raise NotImplementedError()


class SelectionSupport(object):
    # The selection list property is the main observable item for selection.
    selection = ListProperty([])

    # Selection modes:
    #
    #    none -- use the list as a simple list (no select action)
    #
    #    single -- multi-touch/click ignored. single item selecting only
    #
    #    multiple -- multi-touch / incremental clicks to select allowed
    #
    #    filter -- idea only now. Could pass in filtering function to
    #           perform associated items selection
    #
    selection_mode = OptionProperty('multiple',
            options=('none', 'single', 'multiple', 'filter'))

    # allow_empty_selection is the key to cascading selection between
    # several lists, between a list and a dependent view. Having selection
    # automatically maintained, together with bindings, is important for
    # all but simple displays of list items.
    allow_empty_selection = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(SelectionSupport, self).__init__(**kwargs)
        self.bind(data=self.initialize_selection,
                  selection_mode=self.initialize_selection,
                  allow_empty_selection=self.initialize_selection)

    def handle_selection(self, obj):
        if obj not in self.selection:
            if self.selection_mode == 'single' and len(self.selection) > 0:
                for selected_obj in self.selection:
                    self.deselect_object(selected_obj)
            self.select_object(obj)
        else:
            self.deselect_object(obj)

        self.dispatch('on_select')
        self.update_selection()
        print 'selection is now', self.selection

    def select_object(self, obj):
        obj.select()
        obj.is_selected = True
        self.selection.append(obj)

    # l: the list of objects to become the new selection, or to add to the
    #    existing selection, if extend is True
    #
    # extend: boolean for whether or not to extend the existing list
    #
    def select_list(self, l, extend):
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

    def update_selection(self, *args):
        if self.allow_empty_selection is False:
            if len(self.selection) == 0:
                if len(self.data) > 0:
                    v = self.get_view(0)
                    print 'selecting first data item view', v, v.is_selected
                    self.handle_selection(self.get_view(0))

    # Is this needed as special case for resetting? Or can update_selection
    # be modified for this case?
    def initialize_selection(self, *args):
        print 'initialize_selection'
        self.selection = []
        self.update_selection()
