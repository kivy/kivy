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
