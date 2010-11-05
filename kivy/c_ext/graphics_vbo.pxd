from buffer cimport Buffer
from c_opengl cimport GLuint
from graphics_vertex cimport vertex

cdef class VBO:
    cdef GLuint id
    cdef int usage
    cdef int target
    cdef list format
    cdef Buffer data
    cdef int need_upload
    cdef int vbo_size

    cdef create_buffer(self)
    cdef allocate_buffer(self)
    cdef update_buffer(self)
    cdef bind(self)
    cdef unbind(self)
    cdef add_vertices(self, void *v, int* indices, int count)
    cdef update_vertices(self, int index, vertex* v, int count)
    cdef remove_vertices(self, int* indices, int count)

