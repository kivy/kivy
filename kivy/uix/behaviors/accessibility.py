from kivy.uix import widget


class AccessibleBehavior(object):
    # Which widget currently has the focus?
    focused_widget = None
    # Updated widgets since the previous frame.
    # If a widget was added or removed, then its parent must be in that dict as well.
    # Widgets should probably be grouped by the uid of their root window to support multiple windows, but I haven't found a practical way to get it: on_parent is called too early.
    updated_widgets = {}

    def __init__(self, **kwargs):
        super(AccessibleBehavior, self).__init__(**kwargs)
        self.is_clickable = False
        self.is_focusable = False

    def grab_focus(self):
        # When a widget gets focused, no need to update its accessible representation, unless gaining or losing the focus updates some of its properties.
        widget.focused_widget = self

    def on_accessibility_action(self, action):
        pass
