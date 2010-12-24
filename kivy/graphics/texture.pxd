from c_opengl cimport GLuint

cdef class Texture:
    cdef list tex_coords
    cdef int _width
    cdef int _height
    cdef GLuint _target
    cdef GLuint _id
    cdef int _mipmap
    cdef GLuint _gl_wrap
    cdef GLuint _gl_min_filter
    cdef GLuint _gl_max_filter
    cdef int _rectangle
    cpdef flip_vertical(self)
    cpdef get_region(self, x, y, width, height)
    cpdef bind(self)
    cpdef enable(self)
    cpdef disable(self)

