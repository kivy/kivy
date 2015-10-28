from c_opengl cimport GLuint

cdef class PBO:
    cdef object __weakref__
    cdef GLuint _id
    cdef int width
    cdef int height
    cdef int data_size

    cdef void release(self)
    cpdef GLuint get_id(self)
