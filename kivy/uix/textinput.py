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
key will defocus the textinput and emit on_text_validate event) ::

    def on_enter(instance, value):
        print 'User pressed enter in', instance

    textinput = TextInput(text='Hello world', multiline=False)
    textinput.bind(on_text_validate=on_enter)

To run a callback when the text changes ::

    def on_text(instance, value):
        print 'The widget', instance, 'have:', value

    textinput = TextInput()
    textinput.bind(text=on_text)

You can 'focus' a textinput, meaning that the input box will be highlighted,
and keyboard will be requested ::

    textinput = TextInput(focus=True)

The textinput is defocused if the 'escape' key is pressed, or if another
widget requests the keyboard. You can bind a callback to focus property to
get notified of focus changes ::

    def on_focus(instance, value):
        if value:
            print 'User focused', instance
        else:
            print 'User defocused', instance

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
control + a     Select all the content
=============== ========================================================

'''


__all__ = ('TextInput', )

import sys

from functools import partial
from kivy.logger import Logger
from kivy.utils import boundary
from kivy.clock import Clock
from kivy.cache import Cache
from kivy.core.text import Label
from kivy.uix.widget import Widget
from kivy.uix.bubble import Bubble
from kivy.graphics import Color, Rectangle
from kivy.properties import StringProperty, NumericProperty, \
        ReferenceListProperty, BooleanProperty, AliasProperty, \
        ListProperty, ObjectProperty

Cache.register('textinput.label', timeout=60.)

FL_IS_NEWLINE = 0x01

# late binding
Clipboard = None


class TextInputCutCopyPaste(Bubble):
    # Internal class used for showing the little bubble popup when
    # copy/cut/paste happen.

    textinput = ObjectProperty(None)

    def do(self, action):
        textinput = self.textinput

        global Clipboard
        if Clipboard is None:
            from kivy.core.clipboard import Clipboard

        if action == 'cut':
            Clipboard.put(textinput.selection_text, 'text/plain')
            textinput.delete_selection()
        elif action == 'copy':
            Clipboard.put(textinput.selection_text, 'text/plain')
        elif action == 'paste':
            data = Clipboard.get('text/plain')
            if data:
                textinput.delete_selection()
                textinput.insert_text(data)


class TextInput(Widget):
    '''TextInput class, see module documentation for more information.

    :Events:
        `on_text_validate`
            Fired only in multiline=False mode, when the user hits 'enter'.
            This will also unfocus the textinput.
    '''

    def __init__(self, **kwargs):
        self._win = None
        self._cursor_blink_time = Clock.get_time()
        self._cursor = [0, 0]
        self._selection = False
        self._selection_finished = True
        self._selection_touch = None
        self.selection_text = ''
        self.selection_from = None
        self.selection_to = None
        self._bubble = None
        self._lines_flags = []
        self._lines_labels = []
        self._lines_rects = []
        self._line_spacing = 0
        self._label_cached = None
        self._line_options = None
        self._keyboard = None
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

        self.register_event_type('on_text_validate')

        super(TextInput, self).__init__(**kwargs)

        self.bind(font_size=self._trigger_refresh_line_options,
                  font_name=self._trigger_refresh_line_options)

        self.bind(padding_x=self._trigger_refresh_text,
                  padding_y=self._trigger_refresh_text,
                  tab_width=self._trigger_refresh_text,
                  font_size=self._trigger_refresh_text,
                  font_name=self._trigger_refresh_text,
                  size=self._trigger_refresh_text)

        self.bind(pos=self._trigger_update_graphics)

        self._trigger_refresh_line_options()
        self._trigger_refresh_text()

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
            for row in xrange(cr):
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
        '''Get the cursor x offset on the current line
        '''
        offset = 0
        if self.cursor_col:
            offset = self._get_text_width(
                self._lines[self.cursor_row][:self.cursor_col])
        return offset

    def get_cursor_from_index(self, index):
        '''Return the (row, col) of the cursor from text index
        '''
        index = boundary(index, 0, len(self.text))
        if index <= 0:
            return 0, 0
        lf = self._lines_flags
        l = self._lines
        i = 0
        for row in xrange(len(l)):
            ni = i + len(l[row])
            if lf[row] & FL_IS_NEWLINE:
                ni += 1
                i += 1
            if ni >= index:
                return index - i, row
            i = ni
        return index, row

    def insert_text(self, substring):
        '''Insert new text on the current cursor position
        '''
        cc, cr = self.cursor
        ci = self.cursor_index()
        text = self._lines[cr]
        new_text = text[:cc] + substring + text[cc:]
        self._set_line_text(cr, new_text)
        self._trigger_refresh_text()
        self.cursor = self.get_cursor_from_index(ci + len(substring))

    def do_backspace(self):
        '''Do backspace operation from the current cursor position.
        This action might do lot of things like:

            - removing the current selection if available
            - removing the previous char, and back the cursor
            - do nothing, if we are at the start.

        '''
        cc, cr = self.cursor
        text = self._lines[cr]
        cursor_index = self.cursor_index()
        if cc == 0 and cr == 0:
            return
        if cc == 0:
            text_last_line = self._lines[cr - 1]
            self._set_line_text(cr - 1, text_last_line + text)
            self._delete_line(cr)
        else:
            #ch = text[cc-1]
            new_text = text[:cc-1] + text[cc:]
            self._set_line_text(cr, new_text)

        self._refresh_text_from_property()
        self.cursor = self.get_cursor_from_index(cursor_index - 1)

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

            Current page are 3 lines before/after

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
            col, row = self.get_cursor_from_index(self.cursor_index() - 1)
        elif action == 'cursor_right':
            col, row = self.get_cursor_from_index(self.cursor_index() + 1)
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
        l = self._lines
        dy = self.line_height + self._line_spacing
        cx = x - self.x
        scrl_y = self.scroll_y
        scrl_y = scrl_y/ dy if scrl_y > 0 else 0
        cy = (self.top - self.padding_y + scrl_y * dy) - y
        cy = int(boundary(round(cy / dy), 0, len(l) - 1))
        dcx = 0
        for i in xrange(1, len(l[cy])+1):
            if self._get_text_width(l[cy][:i]) >= cx:
                break
            dcx = i
        cx = dcx
        return cx, cy

    #
    # Selection control
    #
    def cancel_selection(self):
        '''Cancel current selection (if any)
        '''
        self._selection = False
        self._selection_finished = True
        self._selection_touch = None
        self._trigger_update_graphics()

    def delete_selection(self):
        '''Delete the current text selection (if any)
        '''
        scrl_x = self.scroll_x
        scrl_y = self.scroll_y
        if not self._selection:
            return
        v = self.text
        a, b = self.selection_from, self.selection_to
        if a > b:
            a, b = b, a
        text = v[:a] + v[b:]
        self.text = text
        self.cursor = self.get_cursor_from_index(a)
        self.scroll_x = scrl_x
        self.scroll_y = scrl_y
        self.cancel_selection()

    def _update_selection(self, finished=False):
        '''Update selection text and order of from/to if finished is True.
        Can be called multiple times until finished=True.
        '''
        a, b = self.selection_from, self.selection_to
        if a > b:
            a, b = b, a
        self._selection_finished = finished
        self.selection_text = self.text[a:b]
        if not finished:
            self._selection = True
        else:
            self._selection = bool(len(self.selection_text))
            self._selection_touch = None
        self._trigger_update_graphics()

    #
    # Touch control
    #
    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return False
        if not self.focus:
            self.focus = True
        touch.grab(self)
        self.cursor = self.get_cursor_from_xy(touch.x, touch.y)
        if not self._selection_touch:
            self.cancel_selection()
            self._selection_touch = touch
            self.selection_from = self.selection_to = self.cursor_index()
            self._update_selection()
        return True

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
            self.selection_to = self.cursor_index()
            self._update_selection()
            return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return
        touch.ungrab(self)
        if not self.focus:
            return False
        if self._selection_touch is touch:
            self.selection_to = self.cursor_index()
            self._update_selection(True)
            # show Bubble
            win = self._win
            if not win:
                self._win = win = self.get_root_window()
            if not win:
                Logger.warning('Textinput: '
                    'Cannot show bubble, unable to get root window')
                return True
            if self.selection_to != self.selection_from:
                self._show_cut_copy_paste(touch.pos, win)
            else:
                win.remove_widget(self._bubble)
            return True

    def _show_cut_copy_paste(self, pos, win, parent_changed = False, *l):
        # Show a bubble with cut copy and paste buttons
        bubble = self._bubble
        if bubble is None:
            self._bubble = bubble = TextInputCutCopyPaste(textinput=self)
            self.bind(parent = partial(self._show_cut_copy_paste,
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
        bubble.pos = (t_pos[0] - bubble_size[0] / 2., t_pos[1])
        bubble_pos = bubble.pos
        lh, ls = self.line_height, self._line_spacing

        # FIXME found a way to have that feature available for everybody
        if bubble_pos[0] < 0:
            # bubble beyond left of window
            if bubble.pos[1] > (win_size[1]- bubble_size[1]):
                # bubble above window height
                bubble.pos = (0, (t_pos[1]) - (bubble_size[1] + lh + ls))
                bubble.arrow_pos = 'top_left'
            else:
                bubble.pos = (0, bubble_pos[1])
                bubble.arrow_pos = 'bottom_left'
        elif bubble.right > win_size[0]:
            # bubble beyond right of window
            if bubble_pos[1] > (win_size[1]- bubble_size[1]):
                # bubble above window height
                bubble.pos = (win_size[0] - bubble_size[0],
                        (t_pos[1]) - (bubble_size[1] + lh + ls))
                bubble.arrow_pos = 'top_right'
            else:
                bubble.right = win_size[0]
                bubble.arrow_pos = 'bottom_right'
        else:
            if bubble_pos[1] > (win_size[1]- bubble_size[1]):
                # bubble above window height
                bubble.pos = (bubble_pos[0],
                        (t_pos[1]) - (bubble_size[1] + lh + ls))
                bubble.arrow_pos = 'top_mid'
            else:
                bubble.arrow_pos = 'bottom_mid'

        win.add_widget(self._bubble)

    #
    # Private
    #
    def on_focus(self, instance, value, *largs):
        win = self._win
        if not win:
            self._win = win = self.get_root_window()
        if not win:
            # we got argument, it could be the previous schedule
            # cancel focus.
            if len(largs):
                Logger.warning('Textinput: '
                    'Cannot focus the element, unable to get root window')
                return
            else:
                Clock.schedule_once(partial(self.on_focus, self, value), 0)
            return
        if value:
            keyboard = win.request_keyboard(self._keyboard_released, self)
            self._keyboard = keyboard
            keyboard.bind(
                on_key_down=self._keyboard_on_key_down,
                on_key_up=self._keyboard_on_key_up)
            Clock.schedule_interval(self._do_blink_cursor, 1 / 2.)
        else:
            keyboard = self._keyboard
            keyboard.unbind(
                on_key_down=self._keyboard_on_key_down,
                on_key_up=self._keyboard_on_key_up)
            keyboard.release()
            self.cancel_selection()
            Clock.unschedule(self._do_blink_cursor)
            self._win = None

    def _keyboard_released(self):
        # Callback called when the real keyboard is taken by someone else
        # called by the window if the keyboard is taken by somebody else
        # FIXME: handle virtual keyboard.
        self.focus = False

    def _get_text_width(self, text):
        # Return the width of a text, according to the current line options
        if not self._label_cached:
            self._get_line_options()
        text = text.replace('\t', ' ' * self.tab_width)
        return self._label_cached.get_extents(text)[0]

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
        self._lines.pop(idx)
        self._lines_flags.pop(idx)
        self._lines_labels.pop(idx)
        self.cursor = self.cursor

    def _set_line_text(self, line_num, text):
        # Set current line with other text than the default one.
        self._lines[line_num] = text
        self._lines_labels[line_num] = self._create_line_label(text)

    def _trigger_refresh_line_options(self, *largs):
        Clock.unschedule(self._refresh_line_options)
        Clock.schedule_once(self._refresh_line_options, 0)

    def _refresh_line_options(self, *largs):
        self._line_options = None
        self._get_line_options()
        self._refresh_text(self.text)
        self.cursor = self.get_cursor_from_index(len(self.text))

    def _trigger_refresh_text(self, *largs):
        Clock.unschedule(self._refresh_text_from_property)
        Clock.schedule_once(self._refresh_text_from_property)

    def _refresh_text_from_property(self, *largs):
        self._refresh_text(self.text)

    def _refresh_text(self, text):
        # Refresh all the lines from a new text.
        # By using cache in internal functions, this method should be fast.
        _lines, self._lines_flags = self._split_smart(text)
        self._lines = _lines
        self._lines_labels = [self._create_line_label(x) for x in self._lines]
        self._lines_rects = [Rectangle(texture=x, size=( \
                             x.size if x else (0, 0))) \
                             for x in self._lines_labels]
        line_label = self._lines_labels[0]
        if line_label is None:
            self.line_height = max(1, self.font_size + self.padding_y)
        else:
            self.line_height = line_label.height
        self._line_spacing = 2
        # now, if the text change, maybe the cursor is not as the same place as
        # before. so, try to set the cursor on the good place
        row = self.cursor_row
        self.cursor = self.get_cursor_from_index(self.cursor_index())
        # if we back to a new line, reset the scroll, otherwise, the effect is
        # ugly
        if self.cursor_row != row:
            self.scroll_x = 0
        # with the new text don't forget to update graphics again
        self._trigger_update_graphics()

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
        dy = self.line_height + self._line_spacing

        # adjust view if the cursor is going outside the bounds
        sx = self.scroll_x
        sy = self.scroll_y

        # draw labels
        rects = self._lines_rects
        labels = self._lines_labels
        x = self.x + self.padding_x
        y = self.top - self.padding_y + sy
        miny = self.y + self.padding_y
        maxy = self.top - self.padding_y
        for line_num, value in enumerate(self._lines):
            if miny <= y <= maxy + dy:
                texture = labels[line_num]
                if not texture:
                    y -= dy
                    continue
                size = list(texture.size)
                texc = texture.tex_coords[:]

                # calcul coordinate
                viewport_pos = sx, 0
                vw = self.width - self.padding_x * 2
                vh = self.height - self.padding_y * 2
                tw, th = map(float, size)
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

                texc = (tcx, tcy+tch, tcx+tcw, tcy+tch, tcx+tcw, tcy, tcx, tcy)

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
        dy = self.line_height + self._line_spacing
        rects = self._lines_rects
        y = self.top - self.padding_y + self.scroll_y
        miny = self.y + self.padding_y
        maxy = self.top - self.padding_y
        draw_selection = self._draw_selection
        for line_num, value in enumerate(self._lines):
            if miny <= y <= maxy + dy:
                r = rects[line_num]
                draw_selection(r.pos, r.size, line_num)
            y -= dy

    def _draw_selection(self, pos, size, line_num):
        # Draw the current selection on the widget.
        a, b = self.selection_from, self.selection_to
        if a > b:
            a, b = b, a
        s1c, s1r = self.get_cursor_from_index(a)
        s2c, s2r = self.get_cursor_from_index(b)
        if line_num < s1r or line_num > s2r:
            return
        x, y = pos
        w, h = size
        x1 = x
        x2 = x + w
        if line_num == s1r:
            lines = self._lines[line_num]
            x1 += self._get_text_width(lines[:s1c])
        if line_num == s2r:
            lines = self._lines[line_num]
            x2 = x + self._get_text_width(lines[:s2c])
        maxx = x + self.width - self.padding_x
        if x1 > maxx:
            return
        x2 = min(x2, self.x + self.width - self.padding_x)
        self.canvas.add(Color(*self.selection_color, group='selection'))
        self.canvas.add(Rectangle(
            pos=(x1, pos[1]), size=(x2 - x1, size[1]), group='selection'))

    def on_size(self, instance, value):
        # if the size change, we might do invalid scrolling / text split
        # size the text maybe be put after size_hint have been resolved.
        self._trigger_refresh_text()
        self.scroll_x = self.scroll_y = 0

    def _get_cursor_pos(self):
        # return the current cursor x/y from the row/col
        dy = self.line_height + self._line_spacing
        x = self.x + self.padding_x
        y = self.top - self.padding_y + self.scroll_y
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

    def _create_line_label(self, text):
        # Create a label from a text, using line options
        ntext = text.replace('\n', '').replace('\t', ' ' * self.tab_width)
        kw = self._get_line_options()
        cid = '%s\0%s' % (ntext, str(kw))
        texture = Cache.get('textinput.label', cid)
        if not texture:
            label = Label(text=ntext, **kw)
            label.refresh()
            texture = label.texture
            Cache.append('textinput.label', cid, texture)
        return texture

    def _tokenize(self, text):
        # Tokenize a text string from some delimiters
        if text is None:
            return
        delimiters = ' ,\'".;:\n\r\t'
        oldindex = 0
        for index, char in enumerate(text):
            if char not in delimiters:
                continue
            if oldindex != index:
                yield text[oldindex:index]
            yield text[index:index+1]
            oldindex = index+1
        yield text[oldindex:]

    def _split_smart(self, text):
        # Do a "smart" split. If autowidth or autosize is set,
        # we are not doing smart split, just a split on line break.
        # Otherwise, we are trying to split as soon as possible, to prevent
        # overflow on the widget.

        # depend of the options, split the text on line, or word
        if not self.multiline:
            lines = text.split('\n')
            lines_flags = [0] + [FL_IS_NEWLINE] * (len(lines) - 1)
            return lines, lines_flags

        # no autosize, do wordwrap.
        x = flags = 0
        line = []
        lines = []
        lines_flags = []
        width = self.width - self.padding_x * 2
        text_width = self._get_text_width

        # try to add each word on current line.
        for word in self._tokenize(text):
            is_newline = (word == '\n')
            w = text_width(word)
            # if we have more than the width, or if it's a newline,
            # push the current line, and create a new one
            if (x + w > width and line) or is_newline:
                lines.append(''.join(line))
                lines_flags.append(flags)
                flags = 0
                line = []
                x = 0
            if is_newline:
                flags |= FL_IS_NEWLINE
            else:
                x += w
                line.append(word)
        if line or flags & FL_IS_NEWLINE:
            lines.append(''.join(line))
            lines_flags.append(flags)

        return lines, lines_flags

    def _key_down(self, key, repeat=False):
        displayed_str, internal_str, internal_action, scale = key
        if internal_action is None:
            if self._selection:
                self.delete_selection()
            self.insert_text(displayed_str)
        elif internal_action in ('shift', 'shift_L', 'shift_R'):
            if not self._selection:
                self.selection_from = self.selection_to = self.cursor_index()
                self._selection = True
            self._selection_finished = False
        elif internal_action.startswith('cursor_'):
            self.do_cursor_movement(internal_action)
            if self._selection and not self._selection_finished:
                self.selection_to = self.cursor_index()
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
                self.do_backspace()
        elif internal_action == 'backspace':
            self.do_backspace()
        elif internal_action == 'enter':
            if self.multiline:
                self.insert_text('\n')
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
        global Clipboard
        if Clipboard is None:
            from kivy.core.clipboard import Clipboard

        is_osx = sys.platform == 'darwin'
        # Keycodes on OSX:
        ctrl, cmd = 64, 1024
        key, key_str = keycode

        if text and not key in (self.interesting_keys.keys() + [27]):
            # This allows *either* ctrl *or* cmd, but not both.
            if modifiers == ['ctrl'] or (is_osx and modifiers == ['meta']):
                if key == ord('x'): # cut selection
                    Clipboard.put(self.selection_text, 'text/plain')
                    self.delete_selection()
                elif key == ord('c'): # copy selection
                    Clipboard.put(self.selection_text, 'text/plain')
                elif key == ord('v'): # paste selection
                    data = Clipboard.get('text/plain')
                    if data:
                        self.delete_selection()
                        self.insert_text(data)
                elif key == ord('a'): # select all
                    self.selection_from = 0
                    self.selection_to = len(self.text)
                    self._update_selection(True)
            else:
                if self._selection:
                    self.delete_selection()
                self.insert_text(text)
            #self._recalc_size()
            return

        if key == 27: # escape
            self.focus = False
            return True
        elif key == 9: # tab
            self.insert_text('\t')
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

    #
    # Properties
    #

    _lines = ListProperty([])

    multiline = BooleanProperty(True)
    '''If True, the widget will be able show multiple lines of text. If false,
    "enter" action will defocus the textinput instead of adding a new line.

    :data:`multiline` is a :class:`~kivy.properties.BooleanProperty`, default to
    True
    '''

    cursor_blink = BooleanProperty(False)
    '''This property is used to blink the cursor graphics. The value of
    :data:`cursor_blink` is automatically computed, setting a value on it will
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
        viewport_width = self.width - self.padding_x * 2
        sx = self.scroll_x
        offset = self.cursor_offset()

        # if offset is outside the current bounds, reajust
        if offset > viewport_width + sx:
            self.scroll_x = offset - viewport_width
        if offset < sx:
            self.scroll_x = offset

        # do the same for Y
        # this algo try to center the cursor as much as possible
        dy = self.line_height + self._line_spacing
        offsety = cr * dy
        sy = self.scroll_y
        viewport_height = self.height - self.padding_y * 2 - dy
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
    '''By default, each tab will be replaced by the size of 4 spaces on the text
    input widget. You can set a lower or higher value.

    :data:`tab_width` is a :class:`~kivy.properties.NumericProperty`, default to
    4.
    '''

    padding_x = NumericProperty(0)
    '''Horizontal padding of the text, inside the widget box.

    :data:`padding_x` is a :class:`~kivy.properties.NumericProperty`, default to
    0. This might be changed by the current theme.
    '''

    padding_y = NumericProperty(0)
    '''Vertical padding of the text, inside the widget box.

    :data:`padding_x` is a :class:`~kivy.properties.NumericProperty`, default to
    0. This might be changed by the current theme.
    '''

    padding = ReferenceListProperty(padding_x, padding_y)
    '''Padding of the text, in the format (padding_x, padding_y)

    :data:`padding` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:data:`padding_x`, :data:`padding_y`) properties.
    '''

    scroll_x = NumericProperty(0)
    '''X scrolling value of the viewport. The scrolling is automatically updated
    when the cursor is moving or text is changing. If you are not doing any
    action, you can still change the scroll_x and scroll_y properties.

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
        the selection is drawed after the text.

    :data:`selection_color` is a :class:`~kivy.properties.ListProperty`, default
    to [0.1843, 0.6549, 0.8313, .5]
    '''

    selection_from = NumericProperty(None, allownone=True)
    '''If a selection is happening, or finished, this property will represent
    the cursor index where the selection start.

    :data:`selection_from` is a :class:`~kivy.properties.NumericProperty`,
    default to None
    '''

    selection_to = NumericProperty(None, allownone=True)
    '''If a selection is happening, or finished, this property will represent
    the cursor index where the selection end.

    :data:`selection_to` is a :class:`~kivy.properties.NumericProperty`,
    default to None
    '''

    selection_text = StringProperty('')
    '''Current content selection.

    :data:`selection_text` is a :class:`~kivy.properties.StringProperty`,
    default to ''
    '''

    focus = BooleanProperty(False)
    '''If focus is true, the keyboard will be requested, and you can start to
    write on the textinput.

    :data:`focus` is a :class:`~kivy.properties.BooleanProperty`, default to
    False
    '''

    def _get_text(self):
        lf = self._lines_flags
        l = self._lines
        text = ''.join([('\n' if (lf[i] & FL_IS_NEWLINE) else '') + l[i] \
                        for i in xrange(len(l))])
        return text

    def _set_text(self, text):
        if self.text == text:
            return
        self._refresh_text(text)
        self.cursor = self.get_cursor_from_index(len(text))

    text = AliasProperty(_get_text, _set_text, bind=('_lines', ))
    '''Text of the widget.

    Creation of a simple hello world ::

        widget = TextInput(text='Hello world')

    If you want to create the widget with an unicode string, use ::

        widget = TextInput(text=u'My unicode string')

    :data:`text` a :class:`~kivy.properties.StringProperty`.
    '''

    font_name = StringProperty('DroidSans')
    '''Filename of the font to use, the path can be absolute or relative.
    Relative paths are resolved by the :func:`~kivy.resources.resource_find`
    function.

    .. warning::

        Depending of your text provider, the font file can be ignored. However
        you can mostly use this without trouble.

        If the font used lacks the glyphs for the perticular language/symbols
        you are using, you will see '[]' blank box characters instead of the
        actual glyphs. The solution is to use a font that has the glyphs you
        need to display. For example to display |unicodechar|, use a font like
        freesans.ttf that has the glyph.

        .. |unicodechar| image:: images/unicode-char.png

    :data:`font_name` is a :class:`~kivy.properties.StringProperty`, default to
    'DroidSans'.
    '''

    font_size = NumericProperty(10)
    '''Font size of the text, in pixels.

    :data:`font_size` is a :class:`~kivy.properties.NumericProperty`, default to
    10.
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
