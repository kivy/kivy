# -*- encoding: utf-8 -*-
'''
Text Input
==========

.. versionadded:: 1.0.4

.. image:: images/textinput-mono.jpg
.. image:: images/textinput-multi.jpg

The :class:`TextInput` widget provides a box for editable plain text.

Unicode, multiline, cursor navigation, selection and clipboard features
are supported.

The :class:`TextInput` uses two different coordinate systems:

* (x, y) - coordinates in pixels, mostly used for rendering on screen.
* (row, col) - cursor index in characters / lines, used for selection
  and cursor movement.


Usage example
-------------

To create a multiline :class:`TextInput` (the 'enter' key adds a new line)::

    from kivy.uix.textinput import TextInput
    textinput = TextInput(text='Hello world')

To create a singleline :class:`TextInput`, set the :class:`TextInput.multiline`
property to False (the 'enter' key will defocus the TextInput and emit an
'on_text_validate' event)::

    def on_enter(instance, value):
        print('User pressed enter in', instance)

    textinput = TextInput(text='Hello world', multiline=False)
    textinput.bind(on_text_validate=on_enter)

The textinput's text is stored in its :attr:`TextInput.text` property. To run a
callback when the text changes::

    def on_text(instance, value):
        print('The widget', instance, 'have:', value)

    textinput = TextInput()
    textinput.bind(text=on_text)

You can set the :class:`focus <kivy.uix.behaviors.FocusBehavior>` to a
Textinput, meaning that the input box will be highlighted and keyboard focus
will be requested::

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

See :class:`~kivy.uix.behaviors.FocusBehavior`, from which the
:class:`TextInput` inherits, for more details.


Selection
---------

The selection is automatically updated when the cursor position changes.
You can get the currently selected text from the
:attr:`TextInput.selection_text` property.

Filtering
---------

You can control which text can be added to the :class:`TextInput` by
overwriting :meth:`TextInput.insert_text`. Every string that is typed, pasted
or inserted by any other means into the :class:`TextInput` is passed through
this function. By overwriting it you can reject or change unwanted characters.

For example, to write only in capitalized characters::

    class CapitalInput(TextInput):

        def insert_text(self, substring, from_undo=False):
            s = substring.upper()
            return super(CapitalInput, self).insert_text(s,\
 from_undo=from_undo)

Or to only allow floats (0 - 9 and a single period)::

    class FloatInput(TextInput):

        pat = re.compile('[^0-9]')
        def insert_text(self, substring, from_undo=False):
            pat = self.pat
            if '.' in self.text:
                s = re.sub(pat, '', substring)
            else:
                s = '.'.join([re.sub(pat, '', s) for s in\
 substring.split('.', 1)])
            return super(FloatInput, self).insert_text(s, from_undo=from_undo)

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
Shift + <dir>   Start a text selection. Dir can be Up, Down, Left or
                Right
Control + c     Copy selection
Control + x     Cut selection
Control + p     Paste selection
Control + a     Select all the content
Control + z     undo
Control + r     redo
=============== ========================================================

.. note::
    To enable Emacs-style keyboard shortcuts, you can use
    :class:`~kivy.uix.behaviors.emacs.EmacsBehavior`.

'''


__all__ = ('TextInput', )


import re
import sys
from os import environ
from weakref import ref

from kivy.animation import Animation
from kivy.base import EventLoop
from kivy.cache import Cache
from kivy.clock import Clock
from kivy.config import Config
from kivy.metrics import inch
from kivy.utils import boundary, platform
from kivy.uix.behaviors import FocusBehavior

from kivy.core.text import Label, DEFAULT_FONT
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Callback
from kivy.graphics.context_instructions import Transform
from kivy.graphics.texture import Texture

from kivy.uix.widget import Widget
from kivy.uix.bubble import Bubble
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image

from kivy.properties import StringProperty, NumericProperty, \
    BooleanProperty, AliasProperty, \
    ListProperty, ObjectProperty, VariableListProperty

Cache_register = Cache.register
Cache_append = Cache.append
Cache_get = Cache.get
Cache_remove = Cache.remove
Cache_register('textinput.label', timeout=60.)
Cache_register('textinput.width', timeout=60.)

FL_IS_LINEBREAK = 0x01
FL_IS_WORDBREAK = 0x02
FL_IS_NEWLINE = FL_IS_LINEBREAK | FL_IS_WORDBREAK

# late binding
Clipboard = None
CutBuffer = None
MarkupLabel = None
_platform = platform

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
                textinput._refresh_hint_text()

    from kivy.graphics.context import get_context
    get_context().add_reload_observer(_textinput_clear_cache, True)


class Selector(ButtonBehavior, Image):
    # Internal class for managing the selection Handles.

    window = ObjectProperty()
    target = ObjectProperty()
    matrix = ObjectProperty()

    def __init__(self, **kwargs):
        super(Selector, self).__init__(**kwargs)
        self.matrix = self.target.get_window_matrix()

        with self.canvas.before:
            Callback(self.update_transform)
            PushMatrix()
            self.transform = Transform()

        with self.canvas.after:
            PopMatrix()

    def update_transform(self, cb):
        m = self.target.get_window_matrix()
        if self.matrix != m:
            self.matrix = m
            self.transform.identity()
            self.transform.transform(self.matrix)

    def transform_touch(self, touch):
        matrix = self.matrix.inverse()
        touch.apply_transform_2d(
            lambda x, y: matrix.transform_point(x, y, 0)[:2])

    def on_touch_down(self, touch):
        if self.parent is not EventLoop.window:
            return

        try:
            touch.push()
            self.transform_touch(touch)
            self._touch_diff = self.top - touch.y
            if self.collide_point(*touch.pos):
                FocusBehavior.ignored_touch.append(touch)
            return super(Selector, self).on_touch_down(touch)
        finally:
            touch.pop()


class TextInputCutCopyPaste(Bubble):
    # Internal class used for showing the little bubble popup when
    # copy/cut/paste happen.

    textinput = ObjectProperty(None)
    ''' Holds a reference to the TextInput this Bubble belongs to.
    '''

    but_cut = ObjectProperty(None)
    but_copy = ObjectProperty(None)
    but_paste = ObjectProperty(None)
    but_selectall = ObjectProperty(None)

    matrix = ObjectProperty(None)

    _check_parent_ev = None

    def __init__(self, **kwargs):
        self.mode = 'normal'
        super(TextInputCutCopyPaste, self).__init__(**kwargs)
        self._check_parent_ev = Clock.schedule_interval(self._check_parent, .5)
        self.matrix = self.textinput.get_window_matrix()

        with self.canvas.before:
            Callback(self.update_transform)
            PushMatrix()
            self.transform = Transform()

        with self.canvas.after:
            PopMatrix()

    def update_transform(self, cb):
        m = self.textinput.get_window_matrix()
        if self.matrix != m:
            self.matrix = m
            self.transform.identity()
            self.transform.transform(self.matrix)

    def transform_touch(self, touch):
        matrix = self.matrix.inverse()
        touch.apply_transform_2d(
            lambda x, y: matrix.transform_point(x, y, 0)[:2])

    def on_touch_down(self, touch):
        try:
            touch.push()
            self.transform_touch(touch)
            if self.collide_point(*touch.pos):
                FocusBehavior.ignored_touch.append(touch)
            return super(TextInputCutCopyPaste, self).on_touch_down(touch)
        finally:
            touch.pop()

    def on_touch_up(self, touch):
        try:
            touch.push()
            self.transform_touch(touch)
            for child in self.content.children:
                if ref(child) in touch.grab_list:
                    touch.grab_current = child
                    break
            return super(TextInputCutCopyPaste, self).on_touch_up(touch)
        finally:
            touch.pop()

    def on_textinput(self, instance, value):
        global Clipboard
        if value and not Clipboard and not _is_desktop:
            value._ensure_clipboard()

    def _check_parent(self, dt):
        # this is a prevention to get the Bubble staying on the screen, if the
        # attached textinput is not on the screen anymore.
        parent = self.textinput
        while parent is not None:
            if parent == parent.parent:
                break
            parent = parent.parent
        if parent is None:
            self._check_parent_ev.cancel()
            if self.textinput:
                self.textinput._hide_cut_copy_paste()

    def on_parent(self, instance, value):
        parent = self.textinput
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
            textinput.copy()
        elif action == 'paste':
            textinput.paste()
        elif action == 'selectall':
            textinput.select_all()
            self.mode = ''
            anim = Animation(opacity=0, d=.333)
            anim.bind(on_complete=lambda *args:
                      self.on_parent(self, self.parent))
            anim.start(self.but_selectall)
            return

        self.hide()

    def hide(self):
        parent = self.parent
        if not parent:
            return

        anim = Animation(opacity=0, d=.225)
        anim.bind(on_complete=lambda *args: parent.remove_widget(self))
        anim.start(self)


