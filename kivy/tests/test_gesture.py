import unittest

from kivy.gesture import Gesture, GestureDatabase


class GestureTestCase(unittest.TestCase):
    def setUp(self):
        self.gesture = Gesture()
        self.gesture.add_stroke([(0, 0), (1, 3), (4, 1), (5, 4), (7, 0)])
        self.gesture.normalize()
        self.rotated = self.gesture.rotate(90)

    def test_identical_gesture_score(self):
        self.assertAlmostEqual(self.gesture.get_score(self.gesture), 1.0)

    def test_rotation_sensitive_score(self):
        self.assertAlmostEqual(
            self.gesture.get_score(self.rotated, rotation_invariant=False),
            0.0)

    def test_rigid_rotation_uses_both_gestures(self):
        self.assertAlmostEqual(
            self.gesture.get_rigid_rotation(self.rotated), -90.0)

    def test_rotation_invariant_score(self):
        self.assertAlmostEqual(self.gesture.get_score(self.rotated), 1.0)

    def test_database_finds_rotated_gesture_by_default(self):
        database = GestureDatabase()
        database.add_gesture(self.gesture)
        match = database.find(self.rotated)
        self.assertIsNotNone(match)
        self.assertAlmostEqual(match[0], 1.0)
        self.assertIs(match[1], self.gesture)

    def test_empty_gesture_rotation(self):
        empty = Gesture()
        self.assertEqual(empty.get_rigid_rotation(self.gesture), 0)
        self.assertEqual(self.gesture.get_rigid_rotation(empty), 0)


if __name__ == '__main__':
    unittest.main()
