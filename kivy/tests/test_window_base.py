from itertools import product

from kivy.tests import GraphicUnitTest


class WindowBaseTest(GraphicUnitTest):

    def test_to_normalized_pos(self):
        for x, y in product([0, 319, 50, 51], [0, 239, 50, 51]):
            self.Window.system_size = (320, 240)
            w, h = self.Window.system_size
            expected_sx = x / (w - 1.0)
            expected_sy = y / (h - 1.0)
            result_sx, result_sy = self.Window.to_normalized_pos(x, y)
            assert result_sx == expected_sx
            assert result_sy == expected_sy
