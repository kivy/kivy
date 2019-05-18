import unittest
from kivy.uix.stacklayout import StackLayout
from kivy.uix.widget import Widget


class PaddingSpacingTestCase(unittest.TestCase):
    def test_tb_lr_stacklayout(self):
        stacklayout = StackLayout(
            orientation='tb-lr',
            size=(200, 200),
            padding=20,
            spacing=10)

        widget = Widget(width=100, size_hint=(0.2, 0.4))
        stacklayout.add_widget(widget)
        stacklayout.do_layout()

        self.assertEqual(stacklayout.top - widget.top, 20)
