# -*- encoding: utf8 -*-
'''
Text Input
==========

.. versionadded:: 1.0.4

.. image:: images/textinput-mono.jpg
.. image:: images/textinput-multi.jpg

The :class:`TextInput` widget provides a box of editable plain text.

Unicode, multiline, cursor navigation, selection and clipboard features
are supported.

.. note::

    Two different coordinate systems are used with TextInput:

        - (x, y) Coordinates in pixels, mostly used for rendering on screen
        - (row, col) Cursor index in characters / lines, used for selection
          and cursor movement.


Usage example
-------------

To create a multiline textinput ('enter' key adds a new line)::

    from kivy.uix.textinput import TextInput
    textinput = TextInput(text='Hello world')

To create a monoline textinput, set the multiline property to false ('enter'
key will defocus the textinput and emit on_text_validate event)::

    def on_enter(instance, value):
        print('User pressed enter in', instance)

    textinput = TextInput(text='Hello world', multiline=False)
    textinput.bind(on_text_validate=on_enter)

The textinput's text is stored on its :data:`TextInput.text` property. To run a
callback when the text changes::

    def on_text(instance, value):
        print('The widget', instance, 'have:', value)

    textinput = TextInput()
    textinput.bind(text=on_text)

You can 'focus' a textinput, meaning that the input box will be highlighted,
and keyboard focus will be requested::

    textinput = TextInput(focus=True)

The textinput is defocused if the 'escape' key is pressed, or if another
widget requests the keyboard. You can bind a callback to the focus property to
get notified of focus changes::

    def on_focus(instance, value):
        if value:
            print('User focused', instance)
        else:
            print('User defocused', instance)

    textinput = TextInput()
    textinput.bind(focus=on_focus)


Selection
---------

The selection is automatically updated when the cursor position changes.
You can get the currently selected text from the
:data:`TextInput.selection_text` property.


Default shortcuts
-----------------

=============== ========================================================
   Shortcuts    Description
--------------- --------------------------------------------------------
Left            Move cursor to left
Right           Move cursor to right
Up              Move cursor to up
Down            Move cursor to down
Home            Move cursor at the beginning of the line
End             Move cursor at the end of the line
PageUp          Move cursor to 3 lines before
PageDown        Move cursor to 3 lines after
Backspace       Delete the selection or character before the cursor
Del             Delete the selection of character after the cursor
Shift + <dir>   Start a text selection. Dir can be Up, Down, Left, Right
Control + c     Copy selection
Control + x     Cut selection
Control + p     Paste selection
Control + a     Select all the content
Control + z     undo
Control + r     redo
=============== ========================================================

'''


__all__ = ('TextInput', )

import re
import sys
from functools import partial
from os import environ
from weakref import ref

from kivy.animation import Animation
from kivy.base import EventLoop
from kivy.cache import Cache
from kivy.clock import Clock
from kivy.config import Config
from kivy.compat import PY2
from kivy.logger import Logger
from kivy.metrics import inch
from kivy.utils import boundary, platform

from kivy.core.text import Label
from kivy.graphics import Color, Rectangle

from kivy.uix.widget import Widget
from kivy.uix.bubble import Bubble

from kivy.properties import StringProperty, NumericProperty, \
        ReferenceListProperty, BooleanProperty, AliasProperty, \
        ListProperty, ObjectProperty, VariableListProperty

Cache_register = Cache.register
Cache_append = Cache.append
Cache_get = Cache.get
Cache_remove = Cache.remove
Cache_register('textinput.label', timeout=60.)
Cache_register('textinput.width', timeout=60.)

FL_IS_NEWLINE = 0x01

# late binding
Clipboard = None

# for reloading, we need to keep a list of textinput to retrigger the rendering
_textinput_list = []

# cache the result
_is_osx = sys.platform == 'darwin'

# When we are generating documentation, Config doesn't exist
_is_desktop = False
if Config:
    _is_desktop = Config.getboolean('kivy', 'desktop')

# register an observer to clear the textinput cache when OpenGL will reload
if 'KIVY_DOC' not in environ:

    def _textinput_clear_cache(*l):
        Cache_remove('textinput.label')
        Cache_remove('textinput.width')
        for wr in _textinput_list[:]:
            textinput = wr()
            if textinput is None:
                _textinput_list.remove(wr)
            else:
                textinput._trigger_refresh_text()

    from kivy.graphics.context import get_context
    get_context().add_reload_observer(_textinput_clear_cache, True)


class TextInputCutCopyPaste(Bubble):
    # Internal class used for showing the little bubble popup when
    # copy/cut/paste happen.

    textinput = ObjectProperty(None)
    ''' Holds the ref to the TextInput this Bubble belongs to.
    '''

    but_cut = ObjectProperty(None)
    but_copy = ObjectProperty(None)
    but_paste = ObjectProperty(None)
    but_selectall = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.mode = 'normal'
        super(TextInputCutCopyPaste, self).__init__(**kwargs)
        Clock.schedule_interval(self._check_parent, .5)

    def _check_parent(self, dt):
        # this is a prevention to get the Bubble staying on the screen, if the
        # attached textinput is not on the screen anymore.
        parent = self.textinput
        while parent is not None:
            if parent == parent.parent:
                break
            parent = parent.parent
        if parent is None:
            Clock.unschedule(self._check_parent)
            if self.textinput:
                self.textinput._hide_cut_copy_paste()

    def on_parent(self, instance, value):
        parent = self.textinput
        children = self.content.children
        mode = self.mode

        if parent:
            self.clear_widgets()
            if mode == 'paste':
                # show only paste on long touch
                self.but_selectall.opacity = 1
                widget_list = [self.but_selectall, ]
                if not parent.readonly:
                    widget_list.append(self.but_paste)
            elif parent.readonly:
                # show only copy for read only text input
                widget_list = (self.but_copy, )
            else:
                # normal mode
                widget_list = (self.but_cut, self.but_copy, self.but_paste)

            for widget in widget_list:
                self.add_widget(widget)

    def do(self, action):
        textinput = self.textinput

        if action == 'cut':
            textinput._cut(textinput.selection_text)
        elif action == 'copy':
            textinput._copy(textinput.selection_text)
        elif action == 'paste':
            textinput._paste()
        elif action == 'selectall':
            textinput.select_all()
            self.mode = ''
            anim = Animation(opacity=0, d=.333)
            anim.bind(
                        on_complete=lambda *args:
                                        self.on_parent(self, self.parent))
            anim.start(self.but_selectall)


