from enum import Enum
from kivy.clock import Clock
from kivy.eventmanager import EventManagerBase
from kivy.uix.behaviors.accessibility import AccessibleBehavior

class AccessibilityBase(object):
    def install(self, window_info):
        pass

    def update(self, root_window_changed=False):
        return False

class Role(Enum):
    # Role is the most important property of an accessible widget.
    # It will tell assistive technologies how to present it to the user, which other properties to expect, and what kind of actions can be performed on it.
    UNKNOWN = 0
    STATIC_TEXT = 1
    GENERIC_CONTAINER = 2
    CHECK_BOX = 3
    BUTTON = 4

class Action(Enum):
    # Assistive technologies can request to manipulate widgets on behalf of the user.
    FOCUS = 0
    DEFAULT = 1

class AccessibilityManager(EventManagerBase):
    type_ids = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.clock = None
        self.previous_focus = None
        self.root_window_changed = True

    def _notify_root_window_changed(self):
        self.root_window_changed = True

    def _on_accessibility_action(self, target, action):
        for child in self.window.children[:]:
            if isinstance(child, AccessibleBehavior) and child.accessible_uid == target:
                child.on_accessibility_action(action)
            else:
                for descendant in child.walk():
                    if isinstance(descendant, AccessibleBehavior) and descendant.accessible_uid == target:
                        descendant.on_accessibility_action(action)
                        return

    def start(self):
        self.window.bind(children=lambda w, v: self._notify_root_window_changed())
        self.window.accessibility.action_request_callback = self._on_accessibility_action
        self.clock = Clock.schedule_interval(self.check_for_updates, 0)

    def check_for_updates(self, dt):
        if self.root_window_changed or AccessibleBehavior.updated_widgets != {} or AccessibleBehavior.focused_widget != self.previous_focus:
            if not self.window.accessibility.update(self.root_window_changed):
                return
            self.root_window_changed = False
            AccessibleBehavior.updated_widgets = {}
            self.previous_focus = AccessibleBehavior.focused_widget
