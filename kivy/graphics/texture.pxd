from c_opengl cimport GLuint

cdef class Texture:
    cdef object __weakref__
    cdef unsigned int flags

    cdef object _source
    cdef float _tex_coords[8]
    cdef int _width
    cdef int _height
    cdef GLuint _target
    cdef GLuint _id
    cdef int _mipmap
    cdef object _wrap
    cdef object _min_filter
    cdef object _mag_filter
    cdef int _rectangle
    cdef object _colorfmt
    cdef object _icolorfmt
    cdef object _bufferfmt
    cdef float _uvx
    cdef float _uvy
    cdef float _uvw
    cdef float _uvh
    cdef int _is_allocated
    cdef int _nofree
    cdef list observers
    cdef object _proxyimage
    cdef object _callback

    cdef void update_tex_coords(self)
    cdef void set_min_filter(self, x)
    cdef void set_mag_filter(self, x)
    cdef void set_wrap(self, x)
    cdef void reload(self)
    cdef void _reload_propagate(self, Texture texture)
    cdef void allocate(self)

    cpdef flip_vertical(self)
    cpdef flip_horizontal(self)
    cpdef get_region(self, x, y, width, height)
    cpdef bind(self)

cdef class TextureRegion(Texture):
    cdef int x
    cdef int y
    cdef Texture owner
    cdef void reload(self)
    cpdef bind(self)
