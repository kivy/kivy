'''
uix.textinput tests
========================
'''

import unittest
from itertools import count

from kivy.core.window import Window
from kivy.tests.common import GraphicUnitTest, UTMotionEvent
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.clock import Clock

touch_id = count()


class TextInputTest(unittest.TestCase):

    def test_focusable_when_disabled(self):
        ti = TextInput()
        ti.disabled = True
        ti.focused = True
        ti.bind(focus=self.on_focused)

    def on_focused(self, instance, value):
        self.assertTrue(instance.focused, value)

    def test_wordbreak(self):
        self.test_txt = "Firstlongline\n\nSecondveryverylongline"

        ti = TextInput(width='30dp', size_hint_x=None)
        ti.bind(text=self.on_text)
        ti.text = self.test_txt

    def on_text(self, instance, value):
        # Check if text is modified while recreating from lines and lines_flags
        self.assertEqual(instance.text, self.test_txt)

        # Check if wordbreaking is correctly done
        # If so Secondvery... should start from the 7th line
        pos_S = self.test_txt.index('S')
        self.assertEqual(instance.get_cursor_from_index(pos_S), (0, 6))


class TextInputIMETest(unittest.TestCase):

    def test_ime(self):
        empty_ti = TextInput()
        empty_ti.focused = True
        ti = TextInput(text='abc')
        Window.dispatch('on_textedit', 'ㅎ')
        self.assertEqual(empty_ti.text, 'ㅎ')
        self.assertEqual(ti.text, 'abc')
        ti.focused = True
        Window.dispatch('on_textedit', 'ㅎ')
        self.assertEqual(ti.text, 'abcㅎ')
        Window.dispatch('on_textedit', '하')
        self.assertEqual(ti.text, 'abc하')
        Window.dispatch('on_textedit', '핫')
        Window.dispatch('on_textedit', '')
        Window.dispatch('on_textinput', '하')
        Window.dispatch('on_textedit', 'ㅅ')
        Window.dispatch('on_textedit', '세')
        self.assertEqual(ti.text, 'abc하세')