class TextInput(Widget):
    '''TextInput class. See module documentation for more information.

    :Events:
        `on_text_validate`
            Fired only in multiline=False mode, when the user hits 'enter'.
            This will also unfocus the textinput.
        `on_double_tap`
            Fired when a double tap happen in the text input. The default
            behavior select the text around the cursor position. More info at
            :meth:`on_double_tap`.
        `on_triple_tap`
            Fired when a triple tap happen in the text input. The default
            behavior select the line around the cursor position. More info at
            :meth:`on_triple_tap`.
        `on_quad_touch`
            Fired when four fingers are touching the text input. The default
            behavior select the whole text. More info at :meth:`on_quad_touch`

    .. versionchanged:: 1.7.0
        `on_double_tap`, `on_triple_tap` and `on_quad_touch` events added.
    '''

    __events__ = ('on_text_validate', 'on_double_tap', 'on_triple_tap',
            'on_quad_touch')

    def __init__(self, **kwargs):
        self._win = None
        self._cursor_blink_time = Clock.get_time()
        self._cursor = [0, 0]
        self._selection = False
        self._selection_finished = True
        self._selection_touch = None
        self.selection_text = u''
        self._selection_from = None
        self._selection_to = None
        self._bubble = None
        self._lines_flags = []
        self._lines_labels = []
        self._lines_rects = []
        self._hint_text_flags = []
        self._hint_text_labels = []
        self._hint_text_rects = []
        self._label_cached = None
        self._line_options = None
        self._keyboard = None
        self._keyboard_mode = Config.get('kivy', 'keyboard_mode')
        self.reset_undo()
        self._touch_count = 0
        self.interesting_keys = {
            8: 'backspace',
            13: 'enter',
            127: 'del',
            271: 'enter',
            273: 'cursor_up',
            274: 'cursor_down',
            275: 'cursor_right',
            276: 'cursor_left',
            278: 'cursor_home',
            279: 'cursor_end',
            280: 'cursor_pgup',
            281: 'cursor_pgdown',
            303: 'shift_L',
            304: 'shift_R'}

        super(TextInput, self).__init__(**kwargs)

        self.bind(font_size=self._trigger_refresh_line_options,
                  font_name=self._trigger_refresh_line_options)

        self.bind(padding=self._update_text_options,
                  tab_width=self._update_text_options,
                  font_size=self._update_text_options,
                  font_name=self._update_text_options,
                  size=self._update_text_options,
                  password=self._update_text_options)

        self.bind(pos=self._trigger_update_graphics)

        self._trigger_refresh_line_options()
        self._trigger_refresh_text()

        # when the gl context is reloaded, trigger the text rendering again.
        _textinput_list.append(ref(self, TextInput._reload_remove_observer))

    def on_disabled(self, instance, value):
        if value:
            self.focus = False

    def on_text_validate(self):
        pass

    def cursor_index(self):
        '''Return the cursor index in the text/value.
        '''
        try:
            l = self._lines
            if len(l) == 0:
                return 0
            lf = self._lines_flags
            index, cr = self.cursor
            for row in range(cr):
                if row >= len(l):
                    continue
                index += len(l[row])
                if lf[row] & FL_IS_NEWLINE:
                    index += 1
            if lf[cr] & FL_IS_NEWLINE:
                index += 1
            return index
        except IndexError:
            return 0

    def cursor_offset(self):
        '''Get the cursor x offset on the current line.
        '''
        offset = 0
        row = self.cursor_row
        col = self.cursor_col
        _lines = self._lines
        if col and row < len(_lines):
            offset = self._get_text_width(
                _lines[row][:col], self.tab_width,
                self._label_cached)
        return offset

    def get_cursor_from_index(self, index):
        '''Return the (row, col) of the cursor from text index.
        '''
        index = boundary(index, 0, len(self.text))
        if index <= 0:
            return 0, 0
        lf = self._lines_flags
        l = self._lines
        i = 0
        for row in range(len(l)):
            ni = i + len(l[row])
            if lf[row] & FL_IS_NEWLINE:
                ni += 1
                i += 1
            if ni >= index:
                return index - i, row
            i = ni
        return index, row

    def select_text(self, start, end):
        ''' Select portion of text displayed in this TextInput.

        .. versionadded:: 1.4.0

        :Parameters:
            `start`
                Index of textinput.text from where to start selection
            `end`
                Index of textinput.text till which the selection should be
                displayed
        '''
        if end < start:
            raise Exception('end must be superior to start')
        m = len(self.text)
        self._selection_from = boundary(start, 0, m)
        self._selection_to = boundary(end, 0, m)
        self._selection_finished = True
        self._update_selection(True)
        self._update_graphics_selection()

    def select_all(self):
        ''' Select all of the text displayed in this TextInput

        .. versionadded:: 1.4.0
        '''
        self.select_text(0, len(self.text))

    re_indent = re.compile('^(\s*|)')

    def _auto_indent(self, substring):
        index = self.cursor_index()
        _text = self._get_text(encode=False)
        if index > 0:
            line_start = _text.rfind('\n', 0, index)
            if line_start > -1:
                line = _text[line_start + 1:index]
                indent = self.re_indent.match(line).group()
                substring += indent
        return substring

    def insert_text(self, substring, from_undo=False):
        '''Insert new text on the current cursor position. Override this
        function in order to pre-process text for input validation
        '''
        if self.readonly:
            return

        if not from_undo and self.multiline and self.auto_indent \
                and substring == u'\n':
            substring = self._auto_indent(substring)

        cc, cr = self.cursor
        sci = self.cursor_index
        ci = sci()
        text = self._lines[cr]
        len_str = len(substring)
        insert_at_end = True if text[cc:] == u'' else False
        new_text = text[:cc] + substring + text[cc:]
        self._set_line_text(cr, new_text)

        wrap = (self._get_text_width(
                                    new_text,
                                    self.tab_width,
                                    self._label_cached) > self.width)
        if len_str > 1 or substring == u'\n' or wrap:
            # Avoid refreshing text on every keystroke.
            # Allows for faster typing of text when the amount of text in
            # TextInput gets large.

            start, finish, lines,\
                lineflags, len_lines = self._get_line_from_cursor(cr, new_text)
            # calling trigger here could lead to wrong cursor positioning
            # and repeating of text when keys are added rapidly in a automated
            # fashion. From Android Keyboard for example.
            self._refresh_text_from_property('insert', start, finish, lines,
                lineflags, len_lines)

        self.cursor = self.get_cursor_from_index(ci + len_str)
        # handle undo and redo
        self._set_unredo_insert(ci, ci + len_str, substring, from_undo)

    def _get_line_from_cursor(self, start, new_text):
        # get current paragraph from cursor position
        finish = start
        lines = self._lines
        linesflags = self._lines_flags
        if start and not linesflags[start]:
            start -= 1
            new_text = u''.join((lines[start], new_text))
        try:
            while not linesflags[finish + 1]:
                new_text = u''.join((new_text, lines[finish + 1]))
                finish += 1
        except IndexError:
            pass
        lines, lineflags = self._split_smart(new_text)
        len_lines = max(1, len(lines))
        return start, finish, lines, lineflags, len_lines

    def _set_unredo_insert(self, ci, sci, substring, from_undo):
        # handle undo and redo
        if from_undo:
            return
        self._undo.append({'undo_command': ('insert', ci, sci),
            'redo_command': (ci, substring)})
        # reset redo when undo is appended to
        self._redo = []

    def reset_undo(self):
        '''Reset undo and redo lists from memory.

        .. versionadded:: 1.3.0

        '''
        self._redo = self._undo = []

    def do_redo(self):
        '''Do redo operation

        .. versionadded:: 1.3.0

        This action re-does any command that has been un-done by do_undo/ctrl+z.
        This function is automaticlly called when `ctrl+r` keys are pressed.
        '''
        try:
            x_item = self._redo.pop()
            undo_type = x_item['undo_command'][0]
            _get_cusror_from_index = self.get_cursor_from_index

            if undo_type == 'insert':
                ci, substring = x_item['redo_command']
                self.cursor = _get_cusror_from_index(ci)
                self.insert_text(substring, True)
            elif undo_type == 'bkspc':
                self.cursor = _get_cusror_from_index(x_item['redo_command'])
                self.do_backspace(from_undo=True)
            else:
                # delsel
                ci, sci = x_item['redo_command']
                self._selection_from = ci
                self._selection_to = sci
                self._selection = True
                self.delete_selection(True)
                self.cursor = _get_cusror_from_index(ci)
            self._undo.append(x_item)
        except IndexError:
            # reached at top of undo list
            pass

    def do_undo(self):
        '''Do undo operation

        .. versionadded:: 1.3.0

        This action un-does any edits that have been made since the last
        call to reset_undo().
        This function is automatically called when `ctrl+z` keys are pressed.
        '''
        try:
            x_item = self._undo.pop()
            undo_type = x_item['undo_command'][0]
            self.cursor = self.get_cursor_from_index(x_item['undo_command'][1])

            if undo_type == 'insert':
                ci, sci = x_item['undo_command'][1:]
                self._selection_from = ci
                self._selection_to = sci
                self._selection = True
                self.delete_selection(True)
            elif undo_type == 'bkspc':
                substring = x_item['undo_command'][2:][0]
                self.insert_text(substring, True)
            else:
                # delsel
                substring = x_item['undo_command'][2:][0]
                self.insert_text(substring, True)
            self._redo.append(x_item)
        except IndexError:
            # reached at top of undo list
            pass

    def do_backspace(self, from_undo=False, mode='bkspc'):
        '''Do backspace operation from the current cursor position.
        This action might do several things:

            - removing the current selection if available
            - removing the previous char, and back the cursor
            - do nothing, if we are at the start.

        '''
        if self.readonly:
            return
        cc, cr = self.cursor
        _lines = self._lines
        text = _lines[cr]
        cursor_index = self.cursor_index()
        prev_line_len = len(_lines[cr - 1])
        text_last_line = _lines[cr - 1]

        if cc == 0 and cr == 0:
            return
        _lines_flags = self._lines_flags
        start = cr
        if cc == 0:
            substring = u'\n' if _lines_flags[cr] else u' '
            new_text = text_last_line + text
            self._set_line_text(cr - 1, new_text)
            self._delete_line(cr)
            start = cr - 1
        else:
            #ch = text[cc-1]
            substring = text[cc - 1]
            new_text = text[:cc - 1] + text[cc:]
            self._set_line_text(cr, new_text)

        # refresh just the current line instead of the whole text
        start, finish, lines, lineflags, len_lines =\
                                    self._get_line_from_cursor(start, new_text)
        # avoid trigger refresh, leads to issue with
        # keys/text send rapidly through code.
        self._refresh_text_from_property('del', start, finish, lines,
                                    lineflags, len_lines)

        self.cursor = self.get_cursor_from_index(cursor_index - 1)
        # handle undo and redo
        self._set_undo_redo_bkspc(
                                cursor_index,
                                cursor_index - 1,
                                substring, from_undo)

    def _set_undo_redo_bkspc(self, ol_index, new_index, substring, from_undo):
        # handle undo and redo for backspace
        if from_undo:
            return
        self._undo.append({
            'undo_command': ('bkspc', new_index, substring),
            'redo_command': ol_index})
        #reset redo when undo is appended to
        self._redo = []

    def do_cursor_movement(self, action):
        '''Move the cursor relative to it's current position.
        Action can be one of :

            - cursor_left: move the cursor to the left
            - cursor_right: move the cursor to the right
            - cursor_up: move the cursor on the previous line
            - cursor_down: move the cursor on the next line
            - cursor_home: move the cursor at the start of the current line
            - cursor_end: move the cursor at the end of current line
            - cursor_pgup: move one "page" before
            - cursor_pgdown: move one "page" after

        .. warning::

            Current page has three lines before/after.

        '''
        pgmove_speed = 3
        col, row = self.cursor
        if action == 'cursor_up':
            row = max(row - 1, 0)
            col = min(len(self._lines[row]), col)
        elif action == 'cursor_down':
            row = min(row + 1, len(self._lines) - 1)
            col = min(len(self._lines[row]), col)
        elif action == 'cursor_left':
            if col == 0:
                if row:
                    row -= 1
                    col = len(self._lines[row])
            else:
                col, row = col - 1, row
        elif action == 'cursor_right':
            if col == len(self._lines[row]):
                if row < len(self._lines) - 1:
                    col = 0
                    row += 1
            else:
                col, row = col + 1, row
        elif action == 'cursor_home':
            col = 0
        elif action == 'cursor_end':
            col = len(self._lines[row])
        elif action == 'cursor_pgup':
            row /= pgmove_speed
            col = min(len(self._lines[row]), col)
        elif action == 'cursor_pgdown':
            row = min((row + 1) * pgmove_speed,
                                  len(self._lines) - 1)
            col = min(len(self._lines[row]), col)
        self.cursor = (col, row)

    def get_cursor_from_xy(self, x, y):
        '''Return the (row, col) of the cursor from an (x, y) position.
        '''
        padding_top = self.padding[1]
        l = self._lines
        dy = self.line_height + self.line_spacing
        cx = x - self.x
        scrl_y = self.scroll_y
        scrl_y = scrl_y / dy if scrl_y > 0 else 0
        cy = (self.top - padding_top + scrl_y * dy) - y
        cy = int(boundary(round(cy / dy - 0.5), 0, len(l) - 1))
        dcx = 0
        _get_text_width = self._get_text_width
        _tab_width = self.tab_width
        _label_cached = self._label_cached
        for i in range(1, len(l[cy]) + 1):
            if _get_text_width(l[cy][:i], _tab_width, _label_cached) >= cx:
                break
            dcx = i
        cx = dcx
        return cx, cy

    #
    # Selection control
    #
    def cancel_selection(self):
        '''Cancel current selection (if any).
        '''
        self._selection_from = self._selection_to = self.cursor_index()
        self._selection = False
        self._selection_finished = True
        self._selection_touch = None
        self._trigger_update_graphics()

    def delete_selection(self, from_undo=False):
        '''Delete the current text selection (if any).
        '''
        if self.readonly:
            return
        scrl_x = self.scroll_x
        scrl_y = self.scroll_y
        cc, cr = self.cursor
        if not self._selection:
            return
        v = self._get_text(encode=False)
        a, b = self._selection_from, self._selection_to
        if a > b:
            a, b = b, a
        self.cursor = cursor = self.get_cursor_from_index(a)
        start = cursor
        finish = self.get_cursor_from_index(b)
        cur_line = self._lines[start[1]][:start[0]] +\
            self._lines[finish[1]][finish[0]:]
        lines, lineflags = self._split_smart(cur_line)
        len_lines = len(lines)
        if start[1] == finish[1]:
            self._set_line_text(start[1], cur_line)
        else:
            self._refresh_text_from_property('del', start[1], finish[1], lines,
                lineflags, len_lines)
        self.scroll_x = scrl_x
        self.scroll_y = scrl_y
        # handle undo and redo for delete selecttion
        self._set_unredo_delsel(a, b, v[a:b], from_undo)
        self.cancel_selection()

    def _set_unredo_delsel(self, a, b, substring, from_undo):
        # handle undo and redo for backspace
        if from_undo:
            return

        self._undo.append({
            'undo_command': ('delsel', a, substring),
            'redo_command': (a, b)})
        # reset redo when undo is appended to
        self._redo = []

    def _update_selection(self, finished=False):
        '''Update selection text and order of from/to if finished is True.
        Can be called multiple times until finished is True.
        '''
        a, b = self._selection_from, self._selection_to
        if a > b:
            a, b = b, a
        self._selection_finished = finished
        self.selection_text = self._get_text(encode=False)[a:b]
        if not finished:
            self._selection = True
        else:
            self._selection = bool(len(self.selection_text))
            self._selection_touch = None
        if a == 0:
            # update graphics only on new line
            # allows smoother scrolling, noticeably
            # faster when dealing with large text.
            self._update_graphics_selection()
            #self._trigger_update_graphics()

    #
    # Touch control
    #
    def long_touch(self, dt):
        if self._selection_to == self._selection_from:
            self._show_cut_copy_paste(
                                        self._long_touch_pos,
                                        self._win,
                                        mode='paste')

    def on_double_tap(self):
        '''This event is dispatched when a double tap happens
        inside TextInput. The default behavior is to select the
        word around current cursor position. Override this to provide
        a separate functionality. Alternatively you can bind to this
        event to provide additional functionality.
        '''
        ci = self.cursor_index()
        cc = self.cursor_col
        line = self._lines[self.cursor_row]
        len_line = len(line)
        start = max(0, len(line[:cc]) - line[:cc].rfind(u' ') - 1)
        end = line[cc:].find(u' ')
        end = end if end > - 1 else (len_line - cc)
        Clock.schedule_once(lambda dt: self.select_text(ci - start, ci + end))

    def on_triple_tap(self):
        '''This event is dispatched when a triple tap happens
        inside TextInput. The default behavior is to select the
        line around current cursor position. Override this to provide
        a separate functionality. Alternatively you can bind to this
        event to provide additional functionality.
        '''
        ci = self.cursor_index()
        cc = self.cursor_col
        line = self._lines[self.cursor_row]
        len_line = len(line)
        Clock.schedule_once(lambda dt:
                                self.select_text(ci - cc, ci + (len_line - cc)))

    def on_quad_touch(self):
        '''This event is dispatched when a four fingers are touching
        inside TextInput. The default behavior is to select all text.
        Override this to provide a separate functionality. Alternatively
        you can bind to this event to provide additional functionality.
        '''
        Clock.schedule_once(lambda dt: self.select_all())

    def on_touch_down(self, touch):
        if self.disabled:
            return
        touch_pos = touch.pos
        if not self.collide_point(*touch_pos):
            if self._keyboard_mode == 'multi':
                if self.readonly:
                    self.focus = False
            else:
                self.focus = False
            return False
        if not self.focus:
            self.focus = True
        touch.grab(self)
        self._touch_count += 1
        if touch.is_double_tap:
            self.dispatch('on_double_tap')
        if touch.is_triple_tap:
            self.dispatch('on_triple_tap')
        if self._touch_count == 4:
            self.dispatch('on_quad_touch')

        win = self._win
        if not win:
            self._win = win = EventLoop.window
        if not win:
            Logger.warning('Textinput: '
                'Cannot show bubble, unable to get root window')
            return True

        self._hide_cut_copy_paste(self._win)
        # schedule long touch for paste
        self._long_touch_pos = touch.pos
        Clock.schedule_once(self.long_touch, .5)

        self.cursor = self.get_cursor_from_xy(*touch_pos)
        if not self._selection_touch:
            self.cancel_selection()
            self._selection_touch = touch
            self._selection_from = self._selection_to = self.cursor_index()
            self._update_selection()
        return False

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return
        if not self.focus:
            touch.ungrab(self)
            if self._selection_touch is touch:
                self._selection_touch = None
            return False
        if self._selection_touch is touch:
            self.cursor = self.get_cursor_from_xy(touch.x, touch.y)
            self._selection_to = self.cursor_index()
            self._update_selection()
            return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return
        touch.ungrab(self)
        self._touch_count -= 1

        # schedule long touch for paste
        Clock.unschedule(self.long_touch)

        if not self.focus:
            return False
        if self._selection_touch is touch:
            self._selection_to = self.cursor_index()
            self._update_selection(True)
            # show Bubble
            win = self._win
            if self._selection_to != self._selection_from:
                self._show_cut_copy_paste(touch.pos, win)
            return True

    def _hide_cut_copy_paste(self, win=None):
        win = win or self._win
        if win is None:
            return
        bubble = self._bubble
        if bubble is not None:
            anim = Animation(opacity=0, d=.225)
            anim.bind(on_complete=lambda *args: win.remove_widget(bubble))
            anim.start(bubble)

    def _show_cut_copy_paste(self, pos, win, parent_changed=False, mode='', *l):
        # Show a bubble with cut copy and paste buttons
        if not self.use_bubble:
            return
        bubble = self._bubble
        if bubble is None:
            self._bubble = bubble = TextInputCutCopyPaste(textinput=self)
            self.bind(parent=partial(self._show_cut_copy_paste,
                pos, win, True))
        else:
            win.remove_widget(bubble)
            if not self.parent:
                return
        if parent_changed:
            return

        # Search the position from the touch to the window
        x, y = pos
        t_pos = self.to_window(x, y)
        bubble_size = bubble.size
        win_size = win.size
        bubble.pos = (t_pos[0] - bubble_size[0] / 2., t_pos[1] + inch(.25))
        bubble_pos = bubble.pos
        lh, ls = self.line_height, self.line_spacing

        # FIXME found a way to have that feature available for everybody
        if bubble_pos[0] < 0:
            # bubble beyond left of window
            if bubble.pos[1] > (win_size[1] - bubble_size[1]):
                # bubble above window height
                bubble.pos = (0, (t_pos[1]) - (bubble_size[1] + lh + ls))
                bubble.arrow_pos = 'top_left'
            else:
                bubble.pos = (0, bubble_pos[1])
                bubble.arrow_pos = 'bottom_left'
        elif bubble.right > win_size[0]:
            # bubble beyond right of window
            if bubble_pos[1] > (win_size[1] - bubble_size[1]):
                # bubble above window height
                bubble.pos = (win_size[0] - bubble_size[0],
                        (t_pos[1]) - (bubble_size[1] + lh + ls))
                bubble.arrow_pos = 'top_right'
            else:
                bubble.right = win_size[0]
                bubble.arrow_pos = 'bottom_right'
        else:
            if bubble_pos[1] > (win_size[1] - bubble_size[1]):
                # bubble above window height
                bubble.pos = (bubble_pos[0],
                        (t_pos[1]) - (bubble_size[1] + lh + ls))
                bubble.arrow_pos = 'top_mid'
            else:
                bubble.arrow_pos = 'bottom_mid'

        bubble.mode = mode
        Animation.cancel_all(bubble)
        bubble.opacity = 0
        win.add_widget(bubble)
        Animation(opacity=1, d=.225).start(bubble)

    #
    # Private
    #

    @staticmethod
    def _reload_remove_observer(wr):
        # called when the textinput is deleted
        if wr in _textinput_list:
            _textinput_list.remove(wr)

    def on_focus(self, instance, value, *largs):
        win = self._win
        if not win:
            self._win = win = EventLoop.window
        if not win:
            # we got argument, it could be the previous schedule
            # cancel focus.
            if len(largs):
                Logger.warning('Textinput: ' +
                    'Cannot focus the element, unable to get root window')
                return
            else:
                Clock.schedule_once(partial(self.on_focus, self, value), 0)
            return

        self._editable = editable = (not (self.readonly or self.disabled) or
                    (platform in ('win', 'linux', 'macosx') and
                    self._keyboard_mode == 'system'))

        if value:
            keyboard = win.request_keyboard(self._keyboard_released, self)
            self._keyboard = keyboard
            if editable:
                keyboard.bind(
                    on_key_down=self._keyboard_on_key_down,
                    on_key_up=self._keyboard_on_key_up)
                Clock.schedule_interval(self._do_blink_cursor, 1 / 2.)
            else:
                # in non-editable mode, we still want shortcut (as copy)
                keyboard.bind(
                    on_key_down=self._keyboard_on_key_down)
        else:
            if self._keyboard:
                keyboard = self._keyboard
                keyboard.unbind(
                    on_key_down=self._keyboard_on_key_down,
                    on_key_up=self._keyboard_on_key_up)
                keyboard.release()
                self._keyboard = None
            self.cancel_selection()
            Clock.unschedule(self._do_blink_cursor)
            self._hide_cut_copy_paste(win)
            self._win = None

    def on_readonly(self, instance, value):
        if not value:
            self.focus = False

    def _ensure_clipboard(self):
        global Clipboard
        if hasattr(self, '_clip_mime_type'):
            return
        if Clipboard is None:
            from kivy.core.clipboard import Clipboard
        _platform = platform
        if _platform == 'win':
            self._clip_mime_type = 'text/plain;charset=utf-8'
            # windows clipboard uses a utf-16 encoding
            self._encoding = 'utf-16'
        elif _platform == 'linux':
            self._clip_mime_type = 'UTF8_STRING'
            self._encoding = 'utf-8'
        else:
            self._clip_mime_type = 'text/plain'
            self._encoding = 'utf-8'

    def _cut(self, data):
        self._copy(data)
        self.delete_selection()

    def _copy(self, data):
        # explicitly terminate strings with a null character
        # so as to avoid putting spurious data after the end.
        # MS windows issue.
        self._ensure_clipboard()
        data = data.encode(self._encoding) + b'\x00'
        Clipboard.put(data, self._clip_mime_type)

    def _paste(self):
        self._ensure_clipboard()
        _clip_types = Clipboard.get_types()

        mime_type = self._clip_mime_type
        if mime_type not in _clip_types:
            mime_type = 'text/plain'

        data = Clipboard.get(mime_type)
        if data is not None:
            # decode only if we don't have unicode
            # we would still need to decode from utf-16 (windows)
            # data is of type bytes in PY3
            data = data.decode(self._encoding, 'ignore')
            # remove null strings mostly a windows issue
            data = data.replace(u'\x00', u'')
            self.delete_selection()
            self.insert_text(data)
        data = None

    def _keyboard_released(self):
        # Callback called when the real keyboard is taken by someone else
        # called by the window if the keyboard is taken by somebody else
        # FIXME: handle virtual keyboard.
        self.focus = False

    def _get_text_width(self, text, tab_width, _label_cached):
        # Return the width of a text, according to the current line options
        kw = self._get_line_options()

        try:
            cid = u'{}\0{}'.format(text, kw)
        except UnicodeDecodeError:
            cid = '{}\0{}'.format(text, kw)

        width = Cache_get('textinput.width', cid)
        if width:
            return width
        if not _label_cached:
            _label_cached = self._label_cached
        text = text.replace('\t', ' ' * tab_width)
        if not self.password:
            width = _label_cached.get_extents(text)[0]
        else:
            width = _label_cached.get_extents('*' * len(text))[0]
        Cache_append('textinput.width', cid, width)
        return width

    def _do_blink_cursor(self, dt):
        # Callback called by the timer to blink the cursor, according to the
        # last activity in the widget
        b = (Clock.get_time() - self._cursor_blink_time)
        self.cursor_blink = int(b * 2) % 2

    def on_cursor(self, instance, value):
        # When the cursor is moved, reset the activity timer, and update all
        # the graphics.
        self._cursor_blink_time = Clock.get_time()
        self._trigger_update_graphics()

    def _delete_line(self, idx):
        # Delete current line, and fix cursor position
        assert(idx < len(self._lines))
        self._lines_flags.pop(idx)
        self._lines_labels.pop(idx)
        self._lines.pop(idx)
        self.cursor = self.cursor

    def _set_line_text(self, line_num, text):
        # Set current line with other text than the default one.
        self._lines_labels[line_num] = self._create_line_label(text)
        self._lines[line_num] = text

    def _trigger_refresh_line_options(self, *largs):
        Clock.unschedule(self._refresh_line_options)
        Clock.schedule_once(self._refresh_line_options, 0)

    def _refresh_line_options(self, *largs):
        self._line_options = None
        self._get_line_options()
        self._refresh_text_from_property()
        self._refresh_hint_text()
        self.cursor = self.get_cursor_from_index(len(self.text))

    def _trigger_refresh_text(self, *largs):
        if len(largs) and largs[0] == self:
            largs = ()
        Clock.unschedule(lambda dt: self._refresh_text_from_property(*largs))
        Clock.schedule_once(lambda dt: self._refresh_text_from_property(*largs))

    def _update_text_options(self, *largs):
        Cache_remove('textinput.width')
        self._trigger_refresh_text()

    def _refresh_text_from_trigger(self, dt, *largs):
        self._refresh_text_from_property(*largs)

    def _refresh_text_from_property(self, *largs):
        self._refresh_text(self._get_text(encode=False), *largs)

    def _refresh_text(self, text, *largs):
        # Refresh all the lines from a new text.
        # By using cache in internal functions, this method should be fast.
        mode = 'all'
        if len(largs) > 1:
            mode, start, finish, _lines, _lines_flags, len_lines = largs
            #start = max(0, start)
        else:
            _lines, self._lines_flags = self._split_smart(text)
        _lines_labels = []
        _line_rects = []
        _create_label = self._create_line_label

        for x in _lines:
            lbl = _create_label(x)
            _lines_labels.append(lbl)
            _line_rects.append(
                Rectangle(size=(lbl.size if lbl else (0, 0))))
            lbl = None

        if mode == 'all':
            self._lines_labels = _lines_labels
            self._lines_rects = _line_rects
            self._lines = _lines
        elif mode == 'del':
            if finish > start:
                self._insert_lines(start,
                                finish if start == finish else (finish + 1),
                                len_lines, _lines_flags,
                                _lines, _lines_labels, _line_rects)
        elif mode == 'insert':
            self._insert_lines(
                                start,
                                finish if (start == finish and not len_lines)
                                        else
                                (finish + 1),
                                len_lines, _lines_flags, _lines, _lines_labels,
                                _line_rects)

        line_label = _lines_labels[0]
        min_line_ht = self._label_cached.get_extents('_')[1]
        if line_label is None:
            self.line_height = max(1, min_line_ht)
        else:
            # with markup texture can be of height `1`
            self.line_height = max(line_label.height, min_line_ht)
        #self.line_spacing = 2
        # now, if the text change, maybe the cursor is not at the same place as
        # before. so, try to set the cursor on the good place
        row = self.cursor_row
        self.cursor = self.get_cursor_from_index(self.cursor_index())
        # if we back to a new line, reset the scroll, otherwise, the effect is
        # ugly
        if self.cursor_row != row:
            self.scroll_x = 0
        # with the new text don't forget to update graphics again
        self._trigger_update_graphics()

    def _insert_lines(self, start, finish, len_lines, _lines_flags, _lines,
        _lines_labels, _line_rects):
            self_lines_flags = self._lines_flags
            _lins_flags = []
            _lins_flags.extend(self_lines_flags[:start])
            if len_lines:
                # if not inserting at first line then
                if start:
                    # make sure line flags restored for first line
                    # _split_smart assumes first line to be not a new line
                    _lines_flags[0] = self_lines_flags[start]
                _lins_flags.extend(_lines_flags)
            _lins_flags.extend(self_lines_flags[finish:])
            self._lines_flags = _lins_flags

            _lins_lbls = []
            _lins_lbls.extend(self._lines_labels[:start])
            if len_lines:
                _lins_lbls.extend(_lines_labels)
            _lins_lbls.extend(self._lines_labels[finish:])
            self._lines_labels = _lins_lbls

            _lins_rcts = []
            _lins_rcts.extend(self._lines_rects[:start])
            if len_lines:
                _lins_rcts.extend(_line_rects)
            _lins_rcts.extend(self._lines_rects[finish:])
            self._lines_rects = _lins_rcts

            _lins = []
            _lins.extend(self._lines[:start])
            if len_lines:
                _lins.extend(_lines)
            _lins.extend(self._lines[finish:])
            self._lines = _lins

    def _trigger_update_graphics(self, *largs):
        Clock.unschedule(self._update_graphics)
        Clock.schedule_once(self._update_graphics, -1)

    def _update_graphics(self, *largs):
        # Update all the graphics according to the current internal values.
        #
        # This is a little bit complex, cause we have to :
        #     - handle scroll_x
        #     - handle padding
        #     - create rectangle for the lines matching the viewport
        #     - crop the texture coordinates to match the viewport
        #
        # This is the first step of graphics, the second is the selection.

        self.canvas.clear()
        add = self.canvas.add

        lh = self.line_height
        dy = lh + self.line_spacing

        # adjust view if the cursor is going outside the bounds
        sx = self.scroll_x
        sy = self.scroll_y

        # draw labels
        if not self.focus and (not self._lines or (
            not self._lines[0] and len(self._lines) == 1)):
            rects = self._hint_text_rects
            labels = self._hint_text_labels
            lines = self._hint_text_lines
        else:
            rects = self._lines_rects
            labels = self._lines_labels
            lines = self._lines
        padding_left, padding_top, padding_right, padding_bottom = self.padding
        x = self.x + padding_left
        y = self.top - padding_top + sy
        miny = self.y + padding_bottom
        maxy = self.top - padding_top
        for line_num, value in enumerate(lines):
            if miny <= y <= maxy + dy:
                texture = labels[line_num]
                if not texture:
                    y -= dy
                    continue
                size = list(texture.size)
                texc = texture.tex_coords[:]

                # calcul coordinate
                viewport_pos = sx, 0
                vw = self.width - padding_left - padding_right
                vh = self.height - padding_top - padding_bottom
                tw, th = list(map(float, size))
                oh, ow = tch, tcw = texc[1:3]
                tcx, tcy = 0, 0

                # adjust size/texcoord according to viewport
                if vw < tw:
                    tcw = (vw / tw) * tcw
                    size[0] = vw
                if vh < th:
                    tch = (vh / th) * tch
                    size[1] = vh
                if viewport_pos:
                    tcx, tcy = viewport_pos
                    tcx = tcx / tw * ow
                    tcy = tcy / th * oh

                # cropping
                mlh = lh
                if y > maxy:
                    vh = (maxy - y + lh)
                    tch = (vh / float(lh)) * oh
                    tcy = oh - tch
                    size[1] = vh
                if y - lh < miny:
                    diff = miny - (y - lh)
                    y += diff
                    vh = lh - diff
                    tch = (vh / float(lh)) * oh
                    size[1] = vh

                texc = (
                        tcx,
                        tcy + tch,
                        tcx + tcw,
                        tcy + tch,
                        tcx + tcw,
                        tcy,
                        tcx,
                        tcy)

                # add rectangle.
                r = rects[line_num]
                r.pos = int(x), int(y - mlh)
                r.size = size
                r.texture = texture
                r.tex_coords = texc
                add(r)

            y -= dy

        self._update_graphics_selection()

    def _update_graphics_selection(self):
        if not self._selection:
            return
        self.canvas.remove_group('selection')
        dy = self.line_height + self.line_spacing
        rects = self._lines_rects
        padding_top = self.padding[1]
        padding_bottom = self.padding[3]
        _top = self.top
        y = _top - padding_top + self.scroll_y
        miny = self.y + padding_bottom
        maxy = _top - padding_top
        draw_selection = self._draw_selection
        a, b = self._selection_from, self._selection_to
        if a > b:
            a, b = b, a
        get_cursor_from_index = self.get_cursor_from_index
        s1c, s1r = get_cursor_from_index(a)
        s2c, s2r = get_cursor_from_index(b)
        s2r += 1
        # pass only the selection lines[]
        # passing all the lines can get slow when dealing with a lot of text
        y -= s1r * dy
        _lines = self._lines
        _get_text_width = self._get_text_width
        tab_width = self.tab_width
        _label_cached = self._label_cached
        width = self.width
        padding_left = self.padding[0]
        padding_right = self.padding[2]
        x = self.x
        canvas_add = self.canvas.add
        selection_color = self.selection_color
        for line_num, value in enumerate(_lines[s1r:s2r], start=s1r):
            if miny <= y <= maxy + dy:
                r = rects[line_num]
                draw_selection(r.pos, r.size, line_num, (s1c, s1r),
                    (s2c, s2r - 1), _lines, _get_text_width, tab_width,
                    _label_cached, width, padding_left, padding_right, x,
                    canvas_add, selection_color)
            y -= dy

    def _draw_selection(self, *largs):
        pos, size, line_num, (s1c, s1r), (s2c, s2r),\
         _lines, _get_text_width, tab_width, _label_cached, width,\
         padding_left, padding_right, x, canvas_add, selection_color = largs
        # Draw the current selection on the widget.
        if line_num < s1r or line_num > s2r:
            return
        x, y = pos
        w, h = size
        x1 = x
        x2 = x + w
        if line_num == s1r:
            lines = _lines[line_num]
            x1 += _get_text_width(lines[:s1c], tab_width, _label_cached)
        if line_num == s2r:
            lines = _lines[line_num]
            x2 = x + _get_text_width(lines[:s2c], tab_width, _label_cached)
        width_minus_padding_right = width - padding_right
        maxx = x + width_minus_padding_right
        if x1 > maxx:
            return
        x2 = min(x2, x + width_minus_padding_right)
        canvas_add(Color(*selection_color, group='selection'))
        canvas_add(Rectangle(
            pos=(x1, pos[1]), size=(x2 - x1, size[1]), group='selection'))

    def on_size(self, instance, value):
        # if the size change, we might do invalid scrolling / text split
        # size the text maybe be put after size_hint have been resolved.
        self._trigger_refresh_text()
        self._refresh_hint_text()
        self.scroll_x = self.scroll_y = 0

    def _get_cursor_pos(self):
        # return the current cursor x/y from the row/col
        dy = self.line_height + self.line_spacing
        padding_left = self.padding[0]
        padding_top = self.padding[1]
        x = self.x + padding_left
        y = self.top - padding_top + self.scroll_y
        y -= self.cursor_row * dy
        x, y = x + self.cursor_offset() - self.scroll_x, y
        return x, y

    def _get_line_options(self):
        # Get or create line options, to be used for Label creation
        if self._line_options is None:
            self._line_options = kw = {
                'font_size': self.font_size,
                'font_name': self.font_name,
                'anchor_x': 'left',
                'anchor_y': 'top',
                'padding_x': 0,
                'padding_y': 0,
                'padding': (0, 0)}
            self._label_cached = Label(**kw)
        return self._line_options

    def _create_line_label(self, text, hint=False):
        # Create a label from a text, using line options
        ntext = text.replace(u'\n', u'').replace(u'\t', u' ' * self.tab_width)
        if self.password and not hint:  # Don't replace hint_text with *
            ntext = u'*' * len(ntext)
        kw = self._get_line_options()
        cid = '%s\0%s' % (ntext, str(kw))
        texture = Cache_get('textinput.label', cid)

        if not texture:
            # FIXME right now, we can't render very long line...
            # if we move on "VBO" version as fallback, we won't need to do this.
            # try to found the maximum text we can handle
            label = None
            label_len = len(ntext)
            ld = None
            while True:
                try:
                    label = Label(text=ntext[:label_len], **kw)
                    label.refresh()
                    if ld is not None and ld > 2:
                        ld = int(ld / 2)
                        label_len += ld
                    else:
                        break
                except:
                    # exception happen when we tried to render the text
                    # reduce it...
                    if ld is None:
                        ld = len(ntext)
                    ld = int(ld / 2)
                    if ld < 2 and label_len:
                        label_len -= 1
                    label_len -= ld
                    continue

            # ok, we found it.
            texture = label.texture
            Cache_append('textinput.label', cid, texture)
        return texture

    def _tokenize(self, text):
        # Tokenize a text string from some delimiters
        if text is None:
            return
        delimiters = u' ,\'".;:\n\r\t'
        oldindex = 0
        for index, char in enumerate(text):
            if char not in delimiters:
                continue
            if oldindex != index:
                yield text[oldindex:index]
            yield text[index:index + 1]
            oldindex = index + 1
        yield text[oldindex:]

    def _split_smart(self, text):
        # Do a "smart" split. If autowidth or autosize is set,
        # we are not doing smart split, just a split on line break.
        # Otherwise, we are trying to split as soon as possible, to prevent
        # overflow on the widget.

        # depend of the options, split the text on line, or word
        if not self.multiline:
            lines = text.split(u'\n')
            lines_flags = [0] + [FL_IS_NEWLINE] * (len(lines) - 1)
            return lines, lines_flags

        # no autosize, do wordwrap.
        x = flags = 0
        line = []
        lines = []
        lines_flags = []
        _join = u''.join
        lines_append, lines_flags_append = lines.append, lines_flags.append
        padding_left = self.padding[0]
        padding_right = self.padding[2]
        width = self.width - padding_left - padding_right
        text_width = self._get_text_width
        _tab_width, _label_cached = self.tab_width, self._label_cached

        # try to add each word on current line.
        for word in self._tokenize(text):
            is_newline = (word == u'\n')
            w = text_width(word, _tab_width, _label_cached)
            # if we have more than the width, or if it's a newline,
            # push the current line, and create a new one
            if (x + w > width and line) or is_newline:
                lines_append(_join(line))
                lines_flags_append(flags)
                flags = 0
                line = []
                x = 0
            if is_newline:
                flags |= FL_IS_NEWLINE
            else:
                x += w
                line.append(word)
        if line or flags & FL_IS_NEWLINE:
            lines_append(_join(line))
            lines_flags_append(flags)

        return lines, lines_flags

    def _key_down(self, key, repeat=False):
        displayed_str, internal_str, internal_action, scale = key
        if internal_action is None:
            if self._selection:
                self.delete_selection()
            self.insert_text(displayed_str)
        elif internal_action in ('shift', 'shift_L', 'shift_R'):
            if not self._selection:
                self._selection_from = self._selection_to = self.cursor_index()
                self._selection = True
            self._selection_finished = False
        elif internal_action.startswith('cursor_'):
            cc, cr = self.cursor
            self.do_cursor_movement(internal_action)
            if self._selection and not self._selection_finished:
                self._selection_to = self.cursor_index()
                self._update_selection()
            else:
                self.cancel_selection()
        elif self._selection and internal_action in ('del', 'backspace'):
            self.delete_selection()
        elif internal_action == 'del':
            # Move cursor one char to the right. If that was successful,
            # do a backspace (effectively deleting char right of cursor)
            cursor = self.cursor
            self.do_cursor_movement('cursor_right')
            if cursor != self.cursor:
                self.do_backspace(mode='del')
        elif internal_action == 'backspace':
            self.do_backspace()
        elif internal_action == 'enter':
            if self.multiline:
                self.insert_text(u'\n')
            else:
                self.dispatch('on_text_validate')
                self.focus = False
        elif internal_action == 'escape':
            self.focus = False
        if internal_action != 'escape':
            #self._recalc_size()
            pass

    def _key_up(self, key, repeat=False):
        displayed_str, internal_str, internal_action, scale = key
        if internal_action in ('shift', 'shift_L', 'shift_R'):
            if self._selection:
                self._update_selection(True)

    def _keyboard_on_key_down(self, window, keycode, text, modifiers):
        self._hide_cut_copy_paste()
        # Keycodes on OSX:
        ctrl, cmd = 64, 1024
        key, key_str = keycode

        # This allows *either* ctrl *or* cmd, but not both.
        is_shortcut = (modifiers == ['ctrl'] or (
            _is_osx and modifiers == ['meta']))
        is_interesting_key = key in (list(self.interesting_keys.keys()) + [27])

        if not self._editable:
            # duplicated but faster testing for non-editable keys
            if text and not is_interesting_key:
                if is_shortcut and key == ord('c'):
                    self._copy(self.selection_text)
            elif key == 27:
                self.focus = False
            return True

        if text and not is_interesting_key:
            if is_shortcut:
                if key == ord('x'):  # cut selection
                    self._cut(self.selection_text)
                elif key == ord('c'):  # copy selection
                    self._copy(self.selection_text)
                elif key == ord('v'):  # paste selection
                    self._paste()
                elif key == ord('a'):  # select all
                    self.select_all()
                elif key == ord('z'):  # undo
                    self.do_undo()
                elif key == ord('r'):  # redo
                    self.do_redo()
            else:
                if self._selection:
                    self.delete_selection()
                self.insert_text(text)
            #self._recalc_size()
            return

        if key == 27:  # escape
            self.focus = False
            return True
        elif key == 9:  # tab
            self.insert_text(u'\t')
            return True

        k = self.interesting_keys.get(key)
        if k:
            key = (None, None, k, 1)
            self._key_down(key)

    def _keyboard_on_key_up(self, window, keycode):
        key, key_str = keycode
        k = self.interesting_keys.get(key)
        if k:
            key = (None, None, k, 1)
            self._key_up(key)

    def on_hint_text(self, instance, value):
        self._refresh_hint_text()

    def _refresh_hint_text(self):
        _lines, self._hint_text_flags = self._split_smart(self.hint_text)
        _hint_text_labels = []
        _hint_text_rects = []
        _create_label = self._create_line_label

        for x in _lines:
            lbl = _create_label(x, hint=True)
            _hint_text_labels.append(lbl)
            _hint_text_rects.append(
                Rectangle(size=(lbl.size if lbl else (0, 0))))
            lbl = None

        self._hint_text_lines = _lines
        self._hint_text_labels = _hint_text_labels
        self._hint_text_rects = _hint_text_rects

        # Remember to update graphics
        self._trigger_update_graphics()

    #
    # Properties
    #

    _lines = ListProperty([])
    _hint_text_lines = ListProperty([])
    _editable = BooleanProperty(True)

    readonly = BooleanProperty(False)
    '''If True, the user will not be able to change the content of a textinput.

    .. versionadded:: 1.3.0

    :data:`readonly` is a :class:`~kivy.properties.BooleanProperty`, default to
    False
    '''

    multiline = BooleanProperty(True)
    '''If True, the widget will be able show multiple lines of text. If False,
    "enter" action will defocus the textinput instead of adding a new line.

    :data:`multiline` is a :class:`~kivy.properties.BooleanProperty`, default to
    True
    '''

    password = BooleanProperty(False)
    '''If True, the widget will display its characters as the character '*'.

    .. versionadded:: 1.2.0

    :data:`password` is a :class:`~kivy.properties.BooleanProperty`, default to
    False
    '''

    cursor_blink = BooleanProperty(False)
    '''This property is used to blink the cursor graphics. The value of
    :data:`cursor_blink` is automatically computed. Setting a value on it will
    have no impact.

    :data:`cursor_blink` is a :class:`~kivy.properties.BooleanProperty`, default
    to False
    '''

    def _get_cursor(self):
        return self._cursor

    def _set_cursor(self, pos):
        if not self._lines:
            self._trigger_refresh_text()
            return
        l = self._lines
        cr = boundary(pos[1], 0, len(l) - 1)
        cc = boundary(pos[0], 0, len(l[cr]))
        cursor = cc, cr
        if self._cursor == cursor:
            return

        self._cursor = cursor

        # adjust scrollview to ensure that the cursor will be always inside our
        # viewport.
        padding_left = self.padding[0]
        padding_right = self.padding[2]
        viewport_width = self.width - padding_left - padding_right
        sx = self.scroll_x
        offset = self.cursor_offset()

        # if offset is outside the current bounds, reajust
        if offset > viewport_width + sx:
            self.scroll_x = offset - viewport_width
        if offset < sx:
            self.scroll_x = offset

        # do the same for Y
        # this algo try to center the cursor as much as possible
        dy = self.line_height + self.line_spacing
        offsety = cr * dy
        sy = self.scroll_y
        padding_top = self.padding[1]
        padding_bottom = self.padding[3]
        viewport_height = self.height - padding_top - padding_bottom - dy
        if offsety > viewport_height + sy:
            sy = offsety - viewport_height
        if offsety < sy:
            sy = offsety
        self.scroll_y = sy

        return True

    cursor = AliasProperty(_get_cursor, _set_cursor)
    '''Tuple of (row, col) of the current cursor position.
    You can set a new (row, col) if you want to move the cursor. The scrolling
    area will be automatically updated to ensure that the cursor will be
    visible inside the viewport.

    :data:`cursor` is a :class:`~kivy.properties.AliasProperty`.
    '''

    def _get_cursor_col(self):
        return self._cursor[0]

    cursor_col = AliasProperty(_get_cursor_col, None, bind=('cursor', ))
    '''Current column of the cursor.

    :data:`cursor_col` is a :class:`~kivy.properties.AliasProperty` to
    cursor[0], read-only.
    '''

    def _get_cursor_row(self):
        return self._cursor[1]

    cursor_row = AliasProperty(_get_cursor_row, None, bind=('cursor', ))
    '''Current row of the cursor.

    :data:`cursor_row` is a :class:`~kivy.properties.AliasProperty` to
    cursor[1], read-only.
    '''

    cursor_pos = AliasProperty(_get_cursor_pos, None, bind=(
        'cursor', 'padding', 'pos', 'size', 'focus',
        'scroll_x', 'scroll_y'))
    '''Current position of the cursor, in (x, y).

    :data:`cursor_pos` is a :class:`~kivy.properties.AliasProperty`, read-only.
    '''

    line_height = NumericProperty(1)
    '''Height of a line. This property is automatically computed from the
    :data:`font_name`, :data:`font_size`. Changing the line_height will have
    no impact.

    :data:`line_height` is a :class:`~kivy.properties.NumericProperty`,
    read-only.
    '''

    tab_width = NumericProperty(4)
    '''By default, each tab will be replaced by four spaces on the text
    input widget. You can set a lower or higher value.

    :data:`tab_width` is a :class:`~kivy.properties.NumericProperty`, default to
    4.
    '''

    padding_x = VariableListProperty([0, 0], length=2)
    '''Horizontal padding of the text: [padding_left, padding_right].

    padding_x also accepts a one argument form [padding_horizontal].

    :data:`padding_x` is a :class:`~kivy.properties.VariableListProperty`,
    default to [0, 0]. This might be changed by the current theme.

    .. deprecated:: 1.7.0
        Use :data:`padding` instead
    '''

    def on_padding_x(self, instance, value):
        self.padding[0] = value[0]
        self.padding[2] = value[1]

    padding_y = VariableListProperty([0, 0], length=2)
    '''Vertical padding of the text: [padding_top, padding_bottom].

    padding_y also accepts a one argument form [padding_vertical].

    :data:`padding_y` is a :class:`~kivy.properties.VariableListProperty`,
    default to [0, 0]. This might be changed by the current theme.

    .. deprecated:: 1.7.0
        Use :data:`padding` instead
    '''

    def on_padding_y(self, instance, value):
        self.padding[1] = value[0]
        self.padding[3] = value[1]

    padding = VariableListProperty([6, 6, 6, 6])
    '''Padding of the text: [padding_left, padding_top, padding_right,
    padding_bottom].

    padding also accepts a two argument form [padding_horizontal,
    padding_vertical] and a one argument form [padding].

    .. versionchanged:: 1.7.0

    Replaced AliasProperty with VariableListProperty.

    :data:`padding` is a :class:`~kivy.properties.VariableListProperty`, default
    to [6, 6, 6, 6].
    '''

    scroll_x = NumericProperty(0)
    '''X scrolling value of the viewport. The scrolling is automatically updated
    when the cursor is moving or text is changing. If there is no action, the
    scroll_x and scroll_y properties may be changed.

    :data:`scroll_x` is a :class:`~kivy.properties.NumericProperty`, default to
    0.
    '''

    scroll_y = NumericProperty(0)
    '''Y scrolling value of the viewport. See :data:`scroll_x` for more
    information.

    :data:`scroll_y` is a :class:`~kivy.properties.NumericProperty`, default to
    0.
    '''

    selection_color = ListProperty([0.1843, 0.6549, 0.8313, .5])
    '''Current color of the selection, in (r, g, b, a) format.

    .. warning::

        The color should always have "alpha" component different from 1, since
        the selection is drawn after the text.

    :data:`selection_color` is a :class:`~kivy.properties.ListProperty`, default
    to [0.1843, 0.6549, 0.8313, .5]
    '''

    border = ListProperty([16, 16, 16, 16])
    '''Border used for :class:`~kivy.graphics.vertex_instructions.BorderImage`
    graphics instruction. Used with :data:`background_normal` and
    :data:`background_active`. Can be used for a custom background.

    .. versionadded:: 1.4.1

    It must be a list of four values: (top, right, bottom, left). Read the
    BorderImage instruction for more information about how to use it.

    :data:`border` is a :class:`~kivy.properties.ListProperty`, default to (16,
    16, 16, 16)
    '''

    background_normal = StringProperty(
        'atlas://data/images/defaulttheme/textinput')
    '''Background image of the TextInput when it's not in focus'.

    .. versionadded:: 1.4.1

    :data:`background_normal` is a :class:`~kivy.properties.StringProperty`,
    default to 'atlas://data/images/defaulttheme/textinput'
    '''

    background_disabled_normal = StringProperty(
        'atlas://data/images/defaulttheme/textinput_disabled')
    '''Background image of the TextInput when disabled'.

    .. versionadded:: 1.8.0

    :data:`background_disabled_normal` is a
    :class:`~kivy.properties.StringProperty`,
    default to 'atlas://data/images/defaulttheme/textinput_disabled'
    '''

    background_active = StringProperty(
        'atlas://data/images/defaulttheme/textinput_active')
    '''Background image of the TextInput when it's in focus'.

    .. versionadded:: 1.4.1

    :data:`background_active` is a
    :class:`~kivy.properties.StringProperty`,
    default to 'atlas://data/images/defaulttheme/textinput_active'
    '''

    background_disabled_active = StringProperty(
        'atlas://data/images/defaulttheme/textinput_disabled_active')
    '''Background image of the TextInput when it's in focus and disabled.

    .. versionadded:: 1.8.0

    :data:`background_disabled_active` is a
    :class:`~kivy.properties.StringProperty`,
    default to 'atlas://data/images/defaulttheme/textinput_disabled_active'
    '''

    background_color = ListProperty([1, 1, 1, 1])
    '''Current color of the background, in (r, g, b, a) format.

    .. versionadded:: 1.2.0

    :data:`background_color` is a :class:`~kivy.properties.ListProperty`,
    default to [1, 1, 1, 1] #White
    '''

    foreground_color = ListProperty([0, 0, 0, 1])
    '''Current color of the foreground, in (r, g, b, a) format.

    .. versionadded:: 1.2.0

    :data:`foreground_color` is a :class:`~kivy.properties.ListProperty`,
    default to [0, 0, 0, 1] #Black
    '''

    disabled_foreground_color = ListProperty([0, 0, 0, .5])
    '''Current color of the foreground, in (r, g, b, a) format when disabled.

    .. versionadded:: 1.8.0

    :data:`disabled_foreground_color` is a
    :class:`~kivy.properties.ListProperty`,
    default to [0, 0, 0, 5] # 50% translucent Black
    '''

    use_bubble = BooleanProperty(not _is_desktop)
    '''Indicates whether the cut copy paste bubble is used

    .. versionadded:: 1.7.0

    :data:`use_bubble` is a :class:`~kivy.properties.BooleanProperty`,
    default to True, and deactivated by default on "desktop".
    '''

    def get_sel_from(self):
        return self._selection_from

    selection_from = AliasProperty(get_sel_from, None)
    '''If a selection is happening, or finished, this property will represent
    the cursor index where the selection started.

    .. versionchanged:: 1.4.0

    :data:`selection_from` is a :class:`~kivy.properties.AliasProperty`,
    default to None, readonly.
    '''

    def get_sel_to(self):
        return self._selection_to

    selection_to = AliasProperty(get_sel_to, None)
    '''If a selection is happening, or finished, this property will represent
    the cursor index where the selection started.

    .. versionchanged:: 1.4.0

    :data:`selection_to` is a :class:`~kivy.properties.AliasProperty`,
    default to None, readonly.
    '''

    selection_text = StringProperty(u'')
    '''Current content selection.

    :data:`selection_text` is a :class:`~kivy.properties.StringProperty`,
    default to '', readonly.
    '''

    focus = BooleanProperty(False)
    '''If focus is True, the keyboard will be requested, and you can start to
    write on the textinput.

    :data:`focus` is a :class:`~kivy.properties.BooleanProperty`, default to
    False

    .. Note::
            Selection is cancelled when TextInput is focused. If you need to
            show selection when TextInput is focused, you should delay
            (use Clock.schedule) the call to the functions for selecting
            text (select_all, select_text).
    '''

    def _get_text(self, encode=True):
        lf = self._lines_flags
        l = self._lines
        len_l = len(l)

        if len(lf) < len_l:
            lf.append(1)

        text = u''.join([(u'\n' if (lf[i] & FL_IS_NEWLINE) else u'') + l[i]
                        for i in range(len_l)])

        if PY2 and encode and type(text) is not str:
            text = text.encode('utf-8')
        return text

    def _set_text(self, text):
        if PY2 and type(text) is str:
            text = text.decode('utf-8')

        if self._get_text(encode=False) == text:
            return
        self._refresh_text(text)
        self.cursor = self.get_cursor_from_index(len(text))

    text = AliasProperty(_get_text, _set_text, bind=('_lines', ))
    '''Text of the widget.

    Creation of a simple hello world::

        widget = TextInput(text='Hello world')

    If you want to create the widget with an unicode string, use::

        widget = TextInput(text=u'My unicode string')

    :data:`text` a :class:`~kivy.properties.StringProperty`.
    '''

    font_name = StringProperty('DroidSans')
    '''Filename of the font to use. The path can be absolute or relative.
    Relative paths are resolved by the :func:`~kivy.resources.resource_find`
    function.

    .. warning::

        Depending on your text provider, the font file can be ignored. However,
        you can mostly use this without trouble.

        If the font used lacks the glyphs for the particular language/symbols
        you are using, you will see '[]' blank box characters instead of the
        actual glyphs. The solution is to use a font that has the glyphs you
        need to display. For example, to display |unicodechar|, use a font like
        freesans.ttf that has the glyph.

        .. |unicodechar| image:: images/unicode-char.png

    :data:`font_name` is a :class:`~kivy.properties.StringProperty`, default to
    'DroidSans'.
    '''

    font_size = NumericProperty('15sp')
    '''Font size of the text, in pixels.

    :data:`font_size` is a :class:`~kivy.properties.NumericProperty`, default to
    10.
    '''

    hint_text = StringProperty('')
    '''Hint text of the widget.

    Shown if text is '' and focus is False.

    .. versionadded:: 1.6.0

    :data:`hint_text` a :class:`~kivy.properties.StringProperty`.
    '''

    hint_text_color = ListProperty([0.5, 0.5, 0.5, 1.0])
    '''Current color of the hint_text text, in (r, g, b, a) format.

    .. versionadded:: 1.6.0

    :data:`hint_text_color` is a :class:`~kivy.properties.ListProperty`,
    default to [0.5, 0.5, 0.5, 1.0] #Grey
    '''

    auto_indent = BooleanProperty(False)
    '''Automatically indent multiline text.

    .. versionadded:: 1.7.0
    '''

    def _get_min_height(self):
        return (len(self._lines) * (self.line_height + self.line_spacing)
                + self.padding[0] + self.padding[2])

    minimum_height = AliasProperty(_get_min_height, None,
                                   bind=('_lines', 'line_spacing', 'padding',
                                         'font_size', 'font_name', 'password',
                                         'hint_text'))
    '''minimum height of the content inside the TextInput.

    .. versionadded:: 1.8.0

    :data:`minimum_height` is a readonly :class:`~kivy.properties.AliasProperty`
    '''

    line_spacing = NumericProperty(0)
    '''Space taken up between the lines.

    .. versionadded:: 1.8.0

    :data:`line_spacing` is a :class:`~kivy.properties.NumericProperty`,
    default to '0'
    '''


if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout

    class TextInputApp(App):

        def build(self):
            root = BoxLayout(orientation='vertical')
            textinput = TextInput(multiline=True)
            textinput.text = __doc__
            root.add_widget(textinput)
            textinput2 = TextInput(text='monoline textinput',
                                   size_hint=(1, None), height=30)
            root.add_widget(textinput2)
            return root

    TextInputApp().run()
