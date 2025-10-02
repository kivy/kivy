# This example has been tested on Windows only.
# To try it out:
# - Enable the Narrator
# - Launch the program
# Use Tab and Shift+Tab to move the focus
# Use CapsLock+Enter to activate the buttons or toggle the checkbox

from kivy.app import App
from kivy.core.accessibility import AccessibilityManager, Action
from kivy.uix.widget import Role
from kivy.uix.behaviors.accessibility import AccessibleBehavior
from kivy.uix.behaviors.focus import FocusBehavior
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label

def update_text(widget, text):
    widget.accessible_name = text


class AccessibleLabel(AccessibleBehavior, Label):
    # Usually a label should be linked to another widget for which it can provide the name or description.
    # This is why labels aren't focusable.
    def __init__(self, **kwargs):
        super(AccessibleLabel, self).__init__(**kwargs)
        self.accessible_role = Role.CAPTION
        self.bind(text=update_text)


class AccessibleButton(AccessibleBehavior, FocusBehavior, Button):
    def __init__(self, **kwargs):
        super(AccessibleButton, self).__init__(**kwargs)
        self.accessible_role = Role.BUTTON
        self.is_clickable = True
        self.is_focusable = True
        self.bind(text=update_text)

    def on_accessibility_action(self, action):
        if action == Action.FOCUS:
            self.focus = True
        elif action == Action.DEFAULT:
            self.trigger_action(0)

class AccessibleCheckBox(AccessibleBehavior, FocusBehavior, CheckBox):
    def __init__(self, **kwargs):
        super(AccessibleCheckBox, self).__init__(**kwargs)
        self.accessible_role = Role.TOGGLE
        self.accessible_checked_state = False
        self.accessible_size = self.size
        self.is_focusable = True
        self.is_clickable = True

    def on_accessibility_action(self, action):
        if action == Action.FOCUS:
            self.focus = True
        elif action == Action.DEFAULT:
            self.trigger_action(0)


class AccessibleBoxLayout(AccessibleBehavior, BoxLayout):
    # We keep this kind of widget in the UI tree mostly for convenience, but AccessKit will filter them out.
    def __init__(self, **kwargs):
        super(AccessibleBoxLayout, self).__init__(**kwargs)
        self.accessible_role = Role.GENERIC_CONTAINER
        self.accessible_size = self.size


class AccessibleApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accessibility_manager = AccessibilityManager()
    
    def build(self):

        title = AccessibleLabel(text='Accessible app with Kivy')

        button_1 = AccessibleButton(text='Button 1')
        button_1.bind(on_press=lambda j: print("Button 1 was pressed."))

        button_2 = AccessibleButton(text='Button 2')
        button_1.focus_next = button_2
        button_2.bind(on_press=lambda j: print("Button 2 was pressed."))

        checkbox = AccessibleCheckBox()
        button_2.focus_next = checkbox
        checkbox.focus_next = button_1

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
