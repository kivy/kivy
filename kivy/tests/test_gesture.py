import unittest
from kivy.gesture import Gesture, GestureDatabase
import string


class GestureTestCase(unittest.TestCase):

    def test_horizontal_gesture(self):
        assert Gesture(point_list=13) == Gesture(point_list=12)
        assert Gesture(point_list=13) == Gesture(point_list=46)
        assert Gesture(point_list=13) == Gesture(point_list=79)

    def test_vertical_gesture(self):
        assert Gesture(point_list=17) == Gesture(point_list=28)
        assert Gesture(point_list=17) == Gesture(point_list=39)
        assert Gesture(point_list=17) == Gesture(point_list=14)

    def test_diagonal_gesture(self):
        assert Gesture(point_list=19) == Gesture(point_list=26)
        assert Gesture(point_list=19) == Gesture(point_list=48)
        assert Gesture(point_list=19) == Gesture(point_list=15)
        assert Gesture(point_list=37) == Gesture(point_list=24)
        assert Gesture(point_list=37) == Gesture(point_list=68)
        assert Gesture(point_list=37) == Gesture(point_list=35)

    def test_3valued_gesture(self):
        assert Gesture(point_list=13) == Gesture(point_list=123)
        assert Gesture(point_list=17) == Gesture(point_list=147)
        assert Gesture(point_list=19) == Gesture(point_list=159)

    def test_reversed_gesture(self):
        assert Gesture(point_list=13) != Gesture(point_list=31)
        assert Gesture(point_list=17) != Gesture(point_list=71)
        assert Gesture(point_list=19) != Gesture(point_list=91)

    def test_scaled_gesture(self):
        assert Gesture(point_list=13) == \
            Gesture(point_list=[(100, 100), (0, 100)])
        assert Gesture(point_list=17) == \
            Gesture(point_list=[(100, 100), (100, 0)])
        assert Gesture(point_list=19) == \
            Gesture(point_list=[(100, 100), (0, 0)])


if __name__ == '__main__':
    unittest.main()
