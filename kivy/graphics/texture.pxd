from c_opengl cimport GLuint

cdef class Texture:
    cdef object __weakref__

    cdef object _source
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
    cdef bytes _bufferfmt
    cdef float _uvx
    cdef float _uvy
    cdef float _uvw
    cdef float _uvh
    cdef int _is_allocated
    cdef int _nofree
    cdef list observers

    cdef void update_tex_coords(self)
    cdef void set_min_filter(self, str x)
    cdef void set_mag_filter(self, str x)
    cdef void set_wrap(self, str x)
    cdef void reload(self)

    cpdef flip_vertical(self)
    cpdef get_region(self, x, y, width, height)
    cpdef bind(self)

cdef class TextureRegion(Texture):
    cdef int x
    cdef int y
    cdef Texture owner
    cdef void reload(self)
