"""
Custom Keyboards
================

This demo shows how to create and display custom keyboards on screen.
Note that the new "input_type" property of the TextInput means that this
is rarely needed. We provide this demo for the sake of completeness.
"""
# Author: Zen-CODE
from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.vkeyboard import VKeyboard
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from functools import partial
from kivy.config import Config
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy import require

# This example uses features introduced in Kivy 1.8.0, namely being able
# to load custom json files from the app folder.
require("1.8.0")

Builder.load_string('''
<KeyboardScreen>:
    displayLabel: displayLabel
    kbContainer: kbContainer
    BoxLayout:
        orientation: 'vertical'
        Label:
            size_hint_y: 0.15
            text: "Available Keyboard Layouts"
        BoxLayout:
            id: kbContainer
            size_hint_y: 0.2
            orientation: "horizontal"
            padding: 10
        Label:
            id: displayLabel
            size_hint_y: 0.15
            markup: True
            text: "[b]Key pressed[/b] - None"
            halign: "center"
        Button:
            text: "Back"
            size_hint_y: 0.1
            on_release: root.manager.current = "mode"
        Widget:
            # Just a space taker to allow for the popup keyboard
            size_hint_y: 0.5

<ModeScreen>:
    center_label: center_label
    mode_spinner: mode_spinner
    FloatLayout:
        BoxLayout:
            orientation: "vertical"
            size_hint: 0.8, 0.8
            pos_hint: {"x": 0.1, "y": 0.1}
            padding: "5sp"
            spacing: "5sp"
            Label:
                canvas:
                    Color:
                        rgba: 0, 0, 1, 0.3
                    Rectangle:
                        pos: self.pos
                        size: self.size

                text: "Custom Keyboard Demo"
                size_hint_y: 0.1
            Label:
                id: center_label
                markup: True
                size_hint_y: 0.6
            BoxLayout:
                orientation: "horizontal"
                size_hint_y: 0.1
                padding: "5sp"
                Widget:
                    size_hint_x: 0.2
                Label:
                    text: "Current keyboard mode :"
                Spinner:
                    id: mode_spinner
                    values: "''", "'dock'", "'system'", "'systemanddock'",\
                            "'systemandmulti'"
                Button:
                    text: "Set"
                    on_release: root.set_mode(mode_spinner.text)
                Widget:
                    size_hint_x: 0.2
            Widget:
                size_hint_y: 0.1
            BoxLayout:
                orientation: "horizontal"
                size_hint_y: 0.1
                Button:
                    text: "Exit"
                    on_release: exit()
                Button:
                    text: "Continue"
                    on_release: root.next()

''')


class ModeScreen(Screen):
    """
    Present the option to change keyboard mode and warn of system-wide
    consequences.
    """
    center_label = ObjectProperty()
    mode_spinner = ObjectProperty()

    keyboard_mode = ""

    def on_pre_enter(self, *args):
        """ Detect the current keyboard mode and set the text of the main
        label accordingly. """

        self.keyboard_mode = Config.get("kivy", "keyboard_mode")
        self.mode_spinner.text = "'{0}'".format(self.keyboard_mode)

        p1 = "Current keyboard mode: '{0}'\n\n".format(self.keyboard_mode)
        if self.keyboard_mode in ['dock', 'system', 'systemanddock']:
            p2 = "You have the right setting to use this demo.\n\n"
        else:
            p2 = "You need the keyboard mode to 'dock', 'system' or '"\
                 "'systemanddock'(below)\n in order to "\
                 "use custom onscreen keyboards.\n\n"

        p3 = "[b][color=#ff0000]Warning:[/color][/b] This is a system-wide " \
            "setting and will affect all Kivy apps. If you change the\n" \
            " keyboard mode, please use this app" \
            " to reset this value to it's original one."

        self.center_label.text = "".join([p1, p2, p3])

    def set_mode(self, mode):
        """ Sets the keyboard mode to the one specified """
        Config.set("kivy", "keyboard_mode", mode.replace("'", ""))
        Config.write()
        self.center_label.text = "Please restart the application for this\n" \
            "setting to take effect."

    def next(self):
        """ Continue to the main screen """
        self.manager.current = "keyboard"


class KeyboardScreen(Screen):
    """
    Screen containing all the available keyboard layouts. Clicking the buttons
    switches to these layouts.
    """
    displayLabel = ObjectProperty()
    kbContainer = ObjectProperty()

    def __init__(self, **kwargs):
        super(KeyboardScreen, self).__init__(**kwargs)
        self._add_keyboards()
        self._keyboard = None

    def _add_keyboards(self):
        """ Add a buttons for each available keyboard layout. When clicked,
        the buttons will change the keyboard layout to the one selected. """
        layouts = list(VKeyboard().available_layouts.keys())
        # Add the file in our app directory, the .json extension is required.
        layouts.append("numeric.json")
        for key in layouts:
            self.kbContainer.add_widget(
                Button(
                    text=key,
                    on_release=partial(self.set_layout, key)))

    def set_layout(self, layout, button):
        """ Change the keyboard layout to the one specified by *layout*. """
        kb = Window.request_keyboard(
            self._keyboard_close, self)
        if kb.widget:
            # If the current configuration supports Virtual Keyboards, this
            # widget will be a kivy.uix.vkeyboard.VKeyboard instance.
            self._keyboard = kb.widget
            self._keyboard.layout = layout
        else:
            self._keyboard = kb

        self._keyboard.bind(on_key_down=self.key_down,
                            on_key_up=self.key_up)

    def _keyboard_close(self, *args):
        """ The active keyboard is being closed. """
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self.key_down)
            self._keyboard.unbind(on_key_up=self.key_up)
            self._keyboard = None

    def key_down(self, keyboard, keycode, text, modifiers):
        """ The callback function that catches keyboard events. """
        self.displayLabel.text = u"Key pressed - {0}".format(text)

    # def key_up(self, keyboard, keycode):
    def key_up(self, keyboard, keycode, *args):
        """ The callback function that catches keyboard events. """
        self.displayLabel.text += u" (up {0[1]})".format(keycode)


class KeyboardDemo(App):
    sm = None  # The root screen manager

    def build(self):
        self.sm = ScreenManager()
        self.sm.add_widget(ModeScreen(name="mode"))
        self.sm.add_widget(KeyboardScreen(name="keyboard"))
        self.sm.current = "mode"
        return self.sm


if __name__ == "__main__":
    KeyboardDemo().run()
