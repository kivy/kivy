from c_opengl cimport *
from instructions cimport RenderContext, Canvas

cdef class Fbo(RenderContext):
    cdef int width
    cdef int height
    cdef int depthbuffer_attached
    cdef list clear_color
    cdef GLuint buffer_id
    cdef GLuint depthbuffer_id
    cdef object texture

    cpdef bind(self)
    cpdef release(self)
    cpdef clear(self)


