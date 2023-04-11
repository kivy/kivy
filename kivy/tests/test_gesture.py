import unittest
from kivy.gesture import Gesture, GestureDatabase
import string


class GestureTestCase(unittest.TestCase):

    def test_horizontal_gesture(self):
        assert Gesture(points=13) == Gesture(points=12)
        assert Gesture(points=13) == Gesture(points=46)
        assert Gesture(points=13) == Gesture(points=79)

    def test_vertical_gesture(self):
        assert Gesture(points=17) == Gesture(points=28)
        assert Gesture(points=17) == Gesture(points=39)
        assert Gesture(points=17) == Gesture(points=14)

    def test_diagonal_gesture(self):
        assert Gesture(points=19) == Gesture(points=26)
        assert Gesture(points=19) == Gesture(points=48)
        assert Gesture(points=19) == Gesture(points=15)
        assert Gesture(points=37) == Gesture(points=24)
        assert Gesture(points=37) == Gesture(points=68)
        assert Gesture(points=37) == Gesture(points=35)

    def test_3valued_gesture(self):
        assert Gesture(points=13) == Gesture(points=123)
        assert Gesture(points=17) == Gesture(points=147)
        assert Gesture(points=19) == Gesture(points=159)

    def test_reversed_gesture(self):
        assert Gesture(points=13) != Gesture(points=31)
        assert Gesture(points=17) != Gesture(points=71)
        assert Gesture(points=19) != Gesture(points=91)

    def test_scaled_gesture(self):
        assert Gesture(points=13) == \
            Gesture(points=[(100, 100), (0, 100)])
        assert Gesture(points=17) == \
            Gesture(points=[(100, 100), (100, 0)])
        assert Gesture(points=19) == \
            Gesture(points=[(100, 100), (0, 0)])


if __name__ == '__main__':
    unittest.main()
