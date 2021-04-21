from itertools import product

from kivy.tests import GraphicUnitTest


class WindowBaseTest(GraphicUnitTest):

    def test_to_normalized_pos(self):
        old_system_size = self.Window.system_size[:]
        self.Window.system_size = w, h = (320, 240)
        try:
            for x, y in product([0, 319, 50, 51], [0, 239, 50, 51]):
                expected_sx = x / (w - 1.0)
                expected_sy = y / (h - 1.0)
                result_sx, result_sy = self.Window.to_normalized_pos(x, y)
                assert result_sx == expected_sx
                assert result_sy == expected_sy
        finally:
            self.Window.system_size = old_system_size
