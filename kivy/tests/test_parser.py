import unittest
from unittest.mock import patch

from kivy.parser import parse_color


class ParseColorTest(unittest.TestCase):

    def test_excess_components_use_invalid_color_fallback(self):
        for color in ('rgb(1, 2, 3, 4, 5)', 'rgba(1, 2, 3, 4, 5, 6)'):
            with self.subTest(color=color):
                with patch('kivy.parser.Logger.warning') as warning:
                    self.assertEqual(parse_color(color), (0, 0, 0, 1))
                    warning.assert_called_once_with(
                        'ColorParser: Invalid color for %r' % color)

    def test_missing_components_use_invalid_color_fallback(self):
        with patch('kivy.parser.Logger.warning') as warning:
            self.assertEqual(parse_color('rgb(1, 2)'), (0, 0, 0, 1))
            warning.assert_called_once()

    def test_valid_colors(self):
        for color, expected in [
                ('rgb(255, 0, 0)', [1., 0., 0., 1.]),
                ('rgba(255, 0, 0, 128)', [1., 0., 0., 128 / 255.]),
                ('rgb(255, 0, 0, 128)', [1., 0., 0., 128 / 255.]),
                ('#ff0000', [1., 0., 0., 1.])]:
            with self.subTest(color=color):
                with patch('kivy.parser.Logger.warning') as warning:
                    self.assertEqual(parse_color(color), expected)
                    warning.assert_not_called()


if __name__ == '__main__':
    unittest.main()
