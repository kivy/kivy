import unittest

from kivy.vector import Vector
from operator import truediv


class VectorTestCase(unittest.TestCase):
    def test_initializer_oneparameter_as_list(self):
        vector = Vector([1])
        self.assertEqual(vector.x, 1)
        with self.assertRaises(IndexError):
            vector.y

    def test_initializer_oneparameter_as_int(self):
        with self.assertRaises(TypeError):
            Vector(1)

    def test_initializer_twoparameters(self):
        vector = Vector(1, 2)
        self.assertEqual(vector.x, 1)
        self.assertEqual(vector.y, 2)

    def test_initializer_noparameter(self):
        with self.assertRaises(Exception):
            Vector()

    def test_initializer_threeparameters(self):
        with self.assertRaises(Exception):
            Vector(1, 2, 3)

    def test_sum_twovectors(self):
        finalVector = Vector(1, 1) + Vector(1, 1)
        self.assertEqual(finalVector.x, 2)
        self.assertEqual(finalVector.y, 2)

    def test_sum_inplace(self):
        finalVector = Vector(1, 1)
        finalVector += Vector(1, 1)
        self.assertEqual(finalVector.x, 2)
        self.assertEqual(finalVector.y, 2)

    def test_sum_inplace_scalar(self):
        finalVector = Vector(1, 1)
        finalVector += 1
        self.assertEqual(finalVector.x, 2)
        self.assertEqual(finalVector.y, 2)

    def test_sum_scalar(self):
        with self.assertRaises(TypeError):
            Vector(1, 1) + 1

    def test_sub_twovectors(self):
        finalVector = Vector(3, 3) - Vector(2, 2)
        self.assertEqual(finalVector.x, 1)
        self.assertEqual(finalVector.y, 1)

    def test_sub_inplace(self):
        finalVector = Vector(3, 3)
        finalVector -= Vector(2, 2)
        self.assertEqual(finalVector.x, 1)
        self.assertEqual(finalVector.y, 1)

    def test_sub_scalar(self):
        with self.assertRaises(TypeError):
            Vector(3, 3) - 2

    def test_sub_inplace_scalar(self):
        finalVector = Vector(3, 3)
        finalVector -= 2
        self.assertEqual(finalVector.x, 1)
        self.assertEqual(finalVector.y, 1)

    def test_mul_twovectors(self):
        finalVector = Vector(2, 2) * Vector(3, 3)
        self.assertEqual(finalVector.x, 6)
        self.assertEqual(finalVector.y, 6)

    def test_mul_inplace(self):
        finalVector = Vector(2, 2)
        finalVector *= Vector(3, 3)
        self.assertEqual(finalVector.x, 6)
        self.assertEqual(finalVector.y, 6)

    def test_mul_inplace_scalar(self):
        finalVector = Vector(2, 2)
        finalVector *= 3
        self.assertEqual(finalVector.x, 6)
        self.assertEqual(finalVector.y, 6)

    def test_mul_scalar(self):
        finalVector = Vector(2, 2) * 3
        self.assertEqual(finalVector.x, 6)
        self.assertEqual(finalVector.y, 6)

    def test_rmul_list(self):
        finalVector = (3, 3) * Vector(2, 2)
        self.assertEqual(finalVector.x, 6)
        self.assertEqual(finalVector.y, 6)

    def test_rmul_scalar(self):
        finalVector = 3 * Vector(2, 2)
        self.assertEqual(finalVector.x, 6)
        self.assertEqual(finalVector.y, 6)

    def test_div_twovectors(self):
        finalVector = Vector(6, 6) / Vector(2, 2)
        self.assertEqual(finalVector.x, 3)
        self.assertEqual(finalVector.y, 3)

    def test_truediv_twovectors(self):
        finalVector = truediv(Vector(6, 6), Vector(2., 2.))
        self.assertAlmostEqual(finalVector.x, 3.)
        self.assertAlmostEqual(finalVector.y, 3.)

    def test_truediv_scalar(self):
        finalVector = truediv(Vector(6, 6), 2.)
        self.assertAlmostEqual(finalVector.x, 3.)
        self.assertAlmostEqual(finalVector.y, 3.)

    def test_div_inplace(self):
        finalVector = Vector(6, 6)
        finalVector /= Vector(2, 2)
        self.assertEqual(finalVector.x, 3)
        self.assertEqual(finalVector.y, 3)

    def test_div_inplace_scalar(self):
        finalVector = Vector(6, 6)
        finalVector /= 2
        self.assertEqual(finalVector.x, 3)
        self.assertEqual(finalVector.y, 3)

    def test_div_scalar(self):
        finalVector = Vector(6, 6) / 2
        self.assertEqual(finalVector.x, 3)
        self.assertEqual(finalVector.y, 3)

    def test_rdiv_list(self):
        finalVector = (6.0, 6.0) / Vector(3.0, 3.0)
        self.assertEqual(finalVector.x, 2)
        self.assertEqual(finalVector.y, 2)

    def test_rdiv_scalar(self):
        finalVector = 6 / Vector(3, 3)
        self.assertEqual(finalVector.x, 2)
        self.assertEqual(finalVector.y, 2)

    def test_sum_oversizedlist(self):
        Vector(6, 6) + (1, 2)

    def test_negation(self):
        vector = - Vector(1, 1)
        self.assertEqual(vector.x, -1)
        self.assertEqual(vector.y, -1)

    def test_length(self):
        length = Vector(10, 10).length()
        self.assertEqual(length, 14.142135623730951)

    def test_length_zerozero(self):
        length = Vector(0, 0).length()
        self.assertEqual(length, 0)

    def test_length2(self):
        length = Vector(10, 10).length2()
        self.assertEqual(length, 200)

    def test_distance(self):
        distance = Vector(10, 10).distance((5, 10))
        self.assertEqual(distance, 5)

    def test_distance2(self):
        distance = Vector(10, 10).distance2((5, 10))
        self.assertEqual(distance, 25)

    def test_normalize(self):
        vector = Vector(88, 33).normalize()
        self.assertAlmostEqual(vector.x, 0.93632917756904444)
        self.assertAlmostEqual(vector.y, 0.3511234415883917)
        self.assertAlmostEqual(vector.length(), 1.0)

    def test_normalize_zerovector(self):
        vector = Vector(0, 0).normalize()
        self.assertEqual(vector.x, 0)
        self.assertEqual(vector.y, 0)
        self.assertEqual(vector.length(), 0)

    def test_dot(self):
        result = Vector(2, 4).dot((2, 2))
        self.assertEqual(result, 12)

    def test_angle(self):
        result = Vector(100, 0).angle((0, 100))
        self.assertAlmostEqual(result, -90.0)

    def test_rotate(self):
        v = Vector(100, 0)
        v = v.rotate(45)
        self.assertAlmostEqual(v.x, 70.710678118654755)
        self.assertAlmostEqual(v.y, 70.710678118654741)

    def test_(self):
        a = (98, 28)
        b = (72, 33)
        c = (10, -5)
        d = (20, 88)
        result = Vector.line_intersection(a, b, c, d)
        self.assertAlmostEqual(result.x, 15.25931928687196)
        self.assertAlmostEqual(result.y, 43.911669367909241)

    def test_inbbox(self):
        bmin = (0, 0)
        bmax = (100, 100)
        result = Vector.in_bbox((50, 50), bmin, bmax)
        self.assertTrue(result)
        result = Vector.in_bbox((647, -10), bmin, bmax)
        self.assertFalse(result)
