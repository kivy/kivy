from c_opengl cimport GLuint

cdef struct vertex_t:
    float x, y
    float s0, t0
    float s1, t1
    float s2, t2

ctypedef struct vertex_attr_t:
    char *name
    unsigned int index
    unsigned int size
    GLuint type
    unsigned int bytesize
    int per_vertex

cdef class Vertex:
    cdef vertex_t data
    cdef set_pos(self, float x, float y)
    cdef set_tc0(self, float s, float t)
    cdef set_tc1(self, float s, float t)
    cdef set_tc2(self, float s, float t)
