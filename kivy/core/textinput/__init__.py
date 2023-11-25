"""
TextInput
========

An abstraction for TextInput. Based on the selected backend, a different
implementation will be selected.

This TextInput provider has been added in order to support the IME keyboard
on Android and iOS (which is stricly needed for certain languages like Chinese).
A target widget (not necessarly a TextInput UI widget) must be provided as we need
to attach the Core provider to a specific area of the screen. (For keyboard management).

A ``validator`` can be provided to validate the input. It must be a callable. If the
callable returns False, the input will be rejected (and will be asked to the selected backend
to remove the characters from the underlying textinput implementation).

It also allows us to have keyboard suggestions on Android and iOS.

.. versionadded:: 2.3.0

"""

__all__ = (
    "TextInputBase",
    "TextInput",
)

from kivy.core import core_select_lib
from kivy.event import EventDispatcher
from kivy.utils import platform
from kivy.logger import Logger
from kivy.uix.widget import Widget


class TextInputBase(EventDispatcher):
    """Base class for TextInput implementations.

    :Events:
        `on_focus`
            Fired when the textinput focused or unfocused.
        `on_text_changed`
            Fired when the text changed on the underlying textinput.
        `on_selection_changed`
            Fired when the selection changed on the underlying textinput.
    """

    __events__ = (
        "on_focus",
        "on_text_changed",
        "on_selection_changed",
        "on_shortcut",
        "on_keyboard_key_down",
        "on_keyboard_key_up",
        "on_keyboard_textinput",
        "on_action",
    )

    def __init__(self, target: Widget, validator: callable = None):
        self._input_type = "null"
        self.selection = [0, 0]
        self.focus = False
        self.keyboard_suggestions = True
        self._target = target
        self._validator = validator
        self._text = ""

    @property
    def keyboard(self):
        Logger.warning(
            f"{self.__class__.__name__}: This provider does not support the keyboard property"
        )
        return None

    @keyboard.setter
    def keyboard(self, value):
        Logger.warning(
            f"{self.__class__.__name__}: This provider does not support setting the keyboard property"
        )

    @property
    def input_type(self):
        return self._input_type

    @input_type.setter
    def input_type(self, value):
        self._input_type = value

    @property
    def focus(self):
        return self._focus

    @focus.setter
    def focus(self, value):
        self._focus = value
        self.dispatch("on_focus", value)

    @property
    def selected_text(self):
        return self.text[self.selection[0] : self.selection[1]]

    def start(self):
        """Only when start is called the underlying textinput will be created.
        When the underlying textinput is ready to use, it will change the
        focus to True, which will trigger the on_focus event.
        """

    def resume(self):
        self.focus = True

    def stop(self):
        self.focus = False

    def pause(self):
        self.focus = False

    def select(self, start, end):
        self.selection = [start, end]

    def copy(self):
        return self.selected_text

    def cut(self):
        raise NotImplementedError

    def paste(self, substring):
        raise NotImplementedError

    def redo(self):
        raise NotImplementedError

    def reset_redo(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError
    
    def reset_undo(self):
        raise NotImplementedError

    def backspace(self):
        raise NotImplementedError

    def on_focus(self, value):
        pass

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self.dispatch("on_text_changed", value, 0, len(value))

    def on_text_changed(self, value, start, end):
        print("on_text_changed", value, start, end)

    def on_selection_changed(self, start, end):
        pass

    def on_shortcut(self, key):
        pass

    def on_keyboard_key_down(self, keycode, text, modifiers):
        pass

    def on_keyboard_key_up(self, keycode):
        pass

    def on_keyboard_textinput(self, text):
        pass

    def on_action(self, action):
        pass


_providers = []

if platform == "android":
    _providers += (("android", "textinput_android", "TextInputAndroid"),)

if platform == "ios":
    _providers += (("ios", "textinput_ios", "TextInputiOS"),)

# Generic window implementation
# (it receives the keyboard events from the window provider)
_providers += (("window", "textinput_window", "TextInputWindow"),)

TextInput = core_select_lib("textinput", _providers)
