#cython: cdivision=True

'''
Transformation
==============

This module contains a Matrix class used for our Graphics calculations. We
currently support:

- rotation, translation and scaling matrices
- multiplication matrix
- clip matrix (with or without perspective)
- transformation matrix for 3d touch

For more information on transformation matrices, please see the
`OpenGL Matrices Tutorial <http://www.opengl-tutorial.org/beginners-tutorials/tutorial-3-matrices/>`_.

.. versionchanged:: 1.6.0
   Added :meth:`Matrix.perspective`, :meth:`Matrix.look_at` and
   :meth:`Matrix.transpose`.
'''

__all__ = ('Matrix', )

cdef extern from "math.h":
    double sqrt(double x) nogil
    double sin(double x) nogil
    double cos(double x) nogil
    double tan(double x) nogil
    double fabs(double x) nogil

cdef extern from "string.h":
    void *memcpy(void *dest, void *src, int n)
    void *memset(void *s, int c, int n)

cdef double _EPS = 8.8817841970012523e-16

cdef class Matrix:
    '''
    Optimized matrix class for OpenGL::

        >>> from kivy.graphics.transformation import Matrix
        >>> m = Matrix()
        >>> print(m)
        [[ 1.000000 0.000000 0.000000 0.000000 ]
        [ 0.000000 1.000000 0.000000 0.000000 ]
        [ 0.000000 0.000000 1.000000 0.000000 ]
        [ 0.000000 0.000000 0.000000 1.000000 ]]

        [ 0   1   2   3]
        [ 4   5   6   7]
        [ 8   9  10  11]
        [ 12  13  14  15]
    '''

    def __cinit__(self):
        memset(self.mat, 0, sizeof(matrix_t))

    def __init__(self):
        self.identity()

    def get(Matrix self):
        '''Retrieve the value of the current as a flat list.

        .. versionadded:: 1.9.1
        '''

        return (
            self.mat[0], self.mat[1], self.mat[2], self.mat[3],
            self.mat[4], self.mat[5], self.mat[6], self.mat[7],
            self.mat[8], self.mat[9], self.mat[10], self.mat[11],
            self.mat[12], self.mat[13], self.mat[14], self.mat[15])

    def tolist(Matrix self):
        '''Retrieve the value of the current matrix in numpy format.
        for example m.tolist() will return::

            [[1.000000, 0.000000, 0.000000, 0.000000],
            [0.000000, 1.000000, 0.000000, 0.000000],
            [0.000000, 0.000000, 1.000000, 0.000000],
            [0.000000, 0.000000, 0.000000, 1.000000]]

        you can use this format to plug the result straight into numpy
        in this way numpy.array(m.tolist())

        .. versionadded:: 1.9.0
        '''

        return (
            (self.mat[0], self.mat[1], self.mat[2], self.mat[3]),
            (self.mat[4], self.mat[5], self.mat[6], self.mat[7]),
            (self.mat[8], self.mat[9], self.mat[10], self.mat[11]),
            (self.mat[12], self.mat[13], self.mat[14], self.mat[15]))

    def __getitem__(Matrix self, int index):
        '''Retrieve the value at the specified index or slice

        .. versionadded:: 1.9.0
        '''
        return self.mat[index]

    def set(Matrix self, flat=None, array=None):
        '''Insert custom values into the matrix in a flat list format
        or 4x4 array format like below::

            m.set(array=[
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0]]
            )

        .. versionadded:: 1.9.0
        '''
        if flat:
            self.mat[0] = flat[0]
            self.mat[1] = flat[1]
            self.mat[2] = flat[2]
            self.mat[3] = flat[3]
            self.mat[4] = flat[4]
            self.mat[5] = flat[5]
            self.mat[6] = flat[6]
            self.mat[7] = flat[7]
            self.mat[8] = flat[8]
            self.mat[9] = flat[9]
            self.mat[10] = flat[10]
            self.mat[11] = flat[11]
            self.mat[12] = flat[12]
            self.mat[13] = flat[13]
            self.mat[14] = flat[14]
            self.mat[15] = flat[15]
            return

        self.mat[0], self.mat[1], self.mat[2], self.mat[3] = array[0]
        self.mat[4], self.mat[5], self.mat[6], self.mat[7] = array[1]
        self.mat[8], self.mat[9], self.mat[10], self.mat[11] = array[2]
        self.mat[12], self.mat[13], self.mat[14], self.mat[15] = array[3]

    def __setitem__(Matrix self, int index, double value):
        '''given an index and a value update the value at that location

        .. versionadded:: 1.9.0
        '''
        self.mat[index] = value


    cpdef Matrix rotate(Matrix self, double angle, double x, double y, double z):
        '''Rotate the matrix through the angle around the axis (x, y, z)
        (inplace).

        :Parameters:
            `angle`: float
                The angle through which to rotate the matrix
            `x`: float
                X position of the point
            `y`: float
                Y position of the point
            `z`: float
                Z position of the point
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
        '''Scale the current matrix by the specified factors over
        each dimension (inplace).

        :Parameters:
            `x`: float
                The scale factor along the X axis
            `y`: float
                The scale factor along the Y axis
            `z`: float
                The scale factor along the Z axis
        '''
        with nogil:
            self.mat[ 0] *= x;
            self.mat[ 5] *= y;
            self.mat[10] *= z;
        return self

    cpdef Matrix translate(Matrix self, double x, double y, double z):
        '''Translate the matrix.

        :Parameters:
            `x`: float
                The translation factor along the X axis
            `y`: float
                The translation factor along the Y axis
            `z`: float
                The translation factor along the Z axis
            '''
        with nogil:
            self.mat[12] += x
            self.mat[13] += y
            self.mat[14] += z
        return self

    cpdef Matrix perspective(Matrix self, double fovy, double aspect,
            double zNear, double zFar):
        '''Creates a perspective matrix (inplace).

        :Parameters:
            `fovy`: float
                "Field Of View" angle
            `aspect`: float
                Aspect ratio
            `zNear`: float
                Near clipping plane
            `zFar`: float
                Far clippin plane

        .. versionadded:: 1.6.0
        '''
        cdef double f = 1 / tan(fovy / 2. / 360. * 2 * 3.141592653589793)
        self.mat[0]  = f / aspect
        self.mat[1]  = 0.0
        self.mat[2]  = 0.0
        self.mat[3]  = 0.0
        self.mat[4]  = 0.0
        self.mat[5]  = f
        self.mat[6]  = 0.0
        self.mat[7]  = 0.0
        self.mat[8]  = 0.0
        self.mat[9]  = 0.0
        self.mat[10] = (zFar + zNear) / (zNear - zFar)
        self.mat[11] = -1.0
        self.mat[12] = 0.0
        self.mat[13] = 0.0
        self.mat[14] = (2 * zFar * zNear) / (zNear - zFar)
        self.mat[15] = 0.0

    cpdef Matrix view_clip(Matrix self, double left, double right,
            double bottom, double top,
            double near, double far, int perspective):
        '''Create a clip matrix (inplace).

        :Parameters:
            `left`: float
                Co-ordinate
            `right`: float
                Co-ordinate
            `bottom`: float
                Co-ordinate
            `top`: float
                Co-ordinate
            `near`: float
                Co-ordinate
            `far`: float
                Co-ordinate
            `perpective`: int
                Co-ordinate

        .. versionchanged:: 1.6.0
            Enable support for perspective parameter.
        '''
        cdef double t
        if left >= right or bottom >= top or near >= far:
            raise ValueError('invalid frustrum')
        if perspective and near <= _EPS:
            raise ValueError('invalid frustrum: near <= 0')

        with nogil:
            if perspective:
                t = 2.0 * near
                self.mat[0]  = t/(right - left)
                self.mat[4]  = 0.0
                self.mat[8]  = (right + left)/(right - left)
                self.mat[12] = 0.0
                self.mat[1]  = 0.0
                self.mat[5]  = t/(top - bottom)
                self.mat[9]  = (top + bottom)/(top - bottom)
                self.mat[13] = 0.0
                self.mat[2]  = 0.0
                self.mat[6]  = 0.0
                self.mat[10] = -(far + near)/(far - near)
                self.mat[14] = (-t * far)/(far - near)
                self.mat[3]  = 0.0
                self.mat[7]  = 0.0
                self.mat[11] = -1.0
                self.mat[15] = 0.0
            else:
                #(0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15)
                self.mat[0]  = 2.0/(right - left)
                self.mat[4]  = 0.0
                self.mat[8]  = 0.0
                self.mat[12] = (right + left)/(left - right)
                self.mat[1]  = 0.0
                self.mat[5]  = 2.0/(top - bottom)
                self.mat[9]  = 0.0
                self.mat[13] = (top + bottom)/(bottom - top)
                self.mat[2]  = 0.0
                self.mat[6]  = 0.0
                self.mat[10] = -2.0/(far - near)
                self.mat[14] = (far + near)/(near - far)
                self.mat[3]  = 0.0
                self.mat[7]  = 0.0
                self.mat[11] = 0.0
                self.mat[15] = 1.0
        return self

    cpdef look_at(Matrix self, double eyex, double eyey, double eyez,
          double centerx, double centery, double centerz,
          double upx, double upy, double upz):
        '''Returns a new lookat Matrix (similar to
        `gluLookAt <http://www.opengl.org/sdk/docs/man2/xhtml/gluLookAt.xml>`_).

        :Parameters:
            `eyex`: float
                Eyes X co-ordinate
            `eyey`: float
                Eyes Y co-ordinate
            `eyez`: float
                Eyes Z co-ordinate
            `centerx`: float
                The X position of the reference point
            `centery`: float
                The Y position of the reference point
            `centerz`: float
                The Z position of the reference point
            `upx`: float
                The X value up vector.
            `upy`: float
                The Y value up vector.
            `upz`: float
                The Z value up vector.

        .. versionadded:: 1.6.0
        '''

        cdef double x[3]
        cdef double y[3]
        cdef double z[3]
        cdef double mag

        # Make rotation matrix
        # Z vector
        z[0] = eyex - centerx
        z[1] = eyey - centery
        z[2] = eyez - centerz
        mag = sqrt(z[0] * z[0] + z[1] * z[1] + z[2] * z[2])
        if (mag):          # mpichler, 19950515
            z[0] /= mag
            z[1] /= mag
            z[2] /= mag

        # Y vector
        y[0] = upx
        y[1] = upy
        y[2] = upz

        # X vector = Y cross Z
        x[0] = y[1] * z[2] - y[2] * z[1]
        x[1] = -y[0] * z[2] + y[2] * z[0]
        x[2] = y[0] * z[1] - y[1] * z[0]

        # Recompute Y = Z cross X
        y[0] = z[1] * x[2] - z[2] * x[1]
        y[1] = -z[0] * x[2] + z[2] * x[0]
        y[2] = z[0] * x[1] - z[1] * x[0]

        # mpichler, 19950515
        # cross product gives area of parallelogram, which is < 1.0 for
        # non-perpendicular unit-length vectors so normalize x, y here
        mag = sqrt(x[0] * x[0] + x[1] * x[1] + x[2] * x[2])
        if (mag):
            x[0] /= mag
            x[1] /= mag
            x[2] /= mag

        mag = sqrt(y[0] * y[0] + y[1] * y[1] + y[2] * y[2])
        if (mag):
            y[0] /= mag
            y[1] /= mag
            y[2] /= mag

        self.mat[0 + 0 * 4] = x[0]
        self.mat[0 + 1 * 4] = x[1]
        self.mat[0 + 2 * 4] = x[2]
        self.mat[0 + 3 * 4] = 0.0
        self.mat[1 + 0 * 4] = y[0]
        self.mat[1 + 1 * 4] = y[1]
        self.mat[1 + 2 * 4] = y[2]
        self.mat[1 + 3 * 4] = 0.0
        self.mat[2 + 0 * 4] = z[0]
        self.mat[2 + 1 * 4] = z[1]
        self.mat[2 + 2 * 4] = z[2]
        self.mat[2 + 3 * 4] = 0.0
        self.mat[3 + 0 * 4] = 0.0
        self.mat[3 + 1 * 4] = 0.0
        self.mat[3 + 2 * 4] = 0.0
        self.mat[3 + 3 * 4] = 1.0

        cdef Matrix m = Matrix()
        m = self.multiply(m)
        m = m.multiply(Matrix().translate(-eyex, -eyey, -eyez))
        return m

    cpdef tuple transform_point(Matrix self, double x, double y, double z,
            t=None):
        '''Transforms the point by the matrix and returns the transformed point
        as a ``(x, y, z)`` tuple. If the point is a vector ``v``, the returned
        values is ``v2 = matrix * v``.

        If ``t`` is provided, it multiplies it with the last column of the matrix
        and returns the transformed ``(x, y, z, t)``.
        '''
        cdef double tx, ty, tz, tt
        tx = x * self.mat[0] + y * self.mat[4] + z * self.mat[ 8] + self.mat[12];
        ty = x * self.mat[1] + y * self.mat[5] + z * self.mat[ 9] + self.mat[13];
        tz = x * self.mat[2] + y * self.mat[6] + z * self.mat[10] + self.mat[14];
        if t is not None:
            tt = x * self.mat[3] + y * self.mat[7] + z * self.mat[11] + self.mat[15];
            return (tx, ty, tz, tt)
        else:
            return (tx, ty, tz)

    cpdef Matrix identity(self):
        '''Reset the matrix to the identity matrix (inplace).
        '''
        cdef double *m = <double *>self.mat
        with nogil:
            m[0] = m[5] = m[10] = m[15] = 1
            m[1] = m[2] = m[3] = m[4] = m[6] = m[7] = \
            m[8] = m[9] = m[11] = m[12] = m[13] = m[14] = 0
        return self

    cpdef Matrix transpose(self):
        '''Return the transposed matrix as a new Matrix.

        .. versionadded:: 1.6.0
        '''
        cdef Matrix mm = Matrix()
        mm.mat[0]  = self.mat[0]
        mm.mat[4]  = self.mat[1]
        mm.mat[8]  = self.mat[2]
        mm.mat[12] = self.mat[3]
        mm.mat[1]  = self.mat[4]
        mm.mat[5]  = self.mat[5]
        mm.mat[9]  = self.mat[6]
        mm.mat[13] = self.mat[7]
        mm.mat[2]  = self.mat[8]
        mm.mat[6]  = self.mat[9]
        mm.mat[10] = self.mat[10]
        mm.mat[14] = self.mat[11]
        mm.mat[3]  = self.mat[12]
        mm.mat[7]  = self.mat[13]
        mm.mat[11] = self.mat[14]
        mm.mat[15] = self.mat[15]
        return mm

    cpdef Matrix inverse(self):
        '''Return the inverse of the matrix as a new Matrix.
        '''
        cdef Matrix mr = Matrix()
        cdef double *m = <double *>self.mat
        cdef double *r = <double *>mr.mat

        cdef double a11 = m[0]
        cdef double a12 = m[1]
        cdef double a13 = m[2]
        cdef double a14 = m[3]
        cdef double a21 = m[4]
        cdef double a22 = m[5]
        cdef double a23 = m[6]
        cdef double a24 = m[7]
        cdef double a31 = m[8]
        cdef double a32 = m[9]
        cdef double a33 = m[10]
        cdef double a34 = m[11]
        cdef double a41 = m[12]
        cdef double a42 = m[13]
        cdef double a43 = m[14]
        cdef double a44 = m[15]

        cdef double det2231
        cdef double det2331
        cdef double det2332
        cdef double det2431
        cdef double det2432
        cdef double det2433

        cdef double det2142
        cdef double det2143
        cdef double det2144
        cdef double det2243
        cdef double det2244
        cdef double det2344

        cdef double det3142
        cdef double det3143
        cdef double det3144
        cdef double det3243
        cdef double det3244
        cdef double det3344

        cdef double det11
        cdef double det12
        cdef double det13
        cdef double det14

        cdef double det21
        cdef double det22
        cdef double det23
        cdef double det24

        cdef double det31
        cdef double det32
        cdef double det33
        cdef double det34

        cdef double det41
        cdef double det42
        cdef double det43
        cdef double det44

        cdef double det
        with nogil:
            det2231 = a22 * a31 - a21 * a32
            det2331 = a23 * a31 - a21 * a33
            det2332 = a23 * a32 - a22 * a33
            det2431 = a24 * a31 - a21 * a34
            det2432 = a24 * a32 - a22 * a34
            det2433 = a24 * a33 - a23 * a34

            det2142 = a21 * a42 - a22 * a41
            det2143 = a21 * a43 - a23 * a41
            det2144 = a21 * a44 - a24 * a41
            det2243 = a22 * a43 - a23 * a42
            det2244 = a22 * a44 - a24 * a42
            det2344 = a23 * a44 - a24 * a43

            det3142 = a31 * a42 - a32 * a41
            det3143 = a31 * a43 - a33 * a41
            det3144 = a31 * a44 - a34 * a41
            det3243 = a32 * a43 - a33 * a42
            det3244 = a32 * a44 - a34 * a42
            det3344 = a33 * a44 - a34 * a43

            det11 =   a22 * det3344 - a23 * det3244 + a24 * det3243
            det12 = - a21 * det3344 + a23 * det3144 - a24 * det3143
            det13 =   a21 * det3244 - a22 * det3144 + a24 * det3142
            det14 = - a21 * det3243 + a22 * det3143 - a23 * det3142

            det21 = - a12 * det3344 + a13 * det3244 - a14 * det3243
            det22 =   a11 * det3344 - a13 * det3144 + a14 * det3143
            det23 = - a11 * det3244 + a12 * det3144 - a14 * det3142
            det24 =   a11 * det3243 - a12 * det3143 + a13 * det3142

            det31 =   a12 * det2344 - a13 * det2244 + a14 * det2243
            det32 = - a11 * det2344 + a13 * det2144 - a14 * det2143
            det33 =   a11 * det2244 - a12 * det2144 + a14 * det2142
            det34 = - a11 * det2243 + a12 * det2143 - a13 * det2142

            det41 =   a12 * det2433 - a13 * det2432 + a14 * det2332
            det42 = - a11 * det2433 + a13 * det2431 - a14 * det2331
            det43 =   a11 * det2432 - a12 * det2431 + a14 * det2231
            det44 = - a11 * det2332 + a12 * det2331 - a13 * det2231

            det = a11 * det11 + a12 * det12 + a13 * det13 + a14 * det14

        if det == 0:
            return

        cdef double idet = 1 / det

        with nogil:
            r[ 0] = det11 * idet
            r[ 1] = det21 * idet
            r[ 2] = det31 * idet
            r[ 3] = det41 * idet
            r[ 4] = det12 * idet
            r[ 5] = det22 * idet
            r[ 6] = det32 * idet
            r[ 7] = det42 * idet
            r[ 8] = det13 * idet
            r[ 9] = det23 * idet
            r[10] = det33 * idet
            r[11] = det43 * idet
            r[12] = det14 * idet
            r[13] = det24 * idet
            r[14] = det34 * idet
            r[15] = det44 * idet

        return mr

    cpdef Matrix normal_matrix(self):
        '''Computes the normal matrix, which is the inverse transpose
        of the top left 3x3 modelview matrix used to transform normals
        into eye/camera space.

        .. versionadded:: 1.6.0
        '''
        cdef Matrix nm = Matrix().multiply(self)
        nm = nm.inverse().transpose()
        nm.mat[3] = 0
        nm.mat[7] = 0
        nm.mat[11] = 0
        nm.mat[12] = 0
        nm.mat[13] = 0
        nm.mat[14] = 0
        nm.mat[15] = 1
        return nm

    cpdef Matrix multiply(Matrix mb, Matrix ma):
        '''Multiply the given matrix with self (from the left)
        i.e. we premultiply the given matrix by the current matrix and return
        the result (not inplace)::

            m.multiply(n) -> n * m

        :Parameters:
            `ma`: Matrix
                The matrix to multiply by
        '''
        cdef Matrix mr = Matrix()
        cdef double *a = <double *>ma.mat
        cdef double *b = <double *>mb.mat
        cdef double *r = <double *>mr.mat
        with nogil:
            r[ 0] = a[ 0] * b[0] + a[ 1] * b[4] + a[ 2] * b[ 8] + a[ 3] * b[12]
            r[ 4] = a[ 4] * b[0] + a[ 5] * b[4] + a[ 6] * b[ 8] + a[ 7] * b[12]
            r[ 8] = a[ 8] * b[0] + a[ 9] * b[4] + a[10] * b[ 8] + a[11] * b[12]
            r[12] = a[12] * b[0] + a[13] * b[4] + a[14] * b[ 8] + a[15] * b[12]
            r[ 1] = a[ 0] * b[1] + a[ 1] * b[5] + a[ 2] * b[ 9] + a[ 3] * b[13]
            r[ 5] = a[ 4] * b[1] + a[ 5] * b[5] + a[ 6] * b[ 9] + a[ 7] * b[13]
            r[ 9] = a[ 8] * b[1] + a[ 9] * b[5] + a[10] * b[ 9] + a[11] * b[13]
            r[13] = a[12] * b[1] + a[13] * b[5] + a[14] * b[ 9] + a[15] * b[13]
            r[ 2] = a[ 0] * b[2] + a[ 1] * b[6] + a[ 2] * b[10] + a[ 3] * b[14]
            r[ 6] = a[ 4] * b[2] + a[ 5] * b[6] + a[ 6] * b[10] + a[ 7] * b[14]
            r[10] = a[ 8] * b[2] + a[ 9] * b[6] + a[10] * b[10] + a[11] * b[14]
            r[14] = a[12] * b[2] + a[13] * b[6] + a[14] * b[10] + a[15] * b[14]
            r[ 3] = a[ 0] * b[3] + a[ 1] * b[7] + a[ 2] * b[11] + a[ 3] * b[15]
            r[ 7] = a[ 4] * b[3] + a[ 5] * b[7] + a[ 6] * b[11] + a[ 7] * b[15]
            r[11] = a[ 8] * b[3] + a[ 9] * b[7] + a[10] * b[11] + a[11] * b[15]
            r[15] = a[12] * b[3] + a[13] * b[7] + a[14] * b[11] + a[15] * b[15]
        return mr

    cpdef project(Matrix self, double objx, double objy, double objz, Matrix model, Matrix proj,
            double vx, double vy, double vw, double vh):
        '''Project a point from 3d space into a 2d viewport.

        :Parameters:
            `objx`: float
                Points X co-ordinate
            `objy`: float
                Points Y co-ordinate
            `objz`: float
                Points Z co-ordinate
            `model`: Matrix
                The model matrix
            `proj`: Matrix
                The projection matrix
            `vx`: float
                Viewports X co-ordinate
            `vy`: float
                Viewports y co-ordinate
            `vw`: float
                Viewports width
            `vh`: float
                Viewports height

        .. versionadded:: 1.7.0
        '''
        cdef double winx, winy, winz
        cdef list point = list(model.transform_point(objx, objy, objz, 1.0))
        point = list(proj.transform_point(*point))

        if point[3] == 0:
            return None

        point[0] /= point[3]
        point[1] /= point[3]
        point[2] /= point[3]

        winx = vx + (1 + point[0]) * vw / 2.
        winy = vy + (1 + point[1]) * vh / 2.
        winz = (1 + point[2]) / 2.

        return (winx, winy, winz)

    def __str__(self):
        cdef double *m = <double *>self.mat
        return '[[ %f %f %f %f ]\n[ %f %f %f %f ]\n' \
               '[ %f %f %f %f ]\n[ %f %f %f %f ]]' % (
                   m[0], m[1], m[2], m[3],
                   m[4], m[5], m[6], m[7],
                   m[8], m[9], m[10], m[11],
                   m[12], m[13], m[14], m[15])
