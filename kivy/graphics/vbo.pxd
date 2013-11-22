from buffer cimport Buffer
from c_opengl cimport GLuint
from vertex cimport vertex_t, vertex_attr_t, VertexFormat

cdef VertexFormat default_vertex

cdef class VBO:
    cdef object __weakref__

    cdef GLuint id
    cdef int usage
    cdef int target
    cdef vertex_attr_t *format
    cdef long format_count
    cdef long format_size
    cdef Buffer data
    cdef short flags
    cdef long vbo_size
    cdef VertexFormat vertex_format

    cdef void update_buffer(self)
    cdef void bind(self)
    cdef void unbind(self)
    cdef void add_vertex_data(self, void *v, unsigned short* indices, int count)
    cdef void update_vertex_data(self, int index, void* v, int count)
    cdef void remove_vertex_data(self, unsigned short* indices, int count)
    cdef void reload(self)
    cdef int have_id(self)


cdef class VertexBatch:
    cdef object __weakref__

    cdef VBO vbo
    cdef Buffer elements
    cdef Buffer vbo_index
    cdef GLuint mode
    cdef str mode_str
    cdef GLuint id
    cdef int usage
    cdef short flags
    cdef long elements_size

    cdef void clear_data(self)
    cdef void set_data(self, void *vertices, int vertices_count,
                       unsigned short *indices, int indices_count)
    cdef void append_data(self, void *vertices, int vertices_count,
                          unsigned short *indices, int indices_count)
    cdef void draw(self)
    cdef void set_mode(self, str mode)
    cdef str get_mode(self)
    cdef int count(self)
    cdef void reload(self)
    cdef int have_id(self)
