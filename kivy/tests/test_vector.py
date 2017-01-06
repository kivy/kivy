import unittest
from hypothesis import given
from hypothesis.strategies import integers, floats

from kivy.vector import Vector
from operator import truediv

inf = float('inf')


class VectorTestCase(unittest.TestCase):
    def test_initializer_oneparameter_as_list(self):
        vector = Vector([1])
        self.assertEqual(vector.x, 1)
        with self.assertRaises(IndexError):
            vector.y

    def test_initializer_oneparameter_as_int(self):
        with self.assertRaises(TypeError):
            Vector(1)

    @given(integers(), integers())
    def test_initializer_twoparameters(self, a, b):
        vector = Vector(a, b)
        self.assertEqual(vector.x, a)
        self.assertEqual(vector.y, b)

    def test_initializer_noparameter(self):
        with self.assertRaises(Exception):
            Vector()

    def test_initializer_threeparameters(self):
        with self.assertRaises(Exception):
            Vector(1, 2, 3)

    @given(integers(), integers(), integers(), integers())
    def test_sum_twovectors(self, a, b, c, d):
        finalVector = Vector(a, b) + Vector(c, d)
        self.assertEqual(finalVector.x, a + c)
        self.assertEqual(finalVector.y, b + d)

    @given(integers(), integers(), integers(), integers())
    def test_sum_inplace(self, a, b, c, d):
        finalVector = Vector(a, b)
        finalVector += Vector(c, d)
        self.assertEqual(finalVector.x, a + c)
        self.assertEqual(finalVector.y, b + d)

    @given(integers(), integers(), integers())
    def test_sum_inplace_scalar(self, a, b, c):
        finalVector = Vector(a, b)
        finalVector += c
        self.assertEqual(finalVector.x, a + c)
        self.assertEqual(finalVector.y, b + c)

    @given(integers(), integers(), integers())
    def test_sum_scalar(self, a, b, c):
        with self.assertRaises(TypeError):
            Vector(a, b) + c

    @given(integers(), integers(), integers(), integers())
    def test_sub_twovectors(self, a, b, c, d):
        finalVector = Vector(a, b) - Vector(c, d)
        self.assertEqual(finalVector.x, a - c)
        self.assertEqual(finalVector.y, b - d)

    @given(integers(), integers(), integers(), integers())
    def test_sub_inplace(self, a, b, c, d):
        finalVector = Vector(a, b)
        finalVector -= Vector(c, d)
        self.assertEqual(finalVector.x, a - c)
        self.assertEqual(finalVector.y, b - d)

    @given(integers(), integers(), integers())
    def test_sub_scalar(self, a, b, c):
        with self.assertRaises(TypeError):
            Vector(a, b) - c

    @given(integers(), integers(), integers())
    def test_sub_inplace_scalar(self, a, b, c):
        finalVector = Vector(a, b)
        finalVector -= c
        self.assertEqual(finalVector.x, a - c)
        self.assertEqual(finalVector.y, b - c)

    @given(integers(), integers(), integers(), integers())
    def test_mul_twovectors(self, a, b, c, d):
        finalVector = Vector(a, b) * Vector(c, d)
        self.assertEqual(finalVector.x, a * c)
        self.assertEqual(finalVector.y, b * d)

    @given(integers(), integers(), integers(), integers())
    def test_mul_inplace(self, a, b, c, d):
        finalVector = Vector(a, b)
        finalVector *= Vector(c, d)
        self.assertEqual(finalVector.x, a * c)
        self.assertEqual(finalVector.y, b * d)

    @given(integers(), integers(), integers())
    def test_mul_inplace_scalar(self, a, b, c):
        finalVector = Vector(a, b)
        finalVector *= c
        self.assertEqual(finalVector.x, a * c)
        self.assertEqual(finalVector.y, b * c)

    @given(integers(), integers(), integers())
    def test_mul_scalar(self, a, b, c):
        finalVector = Vector(a, b) * c
        self.assertEqual(finalVector.x, a * c)
        self.assertEqual(finalVector.y, b * c)

    @given(integers(), integers(), integers(), integers())
    def test_rmul_list(self, a, b, c, d):
        finalVector = (a, b) * Vector(c, d)
        self.assertEqual(finalVector.x, a * c)
        self.assertEqual(finalVector.y, b * d)

    @given(integers(), integers(), integers())
    def test_rmul_scalar(self, a, b, c):
        finalVector = a * Vector(b, c)
        self.assertEqual(finalVector.x, a * b)
        self.assertEqual(finalVector.y, a * c)

    @given(integers(), integers(), integers(min_value=1), integers(min_value=1))
    def test_div_twovectors(self, a, b, c, d):
        finalVector = Vector(a, b) / Vector(c, d)
        self.assertEqual(finalVector.x, a / c)
        self.assertEqual(finalVector.y, b / d)

    @given(integers(), integers(), floats(min_value=.1), floats(min_value=.1))
    def test_truediv_twovectors(self, a, b, c, d):
        finalVector = truediv(Vector(a, b), Vector(c, d))
        self.assertAlmostEqual(finalVector.x, a / c)
        self.assertAlmostEqual(finalVector.y, b / d)

    @given(integers(), integers(), floats(min_value=.01, max_value=10. ** 100))
    def test_truediv_scalar(self, a, b, c):
        finalVector = truediv(Vector(a, b), c)
        self.assertAlmostEqual(finalVector.x, a / c)
        self.assertAlmostEqual(finalVector.y, b / c)

    @given(
        integers(), integers(),
        floats(min_value=.1, max_value=10. ** 100),
        floats(min_value=.1, max_value=10 ** 100)
    )
    def test_div_inplace(self, a, b, c, d):
        finalVector = Vector(a, b)
        finalVector /= Vector(c, d)
        self.assertEqual(finalVector.x, a / c)
        self.assertEqual(finalVector.y, b / d)

    @given(integers(), integers(), floats(min_value=.1, max_value=10. ** 100))
    def test_div_inplace_scalar(self, a, b, c):
        finalVector = Vector(a, b)
        finalVector /= c
        self.assertEqual(finalVector.x, a / c)
        self.assertEqual(finalVector.y, b / c)

    @given(integers(), integers(), floats(min_value=.1, max_value=10. ** 100))
    def test_div_scalar(self, a, b, c):
        finalVector = Vector(a, b) / c
        self.assertEqual(finalVector.x, a / c)
        self.assertEqual(finalVector.y, b / c)

    @given(
        floats(min_value=-inf), floats(min_value=-inf),
        floats(min_value=.1, max_value=10. ** 100),
        floats(min_value=.1, max_value=10. ** 100)
    )
    def test_rdiv_list(self, a, b, c, d):
        finalVector = (a, b) / Vector(c, d)
        self.assertEqual(finalVector.x, a / c)
        self.assertEqual(finalVector.y, b / d)

    @given(
        floats(min_value=-inf),
        floats(min_value=.1, max_value=10. ** 100),
        floats(min_value=.1, max_value=10. ** 100)
    )
    def test_rdiv_scalar(self, a, b, c):
        finalVector = a / Vector(b, c)
        self.assertEqual(finalVector.x, a / b)
        self.assertEqual(finalVector.y, a / c)

    @given(integers(), integers(), integers(), integers())
    def test_sum_oversizedlist(self, a, b, c, d):
        v = Vector(a, b) + (c, d)
        self.assertEqual(v.x, a + c)
        self.assertEqual(v.y, b + d)

    @given(integers(), integers())
    def test_negation(self, a, b):
        vector = - Vector(a, b)
        self.assertEqual(vector.x, - a)
        self.assertEqual(vector.y, - b)

    @given(integers(), integers())
    def test_length(self, a, b):
        length = Vector(a, b).length()
        self.assertEqual(length, (a ** 2 + b ** 2) ** .5)

    def test_length_zerozero(self):
        length = Vector(0, 0).length()
        self.assertEqual(length, 0)

    @given(integers(), integers())
    def test_length2(self, a, b):
        length = Vector(a, b).length2()
        self.assertEqual(length, (a ** 2 + b ** 2))

    # higher values can break the test, for small difference of result
    @given(
        floats(min_value=-10 ** 5, max_value=10 ** 5),
        floats(min_value=-10 ** 5, max_value=10 ** 5),
        floats(min_value=1, max_value=10 ** 10)
    )
    def test_distance(self, a, b, c):
        distance = Vector(a, b).distance((a - c, b))
        self.assertAlmostEqual(distance, c)

    @given(integers(), integers(), integers())
    def test_distance2(self, a, b, c):
        distance = Vector(a, b).distance2((a - c, b))
        self.assertEqual(distance, c ** 2)

    # need at least one value to be not 0
    @given(
        floats(min_value=-10. ** 100, max_value=10. ** 100),
        floats(min_value=0.1, max_value=10. ** 100)
    )
    def test_normalize(self, a, b):
        vector = Vector(a, b).normalize()
        l = (a ** 2 + b ** 2) ** .5
        self.assertAlmostEqual(vector.x, a / l)
        self.assertAlmostEqual(vector.y, b / l)
        self.assertAlmostEqual(vector.length(), 1.0)

    def test_normalize_zerovector(self):
        vector = Vector(0, 0).normalize()
        self.assertEqual(vector.x, 0)
        self.assertEqual(vector.y, 0)
        self.assertEqual(vector.length(), 0)

    @given(integers(), integers(), integers(), integers())
    def test_dot(self, a, b, c, d):
        result = Vector(a, b).dot((c, d))
        self.assertEqual(result, a * c + b * d)

    @given(integers(min_value=1), integers(min_value=1))
    def test_angle(self, a, b):
        result = Vector(a, 0).angle((0, b))
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

    @given(
        integers(), integers(),
        integers(min_value=1), integers(min_value=1)
    )
    def test_inbbox(self, a, b, c, d):
        bmin = (a, b)
        bmax = (a + c, b + d)
        self.assertTrue(Vector.in_bbox((a + c / 2, b + d / 2), bmin, bmax))
        self.assertTrue(Vector.in_bbox((a + c, b), bmin, bmax))
        self.assertTrue(Vector.in_bbox((a, b + d), bmin, bmax))

        self.assertFalse(Vector.in_bbox((a + c + 1, b), bmin, bmax))
        self.assertFalse(Vector.in_bbox((a, b - 1), bmin, bmax))
