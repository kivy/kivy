from kivy.properties import ObjectProperty, \
                            ListProperty, BooleanProperty, OptionProperty

# selection.py contains several "mixin" classes relating to selection, either
# for view to implement a list of items, for the items themselves, or for a
# view to observe selection.

# The idea for SelectionSupport as mixin, comes from SproutCore's mixin of the
# same name.

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
    # arranged_objects can be a list of strings, or a list of objects that
    # can implement SelectableItem.
    #
    # If SelectableItem objects, what do we need for them to implement, in
    # addition to the selection properties and methods already in place?
    #
    arranged_objects = ListProperty([])

    selection = ListProperty([])
    selection_mode = OptionProperty('multiple',
            options=('none', 'single', 'multiple', 'filter'))
    allow_empty_selection = BooleanProperty(True)

    registered_selection_observers = ListProperty([])

    def __init__(self, **kwargs):
        super(SelectionSupport, self).__init__(**kwargs)
        self.bind(arranged_objects=self.update_selection)
        self.bind(selection_mode=self.update_selection)
        self.bind(allow_empty_selection=self.update_selection)

    def register_selection_observer(self, obs):
        if isinstance(obs, SelectionObserver):
            self.registered_selection_observers.append(obs)
            obs.observed_selection_changed(self)
        print 'registered_selection_observers:', \
            len(self.registered_selection_observers)

    def unregister_selection_observer(self, obs):
        if obs in self.registered_selection_observers:
            self.registered_selection_observers.remove(obs)

    def handle_selection(self, obj):
        if obj not in self.selection:
            if self.selection_mode == 'single' and len(self.selection) > 0:
                for selected_obj in self.selection:
                    self.deselect_object(selected_obj)
            self.select_object(obj)
        else:
            self.deselect_object(obj)

        # dispatch will use the Kivy property-observing system.
        #
        # update_selection will push out to registered selection observers.
        #
        # Which is the way to go?
        #
        self.dispatch('on_select')
        self.update_selection()
        print 'selection is now', self.selection

    def select_object(self, obj):
        obj.select()
        self.selection.append(obj)

    # l: the list of objects to become the new selection, or to add to the
    #    existing selection, if extend is True
    #
    # extend: boolean for whether or not to extend the existing list
    #
    def select_list(self, l, extend):
        for obj in l:
            if not obj.is_selected:
                obj.select()
        if extend:
            self.selection.extend(l)
        else:
            self.selection = l

    def deselect_object(self, obj):
        obj.deselect()
        self.selection.remove(obj)

    def deselect_list(self, l):
        for obj in l:
            self.deselect_object(obj)

    # Override to return the first selectable object.  For example, if you
    # have groups or want to otherwise limit the kinds of objects that can be
    # selected. [TODO] This comment presently has no context -- the idea for
    # having grouped items, as might be done for something like a TreeView,
    # has not been addressed. So, as it is, it simple grabs the first item
    # in arranged_objects.
    #
    # The default implementation returns first object at index 0.
    #
    def first_selectable_object(self):
        if len(self.arranged_objects) > 0:
            return self.arranged_objects[0]
        return None

    def update_selection(self, *args):
        if self.allow_empty_selection is False:
            if len(self.selection) == 0:
                # [TODO] In present design, arranged_objects is a list of
                #        strings in parallel with items (instances of cls),
                #        so fso will not be SelectableItem. Fix by adding
                #        a properly handled sort_key ref into items dict,
                #        perhaps.
                fso = self.first_selectable_object()
                if fso is not None:
                    if isinstance(fso, SelectableItem):
                        fso.select()
                    else:
                        view = self.get_view(self.arranged_objects.index(fso))
                        self.handle_selection(view)

        for obs in self.registered_selection_observers:
            obs.observed_selection_changed(self)

    def initialize_selection(self, *args):
        self.selection = []
        self.update_selection()
