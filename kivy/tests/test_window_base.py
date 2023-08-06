from itertools import product

from kivy.tests import GraphicUnitTest
from kivy.logger import LoggerHistory


class WindowBaseTest(GraphicUnitTest):

    def test_to_normalized_pos(self):
        win = self.Window
        old_system_size = win.system_size[:]
        win.system_size = w, h = type(old_system_size)((320, 240))
        try:
            for x, y in product([0, 319, 50, 51], [0, 239, 50, 51]):
                expected_sx = x / (w - 1.0)
                expected_sy = y / (h - 1.0)
                result_sx, result_sy = win.to_normalized_pos(x, y)
                assert result_sx == expected_sx
                assert result_sy == expected_sy
        finally:
            win.system_size = old_system_size


class WindowOpacityTest(GraphicUnitTest):

    def setUp(self):
        super().setUp()
        self._prev_window_opacity = self.Window.opacity
        self._prev_history = LoggerHistory.history[:]

    def tearDown(self):
        self.Window.opacity = self._prev_window_opacity
        LoggerHistory.history[:] = self._prev_history
        super().tearDown()

    def check_opacity_support(self):
        LoggerHistory.clear_history()
        self.Window.opacity = 0.2
        return not LoggerHistory.history

    def test_window_opacity_property(self):
        if self.check_opacity_support():
            opacity = 0.5
            self.Window.opacity = opacity
            self.assertEqual(self.Window.opacity, opacity)

    def test_window_opacity_clamping_positive(self):
        if self.check_opacity_support():
            self.Window.opacity = 1.5
            self.assertEqual(self.Window.opacity, 1.0)

    def test_window_opacity_clamping_negative(self):
        if self.check_opacity_support():
            self.Window.opacity = -1.5
            self.assertEqual(self.Window.opacity, 0.0)
