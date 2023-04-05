import unittest
from kivy.gesture import Gesture, GestureDatabase
import string


class GestureTestCase(unittest.TestCase):

    class TestGesture(Gesture):
        ''' Define shorthand for gesture reference points as if it were a keypad
            of a phone. Assume a 3 x 3 grid, labeled '1', '2', '3' etc
        '''
        _keypad = {'1': (1, 1), '2': (0, 1), '3': (-1, 1),
                   '4': (1, 0), '5': (0, 0), '6': (-1, 0),
                   '7': (1, -1), '8': (0, -1), '9': (-1, -1)
                   }

        def __init__(self, tolerance=None, name=None, points=None):
            super().__init__(tolerance)
            if name is not None:
                self.name = name

            if isinstance(points, int):
                points = str(points)
            if isinstance(points, str):
                points = list(map(lambda x: self._keypad[x], str(points)))
            if isinstance(points, list):
                self.add_stroke(point_list=points)
                self.normalize()

    def test_horizontal_gesture(self):
        assert self.TestGesture(points=13) == self.TestGesture(points=12)
        assert self.TestGesture(points=13) == self.TestGesture(points=46)
        assert self.TestGesture(points=13) == self.TestGesture(points=79)

    def test_vertical_gesture(self):
        assert self.TestGesture(points=17) == self.TestGesture(points=28)
        assert self.TestGesture(points=17) == self.TestGesture(points=39)
        assert self.TestGesture(points=17) == self.TestGesture(points=14)

    def test_diagonal_gesture(self):
        assert self.TestGesture(points=19) == self.TestGesture(points=26)
        assert self.TestGesture(points=19) == self.TestGesture(points=48)
        assert self.TestGesture(points=19) == self.TestGesture(points=15)
        assert self.TestGesture(points=37) == self.TestGesture(points=24)
        assert self.TestGesture(points=37) == self.TestGesture(points=68)
        assert self.TestGesture(points=37) == self.TestGesture(points=35)

    def test_3valued_gesture(self):
        assert self.TestGesture(points=13) == self.TestGesture(points=123)
        assert self.TestGesture(points=17) == self.TestGesture(points=147)
        assert self.TestGesture(points=19) == self.TestGesture(points=159)

    def test_reversed_gesture(self):
        assert self.TestGesture(points=13) != self.TestGesture(points=31)
        assert self.TestGesture(points=17) != self.TestGesture(points=71)
        assert self.TestGesture(points=19) != self.TestGesture(points=91)

    def test_scaled_gesture(self):
        assert self.TestGesture(points=13) == \
            self.TestGesture(points=[(100, 100), (0, 100)])
        assert self.TestGesture(points=17) == \
            self.TestGesture(points=[(100, 100), (100, 0)])
        assert self.TestGesture(points=19) == \
            self.TestGesture(points=[(100, 100), (0, 0)])


if __name__ == '__main__':
    unittest.main()
