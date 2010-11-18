
cdef object get_default_texture()
    
cdef class TextureManager:
    cdef dict textures
    cdef dict texture_units
    cdef list free_texture_units

    cdef int bind_texture(self, object texture)
    cdef release_texture(self, object texture)
    cdef bind_all(self)
    cdef release_all(self)
    cdef reset(self)
