#cython: cdivision=True

'''
Transformation
==============

This module contain a Matrix class, used for our Graphics calculation. We are
supporting:

- rotation, translation, scaling matrix
- multiply matrix
- create clip matrix (with or without perspective)
- transform 3d touch on a matrix

'''

__all__ = ('Matrix', )

cdef extern from "math.h":
    double sqrt(double x) nogil
    double sin(double x) nogil
    double cos(double x) nogil
    double fabs(double x) nogil

cdef extern from "string.h":
    void *memcpy(void *dest, void *src, int n)
    void *memset(void *s, int c, int n)

cdef double _EPS = 8.8817841970012523e-16

cdef class Matrix:
    '''Optimized matrix class for OpenGL ::

        >>> from kivy.graphics.transformation import Matrix
        >>> m = Matrix()
        >>> print m
        [[ 1.000000 0.000000 0.000000 0.000000 ]
        [ 0.000000 1.000000 0.000000 0.000000 ]
        [ 0.000000 0.000000 1.000000 0.000000 ]
        [ 0.000000 0.000000 0.000000 1.000000 ]]

        [ 0   1   2   3]
        [ 4   5   6   7]
        [ 8   9  10  11]
        [12  13  14  15]

    '''

    def __cinit__(self):
        memset(self.mat, 0, sizeof(matrix_t))

    def __init__(self):
        self.identity()

    cpdef Matrix rotate(Matrix self, double angle, double x, double y, double z):
        '''Rotate the matrix with the angle, around the axis (x, y, z)
        '''
        cdef double d, c, s, co, ox, oy, oz, f1, f2, f3, f4, f5, f6, f7, f8, f9
        with nogil:
            d = sqrt(x * x + y * y + z * z)
            if (d != 1.0):
                x /= d
                y /= d
                z /= d
            c = cos(angle)
            s = sin(angle)
            co = 1.0 - c
            ox = x * co
            oy = y * co
            oz = z * co
            f1 = x * ox + c
            f5 = y * oy + c
            f9 = z * oz + c
            d = z * s
            f2 = x * oy - d
            f4 = y * ox + d
            d = y * s
            f3 = x * oz + d
            f7 = z * ox - d
            d = x * s
            f6 = y * oz - d
            f8 = z * oy + d
            ox = self.mat[0]
            oy = self.mat[1]
            oz = self.mat[2]
            self.mat[0] = ox * f1 + oy * f2 + oz * f3
            self.mat[1] = ox * f4 + oy * f5 + oz * f6
            self.mat[2] = ox * f7 + oy * f8 + oz * f9
            ox = self.mat[4]
            oy = self.mat[5]
            oz = self.mat[6]
            self.mat[4] = ox * f1 + oy * f2 + oz * f3
            self.mat[5] = ox * f4 + oy * f5 + oz * f6
            self.mat[6] = ox * f7 + oy * f8 + oz * f9
            ox = self.mat[ 8]
            oy = self.mat[ 9]
            oz = self.mat[10]
            self.mat[ 8] = ox * f1 + oy * f2 + oz * f3
            self.mat[ 9] = ox * f4 + oy * f5 + oz * f6
            self.mat[10] = ox * f7 + oy * f8 + oz * f9
        return self

    cpdef Matrix scale(Matrix self, double x, double y, double z):
        '''Scale the matrix current Matrix (inplace).
        '''
        with nogil:
            self.mat[ 0] *= x;
            self.mat[ 5] *= y;
            self.mat[10] *= z;
        return self

    cpdef Matrix translate(Matrix self, double x, double y, double z):
        '''Translate the matrix
        '''
        with nogil:
            self.mat[12] += x
            self.mat[13] += y
            self.mat[14] += z
        return self

    cpdef Matrix view_clip(Matrix self, double left, double right, double bottom, double top,
                             double near, double far, int perspective):
        '''Create a clip matrix (inplace)
        '''
        cdef double t
        if left >= right or bottom >= top or near >= far:
            raise ValueError('invalid frustrum')
        if perspective:
            raise Exception('not tested')
            '''
            # original code
            if near <= _EPS:
                raise ValueError('invalid frustrum: near <= 0')
            '''

        with nogil:
            if perspective:
                t = 2.0 * near
                self.mat[0]  = -t/(right-left)
                self.mat[4]  = 0.0
                self.mat[8]  = (right+left)/(right-left)
                self.mat[12] = 0.0
                self.mat[1]  = 0.0
                self.mat[5]  = -t/(top-bottom)
                self.mat[9]  = (top+bottom)/(top-bottom)
                self.mat[13] = 0.0
                self.mat[2]  = 0.0
                self.mat[6]  = 0.0
                self.mat[10] = -(far+near)/(far-near)
                self.mat[14] = t*far/(far-near)
                self.mat[3]  = 0.0
                self.mat[7]  = 0.0
                self.mat[11] = -1.0
                self.mat[15] = 0.0
            else:
                #(0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15)
                self.mat[0]  = 2.0/(right-left)
                self.mat[4]  = 0.0
                self.mat[8]  = 0.0
                self.mat[12] = (right+left)/(left-right)
                self.mat[1]  = 0.0
                self.mat[5]  = 2.0/(top-bottom)
                self.mat[9]  = 0.0
                self.mat[13] = (top+bottom)/(bottom-top)
                self.mat[2]  = 0.0
                self.mat[6]  = 0.0
                self.mat[10] = 2.0/(far-near)
                self.mat[14] = (far+near)/(near-far)
                self.mat[3]  = 0.0
                self.mat[7]  = 0.0
                self.mat[11] = 0.0
                self.mat[15] = 1.0
        return self

    cpdef tuple transform_point(Matrix self, double x, double y, double z):
        cdef double tx, ty, tz
        with nogil:
            tx = x * self.mat[0] + y * self.mat[4] + z * self.mat[ 8] + self.mat[12];
            ty = x * self.mat[1] + y * self.mat[5] + z * self.mat[ 9] + self.mat[13];
            tz = x * self.mat[2] + y * self.mat[6] + z * self.mat[10] + self.mat[14];
        return (tx, ty, tz)

    cpdef Matrix identity(self):
        '''Reset matrix to identity matrix (inplace)
        '''
        cdef double *m = self.mat
        with nogil:
            m[0] = m[5] = m[10] = m[15] = 1
            m[1] = m[2] = m[3] = m[4] = m[6] = m[7] = \
            m[8] = m[9] = m[11] = m[12] = m[13] = m[14] = 0
        return self

    cpdef Matrix inverse(self):
        '''Return the inverted matrix
        '''
        cdef Matrix mr = Matrix()
        cdef double *m = self.mat, *r = mr.mat
        cdef double det
        with nogil:
            det = m[0] * (m[5] * m[10] - m[9] * m[6]) \
                    - m[4] * (m[1] * m[10] - m[9] * m[2]) \
                    + m[8] * (m[1] * m[ 6] - m[5] * m[2])
        if det == 0:
            return
        with nogil:
            det = 1.0 / det
            r[ 0] =   det * (m[5] * m[10] - m[9] * m[6])
            r[ 4] = - det * (m[4] * m[10] - m[8] * m[6])
            r[ 8] =   det * (m[4] * m[ 9] - m[8] * m[5])
            r[ 1] = - det * (m[1] * m[10] - m[9] * m[2])
            r[ 5] =   det * (m[0] * m[10] - m[8] * m[2])
            r[ 9] = - det * (m[0] * m[ 9] - m[8] * m[1])
            r[ 2] =   det * (m[1] * m[ 6] - m[5] * m[2])
            r[ 6] = - det * (m[0] * m[ 6] - m[4] * m[2])
            r[10] =   det * (m[0] * m[ 5] - m[4] * m[1])
            r[ 3] = 0
            r[ 7] = 0
            r[11] = 0
            r[15] = 1
            r[12] = -(m[12] * r[0] + m[13] * r[4] + m[14] * r[ 8])
            r[13] = -(m[12] * r[1] + m[13] * r[5] + m[14] * r[ 9])
            r[14] = -(m[12] * r[2] + m[13] * r[6] + m[14] * r[10])
        return mr

    cpdef Matrix multiply(Matrix mb, Matrix ma):
        '''Multiply the given matrix with self (from the left).
        I.e., we premultiply the given matrix to the current matrix and return
        the result (not inplace)::

            m.multiply(n) -> n * m
        '''
        cdef Matrix mr = Matrix()
        cdef double *a = ma.mat, *b = mb.mat, *r = mr.mat
        with nogil:
            r[ 0] = a[ 0] * b[0] + a[ 1] * b[4] + a[ 2] * b[ 8]
            r[ 4] = a[ 4] * b[0] + a[ 5] * b[4] + a[ 6] * b[ 8]
            r[ 8] = a[ 8] * b[0] + a[ 9] * b[4] + a[10] * b[ 8]
            r[12] = a[12] * b[0] + a[13] * b[4] + a[14] * b[ 8] + b[12]
            r[ 1] = a[ 0] * b[1] + a[ 1] * b[5] + a[ 2] * b[ 9]
            r[ 5] = a[ 4] * b[1] + a[ 5] * b[5] + a[ 6] * b[ 9]
            r[ 9] = a[ 8] * b[1] + a[ 9] * b[5] + a[10] * b[ 9]
            r[13] = a[12] * b[1] + a[13] * b[5] + a[14] * b[ 9] + b[13]
            r[ 2] = a[ 0] * b[2] + a[ 1] * b[6] + a[ 2] * b[10]
            r[ 6] = a[ 4] * b[2] + a[ 5] * b[6] + a[ 6] * b[10]
            r[10] = a[ 8] * b[2] + a[ 9] * b[6] + a[10] * b[10]
            r[14] = a[12] * b[2] + a[13] * b[6] + a[14] * b[10] + b[14]
            r[ 3] = 0
            r[ 7] = 0
            r[11] = 0
            r[15] = 1
        return mr

    def __str__(self):
        cdef double *m = self.mat
        return '[[ %f %f %f %f ]\n[ %f %f %f %f ]\n' \
               '[ %f %f %f %f ]\n[ %f %f %f %f ]]' % (
                   m[0], m[1], m[2], m[3],
                   m[4], m[5], m[6], m[7],
                   m[8], m[9], m[10], m[11],
                   m[12], m[13], m[14], m[15])

