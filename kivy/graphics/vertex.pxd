from c_opengl cimport GLfloat, GL_FLOAT

cdef struct vertex:
    float x, y
    float s0, t0 
    float s1, t1
    float s2, t2


cdef class Vertex:
    cdef vertex data
    cdef set_pos(self, float x, float y)
    cdef set_tc0(self, float s, float t)
    cdef set_tc1(self, float s, float t)
    cdef set_tc2(self, float s, float t)
