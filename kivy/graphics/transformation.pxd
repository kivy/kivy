ctypedef double matrix_t[16]
ctypedef double quaternion_t[4]

cdef class Matrix

cpdef Matrix matrix_multiply(Matrix b, Matrix a)
cpdef Matrix matrix_inverse(Matrix a)
cpdef Matrix matrix_identity()
cpdef Matrix matrix_scale(double x, double y, double z)
cpdef Matrix matrix_translation(double x, double y, double z)
cpdef Matrix matrix_rotation(double angle, double x, double y, double z)
cpdef Matrix matrix_clip(double left, double right, double bottom, double top,
                         double near, double far, int perspective)
cpdef tuple matrix_transform_point(Matrix m, double x, double y, double z)

cdef class Matrix:
    cdef matrix_t mat
