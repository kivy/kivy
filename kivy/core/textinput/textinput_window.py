import collections

from kivy.core.textinput import TextInputBase
from kivy.base import EventLoop
from kivy.utils import platform


INTERESTING_KEYS = {
    8: "backspace",
    9: "tab",
    13: "enter",
    27: "escape",
    127: "del",
    271: "enter",
    273: "cursor_up",
    274: "cursor_down",
    275: "cursor_right",
    276: "cursor_left",
    278: "cursor_home",
    279: "cursor_end",
    280: "cursor_pgup",
    281: "cursor_pgdown",
    303: "shift_L",
    304: "shift_R",
    305: "ctrl_L",
    306: "ctrl_R",
    308: "alt_L",
    307: "alt_R",
}


class TextInputWindow(TextInputBase):
    _keyboard = None
    _keyboards = {}

    def __init__(self, target, validator=None):
        super().__init__(target, validator)

        # Queues of text changes that can be undone or redone.
        self._undo_text_changes = collections.deque(maxlen=16)
        self._redo_text_changes = collections.deque(maxlen=16)

    @property
    def keyboard(self):
        return self._keyboard

    @keyboard.setter
    def keyboard(self, value):
        need_restart = False
        if self.focus:
            self.stop()
            need_restart = True
        self._keyboard = value
        if need_restart:
            self.start()

    def start(self):
        super().start()
        self._bind_keyboard()
        self.focus = True

    def resume(self):
        self._bind_keyboard()
        super().resume()

    def pause(self):
        self._unbind_keyboard()
        super().pause()

    def stop(self):
        if self.focus:
            self.pause()
        self._release_keyboard()
        super().stop()

    def undo(self):
        if not self._undo_text_changes:
            return

        undo_step = self._undo_text_changes.pop()
        self._redo_text_changes.append(undo_step)

        self._commit_text_change(
            undo_step["previous"]["substring"],
            undo_step["after"]["start_index"],
            undo_step["after"]["end_index"],
            from_undo_redo=True,
        )

    def reset_undo(self):
        self._undo_text_changes.clear()

    def redo(self):
        if not self._redo_text_changes:
            return

        redo_step = self._redo_text_changes.pop()
        self._undo_text_changes.append(redo_step)

        self._commit_text_change(
            redo_step["after"]["substring"],
            redo_step["previous"]["start_index"],
            redo_step["previous"]["end_index"],
            from_undo_redo=True,
        )

    def reset_redo(self):
        self._redo_text_changes.clear()

    def _keyboard_released(self):
        pass

    def _ensure_keyboard(self):
        if self._keyboard is not None:
            return

        self._keyboard = EventLoop.window.request_keyboard(
            self._keyboard_released,
            self._target,
            input_type=self.input_type,
            keyboard_suggestions=self.keyboard_suggestions,
        )

    def _release_keyboard(self):
        keyboard = self._keyboard
        if not keyboard:
            return

        if keyboard in TextInputWindow._keyboards:
            # The keyboard is in use, but may not be by us.
            # we can (and should) only release it if it is.
            if TextInputWindow._keyboards[keyboard] != self:
                return
            print("released")
            self._keyboard.release()
            self._keyboard = None
            del TextInputWindow._keyboards[keyboard]

    def _is_keyboard_in_use(self, keyboard):
        if (
            keyboard in TextInputWindow._keyboards
            and TextInputWindow._keyboards[keyboard]
        ):
            return TextInputWindow._keyboards[keyboard].focus
        return False

    def _key_down(self, key, repeat=False):
        displayed_str, internal_str, internal_action, scale, modifiers = key

        if internal_action is None:
            # Key is not marked as an internal action, so it should be
            # interpreted as text input.
            self._on_keyboard_textinput(self._keyboard, displayed_str)

        elif internal_action == "backspace":
            # Signal the TextInput that we want to delete the selection
            # or the character before the cursor current position.
            self._on_keyboard_textinput(self._keyboard, "")

        elif internal_action == "del":
            # Signal the TextInput that we want to delete the selection
            # or the character after the cursor current position.
            # TODO: I do not like it. We have a better way to do it?
            if self.selection[0] == self.selection[1]:
                self.selection = [self.selection[0], self.selection[0] + 1]
            self._on_keyboard_textinput(self._keyboard, "")

        elif internal_action in ("shift", "shift_L", "shift_R"):
            # TODO: is not working
            # The user pressed shift, and the textinput should receive the
            # shift_key_down event, so it can act accordingly.
            self.dispatch("on_action", "shift_key_down")

        elif internal_action in ("alt_L", "alt_R"):
            # The user pressed alt, and the textinput should receive the
            # alt_key_down event, so it can act accordingly.
            self.dispatch("on_action", "alt_key_down")

        elif internal_action in ("ctrl_L", "ctrl_R"):
            # The user pressed ctrl, and the textinput should receive the
            # ctrl_key_down event, so it can act accordingly.
            self.dispatch("on_action", "ctrl_key_down")

        elif internal_action.startswith("cursor_"):
            # The user wants to move inside the textinput by using the
            # arrow keys. We should signal the TextInput to move the cursor
            # accordingly.
            self.dispatch("on_action", internal_action)

        elif internal_action == "enter":
            if self._validator("\n"):
                # The validator has accepted the 'enter' key as valid, so we should
                # add a new line to the text.
                self._on_keyboard_textinput(self._keyboard, "\n")
            else:
                # The validator has rejected the 'enter' key (e.g. is not a multiline TextInput).
                # We should signal the TextInput to submit the text or act accordingly.
                self.dispatch("on_action", "enter")

        elif internal_action == "tab":
            if self._validator("\t"):
                # The validator has accepted the 'tab' key as valid, so we should
                # add a tab to the text.
                self._on_keyboard_textinput(self._keyboard, "\t")
            else:
                # The validator has rejected the 'tab' key.
                # We should signal the TextInput to act accordingly.
                if "shift" in modifiers:
                    self.dispatch("on_action", "shifttab")
                else:
                    self.dispatch("on_action", "tab")

        elif internal_action == "escape":
            # The user pressed escape, so it likely wants to cancel the
            # focus. We should signal the TextInput to cancel the focus.
            return self.dispatch("on_action", "escape")

    def _key_up(self, key, repeat=False):
        displayed_str, internal_str, internal_action, scale = key

        if internal_action in ("shift", "shift_L", "shift_R"):
            # The user released shift, so it should be interpreted as a
            # shift_key_up event, so the TextInput can act accordingly.
            self.dispatch("on_action", "shift_key_up")

        elif internal_action in ("alt_L", "alt_R"):
            # The user released alt, so it should be interpreted as a
            # alt_key_up event, so the TextInput can act accordingly.
            self.dispatch("on_action", "alt_key_up")
        
        elif internal_action in ("ctrl_L", "ctrl_R"):
            # The user released ctrl, so it should be interpreted as a
            # ctrl_key_up event, so the TextInput can act accordingly.
            self.dispatch("on_action", "ctrl_key_up")

    def _on_keyboard_key_up(self, keyboard, keycode):
        key = keycode[0]
        k = INTERESTING_KEYS.get(key)
        if k:
            key = (None, None, k, 1)
            self._key_up(key)

    def _on_keyboard_key_down(self, keyboard, keycode, text, modifiers):
        key = keycode[0]
        is_interesting_key = key in INTERESTING_KEYS

        # This allows *either* ctrl *or* cmd, but not both.
        modifiers = set(modifiers) - {"capslock", "numlock"}
        is_shortcut = (
            modifiers == {"ctrl"} or (platform == "macosx") and modifiers == {"meta"}
        )

        # That seems like a shortcut, so call the on_shortcut event.
        if is_shortcut and not is_interesting_key and text:
            return self.dispatch("on_shortcut", key)

        # Is a key we are interested in (like backspace, enter, etc.).
        if is_interesting_key:
            key = (None, None, INTERESTING_KEYS.get(key), 1, modifiers)
            return self._key_down(key)

        # The Window says the input is managed via the textinput event,
        # so other keys (text keys) should be ignored.
        if EventLoop.window.managed_textinput:
            return False

        # The key is not interesting, so it should be interpreted as text input.
        return self._on_keyboard_textinput(self._keyboard, text)

    def paste(self, substring):
        self._on_keyboard_textinput(self._keyboard, substring)

    def cut(self):
        data = self.selected_text
        self._on_keyboard_textinput(self._keyboard, "")
        return data

    def _on_keyboard_textinput(self, keyboard, substring):
        start_index, end_index = self.selection
        self._commit_text_change(substring, start_index, end_index)
        return True

    def _on_keyboard_textedit(self, keyboard, composition, start_index, selection_length):
        print("_on_keyboard_textedit", composition, start_index, selection_length)

        if selection_length == 0 and len(composition) != 0:
            # Add the last character of the composition to the text.
            self._commit_text_change(composition[-1], start_index, start_index)
            return True

        self._commit_text_change(composition[start_index:start_index + selection_length], start_index, start_index + selection_length)
        return True

    def _commit_text_change(
        self, substring, start_index, end_index, from_undo_redo=False
    ):

        if substring == "":
            # The change is a deletion or a replacement.
            if start_index == end_index:
                # No selection, delete one character (before the cursor).
                if start_index < 1:
                    # Nothing to delete.
                    return
                start_index -= 1

        if not from_undo_redo:

            self._undo_text_changes.append({
                "previous": {
                    "substring": self._text[start_index:end_index],
                    "start_index": start_index,
                    "end_index": end_index,
                },
                "after": {
                    "substring": substring,
                    "start_index": start_index,
                    "end_index": start_index + len(substring),
                },
            })

        self._text = self._text[:start_index] + substring + self._text[end_index:]

        self.dispatch("on_text_changed", substring, start_index, end_index)

        # We need to update the selection (or cursor) accordingly to the changes made.
        new_index = start_index + len(substring)
        self.selection = [new_index, new_index]
        self.dispatch("on_selection_changed", *self.selection)

    def _bind_keyboard(self):
        self._ensure_keyboard()
        keyboard = self._keyboard

        if not keyboard:
            return False

        if self._is_keyboard_in_use(keyboard):
            # The keyboard is already in use.
            # We should stop the TextInput that is using it.
            TextInputWindow._keyboards[keyboard].stop()

        # We now own the keyboard.
        TextInputWindow._keyboards[keyboard] = self

        keyboard.bind(
            on_key_down=self._on_keyboard_key_down,
            on_key_up=self._on_keyboard_key_up,
            on_textinput=self._on_keyboard_textinput,
            on_textedit=self._on_keyboard_textedit,
        )

    def _unbind_keyboard(self):
        keyboard = self._keyboard
        if not keyboard:
            return
        print("unbind", keyboard, self)
        # We no longer own the keyboard.
        TextInputWindow._keyboards[keyboard] = None

        keyboard.unbind(
            on_key_down=self._on_keyboard_key_down,
            on_key_up=self._on_keyboard_key_up,
            on_textinput=self._on_keyboard_textinput,
            on_textedit=self._on_keyboard_textedit,
        )
