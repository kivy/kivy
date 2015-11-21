'''See :class:`EmacsBehavior` for more details.
'''

__all__ = ('EmacsBehavior', )

from kivy.event import EventDispatcher


class EmacsBehavior(EventDispatcher):

    def __init__(self, **kwargs):
        super(EmacsBehavior, self).__init__(**kwargs)

        self.bindings = {
            'ctrl': {
                'a': lambda: self.do_cursor_movement('cursor_home'),
                'e': lambda: self.do_cursor_movement('cursor_end'),
                'f': lambda: self.do_cursor_movement('cursor_right'),
                'b': lambda: self.do_cursor_movement('cursor_left'),
                'w': lambda: self._cut(self.selection_text),
                'y': self.paste,
            },
            'alt': {
                'w': self.copy,
                'f': lambda: self.do_cursor_movement('cursor_right',
                                                     control=True),
                'b': lambda: self.do_cursor_movement('cursor_left',
                                                     control=True),
                'd': self.delete_word_right,
                '\x08': self.delete_word_left,  # alt + backspace
            },
        }

    def keyboard_on_key_down(self, window, keycode, text, modifiers):

        key, key_str = keycode
        mod = modifiers[0] if modifiers else None
        is_emacs_shortcut = False

        if key in range(256):
            is_emacs_shortcut = ((mod == 'ctrl' and
                                  chr(key) in self.bindings['ctrl'].keys()) or
                                 (mod == 'alt' and
                                  chr(key) in self.bindings['alt'].keys()))
        if is_emacs_shortcut:
            emacs_shortcut = self.bindings[mod][chr(key)]  # Look up mod and key
            emacs_shortcut()
        else:
            super(EmacsBehavior, self).keyboard_on_key_down(window, keycode,
                                                            text, modifiers)

    def delete_word_right(self):
        '''Delete text right of the cursor to the end of the word'''
        start_index = self.cursor_index()
        start_cursor = self.cursor
        self.do_cursor_movement('cursor_right', control=True)
        end_index = self.cursor_index()
        if start_index != end_index:
            self.text = self.text[:start_index] + self.text[end_index:]
            self._set_cursor(pos=start_cursor)

    def delete_word_left(self):
        '''Delete text left of the cursor to the beginning of word'''
        start_index = self.cursor_index()
        self.do_cursor_movement('cursor_left', control=True)
        end_cursor = self.cursor
        end_index = self.cursor_index()
        if start_index != end_index:
            self.text = self.text[:end_index] + self.text[start_index:]
            self._set_cursor(pos=end_cursor)
