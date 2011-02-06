from c_opengl cimport GLuint

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

