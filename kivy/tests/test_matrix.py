import unittest

from kivy.graphics.transformation import Matrix

class MatrixTestCase(unittest.TestCase):
    """
    Test matrices
    kivy.graphics.transformation.Matrix
    """
    def test_multiplication(self):
        """
        Test matrix multiplication
        I - 4x4 identity matrix
        M - any 4x4 matrix
        M * I = I * M = M
        """
        ident = Matrix()
        m = Matrix()
        m.set(array=[[ 1,  2,  3,  4],
                     [ 5,  6,  7,  8],
                     [ 9, 10, 11, 12],
                     [13, 14, 15, 16]])
        im = m.multiply(ident)
        for a, b in zip(m.get(), im.get()):
            self.assertAlmostEqual(a, b, msg='I * M != M')
        mi = ident.multiply(m)
        for a, b in zip(m.get(), mi.get()):
            self.assertAlmostEqual(a, b, msg='M * I != M')

    def test_inversion(self):
        """
        Test matrix inversion M^-1 * M = I
        I - 4x4 identity matrix
        M - any 4x4 matrix
        M^-1 - inverted matrix
        """
        ident = Matrix()
        m = Matrix()
        m.set(array=[[ 1,  1,  1, -1],
                     [ 1,  1, -1,  1],
                     [ 1, -1,  1,  1],
                     [-1,  1,  1,  1]])
        inv = m.inverse()
        mul = inv.multiply(m)
        for a, b in zip(mul.get(), ident.get()):
            self.assertAlmostEqual(a, b, msg='M^-1 * M != I')

    def test_double_inversion(self):
        """
        Test matrix inversion M^-1^-1 = M
        I - 4x4 identity matrix
        M - any 4x4 matrix
        M^-1 - inverted matrix
        """
        m = Matrix()
        m.set(array=[[ 1,  1,  1, -1],
                     [ 1,  1, -1,  1],
                     [ 1, -1,  1,  1],
                     [-1,  1,  1,  1]])
        inv = m.inverse()
        inv2 = inv.inverse()
        for a, b in zip(m.get(), inv2.get()):
            self.assertAlmostEqual(a, b, msg='M^-1^-1 != M')

    def test_inversion_zero_diagonal(self):
        """
        Test inversion of matrix with zero main diagonal
        """
        m = Matrix()
        m.set(array=[[ 0,  1,  0,  0],
                     [ 2,  0,  0,  0],
                     [ 0,  0,  0,  3],
                     [ 0,  0,  4,  0]])
        inv = m.inverse()
        self.assertIsNotNone(inv, 'Matrix inverse method returns empty value!')
        res = [0, 1/2,   0,   0,
               1,   0,   0,   0,
               0,   0,   0, 1/4,
               0,   0, 1/3,   0]
        for a, b in zip(res, inv.get()):
            self.assertAlmostEqual(a, b, msg='Incorrect inversion matrix.')
