ctypedef double matrix_t[16]

cdef class Matrix:
    cdef matrix_t mat
    cpdef Matrix identity(self)
    cpdef Matrix inverse(self)
    cpdef Matrix multiply(Matrix self, Matrix mb)
    cpdef Matrix rotate(Matrix self, double angle, double x, double y, double z)
    cpdef Matrix scale(Matrix self, double x, double y, double z)
    cpdef Matrix translate(Matrix self, double x, double y, double z)
    cpdef Matrix view_clip(Matrix self, double left, double right, double bottom, double top,
                             double near, double far, int perspective)
    cpdef tuple transform_point(Matrix self, double x, double y, double z)
    cpdef Matrix perspective(Matrix self, double fovy, double aspect, double zNear, double zFar)
    cpdef look_at(Matrix self, double eyex, double eyey, double eyez,
            double centerx, double centery, double centerz,
            double upx, double upy, double upz)