class TextInput(FocusBehavior, Widget):
    '''TextInput class. See module documentation for more information.

    :Events:
        `on_text_validate`
            Fired only in multiline=False mode when the user hits 'enter'.
            This will also unfocus the textinput.
        `on_double_tap`
            Fired when a double tap happens in the text input. The default
            behavior selects the text around the cursor position. More info at
            :meth:`on_double_tap`.
        `on_triple_tap`
            Fired when a triple tap happens in the text input. The default
            behavior selects the line around the cursor position. More info at
            :meth:`on_triple_tap`.
        `on_quad_touch`
            Fired when four fingers are touching the text input. The default
            behavior selects the whole text. More info at
            :meth:`on_quad_touch`.

    .. warning::
        When changing a :class:`TextInput` property that requires re-drawing,
        e.g. modifying the :attr:`text`, the updates occur on the next
        clock cycle and not instantly. This might cause any changes to the
        :class:`TextInput` that occur between the modification and the next
        cycle to be ignored, or to use previous values. For example, after
        a update to the :attr:`text`, changing the cursor in the same clock
        frame will move it using the previous text and will likely end up in an
        incorrect position. The solution is to schedule any updates to occur
        on the next clock cycle using
        :meth:`~kivy.clock.ClockBase.schedule_once`.

    .. Note::
        Selection is cancelled when TextInput is focused. If you need to
        show selection when TextInput is focused, you should delay
        (use Clock.schedule) the call to the functions for selecting
        text (select_all, select_text).

    .. versionchanged:: 1.10.0
        `background_disabled_active` has been removed.

    .. versionchanged:: 1.9.0

        :class:`TextInput` now inherits from
        :class:`~kivy.uix.behaviors.FocusBehavior`.
        :attr:`~kivy.uix.behaviors.FocusBehavior.keyboard_mode`,
        :meth:`~kivy.uix.behaviors.FocusBehavior.show_keyboard`,
        :meth:`~kivy.uix.behaviors.FocusBehavior.hide_keyboard`,
        :meth:`~kivy.uix.behaviors.FocusBehavior.focus`,
        and :attr:`~kivy.uix.behaviors.FocusBehavior.input_type`
        have been removed since they are now inherited
        from :class:`~kivy.uix.behaviors.FocusBehavior`.

    .. versionchanged:: 1.7.0
        `on_double_tap`, `on_triple_tap` and `on_quad_touch` events added.
    '''

    __events__ = ('on_text_validate', 'on_double_tap', 'on_triple_tap',
                  'on_quad_touch')

    def __init__(self, **kwargs):
        self._update_graphics_ev = Clock.create_trigger(
            self._update_graphics, -1)
        self.is_focusable = kwargs.get('is_focusable', True)
        self._cursor = [0, 0]
        self._selection = False
        self._selection_finished = True
        self._selection_touch = None
        self.selection_text = u''
        self._selection_from = None
        self._selection_to = None
        self._selection_callback = None
        self._handle_left = None
        self._handle_right = None
        self._handle_middle = None
        self._bubble = None
        self._lines_flags = []
        self._lines_labels = []
        self._lines_rects = []
        self._hint_text_flags = []
        self._hint_text_labels = []
        self._hint_text_rects = []
        self._label_cached = None
        self._line_options = None
        self._keyboard_mode = Config.get('kivy', 'keyboard_mode')
        self._command_mode = False
        self._command = ''
        self.reset_undo()
        self._touch_count = 0
        self._ctrl_l = False
        self._ctrl_r = False
        self._alt_l = False
        self._alt_r = False
        self._refresh_text_from_property_ev = None
        self._long_touch_ev = None
        self._do_blink_cursor_ev = Clock.create_trigger(
            self._do_blink_cursor, .5, interval=True)
        self._refresh_line_options_ev = None
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
            304: 'shift_R',
            305: 'ctrl_L',
            306: 'ctrl_R',
            308: 'alt_L',
            307: 'alt_R'}

        super(TextInput, self).__init__(**kwargs)

        fbind = self.fbind
        refresh_line_options = self._trigger_refresh_line_options
        update_text_options = self._update_text_options

        fbind('font_size', refresh_line_options)
        fbind('font_name', refresh_line_options)

        def handle_readonly(instance, value):
            if value and (not _is_desktop or not self.allow_copy):
                self.is_focusable = False
            if (not (value or self.disabled) or _is_desktop and
                    self._keyboard_mode == 'system'):
                self._editable = True
            else:
                self._editable = False

        fbind('padding', update_text_options)
        fbind('tab_width', update_text_options)
        fbind('font_size', update_text_options)
        fbind('font_name', update_text_options)
        fbind('size', update_text_options)
        fbind('password', update_text_options)
        fbind('password_mask', update_text_options)

        fbind('pos', self._trigger_update_graphics)
        fbind('readonly', handle_readonly)
        fbind('focus', self._on_textinput_focused)
        handle_readonly(self, self.readonly)

        handles = self._trigger_position_handles = Clock.create_trigger(
            self._position_handles)
        self._trigger_show_handles = Clock.create_trigger(
            self._show_handles, .05)
        self._trigger_cursor_reset = Clock.create_trigger(
            self._reset_cursor_blink)
        self._trigger_update_cutbuffer = Clock.create_trigger(
            self._update_cutbuffer)
        refresh_line_options()
        self._trigger_refresh_text()

        fbind('pos', handles)
        fbind('size', handles)

        # when the gl context is reloaded, trigger the text rendering again.
        _textinput_list.append(ref(self, TextInput._reload_remove_observer))

        if platform == 'linux':
            self._ensure_clipboard()

    def on_text_validate(self):
        pass

    def cursor_index(self, cursor=None):
        '''Return the cursor index in the text/value.
        '''
        if not cursor:
            cursor = self.cursor
        try:
            l = self._lines
            if len(l) == 0:
                return 0
            lf = self._lines_flags
            index, cr = cursor
            for row in range(cr):
                if row >= len(l):
                    continue
                index += len(l[row])
                if lf[row] & FL_IS_LINEBREAK:
                    index += 1
            if lf[cr] & FL_IS_LINEBREAK:
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
            if lf[row] & FL_IS_LINEBREAK:
                ni += 1
                i += 1
            if ni >= index:
                return index - i, row
            i = ni
        return index, row

    def select_text(self, start, end):
        ''' Select a portion of text displayed in this TextInput.

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
        ''' Select all of the text displayed in this TextInput.

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
        '''Insert new text at the current cursor position. Override this
        function in order to pre-process text for input validation.
        '''
        if self.readonly or not substring or not self._lines:
            return

        if isinstance(substring, bytes):
            substring = substring.decode('utf8')

        if self.replace_crlf:
            substring = substring.replace(u'\r\n', u'\n')

        mode = self.input_filter
        if mode is not None:
            chr = type(substring)
            if chr is bytes:
                int_pat = self._insert_int_patb
            else:
                int_pat = self._insert_int_patu

            if mode == 'int':
                substring = re.sub(int_pat, chr(''), substring)
            elif mode == 'float':
                if '.' in self.text:
                    substring = re.sub(int_pat, chr(''), substring)
                else:
                    substring = '.'.join([re.sub(int_pat, chr(''), k) for k
                                          in substring.split(chr('.'), 1)])
            else:
                substring = mode(substring, from_undo)
            if not substring:
                return

        self._hide_handles(EventLoop.window)

        if not from_undo and self.multiline and self.auto_indent \
                and substring == u'\n':
            substring = self._auto_indent(substring)

        cc, cr = self.cursor
        sci = self.cursor_index
        ci = sci()
        text = self._lines[cr]
        len_str = len(substring)
        new_text = text[:cc] + substring + text[cc:]
        self._set_line_text(cr, new_text)

        wrap = (self._get_text_width(
            new_text,
            self.tab_width,
            self._label_cached) > (self.width - self.padding[0] -
                                   self.padding[2]))
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
        '''Do redo operation.

        .. versionadded:: 1.3.0

        This action re-does any command that has been un-done by
        do_undo/ctrl+z. This function is automatically called when
        `ctrl+r` keys are pressed.
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
            elif undo_type == 'shiftln':
                direction, rows, cursor = x_item['redo_command'][1:]
                self._shift_lines(direction, rows, cursor, True)
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
        '''Do undo operation.

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
            elif undo_type == 'shiftln':
                direction, rows, cursor = x_item['undo_command'][1:]
                self._shift_lines(direction, rows, cursor, True)
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

            - removing the current selection if available.
            - removing the previous char and move the cursor back.
            - do nothing, if we are at the start.

        '''
        if self.readonly:
            return
        cc, cr = self.cursor
        _lines = self._lines
        text = _lines[cr]
        cursor_index = self.cursor_index()
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
            # ch = text[cc-1]
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
        # reset redo when undo is appended to
        self._redo = []

    _re_whitespace = re.compile(r'\s+')

    def _move_cursor_word_left(self, index=None):
        pos = index or self.cursor_index()
        if pos == 0:
            return self.cursor
        lines = self._lines
        col, row = self.get_cursor_from_index(pos)
        if col == 0:
            row -= 1
            col = len(lines[row])
        while True:
            matches = list(self._re_whitespace.finditer(lines[row], 0, col))
            if not matches:
                if col == 0:
                    if row == 0:
                        return 0, 0
                    row -= 1
                    col = len(lines[row])
                    continue
                return 0, row
            match = matches[-1]
            mpos = match.end()
            if mpos == col:
                if len(matches) > 1:
                    match = matches[-2]
                    mpos = match.end()
                else:
                    if match.start() == 0:
                        if row == 0:
                            return 0, 0
                        row -= 1
                        col = len(lines[row])
                        continue
                    return 0, row
            col = mpos
            return col, row

    def _move_cursor_word_right(self, index=None):
        pos = index or self.cursor_index()
        col, row = self.get_cursor_from_index(pos)
        lines = self._lines
        mrow = len(lines) - 1
        if row == mrow and col == len(lines[row]):
            return col, row
        if col == len(lines[row]):
            row += 1
            col = 0
        while True:
            matches = list(self._re_whitespace.finditer(lines[row], col))
            if not matches:
                if col == len(lines[row]):
                    if row == mrow:
                        return col, row
                    row += 1
                    col = 0
                    continue
                return len(lines[row]), row
            match = matches[0]
            mpos = match.start()
            if mpos == col:
                if len(matches) > 1:
                    match = matches[1]
                    mpos = match.start()
                else:
                    if match.end() == len(lines[row]):
                        if row == mrow:
                            return col, row
                        row += 1
                        col = 0
                        continue
                    return len(lines[row]), row
            col = mpos
            return col, row

    def _expand_range(self, ifrom, ito=None):
        if ito is None:
            ito = ifrom
        rfrom = self.get_cursor_from_index(ifrom)[1]
        rtcol, rto = self.get_cursor_from_index(ito)
        rfrom, rto = self._expand_rows(rfrom, rto + 1 if rtcol else rto)

        return (self.cursor_index((0, rfrom)),
                self.cursor_index((0, rto)))

    def _expand_rows(self, rfrom, rto=None):
        if rto is None or rto == rfrom:
            rto = rfrom + 1
        lines = self._lines
        flags = list(reversed(self._lines_flags))
        while rfrom > 0 and not (flags[rfrom - 1] & FL_IS_NEWLINE):
            rfrom -= 1
        rmax = len(lines) - 1
        while 0 < rto < rmax and not (flags[rto - 1] & FL_IS_NEWLINE):
            rto += 1
        return max(0, rfrom), min(rmax, rto)

    def _shift_lines(self, direction, rows=None, old_cursor=None,
                     from_undo=False):
        if self._selection_callback:
            if from_undo:
                self._selection_callback.cancel()
            else:
                return
        lines = self._lines
        flags = list(reversed(self._lines_flags))
        labels = self._lines_labels
        rects = self._lines_rects
        orig_cursor = self.cursor
        sel = None
        if old_cursor is not None:
            self.cursor = old_cursor

        if not rows:
            sindex = self.selection_from
            eindex = self.selection_to
            if (sindex or eindex) and sindex != eindex:
                sindex, eindex = tuple(sorted((sindex, eindex)))
                sindex, eindex = self._expand_range(sindex, eindex)
            else:
                sindex, eindex = self._expand_range(self.cursor_index())
            srow = self.get_cursor_from_index(sindex)[1]
            erow = self.get_cursor_from_index(eindex)[1]
            sel = sindex, eindex

            if direction < 0 and srow > 0:
                psrow, perow = self._expand_rows(srow - 1)
                rows = ((srow, erow), (psrow, perow))
            elif direction > 0 and erow < len(lines) - 1:
                psrow, perow = self._expand_rows(erow)
                rows = ((srow, erow), (psrow, perow))

        if rows:
            (srow, erow), (psrow, perow) = rows
            if direction < 0:
                m1srow, m1erow = psrow, perow
                m2srow, m2erow = srow, erow
                cdiff = psrow - perow
                xdiff = srow - erow
            else:
                m1srow, m1erow = srow, erow
                m2srow, m2erow = psrow, perow
                cdiff = perow - psrow
                xdiff = erow - srow
            self._lines_flags = list(reversed(
                flags[:m1srow] + flags[m2srow:m2erow] + flags[m1srow:m1erow] +
                flags[m2erow:]))
            self._lines = (lines[:m1srow] + lines[m2srow:m2erow] +
                           lines[m1srow:m1erow] + lines[m2erow:])
            self._lines_labels = (labels[:m1srow] + labels[m2srow:m2erow] +
                                  labels[m1srow:m1erow] + labels[m2erow:])
            self._lines_rects = (rects[:m1srow] + rects[m2srow:m2erow] +
                                 rects[m1srow:m1erow] + rects[m2erow:])
            self._trigger_update_graphics()
            csrow = srow + cdiff
            cerow = erow + cdiff
            sel = (self.cursor_index((0, csrow)),
                   self.cursor_index((0, cerow)))
            self.cursor = self.cursor_col, self.cursor_row + cdiff
            if not from_undo:
                undo_rows = ((srow + cdiff, erow + cdiff),
                             (psrow - xdiff, perow - xdiff))
                self._undo.append({
                    'undo_command': ('shiftln', direction * -1, undo_rows,
                                     self.cursor),
                    'redo_command': ('shiftln', direction, rows, orig_cursor),
                })
                self._redo = []

        if sel:
            def cb(dt):
                self.select_text(*sel)
                self._selection_callback = None
            self._selection_callback = Clock.schedule_once(cb)

    def do_cursor_movement(self, action, control=False, alt=False):
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

        In addition, the behavior of certain actions can be modified:

            - control + cursor_left: move the cursor one word to the left
            - control + cursor_right: move the cursor one word to the right
            - control + cursor_up: scroll up one line
            - control + cursor_down: scroll down one line
            - control + cursor_home: go to beginning of text
            - control + cursor_end: go to end of text
            - alt + cursor_up: shift line(s) up
            - alt + cursor_down: shift line(s) down

        .. versionchanged:: 1.9.1

        '''
        if not self._lines:
            return
        pgmove_speed = int(self.height /
            (self.line_height + self.line_spacing) - 1)
        col, row = self.cursor
        if action == 'cursor_up':
            if self.multiline and control:
                self.scroll_y = max(0, self.scroll_y - self.line_height)
            elif not self.readonly and self.multiline and alt:
                self._shift_lines(-1)
                return
            else:
                row = max(row - 1, 0)
                col = min(len(self._lines[row]), col)
        elif action == 'cursor_down':
            if self.multiline and control:
                maxy = self.minimum_height - self.height
                self.scroll_y = max(0, min(maxy,
                                           self.scroll_y + self.line_height))
            elif not self.readonly and self.multiline and alt:
                self._shift_lines(1)
                return
            else:
                row = min(row + 1, len(self._lines) - 1)
                col = min(len(self._lines[row]), col)
        elif action == 'cursor_left':
            if not self.password and control:
                col, row = self._move_cursor_word_left()
            else:
                if col == 0:
                    if row:
                        row -= 1
                        col = len(self._lines[row])
                else:
                    col, row = col - 1, row
        elif action == 'cursor_right':
            if not self.password and control:
                col, row = self._move_cursor_word_right()
            else:
                if col == len(self._lines[row]):
                    if row < len(self._lines) - 1:
                        col = 0
                        row += 1
                else:
                    col, row = col + 1, row
        elif action == 'cursor_home':
            col = 0
            if control:
                row = 0
        elif action == 'cursor_end':
            if control:
                row = len(self._lines) - 1
            col = len(self._lines[row])
        elif action == 'cursor_pgup':
            row = max(0, row - pgmove_speed)
            col = min(len(self._lines[row]), col)
        elif action == 'cursor_pgdown':
            row = min(row + pgmove_speed, len(self._lines) - 1)
            col = min(len(self._lines[row]), col)
        self.cursor = (col, row)

    def get_cursor_from_xy(self, x, y):
        '''Return the (row, col) of the cursor from an (x, y) position.
        '''
        padding_left = self.padding[0]
        padding_top = self.padding[1]
        l = self._lines
        dy = self.line_height + self.line_spacing
        cx = x - self.x
        scrl_y = self.scroll_y
        scrl_x = self.scroll_x
        scrl_y = scrl_y / dy if scrl_y > 0 else 0
        cy = (self.top - padding_top + scrl_y * dy) - y
        cy = int(boundary(round(cy / dy - 0.5), 0, len(l) - 1))
        _get_text_width = self._get_text_width
        _tab_width = self.tab_width
        _label_cached = self._label_cached
        for i in range(0, len(l[cy])):
            if _get_text_width(l[cy][:i], _tab_width, _label_cached) + \
                  _get_text_width(l[cy][i], _tab_width, _label_cached) * 0.6 +\
                  padding_left > cx + scrl_x:
                cx = i
                break
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
        self.selection_text = u''
        self._trigger_update_graphics()

    def delete_selection(self, from_undo=False):
        '''Delete the current text selection (if any).
        '''
        if self.readonly:
            return
        self._hide_handles(EventLoop.window)
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
        # handle undo and redo for delete selection
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
        _selection_text = self._get_text(encode=False)[a:b]
        self.selection_text = ("" if not self.allow_copy else
                               ((self.password_mask * (b - a)) if
                                self.password else _selection_text))
        if not finished:
            self._selection = True
        else:
            self._selection = bool(len(_selection_text))
            self._selection_touch = None
        if a == 0:
            # update graphics only on new line
            # allows smoother scrolling, noticeably
            # faster when dealing with large text.
            self._update_graphics_selection()
            # self._trigger_update_graphics()

    #
    # Touch control
    #
    def long_touch(self, dt):
        self._long_touch_ev = None
        if self._selection_to == self._selection_from:
            pos = self.to_local(*self._long_touch_pos, relative=False)
            self._show_cut_copy_paste(
                pos, EventLoop.window, mode='paste')

    def on_double_tap(self):
        '''This event is dispatched when a double tap happens
        inside TextInput. The default behavior is to select the
        word around the current cursor position. Override this to provide
        different behavior. Alternatively, you can bind to this
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
        different behavior. Alternatively, you can bind to this
        event to provide additional functionality.
        '''
        ci = self.cursor_index()
        sindex, eindex = self._expand_range(ci)
        Clock.schedule_once(lambda dt: self.select_text(sindex, eindex))

    def on_quad_touch(self):
        '''This event is dispatched when four fingers are touching
        inside TextInput. The default behavior is to select all text.
        Override this to provide different behavior. Alternatively,
        you can bind to this event to provide additional functionality.
        '''
        Clock.schedule_once(lambda dt: self.select_all())

    def on_touch_down(self, touch):
        if self.disabled:
            return

        touch_pos = touch.pos
        if not self.collide_point(*touch_pos):
            return False
        if super(TextInput, self).on_touch_down(touch):
            return True

        if self.focus:
            self._trigger_cursor_reset()

        # Check for scroll wheel
        if 'button' in touch.profile and touch.button.startswith('scroll'):
            scroll_type = touch.button[6:]
            if scroll_type == 'down':
                if self.multiline:
                    if self.scroll_y <= 0:
                        return
                    self.scroll_y -= self.line_height
                else:
                    if self.scroll_x <= 0:
                        return
                    self.scroll_x -= self.line_height
            if scroll_type == 'up':
                if self.multiline:
                    if (self._lines_rects[-1].pos[1] > self.y +
                            self.line_height):
                        return
                    self.scroll_y += self.line_height
                else:
                    if (self.scroll_x + self.width >=
                            self._lines_rects[-1].texture.size[0]):
                        return
                    self.scroll_x += self.line_height

        touch.grab(self)
        self._touch_count += 1
        if touch.is_double_tap:
            self.dispatch('on_double_tap')
        if touch.is_triple_tap:
            self.dispatch('on_triple_tap')
        if self._touch_count == 4:
            self.dispatch('on_quad_touch')

        self._hide_cut_copy_paste(EventLoop.window)
        # schedule long touch for paste
        self._long_touch_pos = touch.pos
        self._long_touch_ev = Clock.schedule_once(self.long_touch, .5)

        self.cursor = self.get_cursor_from_xy(*touch_pos)
        if not self._selection_touch:
            self.cancel_selection()
            self._selection_touch = touch
            self._selection_from = self._selection_to = self.cursor_index()
            self._update_selection()

        if CutBuffer and 'button' in touch.profile and \
                touch.button == 'middle':
            self.insert_text(CutBuffer.get_cutbuffer())
            return True

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
        if self._long_touch_ev is not None:
            self._long_touch_ev.cancel()
            self._long_touch_ev = None

        if not self.focus:
            return False

        if self._selection_touch is touch:
            self._selection_to = self.cursor_index()
            self._update_selection(True)
            # show Bubble
            win = EventLoop.window
            if self._selection_to != self._selection_from:
                self._show_cut_copy_paste(touch.pos, win)
            elif self.use_handles:
                self._hide_handles()
                handle_middle = self._handle_middle
                if handle_middle is None:
                    self._handle_middle = handle_middle = Selector(
                        source=self.handle_image_middle,
                        window=win,
                        target=self,
                        size_hint=(None, None),
                        size=('45dp', '45dp'))
                    handle_middle.bind(on_press=self._handle_pressed,
                                       on_touch_move=self._handle_move,
                                       on_release=self._handle_released)
                if not self._handle_middle.parent and self.text:
                    EventLoop.window.add_widget(handle_middle, canvas='after')
                self._position_handles(mode='middle')
            return True

    def _handle_pressed(self, instance):
        self._hide_cut_copy_paste()
        sf, st = self._selection_from, self.selection_to
        if sf > st:
            self._selection_from, self._selection_to = st, sf

    def _handle_released(self, instance):
        sf, st = self._selection_from, self.selection_to
        if sf == st:
            return

        self._update_selection()
        self._show_cut_copy_paste(
            (instance.right if instance is self._handle_left else instance.x,
             instance.top + self.line_height),
            EventLoop.window)

    def _handle_move(self, instance, touch):
        if touch.grab_current != instance:
            return
        get_cursor = self.get_cursor_from_xy
        handle_right = self._handle_right
        handle_left = self._handle_left
        handle_middle = self._handle_middle

        try:
            touch.push()
            touch.apply_transform_2d(self.to_widget)
            x, y = touch.pos
        finally:
            touch.pop()

        cursor = get_cursor(
            x,
            y + instance._touch_diff + (self.line_height / 2))

        if instance != touch.grab_current:
            return

        if instance == handle_middle:
            self.cursor = cursor
            self._position_handles(mode='middle')
            return

        ci = self.cursor_index(cursor=cursor)
        sf, st = self._selection_from, self.selection_to

        if instance == handle_left:
            self._selection_from = ci
        elif instance == handle_right:
            self._selection_to = ci
        self._trigger_update_graphics()
        self._trigger_position_handles()

    def _position_handles(self, *args, **kwargs):
        if not self.text:
            return
        mode = kwargs.get('mode', 'both')

        lh = self.line_height

        handle_middle = self._handle_middle
        if handle_middle:
            hp_mid = self.cursor_pos
            pos = self.to_local(*hp_mid, relative=True)
            handle_middle.x = pos[0] - handle_middle.width / 2
            handle_middle.top = pos[1] - lh
        if mode[0] == 'm':
            return

        group = self.canvas.get_group('selection')
        if not group:
            return

        EventLoop.window.remove_widget(self._handle_middle)

        handle_left = self._handle_left
        if not handle_left:
            return
        hp_left = group[2].pos
        handle_left.pos = self.to_local(*hp_left, relative=True)
        handle_left.x -= handle_left.width
        handle_left.y -= handle_left.height

        handle_right = self._handle_right
        last_rect = group[-1]
        hp_right = last_rect.pos[0], last_rect.pos[1]
        x, y = self.to_local(*hp_right, relative=True)
        handle_right.x = x + last_rect.size[0]
        handle_right.y = y - handle_right.height

    def _hide_handles(self, win=None):
        win = win or EventLoop.window
        if win is None:
            return
        win.remove_widget(self._handle_right)
        win.remove_widget(self._handle_left)
        win.remove_widget(self._handle_middle)

    def _show_handles(self, dt):
        if not self.use_handles or not self.text:
            return

        win = EventLoop.window

        handle_right = self._handle_right
        handle_left = self._handle_left
        if self._handle_left is None:
            self._handle_left = handle_left = Selector(
                source=self.handle_image_left,
                target=self,
                window=win,
                size_hint=(None, None),
                size=('45dp', '45dp'))
            handle_left.bind(on_press=self._handle_pressed,
                             on_touch_move=self._handle_move,
                             on_release=self._handle_released)
            self._handle_right = handle_right = Selector(
                source=self.handle_image_right,
                target=self,
                window=win,
                size_hint=(None, None),
                size=('45dp', '45dp'))
            handle_right.bind(on_press=self._handle_pressed,
                              on_touch_move=self._handle_move,
                              on_release=self._handle_released)
        else:
            if self._handle_left.parent:
                self._position_handles()
                return
            if not self.parent:
                return

        self._trigger_position_handles()
        if self.selection_from != self.selection_to:
            self._handle_left.opacity = self._handle_right.opacity = 0
            win.add_widget(self._handle_left, canvas='after')
            win.add_widget(self._handle_right, canvas='after')
            anim = Animation(opacity=1, d=.4)
            anim.start(self._handle_right)
            anim.start(self._handle_left)

    def _show_cut_copy_paste(self, pos, win, parent_changed=False,
                             mode='', pos_in_window=False, *l):
        # Show a bubble with cut copy and paste buttons
        if not self.use_bubble:
            return

        bubble = self._bubble
        if bubble is None:
            self._bubble = bubble = TextInputCutCopyPaste(textinput=self)
            self.fbind('parent', self._show_cut_copy_paste, pos, win, True)
            win.bind(
                size=lambda *args: self._hide_cut_copy_paste(win))
            self.bind(cursor_pos=lambda *args: self._hide_cut_copy_paste(win))
        else:
            win.remove_widget(bubble)
            if not self.parent:
                return
        if parent_changed:
            return

        # Search the position from the touch to the window
        lh, ls = self.line_height, self.line_spacing

        x, y = pos
        t_pos = (x, y) if pos_in_window else self.to_window(x, y)
        bubble_size = bubble.size
        bubble_hw = bubble_size[0] / 2.
        win_size = win.size
        bubble_pos = (t_pos[0], t_pos[1] + inch(.25))

        if (bubble_pos[0] - bubble_hw) < 0:
            # bubble beyond left of window
            if bubble_pos[1] > (win_size[1] - bubble_size[1]):
                # bubble above window height
                bubble_pos = (bubble_hw, (t_pos[1]) - (lh + ls + inch(.25)))
                bubble.arrow_pos = 'top_left'
            else:
                bubble_pos = (bubble_hw, bubble_pos[1])
                bubble.arrow_pos = 'bottom_left'
        elif (bubble_pos[0] + bubble_hw) > win_size[0]:
            # bubble beyond right of window
            if bubble_pos[1] > (win_size[1] - bubble_size[1]):
                # bubble above window height
                bubble_pos = (win_size[0] - bubble_hw,
                             (t_pos[1]) - (lh + ls + inch(.25)))
                bubble.arrow_pos = 'top_right'
            else:
                bubble_pos = (win_size[0] - bubble_hw, bubble_pos[1])
                bubble.arrow_pos = 'bottom_right'
        else:
            if bubble_pos[1] > (win_size[1] - bubble_size[1]):
                # bubble above window height
                bubble_pos = (bubble_pos[0],
                             (t_pos[1]) - (lh + ls + inch(.25)))
                bubble.arrow_pos = 'top_mid'
            else:
                bubble.arrow_pos = 'bottom_mid'

        bubble_pos = self.to_widget(*bubble_pos, relative=True)
        bubble.center_x = bubble_pos[0]
        if bubble.arrow_pos[0] == 't':
            bubble.top = bubble_pos[1]
        else:
            bubble.y = bubble_pos[1]
        bubble.mode = mode
        Animation.cancel_all(bubble)
        bubble.opacity = 0
        win.add_widget(bubble, canvas='after')
        Animation(opacity=1, d=.225).start(bubble)

    def _hide_cut_copy_paste(self, win=None):
        bubble = self._bubble
        if not bubble:
            return

        bubble.hide()

    #
    # Private
    #

    @staticmethod
    def _reload_remove_observer(wr):
        # called when the textinput is deleted
        if wr in _textinput_list:
            _textinput_list.remove(wr)

    def _on_textinput_focused(self, instance, value, *largs):

        win = EventLoop.window
        self.cancel_selection()
        self._hide_cut_copy_paste(win)

        if value:
            if (not (self.readonly or self.disabled) or _is_desktop and
                    self._keyboard_mode == 'system'):
                self._trigger_cursor_reset()
                self._editable = True
            else:
                self._editable = False
        else:
            self._do_blink_cursor_ev.cancel()
            self._hide_handles(win)

    def _ensure_clipboard(self):
        global Clipboard, CutBuffer
        if not Clipboard:
            from kivy.core.clipboard import Clipboard, CutBuffer

    def cut(self):
        ''' Copy current selection to clipboard then delete it from TextInput.

        .. versionadded:: 1.8.0

        '''
        self._cut(self.selection_text)

    def _cut(self, data):
        self._ensure_clipboard()
        Clipboard.copy(data)
        self.delete_selection()

    def copy(self, data=''):
        ''' Copy the value provided in argument `data` into current clipboard.
        If data is not of type string it will be converted to string.
        If no data is provided then current selection if present is copied.

        .. versionadded:: 1.8.0

        '''
        self._ensure_clipboard()
        if data:
            return Clipboard.copy(data)
        if self.selection_text:
            return Clipboard.copy(self.selection_text)

    def paste(self):
        ''' Insert text from system :class:`~kivy.core.clipboard.Clipboard`
        into the :class:`~kivy.uix.textinput.TextInput` at current cursor
        position.

        .. versionadded:: 1.8.0

        '''
        self._ensure_clipboard()
        data = Clipboard.paste()
        self.delete_selection()
        self.insert_text(data)

    def _update_cutbuffer(self, *args):
        CutBuffer.set_cutbuffer(self.selection_text)

    def _get_text_width(self, text, tab_width, _label_cached):
        # Return the width of a text, according to the current line options
        kw = self._get_line_options()

        try:
            cid = u'{}\0{}\0{}'.format(text, self.password, kw)
        except UnicodeDecodeError:
            cid = '{}\0{}\0{}'.format(text, self.password, kw)

        width = Cache_get('textinput.width', cid)
        if width:
            return width
        if not _label_cached:
            _label_cached = self._label_cached
        text = text.replace('\t', ' ' * tab_width)
        if not self.password:
            width = _label_cached.get_extents(text)[0]
        else:
            width = _label_cached.get_extents(
                self.password_mask * len(text))[0]
        Cache_append('textinput.width', cid, width)
        return width

    def _do_blink_cursor(self, dt):
        # Callback for blinking the cursor.
        self.cursor_blink = not self.cursor_blink

    def _reset_cursor_blink(self, *args):
        self._do_blink_cursor_ev.cancel()
        self.cursor_blink = 0
        self._do_blink_cursor_ev()

    def on_cursor(self, instance, value):
        # When the cursor is moved, reset cursor blinking to keep it showing,
        # and update all the graphics.
        if self.focus:
            self._trigger_cursor_reset()
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
        if self._refresh_line_options_ev is not None:
            self._refresh_line_options_ev.cancel()
        else:
            self._refresh_line_options_ev = Clock.create_trigger(
                self._refresh_line_options, 0)
        self._refresh_line_options_ev()

    def _refresh_line_options(self, *largs):
        self._line_options = None
        self._get_line_options()
        self._refresh_text_from_property()
        self._refresh_hint_text()
        self.cursor = self.get_cursor_from_index(len(self.text))

    def _trigger_refresh_text(self, *largs):
        if len(largs) and largs[0] == self:
            largs = ()
        if self._refresh_text_from_property_ev is not None:
            self._refresh_text_from_property_ev.cancel()
        self._refresh_text_from_property_ev = Clock.schedule_once(
            lambda dt: self._refresh_text_from_property(*largs))

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
            # start = max(0, start)
            cursor = None
        else:
            cursor = self.cursor_index()
            _lines, self._lines_flags = self._split_smart(text)
        _lines_labels = []
        _line_rects = []
        _create_label = self._create_line_label

        for x in _lines:
            lbl = _create_label(x)
            _lines_labels.append(lbl)
            _line_rects.append(Rectangle(size=lbl.size))

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
                else (finish + 1),
                len_lines, _lines_flags, _lines, _lines_labels,
                _line_rects)

        min_line_ht = self._label_cached.get_extents('_')[1]
        # with markup texture can be of height `1`
        self.line_height = max(_lines_labels[0].height, min_line_ht)
        # self.line_spacing = 2
        # now, if the text change, maybe the cursor is not at the same place as
        # before. so, try to set the cursor on the good place
        row = self.cursor_row
        self.cursor = self.get_cursor_from_index(self.cursor_index()
                                                 if cursor is None else cursor)
        # if we back to a new line, reset the scroll, otherwise, the effect is
        # ugly
        if self.cursor_row != row:
            self.scroll_x = 0
        # with the new text don't forget to update graphics again
        self._trigger_update_graphics()

    def _insert_lines(self, start, finish, len_lines, _lines_flags,
                      _lines, _lines_labels, _line_rects):
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
        self._update_graphics_ev.cancel()
        self._update_graphics_ev()

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
        if not self._lines or (
                not self._lines[0] and len(self._lines) == 1):
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
                if viewport_pos:
                    tcx, tcy = viewport_pos
                    tcx = tcx / tw * (ow)
                    tcy = tcy / th * oh
                if tw - viewport_pos[0] < vw:
                    tcw = tcw - tcx
                    size[0] = tcw * size[0]
                elif vw < tw:
                    tcw = (vw / tw) * tcw
                    size[0] = vw
                if vh < th:
                    tch = (vh / th) * tch
                    size[1] = vh

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
                               (s2c, s2r - 1), _lines, _get_text_width,
                               tab_width, _label_cached, width,
                               padding_left, padding_right, x,
                               canvas_add, selection_color)
            y -= dy
        self._position_handles('both')

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
            x1 -= self.scroll_x
            x1 += _get_text_width(lines[:s1c], tab_width, _label_cached)
        if line_num == s2r:
            lines = _lines[line_num]
            x2 = (x - self.scroll_x) + _get_text_width(lines[:s2c],
                                                       tab_width,
                                                       _label_cached)
        width_minus_padding = width - (padding_right + padding_left)
        maxx = x + width_minus_padding
        if x1 > maxx:
            return
        x1 = max(x1, x)
        x2 = min(x2, x + width_minus_padding)
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
        left = self.x + padding_left
        top = self.top - padding_top
        y = top + self.scroll_y
        y -= self.cursor_row * dy
        x, y = left + self.cursor_offset() - self.scroll_x, y
        if x < left:
            self.scroll_x = 0
            x = left
        if y > top:
            y = top
            self.scroll_y = 0
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
            ntext = self.password_mask * len(ntext)
        kw = self._get_line_options()
        cid = '%s\0%s' % (ntext, str(kw))
        texture = Cache_get('textinput.label', cid)

        if texture is None:
            # FIXME right now, we can't render very long line...
            # if we move on "VBO" version as fallback, we won't need to
            # do this. try to found the maximum text we can handle
            label = None
            label_len = len(ntext)
            ld = None

            # check for blank line
            if not ntext:
                texture = Texture.create(size=(1, 1))
                Cache_append('textinput.label', cid, texture)
                return texture

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
            lines_flags = [0] + [FL_IS_LINEBREAK] * (len(lines) - 1)
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
                flags |= FL_IS_LINEBREAK
            elif width >= 1 and w > width:
                while w > width:
                    split_width = split_pos = 0
                    # split the word
                    for c in word:
                        cw = self._get_text_width(
                            c, self.tab_width, self._label_cached
                        )
                        if split_width + cw > width:
                            break
                        split_width += cw
                        split_pos += 1
                    if split_width == split_pos == 0:
                        # can't fit the word in, give up
                        break
                    lines_append(word[:split_pos])
                    lines_flags_append(flags)
                    flags = FL_IS_WORDBREAK
                    word = word[split_pos:]
                    w -= split_width
                x = w
                line.append(word)
            else:
                x += w
                line.append(word)
        if line or flags & FL_IS_LINEBREAK:
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
        elif internal_action == 'ctrl_L':
            self._ctrl_l = True
        elif internal_action == 'ctrl_R':
            self._ctrl_r = True
        elif internal_action == 'alt_L':
            self._alt_l = True
        elif internal_action == 'alt_R':
            self._alt_r = True
        elif internal_action.startswith('cursor_'):
            cc, cr = self.cursor
            self.do_cursor_movement(internal_action,
                                    self._ctrl_l or self._ctrl_r,
                                    self._alt_l or self._alt_r)
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
            # self._recalc_size()
            pass

    def _key_up(self, key, repeat=False):
        displayed_str, internal_str, internal_action, scale = key
        if internal_action in ('shift', 'shift_L', 'shift_R'):
            if self._selection:
                self._update_selection(True)
        elif internal_action == 'ctrl_L':
            self._ctrl_l = False
        elif internal_action == 'ctrl_R':
            self._ctrl_r = False
        elif internal_action == 'alt_L':
            self._alt_l = False
        elif internal_action == 'alt_R':
            self._alt_r = False

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        # Keycodes on OS X:
        ctrl, cmd = 64, 1024
        key, key_str = keycode
        win = EventLoop.window

        # This allows *either* ctrl *or* cmd, but not both.
        is_shortcut = (modifiers == ['ctrl'] or (
            _is_osx and modifiers == ['meta']))
        is_interesting_key = key in (list(self.interesting_keys.keys()) + [27])

        if not self.write_tab and super(TextInput,
            self).keyboard_on_key_down(window, keycode, text, modifiers):
            return True

        if not self._editable:
            # duplicated but faster testing for non-editable keys
            if text and not is_interesting_key:
                if is_shortcut and key == ord('c'):
                    self.copy()
            elif key == 27:
                self.focus = False
            return True

        if text and not is_interesting_key:

            self._hide_handles(win)
            self._hide_cut_copy_paste(win)
            win.remove_widget(self._handle_middle)

            # check for command modes
            # we use \x01INFO\x02 to get info from IME on mobiles
            # pygame seems to pass \x01 as the unicode for ctrl+a
            # checking for modifiers ensures conflict resolution.

            first_char = ord(text[0])
            if not modifiers and first_char == 1:
                self._command_mode = True
                self._command = ''
            if not modifiers and first_char == 2:
                self._command_mode = False
                self._command = self._command[1:]

            if self._command_mode:
                self._command += text
                return

            _command = self._command
            if _command and first_char == 2:
                from_undo = True
                _command, data = _command.split(':')
                self._command = ''
                if self._selection:
                    self.delete_selection()
                if _command == 'DEL':
                    count = int(data)
                    if not count:
                        self.delete_selection(from_undo=True)
                    end = self.cursor_index()
                    self._selection_from = max(end - count, 0)
                    self._selection_to = end
                    self._selection = True
                    self.delete_selection(from_undo=True)
                    return
                elif _command == 'INSERT':
                    self.insert_text(data, from_undo)
                elif _command == 'INSERTN':
                    from_undo = False
                    self.insert_text(data, from_undo)
                elif _command == 'SELWORD':
                    self.dispatch('on_double_tap')
                elif _command == 'SEL':
                    if data == '0':
                        Clock.schedule_once(lambda dt: self.cancel_selection())
                elif _command == 'CURCOL':
                    self.cursor = int(data), self.cursor_row
                return

            if is_shortcut:
                if key == ord('x'):  # cut selection
                    self._cut(self.selection_text)
                elif key == ord('c'):  # copy selection
                    self.copy()
                elif key == ord('v'):  # paste selection
                    self.paste()
                elif key == ord('a'):  # select all
                    self.select_all()
                elif key == ord('z'):  # undo
                    self.do_undo()
                elif key == ord('r'):  # redo
                    self.do_redo()
            else:
                if EventLoop.window.__class__.__module__ == \
                    'kivy.core.window.window_sdl2':
                    if not (text == ' ' and platform == 'android'):
                        return
                if self._selection:
                    self.delete_selection()
                self.insert_text(text)
            # self._recalc_size()
            return

        if is_interesting_key:
            self._hide_cut_copy_paste(win)
            self._hide_handles(win)

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

    def keyboard_on_key_up(self, window, keycode):
        key, key_str = keycode
        k = self.interesting_keys.get(key)
        if k:
            key = (None, None, k, 1)
            self._key_up(key)

    def keyboard_on_textinput(self, window, text):
        if self._selection:
            self.delete_selection()
        self.insert_text(text, False)

    def on__hint_text(self, instance, value):
        self._refresh_hint_text()

    def _refresh_hint_text(self):
        _lines, self._hint_text_flags = self._split_smart(self.hint_text)
        _hint_text_labels = []
        _hint_text_rects = []
        _create_label = self._create_line_label

        for x in _lines:
            lbl = _create_label(x, hint=True)
            _hint_text_labels.append(lbl)
            _hint_text_rects.append(Rectangle(size=lbl.size))

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
    _insert_int_patu = re.compile(u'[^0-9]')
    _insert_int_patb = re.compile(b'[^0-9]')

    readonly = BooleanProperty(False)
    '''If True, the user will not be able to change the content of a textinput.

    .. versionadded:: 1.3.0

    :attr:`readonly` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    multiline = BooleanProperty(True)
    '''If True, the widget will be able show multiple lines of text. If False,
    the "enter" keypress will defocus the textinput instead of adding a new
    line.

    :attr:`multiline` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    password = BooleanProperty(False)
    '''If True, the widget will display its characters as the character
    set in :attr:`password_mask`.

    .. versionadded:: 1.2.0

    :attr:`password` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    password_mask = StringProperty('*')
    '''Sets the character used to mask the text when :attr:`password` is True.

    .. versionadded:: 1.10.0

    :attr:`password_mask` is a :class:`~kivy.properties.StringProperty` and
    defaults to `'*'`.
    '''

    keyboard_suggestions = BooleanProperty(True)
    '''If True provides auto suggestions on top of keyboard.
    This will only work if :attr:`input_type` is set to `text`.

    .. versionadded:: 1.8.0

    :attr:`keyboard_suggestions` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to True.
    '''

    cursor_blink = BooleanProperty(False)
    '''This property is used to blink the cursor graphic. The value of
    :attr:`cursor_blink` is automatically computed. Setting a value on it will
    have no impact.

    :attr:`cursor_blink` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
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

        # if offset is outside the current bounds, readjust
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
    '''Tuple of (row, col) values indicating the current cursor position.
    You can set a new (row, col) if you want to move the cursor. The scrolling
    area will be automatically updated to ensure that the cursor is
    visible inside the viewport.

    :attr:`cursor` is an :class:`~kivy.properties.AliasProperty`.
    '''

    def _get_cursor_col(self):
        return self._cursor[0]

    cursor_col = AliasProperty(_get_cursor_col, None, bind=('cursor', ))
    '''Current column of the cursor.

    :attr:`cursor_col` is an :class:`~kivy.properties.AliasProperty` to
    cursor[0], read-only.
    '''

    def _get_cursor_row(self):
        return self._cursor[1]

    cursor_row = AliasProperty(_get_cursor_row, None, bind=('cursor', ))
    '''Current row of the cursor.

    :attr:`cursor_row` is an :class:`~kivy.properties.AliasProperty` to
    cursor[1], read-only.
    '''

    cursor_pos = AliasProperty(_get_cursor_pos, None, bind=(
        'cursor', 'padding', 'pos', 'size', 'focus',
        'scroll_x', 'scroll_y'))
    '''Current position of the cursor, in (x, y).

    :attr:`cursor_pos` is an :class:`~kivy.properties.AliasProperty`,
    read-only.
    '''

    cursor_color = ListProperty([1, 0, 0, 1])
    '''Current color of the cursor, in (r, g, b, a) format.

    .. versionadded:: 1.9.0

    :attr:`cursor_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [1, 0, 0, 1].
    '''

    cursor_width = NumericProperty('1sp')
    '''Current width of the cursor.

    .. versionadded:: 1.10.0

    :attr:`cursor_width` is a :class:`~kivy.properties.NumericProperty` and
    defaults to '1sp'.
    '''

    line_height = NumericProperty(1)
    '''Height of a line. This property is automatically computed from the
    :attr:`font_name`, :attr:`font_size`. Changing the line_height will have
    no impact.

    .. note::

        :attr:`line_height` is the height of a single line of text.
        Use :attr:`minimum_height`, which also includes padding, to
        get the height required to display the text properly.

    :attr:`line_height` is a :class:`~kivy.properties.NumericProperty`,
    read-only.
    '''

    tab_width = NumericProperty(4)
    '''By default, each tab will be replaced by four spaces on the text
    input widget. You can set a lower or higher value.

    :attr:`tab_width` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 4.
    '''

    padding_x = VariableListProperty([0, 0], length=2)
    '''Horizontal padding of the text: [padding_left, padding_right].

    padding_x also accepts a one argument form [padding_horizontal].

    :attr:`padding_x` is a :class:`~kivy.properties.VariableListProperty` and
    defaults to [0, 0]. This might be changed by the current theme.

    .. deprecated:: 1.7.0
        Use :attr:`padding` instead.
    '''

    def on_padding_x(self, instance, value):
        self.padding[0] = value[0]
        self.padding[2] = value[1]

    padding_y = VariableListProperty([0, 0], length=2)
    '''Vertical padding of the text: [padding_top, padding_bottom].

    padding_y also accepts a one argument form [padding_vertical].

    :attr:`padding_y` is a :class:`~kivy.properties.VariableListProperty` and
    defaults to [0, 0]. This might be changed by the current theme.

    .. deprecated:: 1.7.0
        Use :attr:`padding` instead.
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

    :attr:`padding` is a :class:`~kivy.properties.VariableListProperty` and
    defaults to [6, 6, 6, 6].
    '''

    scroll_x = NumericProperty(0)
    '''X scrolling value of the viewport. The scrolling is automatically
    updated when the cursor is moved or text changed. If there is no
    user input, the scroll_x and scroll_y properties may be changed.

    :attr:`scroll_x` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    scroll_y = NumericProperty(0)
    '''Y scrolling value of the viewport. See :attr:`scroll_x` for more
    information.

    :attr:`scroll_y` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    selection_color = ListProperty([0.1843, 0.6549, 0.8313, .5])
    '''Current color of the selection, in (r, g, b, a) format.

    .. warning::

        The color should always have an "alpha" component less than 1
        since the selection is drawn after the text.

    :attr:`selection_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [0.1843, 0.6549, 0.8313, .5].
    '''

    border = ListProperty([4, 4, 4, 4])
    '''Border used for :class:`~kivy.graphics.vertex_instructions.BorderImage`
    graphics instruction. Used with :attr:`background_normal` and
    :attr:`background_active`. Can be used for a custom background.

    .. versionadded:: 1.4.1

    It must be a list of four values: (bottom, right, top, left). Read the
    BorderImage instruction for more information about how to use it.

    :attr:`border` is a :class:`~kivy.properties.ListProperty` and defaults
    to (4, 4, 4, 4).
    '''

    background_normal = StringProperty(
        'atlas://data/images/defaulttheme/textinput')
    '''Background image of the TextInput when it's not in focus.

    .. versionadded:: 1.4.1

    :attr:`background_normal` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/textinput'.
    '''

    background_disabled_normal = StringProperty(
        'atlas://data/images/defaulttheme/textinput_disabled')
    '''Background image of the TextInput when disabled.

    .. versionadded:: 1.8.0

    :attr:`background_disabled_normal` is a
    :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/textinput_disabled'.
    '''

    background_active = StringProperty(
        'atlas://data/images/defaulttheme/textinput_active')
    '''Background image of the TextInput when it's in focus.

    .. versionadded:: 1.4.1

    :attr:`background_active` is a
    :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/textinput_active'.
    '''

    background_color = ListProperty([1, 1, 1, 1])
    '''Current color of the background, in (r, g, b, a) format.

    .. versionadded:: 1.2.0

    :attr:`background_color` is a :class:`~kivy.properties.ListProperty`
    and defaults to [1, 1, 1, 1] (white).
    '''

    foreground_color = ListProperty([0, 0, 0, 1])
    '''Current color of the foreground, in (r, g, b, a) format.

    .. versionadded:: 1.2.0

    :attr:`foreground_color` is a :class:`~kivy.properties.ListProperty`
    and defaults to [0, 0, 0, 1] (black).
    '''

    disabled_foreground_color = ListProperty([0, 0, 0, .5])
    '''Current color of the foreground when disabled, in (r, g, b, a) format.

    .. versionadded:: 1.8.0

    :attr:`disabled_foreground_color` is a
    :class:`~kivy.properties.ListProperty` and
    defaults to [0, 0, 0, 5] (50% transparent black).
    '''

    use_bubble = BooleanProperty(not _is_desktop)
    '''Indicates whether the cut/copy/paste bubble is used.

    .. versionadded:: 1.7.0

    :attr:`use_bubble` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to True on mobile OS's, False on desktop OS's.
    '''

    use_handles = BooleanProperty(not _is_desktop)
    '''Indicates whether the selection handles are displayed.

    .. versionadded:: 1.8.0

    :attr:`use_handles` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to True on mobile OS's, False on desktop OS's.
    '''

    suggestion_text = StringProperty('')
    '''Shows a suggestion text at the end of the current line.
    The feature is useful for text autocompletion, and it does not implement
    validation (accepting the suggested text on enter etc.).
    This can also be used by the IME to setup the current word being edited.

    .. versionadded:: 1.9.0

    :attr:`suggestion_text` is a :class:`~kivy.properties.StringProperty` and
    defaults to `''`.
    '''

    def on_suggestion_text(self, instance, value):
        global MarkupLabel
        if not MarkupLabel:
            from kivy.core.text.markup import MarkupLabel

        cursor_row = self.cursor_row
        if cursor_row >= len(self._lines) or self.canvas is None:
            return

        cursor_pos = self.cursor_pos
        txt = self._lines[cursor_row]

        kw = self._get_line_options()
        rct = self._lines_rects[cursor_row]

        lbl = text = None
        if value:
            lbl = MarkupLabel(
                text=txt + "[b]{}[/b]".format(value), **kw)
        else:
            lbl = Label(**kw)
            text = txt

        lbl.refresh()

        self._lines_labels[cursor_row] = lbl.texture
        rct.size = lbl.size
        self._update_graphics()

    def get_sel_from(self):
        return self._selection_from

    selection_from = AliasProperty(get_sel_from, None)
    '''If a selection is in progress or complete, this property will represent
    the cursor index where the selection started.

    .. versionchanged:: 1.4.0
        :attr:`selection_from` is an :class:`~kivy.properties.AliasProperty`
        and defaults to None, readonly.
    '''

    def get_sel_to(self):
        return self._selection_to

    selection_to = AliasProperty(get_sel_to, None)
    '''If a selection is in progress or complete, this property will represent
    the cursor index where the selection started.

    .. versionchanged:: 1.4.0
        :attr:`selection_to` is an :class:`~kivy.properties.AliasProperty` and
        defaults to None, readonly.
    '''

    selection_text = StringProperty(u'')
    '''Current content selection.

    :attr:`selection_text` is a :class:`~kivy.properties.StringProperty`
    and defaults to '', readonly.
    '''

    def on_selection_text(self, instance, value):
        if value:
            if self.use_handles:
                self._trigger_show_handles()
            if CutBuffer and not self.password:
                self._trigger_update_cutbuffer()

    def _get_text(self, encode=False):
        lf = self._lines_flags
        l = self._lines
        len_l = len(l)

        if len(lf) < len_l:
            lf.append(1)

        text = u''.join([(u'\n' if (lf[i] & FL_IS_LINEBREAK) else u'') + l[i]
                        for i in range(len_l)])

        if encode and not isinstance(text, bytes):
            text = text.encode('utf8')
        return text

    def _set_text(self, text):
        if isinstance(text, bytes):
            text = text.decode('utf8')

        if self.replace_crlf:
            text = text.replace(u'\r\n', u'\n')

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

    :attr:`text` is an :class:`~kivy.properties.AliasProperty`.
    '''

    font_name = StringProperty(DEFAULT_FONT)
    '''Filename of the font to use. The path can be absolute or relative.
    Relative paths are resolved by the :func:`~kivy.resources.resource_find`
    function.

    .. warning::

        Depending on your text provider, the font file may be ignored. However,
        you can mostly use this without problems.

        If the font used lacks the glyphs for the particular language/symbols
        you are using, you will see '[]' blank box characters instead of the
        actual glyphs. The solution is to use a font that has the glyphs you
        need to display. For example, to display |unicodechar|, use a font like
        freesans.ttf that has the glyph.

        .. |unicodechar| image:: images/unicode-char.png

    :attr:`font_name` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'Roboto'. This value is taken
    from :class:`~kivy.config.Config`.
    '''

    font_size = NumericProperty('15sp')
    '''Font size of the text in pixels.

    :attr:`font_size` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 15\ :attr:`~kivy.metrics.sp`.
    '''
    _hint_text = StringProperty('')

    def _set_hint_text(self, value):
        if isinstance(value, bytes):
            value = value.decode('utf8')
        self._hint_text = value

    def _get_hint_text(self):
        return self._hint_text

    hint_text = AliasProperty(
        _get_hint_text, _set_hint_text, bind=('_hint_text', ))
    '''Hint text of the widget, shown if text is ''.

    .. versionadded:: 1.6.0

    .. versionchanged:: 1.10.0
        The property is now an AliasProperty and byte values are decoded to
        strings. The hint text will stay visible when the widget is focused.

    :attr:`hint_text` a :class:`~kivy.properties.AliasProperty` and defaults
    to ''.
    '''

    hint_text_color = ListProperty([0.5, 0.5, 0.5, 1.0])
    '''Current color of the hint_text text, in (r, g, b, a) format.

    .. versionadded:: 1.6.0

    :attr:`hint_text_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [0.5, 0.5, 0.5, 1.0] (grey).
    '''

    auto_indent = BooleanProperty(False)
    '''Automatically indent multiline text.

    .. versionadded:: 1.7.0

    :attr:`auto_indent` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    replace_crlf = BooleanProperty(True)
    '''Automatically replace CRLF with LF.

    .. versionadded:: 1.9.1

    :attr:`replace_crlf` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    allow_copy = BooleanProperty(True)
    '''Decides whether to allow copying the text.

    .. versionadded:: 1.8.0

    :attr:`allow_copy` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    def _get_min_height(self):
        return (len(self._lines) * (self.line_height + self.line_spacing) +
                self.padding[1] + self.padding[3])

    minimum_height = AliasProperty(_get_min_height, None,
                                   bind=('_lines', 'line_spacing', 'padding',
                                         'font_size', 'font_name', 'password',
                                         'hint_text', 'line_height'))
    '''Minimum height of the content inside the TextInput.

    .. versionadded:: 1.8.0

    :attr:`minimum_height` is a readonly
    :class:`~kivy.properties.AliasProperty`.

    .. warning::
        :attr:`minimum_width` is calculated based on :attr:`width` therefore
        code like this will lead to an infinite loop::

            <FancyTextInput>:
                height: self.minimum_height
                width: self.height
    '''

    line_spacing = NumericProperty(0)
    '''Space taken up between the lines.

    .. versionadded:: 1.8.0

    :attr:`line_spacing` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    input_filter = ObjectProperty(None, allownone=True)
    ''' Filters the input according to the specified mode, if not None. If
    None, no filtering is applied.

    .. versionadded:: 1.9.0

    :attr:`input_filter` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to `None`. Can be one of `None`, `'int'` (string), or `'float'`
    (string), or a callable. If it is `'int'`, it will only accept numbers.
    If it is `'float'` it will also accept a single period. Finally, if it is
    a callable it will be called with two parameters; the string to be added
    and a bool indicating whether the string is a result of undo (True). The
    callable should return a new substring that will be used instead.
    '''

    handle_image_middle = StringProperty(
        'atlas://data/images/defaulttheme/selector_middle')
    '''Image used to display the middle handle on the TextInput for cursor
    positioning.

    .. versionadded:: 1.8.0

    :attr:`handle_image_middle` is a :class:`~kivy.properties.StringProperty`
    and defaults to 'atlas://data/images/defaulttheme/selector_middle'.
    '''

    def on_handle_image_middle(self, instance, value):
        if self._handle_middle:
            self._handle_middle.source = value

    handle_image_left = StringProperty(
        'atlas://data/images/defaulttheme/selector_left')
    '''Image used to display the Left handle on the TextInput for selection.

    .. versionadded:: 1.8.0

    :attr:`handle_image_left` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/selector_left'.
    '''

    def on_handle_image_left(self, instance, value):
        if self._handle_left:
            self._handle_left.source = value

    handle_image_right = StringProperty(
        'atlas://data/images/defaulttheme/selector_right')
    '''Image used to display the Right handle on the TextInput for selection.

    .. versionadded:: 1.8.0

    :attr:`handle_image_right` is a
    :class:`~kivy.properties.StringProperty` and defaults to
    'atlas://data/images/defaulttheme/selector_right'.
    '''

    def on_handle_image_right(self, instance, value):
        if self._handle_right:
            self._handle_right.source = value

    write_tab = BooleanProperty(True)
    '''Whether the tab key should move focus to the next widget or if it should
    enter a tab in the :class:`TextInput`. If `True` a tab will be written,
    otherwise, focus will move to the next widget.

    .. versionadded:: 1.9.0

    :attr:`write_tab` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to `True`.
    '''


if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.lang import Builder

    class TextInputApp(App):

        def build(self):

            Builder.load_string('''
<TextInput>
    on_text:
        self.suggestion_text = ''
        self.suggestion_text = 'ion_text'

''')
            root = BoxLayout(orientation='vertical')
            textinput = TextInput(multiline=True, use_bubble=True,
                                  use_handles=True)
            # textinput.text = __doc__
            root.add_widget(textinput)
            textinput2 = TextInput(multiline=False, text='monoline textinput',
                                   size_hint=(1, None), height=30)
            root.add_widget(textinput2)
            return root

    TextInputApp().run()
