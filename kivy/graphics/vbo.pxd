from buffer cimport Buffer
from c_opengl cimport GLuint
from vertex cimport vertex

cdef class VBO:
    cdef GLuint id
    cdef int usage
    cdef int target
    cdef list format
    cdef Buffer data
    cdef int need_upload
    cdef int vbo_size

    cdef allocate_buffer(self)
    cdef update_buffer(self)
    cdef bind(self)
    cdef unbind(self)
    cdef add_vertex_data(self, void *v, int* indices, int count)
    cdef update_vertex_data(self, int index, vertex* v, int count)
    cdef remove_vertex_data(self, int* indices, int count)


cdef class VertexBatch:
    cdef VBO vbo
    cdef Buffer elements
    cdef Buffer vbo_index
    cdef list vertices
    cdef list indices
    cdef GLuint mode

    cdef set_data(self, list vertices, list indices)
    cdef build(self)
    cdef draw(self)
    cdef set_mode(self, str mode)
