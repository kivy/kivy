# This example has been tested on Windows only.
# To try it out:
# - Enable the Narrator
# - Launch the program
# Use Tab and Shift+Tab to move the focus
# Use CapsLock+Enter to activate the buttons or toggle the checkbox

from kivy.app import App
from kivy.core.accessibility import AccessibilityManager, Action, Role
from kivy.uix.behaviors.accessibility import AccessibleBehavior
from kivy.uix.behaviors.focus import FocusBehavior
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label

def update_pos(widget, pos):
    widget.accessible_pos = pos

def update_size(widget, size):
    widget.accessible_size = size

def update_text(widget, text):
    widget.accessible_name = text

def grab_focus(widget, is_focused):
    # This is obviously incompatible with multi-keyboard setup, but assistive technologies only allow one element to be focused at a time.
    if is_focused:
        widget.grab_focus()

class AccessibleLabel(AccessibleBehavior, Label):
    # Usually a label should be linked to another widget for which it can provide the name or description.
    # This is why labels aren't focusable.
    def __init__(self, **kwargs):
        super(AccessibleLabel, self).__init__(**kwargs)
        self.accessible_role = Role.STATIC_TEXT
        self.accessible_pos = self.pos
        self.accessible_size = self.size
        self.accessible_name = self.text
        self.bind(pos=update_pos)
        self.bind(size=update_size)
        self.bind(text=update_text)


class AccessibleButton(AccessibleBehavior, FocusBehavior, Button):
    def __init__(self, **kwargs):
        super(AccessibleButton, self).__init__(**kwargs)
        self.accessible_role = Role.BUTTON
        self.accessible_pos = self.pos
        self.accessible_size = self.size
        self.accessible_name = self.text
        self.is_clickable = True
        self.is_focusable = True
        self.bind(pos=update_pos)
        self.bind(size=update_size)
        self.bind(text=update_text)
        self.bind(focus=grab_focus)

    def on_accessibility_action(self, action):
        if action == Action.FOCUS:
            self.focus = True
        elif action == Action.DEFAULT:
            self.trigger_action(0)


def update_active(widget, is_active):
    widget.accessible_checked_state = is_active
    widget.update()

class AccessibleCheckBox(AccessibleBehavior, FocusBehavior, CheckBox):
    def __init__(self, **kwargs):
        super(AccessibleCheckBox, self).__init__(**kwargs)
        self.accessible_role = Role.CHECK_BOX
        self.accessible_checked_state = False
        self.accessible_pos = self.pos
        self.accessible_size = self.size
        self.is_clickable = True
        self.is_focusable = True
        self.bind(pos=update_pos)
        self.bind(size=update_size)
        self.bind(focus=grab_focus)
        self.bind(active=update_active)

    def on_accessibility_action(self, action):
        if action == Action.FOCUS:
            self.focus = True
        elif action == Action.DEFAULT:
            self.trigger_action(0)


def update_children(widget, children):
    widget.accessible_children = children


class AccessibleBoxLayout(AccessibleBehavior, BoxLayout):
    # We keep this kind of widget in the UI tree mostly for convenience, but AccessKit will filter them out.
    def __init__(self, **kwargs):
        super(AccessibleBoxLayout, self).__init__(**kwargs)
        self.accessible_role = Role.GENERIC_CONTAINER
        self.accessible_pos = self.pos
        self.accessible_size = self.size
        self.bind(children=update_children)
        self.bind(pos=update_pos)
        self.bind(size=update_size)


class AccessibleApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accessibility_manager = AccessibilityManager()
    
    def build(self):

        title = AccessibleLabel(text='Accessible app with Kivy')

        button_1 = AccessibleButton(text='Button 1')
        button_1.bind(on_press=lambda j: print("Button 1 was pressed."))

        button_2 = AccessibleButton(text='Button 2')
        button_2.bind(on_press=lambda j: print("Button 2 was pressed."))

        checkbox = AccessibleCheckBox()

        buttons = AccessibleBoxLayout(orientation='horizontal')
        buttons.add_widget(button_1)
        button_1.focus = True
        buttons.add_widget(button_2)
        buttons.add_widget(checkbox)

        layout = AccessibleBoxLayout(orientation='vertical')
        layout.add_widget(title)
        layout.add_widget(buttons)

        return layout

    def on_start(self):
        super().on_start()
        self.root_window.register_event_manager(self.accessibility_manager)

    def on_stop(self):
        super().on_stop()


if __name__ == '__main__':
    AccessibleApp().run()
