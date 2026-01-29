from abc import ABC, abstractmethod
from enum import Enum
from kivy.clock import Clock
from kivy.eventmanager import EventManagerBase
from kivy.uix import widget


providers = []
provider = None


class AccessibilityBase(ABC):
    def __init_subclass__(cls, **kwargs):
        providers.append(cls)

    @abstractmethod
    def install(self, window_info):
        pass


class Action(Enum):
    # Assistive technologies can request to manipulate widgets on behalf of the user.
    FOCUS = 0
    DEFAULT = 1


class AccessibilityManager(EventManagerBase):
    type_ids = ()

    def __init__(self, **kwargs):
        from . import accessibility_accesskit

        super().__init__(**kwargs)
        self.clock = None
        self.previous_focus = None
        self.root_window_changed = True

    def _notify_root_window_changed(self):
        self.root_window_changed = True

    def _on_accessibility_action(self, target, action):
        from kivy.uix.behaviors.accessibility import AccessibleBehavior
        for child in self.window.children[:]:
            if isinstance(child, AccessibleBehavior) and child.uid == target:
                child.on_accessibility_action(action)
            else:
                for descendant in child.walk():
                    if (
                        isinstance(descendant, AccessibleBehavior)
                        and descendant.uid == target
                    ):
                        descendant.on_accessibility_action(action)
                        return

    def start(self):
        self.window.bind(children=lambda w, v: self._notify_root_window_changed())
        if self.window.accessibility:
            self.window.accessibility.action_request_callback = (
                self._on_accessibility_action
            )
        self.clock = Clock.schedule_interval(self.check_for_updates, 0)

    def check_for_updates(self, dt):
        if (
            self.root_window_changed
            or widget.updated_widgets != {}
            or widget.focused_widget != self.previous_focus
        ):
            if self.window.accessibility and not self.window.accessibility.update(
                    self.root_window_changed
            ):
                return
            self.root_window_changed = False
            widget.updated_widgets = {}
            widget.previous_focus = widget.focused_widget


class Role(Enum):
    # Role is the most important property of an accessible widget.
    # It will tell assistive technologies how to present it to the user,
    # which other properties to expect, and what kind of actions can be
    # performed on it.
    UNKNOWN = 0
    """No information about how to present this widget"""
    LABEL = 1
    """This widget's text explains another widget"""
    GENERIC_CONTAINER = 2
    """The widget is for containing other widgets

    In Kivy, generic containers are usually :class:`~kivy.uix.layout.Layout`s.

    """
    TOGGLE = 3
    """The widget is in one of two possible Boolean states, which the user may switch

    The widget is most likely either :class:`~kivy.uix.togglebutton.ToggleButton` or
    :class:`kivy.uix.checkbox.CheckBox`.

    """
    BUTTON = 4
    """A button that does one thing when pressed"""
    DOCUMENT = 5
    """A large amount of text the user may want to read

    DOCUMENT may be a container for many LABEL widgets or similar.

    """
    PARAGRAPH = 6
    """A piece of text within a document"""
    HEADING = 7
    """Text starting a section of a document or a menu"""
    MENU = 8
    """Modal/drop/accordion/etc. menu with many related widgets inside"""
