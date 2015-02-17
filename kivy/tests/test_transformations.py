import unittest

from kivy.graphics.transformation import Matrix


class TransformationsTestCase(unittest.TestCase):
    def test_dot(self):
        """ Placeholder we probably should have tests, currently need
        get and set methods merging to test but then we can do
        something like the test below but this is nonsense currently"""
        matrix1 = Matrix()
        matrix2 = Matrix()

        result = matrix1.dot(
            Matrix.set([
                [2.08721089, 0.0, 0.0, 0.0],
                [0.0, 2.14450693, 0.0, 0.0],
                [0.0, 0.0, -1.66666663, -1.0],
                [0.0, 0.0, -53.33333206, 0.0]]))
        self.assertEqual(result.get(), [
            [2.08721089, 0.0, 0.0, 0.0],
            [0.0, 2.14450693, 0.0, 0.0],
            [0.0, 0.0, -1.66666663, -1.0],
            [0.0, 0.0, -53.33333206, 0.0]])
