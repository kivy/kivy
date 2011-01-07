cdef extern from "math.h":
    double sqrt(double x)
    double sin(double x)
    double cos(double x)
    double fabs(double x)

cdef extern from "string.h":
    void *memcpy(void *dest, void *src, int n)
    void *memset(void *s, int c, int n)

cdef class Matrix:
    def __cinit__(self):
        memset(self.mat, 0, sizeof(matrix_t))

    def __str__(self):
        cdef double *m = self.mat
        return '[[ %f %f %f %f ]\n[ %f %f %f %f ]\n' \
               '[ %f %f %f %f ]\n[ %f %f %f %f ]]' % (
                   m[0], m[1], m[2], m[3],
                   m[4], m[5], m[6], m[7],
                   m[8], m[9], m[10], m[11],
                   m[12], m[13], m[14], m[15])

cpdef Matrix matrix_inverse(Matrix m):
    cdef Matrix r = Matrix()
    cdef double det
    det = m.mat[0] * (m.mat[5] * m.mat[10] - m.mat[9] * m.mat[6]) \
            - m.mat[4] * (m.mat[1] * m.mat[10] - m.mat[9] * m.mat[2]) \
            + m.mat[8] * (m.mat[1] * m.mat[ 6] - m.mat[5] * m.mat[2])
    if det == 0:
        return
    det = 1.0 / det
    r.mat[ 0] =   det * (m.mat[5] * m.mat[10] - m.mat[9] * m.mat[6])
    r.mat[ 4] = - det * (m.mat[4] * m.mat[10] - m.mat[8] * m.mat[6])
    r.mat[ 8] =   det * (m.mat[4] * m.mat[ 9] - m.mat[8] * m.mat[5])
    r.mat[ 1] = - det * (m.mat[1] * m.mat[10] - m.mat[9] * m.mat[2])
    r.mat[ 5] =   det * (m.mat[0] * m.mat[10] - m.mat[8] * m.mat[2])
    r.mat[ 9] = - det * (m.mat[0] * m.mat[ 9] - m.mat[8] * m.mat[1])
    r.mat[ 2] =   det * (m.mat[1] * m.mat[ 6] - m.mat[5] * m.mat[2])
    r.mat[ 6] = - det * (m.mat[0] * m.mat[ 6] - m.mat[4] * m.mat[2])
    r.mat[10] =   det * (m.mat[0] * m.mat[ 5] - m.mat[4] * m.mat[1])
    r.mat[ 3] = 0
    r.mat[ 7] = 0
    r.mat[11] = 0
    r.mat[15] = 1
    r.mat[12] = -(m.mat[12] * r.mat[0] + m.mat[13] * r.mat[4] + m.mat[14] * r.mat[ 8])
    r.mat[13] = -(m.mat[12] * r.mat[1] + m.mat[13] * r.mat[5] + m.mat[14] * r.mat[ 9])
    r.mat[14] = -(m.mat[12] * r.mat[2] + m.mat[13] * r.mat[6] + m.mat[14] * r.mat[10])
    return r

cpdef Matrix matrix_multiply(Matrix b, Matrix a):
    cdef Matrix r = Matrix()
    r.mat[ 0] = a.mat[ 0] * b.mat[0] + a.mat[ 1] * b.mat[4] + a.mat[ 2] * b.mat[ 8]
    r.mat[ 4] = a.mat[ 4] * b.mat[0] + a.mat[ 5] * b.mat[4] + a.mat[ 6] * b.mat[ 8]
    r.mat[ 8] = a.mat[ 8] * b.mat[0] + a.mat[ 9] * b.mat[4] + a.mat[10] * b.mat[ 8]
    r.mat[12] = a.mat[12] * b.mat[0] + a.mat[13] * b.mat[4] + a.mat[14] * b.mat[ 8] + b.mat[12]
    r.mat[ 1] = a.mat[ 0] * b.mat[1] + a.mat[ 1] * b.mat[5] + a.mat[ 2] * b.mat[ 9]
    r.mat[ 5] = a.mat[ 4] * b.mat[1] + a.mat[ 5] * b.mat[5] + a.mat[ 6] * b.mat[ 9]
    r.mat[ 9] = a.mat[ 8] * b.mat[1] + a.mat[ 9] * b.mat[5] + a.mat[10] * b.mat[ 9]
    r.mat[13] = a.mat[12] * b.mat[1] + a.mat[13] * b.mat[5] + a.mat[14] * b.mat[ 9] + b.mat[13]
    r.mat[ 2] = a.mat[ 0] * b.mat[2] + a.mat[ 1] * b.mat[6] + a.mat[ 2] * b.mat[10]
    r.mat[ 6] = a.mat[ 4] * b.mat[2] + a.mat[ 5] * b.mat[6] + a.mat[ 6] * b.mat[10]
    r.mat[10] = a.mat[ 8] * b.mat[2] + a.mat[ 9] * b.mat[6] + a.mat[10] * b.mat[10]
    r.mat[14] = a.mat[12] * b.mat[2] + a.mat[13] * b.mat[6] + a.mat[14] * b.mat[10] + b.mat[14]
    r.mat[ 3] = 0
    r.mat[ 7] = 0
    r.mat[11] = 0
    r.mat[15] = 1
    return r

