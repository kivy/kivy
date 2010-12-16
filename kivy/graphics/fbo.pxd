from c_opengl cimport *
from instructions cimport RenderContext, Canvas

class Fbo(RenderContext):
    cdef int width
    cdef int height
    cdef int depthbuffer_attached
    cdef list clear_color
    cdef GLuint buffer_id
    cdef GLuint depthbuffer_id
    cdef object texture

    cdef bind(self)
    cdef release(self)
    cdef clear(self)


