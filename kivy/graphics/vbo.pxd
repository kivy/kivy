from buffer cimport Buffer
from c_opengl cimport GLuint
from vertex cimport vertex_t, vertex_attr_t

cdef int vbo_vertex_attr_count()
cdef vertex_attr_t *vbo_vertex_attr_list()

cdef class VBO:
    cdef GLuint id
    cdef int usage
    cdef int target
    cdef vertex_attr_t *format
    cdef int format_count
    cdef Buffer data
    cdef int need_upload
    cdef int vbo_size

    cdef void allocate_buffer(self)
    cdef void update_buffer(self)
    cdef void bind(self)
    cdef void unbind(self)
    cdef void add_vertex_data(self, void *v, unsigned short* indices, int count)
    cdef void update_vertex_data(self, int index, vertex_t* v, int count)
    cdef void remove_vertex_data(self, unsigned short* indices, int count)


cdef class VertexBatch:
    cdef VBO vbo
    cdef Buffer elements
    cdef Buffer vbo_index
    cdef GLuint mode
    cdef str mode_str

    cdef void clear_data(self)
    cdef void set_data(self, vertex_t *vertices, int vertices_count,
                       unsigned short *indices, int indices_count)
    cdef void append_data(self, vertex_t *vertices, int vertices_count,
                          unsigned short *indices, int indices_count)
    cdef void draw(self)
    cdef void set_mode(self, str mode)
    cdef str get_mode(self)
    cdef int count(self)
