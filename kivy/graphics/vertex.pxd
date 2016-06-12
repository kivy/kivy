from kivy.graphics.cgl cimport GLuint

cdef struct vertex_t:
    float x, y
    float s0, t0

ctypedef struct vertex_attr_t:
    char *name
    unsigned int index
    unsigned int size
    GLuint type
    unsigned int bytesize
    int per_vertex

cdef class VertexFormat:
    cdef vertex_attr_t *vattr
    cdef long vattr_count
    cdef unsigned int vsize
    cdef unsigned int vbytesize
    cdef object last_shader
