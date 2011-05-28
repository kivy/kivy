from c_opengl cimport GLuint

cdef class Texture:
    cdef float _tex_coords[8]
    cdef int _width
    cdef int _height
    cdef GLuint _target
    cdef GLuint _id
    cdef int _mipmap
    cdef str _wrap
    cdef str _min_filter
    cdef str _mag_filter
    cdef int _rectangle
    cdef bytes _colorfmt
    cdef float _uvx
    cdef float _uvy
    cdef float _uvw
    cdef float _uvh
    cdef int _is_allocated

    cdef update_tex_coords(self)
    cdef set_min_filter(self, str x)
    cdef set_mag_filter(self, str x)
    cdef set_wrap(self, str x)

    cpdef flip_vertical(self)
    cpdef get_region(self, x, y, width, height)
    cpdef bind(self)

