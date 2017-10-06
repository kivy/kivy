'''
uix.textinput tests
========================
'''

import unittest

from kivy.tests.common import GraphicUnitTest
from kivy.uix.textinput import TextInput


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
        self.assertEquals(instance.text, self.test_txt)

        # Check if wordbreaking is correctly done
        # If so Secondvery... should start from the 7th line
        pos_S = self.test_txt.index('S')
        self.assertEquals(instance.get_cursor_from_index(pos_S), (0, 6))


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


if __name__ == '__main__':
    import unittest
    unittest.main()
