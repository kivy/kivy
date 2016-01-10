from c_opengl cimport GLuint, GLint
from instructions cimport RenderContext, Canvas
from texture cimport Texture

cdef class Fbo(RenderContext):
    cdef int _width
    cdef int _height
    cdef int _depthbuffer_attached
    cdef int _stencilbuffer_attached
    cdef int _push_viewport
    cdef float _clear_color[4]
    cdef GLuint buffer_id
    cdef GLuint depthbuffer_id
    cdef GLuint stencilbuffer_id
    cdef GLint _viewport[4]
    cdef Texture _texture
    cdef int _is_bound
    cdef list observers

    cpdef clear_buffer(self)
    cpdef bind(self)
    cpdef release(self)
    cpdef get_pixel_color(self, int wx, int wy)

    cdef void create_fbo(self)
    cdef void delete_fbo(self)
    cdef int apply(self) except -1
    cdef void raise_exception(self, str message, int status=?)
    cdef str resolve_status(self, int status)
    cdef void reload(self)
