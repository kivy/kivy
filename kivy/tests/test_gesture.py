import unittest
from kivy.gesture import Gesture, GestureDatabase
import string
import random


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
            Gesture(point_list=[(0, 100), (100, 100)])
        assert Gesture(point_list=17) == \
            Gesture(point_list=[(100, 100), (100, 0)])
        assert Gesture(point_list=19) == \
            Gesture(point_list=[(0, 100), (100, 0)])


class GestureDatabaseTestCase(unittest.TestCase):
    _strokes = {
        'right': 13,
        'left': 31,
        'down': 14,
        'up': 41,
        '3down': 7297,
        '3up': 1381,
        '3left': 1671,
        '3right': 4394,
        'V': 183,
        'V-inv': 729,
        'box-1': 13971,
        'box-3': 39713,
        'box-9': 97139,
        'box-7': 71397,
        'box-1-ccw': 17931,
        'box-3-ccw': 31793,
        'box-9-ccw': 93179,
        'box-7-ccw': 79317,
        'W': 17593,
        'M': 71539,
        'N': 7193,
        'Sigma': 31579
    }

    def setUp(self):
        # initialize database
        self.gestureDb = GestureDatabase()
        for name, points in self._strokes.items():
            self.gestureDb.add_gesture(Gesture(name=name, point_list=points))

    def test_gesture_database(self):
        # find all strokes in database
        for name, points in self._strokes.items():
            stroke = self.gestureDb.find(Gesture(point_list=points), 0.95,
                                         False)
            assert stroke[1].name == name

    def test_gesture_robustness(self):
        random.seed(a=1)
        amp = 0.1
        points = ((-1 + random.uniform(-amp, amp), random.uniform(-amp, amp)),
                  (random.uniform(-amp, amp), random.uniform(-amp, amp)))
        stroke = self.gestureDb.find(Gesture(point_list=points), 0.9, False)
        assert stroke[1].name == 'right'

        points = ((random.uniform(-amp, amp), random.uniform(-amp, amp)),
                  (random.uniform(-amp, amp), -1 + random.uniform(-amp, amp)))
        stroke = self.gestureDb.find(Gesture(point_list=points), 0.9, False)
        assert stroke[1].name == 'down'


if __name__ == '__main__':
    unittest.main()
