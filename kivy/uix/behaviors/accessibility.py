class AccessibleBehavior(object):
    # Which widget currently has the focus?
    focused_widget = None
    # Updated widgets since the previous frame.
    # If a widget was added or removed, then its parent must be in that dict as well.
    # Widgets should probably be grouped by the uid of their root window to support multiple windows, but I haven't found a practical way to get it: on_parent is called too early.
    updated_widgets = {}

    def __init__(self, **kwargs):
        super(AccessibleBehavior, self).__init__(**kwargs)
        
        from kivy.core.accessibility import Role

        self.accessible_checked_state = None
        self.accessible_children = None
        self.accessible_name = None
        self.accessible_pos = None
        self.accessible_role = Role.UNKNOWN
        self.accessible_size = None
        self.is_clickable = False
        self.is_focusable = False

    def grab_focus(self):
        # When a widget gets focused, no need to update its accessible representation, unless gaining or losing the focus updates some of its properties.
        AccessibleBehavior.focused_widget = self

    def update(self):
        # This must be called whenever some of the widget's properties have changed.
        AccessibleBehavior.updated_widgets[self.uid] = self

    def on_accessibility_action(self, action):
        pass
