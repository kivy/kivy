'''
uix.textinput tests
========================
'''

import unittest

from kivy.uix.textinput import TextInput


class UixGridLayoutTest(unittest.TestCase):

    def test_focusable_when_disabled(self):
        ti = TextInput()
        ti.disabled = True
        ti.focused = True
        ti.bind(focus=self.on_focused)

    def on_focused(self, instance, value):
        print instance.focused
        self.assertTrue(instance.focused, value)