cpdef Matrix matrix_identity():
    cdef Matrix m = Matrix()
    m.mat[ 0] = 1
    m.mat[ 1] = 0
    m.mat[ 2] = 0
    m.mat[ 3] = 0
    m.mat[ 4] = 0
    m.mat[ 5] = 1
    m.mat[ 6] = 0
    m.mat[ 7] = 0
    m.mat[ 8] = 0
    m.mat[ 9] = 0
    m.mat[10] = 1
    m.mat[11] = 0
    m.mat[12] = 0
    m.mat[13] = 0
    m.mat[14] = 0
    m.mat[15] = 1
    return m

cpdef Matrix matrix_scale(double x, double y, double z):
    cdef Matrix m = matrix_identity()
    m.mat[0] = x
    m.mat[5] = y
    m.mat[10]= z
    return m

cpdef Matrix matrix_translation(double x, double y, double z):
    cdef Matrix m = matrix_identity()
    m.mat[12] = x
    m.mat[13] = y
    m.mat[14] = z
    return m

cpdef Matrix matrix_rotation(double angle, double x, double y, double z):
    cdef Matrix m = matrix_identity()
    cdef double d, c, s, co, ox, oy, oz, f1, f2, f3, f4, f5, f6, f7, f8, f9
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
    ox = m.mat[0]
    oy = m.mat[1]
    oz = m.mat[2]
    m.mat[0] = ox * f1 + oy * f2 + oz * f3
    m.mat[1] = ox * f4 + oy * f5 + oz * f6
    m.mat[2] = ox * f7 + oy * f8 + oz * f9
    ox = m.mat[4]
    oy = m.mat[5]
    oz = m.mat[6]
    m.mat[4] = ox * f1 + oy * f2 + oz * f3
    m.mat[5] = ox * f4 + oy * f5 + oz * f6
    m.mat[6] = ox * f7 + oy * f8 + oz * f9
    ox = m.mat[ 8]
    oy = m.mat[ 9]
    oz = m.mat[10]
    m.mat[ 8] = ox * f1 + oy * f2 + oz * f3
    m.mat[ 9] = ox * f4 + oy * f5 + oz * f6
    m.mat[10] = ox * f7 + oy * f8 + oz * f9
    return m

cdef double _EPS = 8.8817841970012523e-16
cpdef Matrix matrix_clip(double left, double right, double bottom, double top,
                         double near, double far, int perspective):
    cdef Matrix m = Matrix()
    if left >= right or bottom >= top or near >= far:
        raise ValueError('invalid frustrum')
    if perspective:
        raise Exception('not tested')
        if near <= _EPS:
            raise ValueError('invalid frustrum: near <= 0')
        t = 2.0 * near
        m.mat[0]  = -t/(right-left)
        m.mat[4]  = 0.0
        m.mat[8]  = (right+left)/(right-left)
        m.mat[12] = 0.0
        m.mat[1]  = 0.0
        m.mat[5]  = -t/(top-bottom)
        m.mat[9]  = (top+bottom)/(top-bottom)
        m.mat[13] = 0.0
        m.mat[2]  = 0.0
        m.mat[6]  = 0.0
        m.mat[10] = -(far+near)/(far-near)
        m.mat[14] = t*far/(far-near)
        m.mat[3]  = 0.0
        m.mat[7]  = 0.0
        m.mat[11] = -1.0
        m.mat[15] = 0.0
    else:
        #(0, 4, 8, 12, 1, 5, 9, 13, 2, 6, 10, 14, 3, 7, 11, 15)
        m.mat[0]  = 2.0/(right-left)
        m.mat[4]  = 0.0
        m.mat[8]  = 0.0
        m.mat[12] = (right+left)/(left-right)
        m.mat[1]  = 0.0
        m.mat[5]  = 2.0/(top-bottom)
        m.mat[9]  = 0.0
        m.mat[13] = (top+bottom)/(bottom-top)
        m.mat[2]  = 0.0
        m.mat[6]  = 0.0
        m.mat[10] = 2.0/(far-near)
        m.mat[14] = (far+near)/(near-far)
        m.mat[3]  = 0.0
        m.mat[7]  = 0.0
        m.mat[11] = 0.0
        m.mat[15] = 1.0
    return m

cpdef tuple matrix_transform_point(Matrix m, double x, double y, double z):
    cdef double tx, ty, tz
    tx = x * m.mat[0] + y * m.mat[4] + z * m.mat[ 8] + m.mat[12];
    ty = x * m.mat[1] + y * m.mat[5] + z * m.mat[ 9] + m.mat[13];
    tz = x * m.mat[2] + y * m.mat[6] + z * m.mat[10] + m.mat[14];
    return (tx, ty, tz)
