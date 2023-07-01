from itertools import product

from kivy.tests import GraphicUnitTest


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

    def test_window_opacity_property(self):
        window = self.Window
        opacity = 0.5
        window.opacity = opacity
        self.assertEqual(window.opacity, opacity)

        from kivy.logger import LoggerHistory

        window.opacity = 15
        self.assertEqual(LoggerHistory.history[0].msg,
                         'Window: The opacity value of '
                         'the window should be in the '
                         'range from 0.0 to 1.0.')

        LoggerHistory.clear_history()

        window.opacity = -15
        assert len(LoggerHistory.history) == 1
