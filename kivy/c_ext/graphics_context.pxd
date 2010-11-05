from graphics_shader cimport Shader

cdef class GraphicContext:
    cdef dict state
    cdef list stack
    cdef set journal
    cdef readonly int need_flush
    cdef Shader _default_shader
    cdef object _default_texture
    cdef int need_redraw

    cpdef post_update(self)
    cpdef finish_frame(self)
    cpdef set(self, str key, value)
    cpdef get(self, str key)
    cpdef reset(self)
    cpdef save(self)
    cpdef restore(self)
    cpdef flush(self)

