from kivy.uix import widget


class AccessibleBehavior(object):

    def __init__(self, **kwargs):
        super(AccessibleBehavior, self).__init__(**kwargs)
        self.is_clickable = False
        self.is_focusable = False

    def grab_focus(self):
        # When a widget gets focused, no need to update its accessible representation, unless gaining or losing the focus updates some of its properties.
        widget.focused_widget = self

    def on_accessibility_action(self, action):
        pass