class TextInputGraphicTest(GraphicUnitTest):
    def test_text_validate(self):
        ti = TextInput(multiline=False)
        ti.focus = True

        self.render(ti)
        self.assertFalse(ti.multiline)
        self.assertTrue(ti.focus)
        self.assertTrue(ti.text_validate_unfocus)

        ti.validate_test = None

        ti.bind(on_text_validate=lambda *_: setattr(
            ti, 'validate_test', True
        ))
        ti._key_down(
            (
                None,     # displayed_str
                None,     # internal_str
                'enter',  # internal_action
                1         # scale
            ),
            repeat=False
        )
        self.assertTrue(ti.validate_test)
        self.assertFalse(ti.focus)

        ti.validate_test = None
        ti.text_validate_unfocus = False
        ti.focus = True
        self.assertTrue(ti.focus)

        ti._key_down(
            (None, None, 'enter', 1),
            repeat=False
        )
        self.assertTrue(ti.validate_test)
        self.assertTrue(ti.focus)

    def test_selection_enter_multiline(self):
        text = 'multiline\ntext'
        ti = TextInput(multiline=True, text=text)
        ti.focus = True

        self.render(ti)
        self.assertTrue(ti.focus)

        # assert cursor is here:
        # multiline
        # text$
        self.assertEqual(
            ti.cursor, (
                len(text.split('\n')[-1]),
                len(text.split('\n')) - 1
            )
        )

        # move and check position
        # mult$iline
        # text
        ti._key_down(     # push selection
            (
                None,     # displayed_str
                None,     # internal_str
                'shift',  # internal_action
                1         # scale
            ),
            repeat=False
        )
        ti._key_down(
            (None, None, 'cursor_up', 1),
            repeat=False
        )
        # pop selection
        ti._key_up(
            (None, None, 'shift', 1),
            repeat=False
        )
        self.assertEqual(
            ti.cursor, (
                len(text.split('\n')[-1]),
                len(text.split('\n')) - 2
            )
        )
        self.assertEqual(ti.text, text)

        # overwrite selection with \n
        ti._key_down(
            (None, None, 'enter', 1),
            repeat=False
        )
        self.assertEqual(ti.text, text[:4] + '\n')

    def test_selection_enter_singleline(self):
        text = 'singleline'
        ti = TextInput(multiline=False, text=text)
        ti.focus = True

        self.render(ti)
        self.assertTrue(ti.focus)

        # assert cursor is here:
        # singleline$
        self.assertEqual(ti.cursor, (len(text), 0))

        # move and check position
        # single$line
        steps = 4
        options = ((
            'enter',
            text
        ), (
            'backspace',
            text[:len(text) - steps]
        ))
        for key, txt in options:
            # push selection
            ti._key_down((None, None, 'shift', 1), repeat=False)
            for _ in range(steps):
                ti._key_down(
                    (None, None, 'cursor_left', 1),
                    repeat=False
                )

            # pop selection
            ti._key_up((None, None, 'shift', 1), repeat=False)
            self.assertEqual(
                ti.cursor, (len(text[:-steps]), 0)
            )
            self.assertEqual(ti.text, text)

            # try to overwrite selection with \n
            # (shouldn't work because single line)
            ti._key_down(
                (None, None, key, 1),
                repeat=False
            )
            self.assertEqual(ti.text, txt)
            ti._key_down((None, None, 'cursor_end', 1), repeat=False)

    def test_del(self):
        text = 'some_random_text'
        ti = TextInput(multiline=False, text=text)
        ti.focus = True

        self.render(ti)
        self.assertTrue(ti.focus)

        # assert cursor is here:
        self.assertEqual(ti.cursor, (len(text), 0))

        steps_skip = 2
        steps_select = 4
        del_key = 'del'

        for _ in range(steps_skip):
            ti._key_down(
                (None, None, 'cursor_left', 1),
                repeat=False
            )
        # cursor at the place of ^
        # some_random_te^xt

        # push selection
        ti._key_down((None, None, 'shift', 1), repeat=False)
        for _ in range(steps_select):
            ti._key_down(
                (None, None, 'cursor_left', 1),
                repeat=False
            )

        # pop selection
        ti._key_up((None, None, 'shift', 1), repeat=False)

        # cursor at the place of ^, selection between * chars
        # some_rando*^m_te*xt

        self.assertEqual(
            ti.cursor, (len(text[:-steps_select - steps_skip]), 0)
        )
        self.assertEqual(ti.text, text)

        ti._key_down(
            (None, None, del_key, 1),
            repeat=False
        )
        # cursor now at: some_rando^xt
        self.assertEqual(ti.text, 'some_randoxt')

        ti._key_down(
            (None, None, del_key, 1),
            repeat=False
        )
        self.assertEqual(ti.text, 'some_randot')

    def test_escape(self):
        text = 'some_random_text'
        escape_key = 'escape'
        ti = TextInput(multiline=False, text=text)
        ti.focus = True

        self.render(ti)
        self.assertTrue(ti.focus)

        ti._key_down(
            (None, None, escape_key, 1),
            repeat=False
        )
        self.assertFalse(ti.focus)
        self.assertEqual(ti.text, text)

    def test_no_shift_cursor_arrow_on_selection(self):
        text = 'some_random_text'
        ti = TextInput(multiline=False, text=text)
        ti.focus = True

        self.render(ti)
        self.assertTrue(ti.focus)

        # assert cursor is here:
        self.assertEqual(ti.cursor, (len(text), 0))

        steps_skip = 2
        steps_select = 4

        for _ in range(steps_skip):
            ti._key_down(
                (None, None, 'cursor_left', 1),
                repeat=False
            )
        # cursor at the place of ^
        # some_random_te^xt

        # push selection
        ti._key_down((None, None, 'shift', 1), repeat=False)
        for _ in range(steps_select):
            ti._key_down(
                (None, None, 'cursor_left', 1),
                repeat=False
            )

        # pop selection
        ti._key_up((None, None, 'shift', 1), repeat=False)

        # cursor at the place of ^, selection between * chars
        # some_rando*^m_te*xt

        ti._key_down(
            (None, None, 'cursor_right', 1),
            repeat=False
        )
        self.assertEqual(ti.cursor, (len(text) - steps_skip, 0))

    def test_cursor_movement_control(self):
        text = "these are\nmany words"
        ti = TextInput(multiline=True, text=text)

        ti.focus = True

        self.render(ti)
        self.assertTrue(ti.focus)

        # assert cursor is here:
        self.assertEqual(
            ti.cursor, (
                len(text.split('\n')[-1]),
                len(text.split('\n')) - 1
            )
        )

        options = (
                ('cursor_left', (5, 1)),
                ('cursor_left', (0, 1)),
                ('cursor_left', (6, 0)),
                ('cursor_right', (9, 0)),
                ('cursor_right', (4, 1)))

        for key, pos in options:
            ti._key_down((None, None, 'ctrl_L', 1), repeat=False)
            ti._key_down((None, None, key, 1), repeat=False)

            self.assertEqual(ti.cursor, pos)

            ti._key_up((None, None, 'ctrl_L', 1), repeat=False)

    def test_cursor_blink(self):
        ti = TextInput(cursor_blink=True)
        ti.focus = True

        # overwrite blinking event, because too long delay
        ti._do_blink_cursor_ev = Clock.create_trigger(
            ti._do_blink_cursor, 0.01, interval=True
        )

        self.render(ti)

        # from kwargs cursor_blink == True
        self.assertTrue(ti.cursor_blink)
        self.assertTrue(ti._do_blink_cursor_ev.is_triggered)

        # set whether to blink & check if resets
        ti.cursor_blink = False
        for i in range(30):
            self.advance_frames(int(0.01 * Clock._max_fps) + 1)
            self.assertFalse(ti._do_blink_cursor_ev.is_triggered)

            # no blinking, cursor visible
            self.assertFalse(ti._cursor_blink)

        ti.cursor_blink = True
        self.assertTrue(ti.cursor_blink)
        for i in range(30):
            self.advance_frames(int(0.01 * Clock._max_fps) + 1)
            self.assertTrue(ti._do_blink_cursor_ev.is_triggered)

    def test_visible_lines_range(self):
        ti = self.make_scrollable_text_input()
        assert ti._visible_lines_range == (20, 30)

        ti.height = ti_height_for_x_lines(ti, 2.5)
        ti.do_cursor_movement('cursor_home', control=True)
        self.advance_frames(1)
        assert ti._visible_lines_range == (0, 3)

        ti.height = ti_height_for_x_lines(ti, 0)
        self.advance_frames(1)
        assert ti._visible_lines_range == (0, 0)

    def test_keyboard_scroll(self):
        ti = self.make_scrollable_text_input()

        prev_cursor = ti.cursor
        ti.do_cursor_movement('cursor_home', control=True)
        self.advance_frames(1)
        assert ti._visible_lines_range == (0, 10)
        assert prev_cursor != ti.cursor

        prev_cursor = ti.cursor
        ti.do_cursor_movement('cursor_down', control=True)
        self.advance_frames(1)
        assert ti._visible_lines_range == (1, 11)
        # cursor position (col and row) should not be
        # changed by "ctrl + cursor_down" and "ctrl + cursor_up"
        assert prev_cursor == ti.cursor

        prev_cursor = ti.cursor
        ti.do_cursor_movement('cursor_up', control=True)
        self.advance_frames(1)
        assert ti._visible_lines_range == (0, 10)
        assert prev_cursor == ti.cursor

        prev_cursor = ti.cursor
        ti.do_cursor_movement('cursor_end', control=True)
        self.advance_frames(1)
        assert ti._visible_lines_range == (20, 30)
        assert prev_cursor != ti.cursor

    def test_scroll_doesnt_move_cursor(self):
        ti = self.make_scrollable_text_input()

        from kivy.base import EventLoop
        win = EventLoop.window
        touch = UTMotionEvent("unittest", next(touch_id), {
            "x": ti.center_x / float(win.width),
            "y": ti.center_y / float(win.height),
        })
        touch.profile.append('button')
        touch.button = 'scrolldown'

        prev_cursor = ti.cursor
        assert ti._visible_lines_range == (20, 30)
        EventLoop.post_dispatch_input("begin", touch)
        EventLoop.post_dispatch_input("end", touch)
        self.advance_frames(1)
        assert ti._visible_lines_range == (19, 29)
        assert ti.cursor == prev_cursor

    def test_vertical_scroll_doesnt_depend_on_lines_rendering(self):
        # TextInput.on_touch_down was checking the possibility to scroll_up
        # using the positions of the rendered lines' rects. These positions
        # don't change when the lines are skipped (e.g. during fast scroll
        # or ctrl+cursor_home) which lead to scroll freeze
        ti = self.make_scrollable_text_input()

        # move viewport to the first line
        ti.do_cursor_movement('cursor_home', control=True)
        self.advance_frames(1)
        assert ti._visible_lines_range == (0, 10)

        from kivy.base import EventLoop
        win = EventLoop.window

        # slowly scroll to the last line to render all lines at least once
        for _ in range(30):  # little overscroll is important for detection
            touch = UTMotionEvent("unittest", next(touch_id), {
                "x": ti.center_x / float(win.width),
                "y": ti.center_y / float(win.height),
            })
            touch.profile.append('button')
            touch.button = 'scrollup'

            EventLoop.post_dispatch_input("begin", touch)
            EventLoop.post_dispatch_input("end", touch)
            self.advance_frames(1)
        assert ti._visible_lines_range == (20, 30)

        # jump to the first line again
        ti.do_cursor_movement('cursor_home', control=True)

        # temp fix: only change of cursor position triggers update as for now
        ti._trigger_update_graphics()

        self.advance_frames(1)
        assert ti._visible_lines_range == (0, 10)

        # scrolling up should work now
        touch = UTMotionEvent("unittest", next(touch_id), {
            "x": ti.center_x / float(win.width),
            "y": ti.center_y / float(win.height),
        })
        touch.profile.append('button')
        touch.button = 'scrollup'
        EventLoop.post_dispatch_input("begin", touch)
        EventLoop.post_dispatch_input("end", touch)
        self.advance_frames(1)
        assert ti._visible_lines_range == (1, 11)

    def test_selectall_copy_paste(self):
        text = 'test'
        ti = TextInput(multiline=False, text=text)
        ti.focus = True
        self.render(ti)

        from kivy.base import EventLoop
        win = EventLoop.window

        # select all
        # win.dispatch(event_name, key, scancode, kstr, modifiers)
        win.dispatch('on_key_down', 97, 4, 'a', ['capslock', 'ctrl'])
        win.dispatch('on_key_up', 97, 4)
        self.advance_frames(1)

        # copy
        win.dispatch('on_key_down', 99, 6, 'c',
                     ['capslock', 'numlock', 'ctrl'])
        win.dispatch('on_key_up', 99, 6)
        self.advance_frames(1)

        # home
        win.dispatch('on_key_down', 278, 74, None, ['capslock'])
        win.dispatch('on_key_up', 278, 74)
        self.advance_frames(1)

        # paste
        win.dispatch('on_key_down', 118, 25, 'v', ['numlock', 'ctrl'])
        win.dispatch('on_key_up', 118, 25)
        self.advance_frames(1)

        assert ti.text == 'testtest'

    def make_scrollable_text_input(self, num_of_lines=30, n_lines_to_show=10):
        """Prepare and start rendering the scrollable text input.

           num_of_lines -- amount of dummy lines used as contents
           n_lines_to_show -- amount of lines to fit in viewport
        """
        # create TextInput instance with dummy contents
        text = '\n'.join(map(str, range(num_of_lines)))
        ti = TextInput(text=text)
        ti.focus = True

        # use container to have flexible TextInput size
        container = Widget()
        container.add_widget(ti)
        self.render(container)

        # change TextInput's size to contain the needed amount of lines
        ti.height = ti_height_for_x_lines(ti, n_lines_to_show)
        self.advance_frames(1)
        return ti


def ti_height_for_x_lines(ti, x):
    """Calculate TextInput height required to display x lines in viewport.

    ti -- TextInput object being used
    x -- number of lines to display
    """
    padding_top = ti.padding[1]
    padding_bottom = ti.padding[3]
    return int((ti.line_height + ti.line_spacing) * x
               + padding_top + padding_bottom)


if __name__ == '__main__':
    import unittest
    unittest.main()
