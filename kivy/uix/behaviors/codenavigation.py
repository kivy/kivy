'''
Code Navigation Behavior
========================

The :class:`~kivy.uix.bahviors.CodeNavigationBehavior` modifies navigation
behavior in the :class:`~kivy.uix.textinput.TextInput`, making it work like an
IDE instead of a word processor.

Using this mixin gives the TextInput the ability to recognize whitespace,
punctuation and case variations (e.g. CamelCase) when moving over text. It
is currently used by the :class:`~kivy.uix.codeinput.CodeInput` widget.
'''

__all__ = ('CodeNavigationBehavior', )

from kivy.event import EventDispatcher
import string


class CodeNavigationBehavior(EventDispatcher):
    '''Code navigation behavior. Modifies the navigation behavior in TextInput
    to work like an IDE instead of a word processor. Please see the
    :mod:`code navigation behaviors module <kivy.uix.behaviors.codenavigation>`
    documentation for more information.

    .. versionadded:: 1.9.1
    '''

    def _move_cursor_word_left(self, index=None):
        pos = index or self.cursor_index()
        pos -= 1

        if pos == 0:
            return 0, 0

        col, row = self.get_cursor_from_index(pos)
        lines = self._lines

        ucase = string.ascii_uppercase
        lcase = string.ascii_lowercase
        ws = string.whitespace
        punct = string.punctuation

        mode = 'normal'

        rline = lines[row]
        c = rline[col] if len(rline) > col else '\n'
        if c in ws:
            mode = 'ws'
        elif c == '_':
            mode = 'us'
        elif c in punct:
            mode = 'punct'
        elif c not in ucase:
            mode = 'camel'

        while True:
            if col == -1:
                if row == 0:
                    return 0, 0
                row -= 1
                rline = lines[row]
                col = len(rline)
            lc = c
            c = rline[col] if len(rline) > col else '\n'
            if c == '\n':
                if lc not in ws:
                    col += 1
                break
            if mode in ('normal', 'camel') and c in ws:
                col += 1
                break
            if mode in ('normal', 'camel') and c in punct:
                col += 1
                break
            if mode == 'camel' and c in ucase:
                break
            if mode == 'punct' and (c == '_' or c not in punct):
                col += 1
                break
            if mode == 'us' and c != '_' and (c in punct or c in ws):
                col += 1
                break

            if mode == 'us' and c != '_':
                mode = ('normal' if c in ucase
                        else 'ws' if c in ws
                else 'camel')
            elif mode == 'ws' and c not in ws:
                mode = ('normal' if c in ucase
                        else 'us' if c == '_'
                else 'punct' if c in punct
                else 'camel')

            col -= 1

        if col > len(rline):
            if row == len(lines) - 1:
                return row, len(lines[row])
            row += 1
            col = 0

        return col, row

    def _move_cursor_word_right(self, index=None):
        pos = index or self.cursor_index()
        col, row = self.get_cursor_from_index(pos)
        lines = self._lines
        mrow = len(lines) - 1

        if row == mrow and col == len(lines[row]):
            return col, row

        ucase = string.ascii_uppercase
        lcase = string.ascii_lowercase
        ws = string.whitespace
        punct = string.punctuation

        mode = 'normal'

        rline = lines[row]
        c = rline[col] if len(rline) > col else '\n'
        if c in ws:
            mode = 'ws'
        elif c == '_':
            mode = 'us'
        elif c in punct:
            mode = 'punct'
        elif c in lcase:
            mode = 'camel'

        while True:
            if mode in ('normal', 'camel', 'punct') and c in ws:
                mode = 'ws'
            elif mode in ('normal', 'camel') and c == '_':
                mode = 'us'
            elif mode == 'normal' and c not in ucase:
                mode = 'camel'

            if mode == 'us':
                if c in ws:
                    mode = 'ws'
                elif c != '_':
                    break
            if mode == 'ws' and c not in ws:
                break
            if mode == 'camel' and c in ucase:
                break
            if mode == 'punct' and (c == '_' or c not in punct):
                break
            if mode != 'punct' and c != '_' and c in punct:
                break

            col += 1

            if col > len(rline):
                if row == mrow:
                    return len(rline), mrow
                row += 1
                rline = lines[row]
                col = 0

            c = rline[col] if len(rline) > col else '\n'
            if c == '\n':
                break

        return col, row
