from kivy.graphics.instructions cimport VertexInstruction
from kivy.graphics.vertex cimport VertexFormat


cdef class Bezier(VertexInstruction):
    cdef list _points
    cdef int _segments
    cdef bint _loop
    cdef int _dash_offset, _dash_length

    cdef void build(self)


cdef class StripMesh(VertexInstruction):
    cdef int icount
    cdef int li, lic
    cdef int add_triangle_strip(self, float *vertices, int vcount, int icount,
            int mode)


cdef class Mesh(VertexInstruction):
    cdef list _vertices
    cdef list _indices
    cdef VertexFormat vertex_format
    cdef int is_built

    cdef void build_triangle_fan(self, float *vertices, int vcount, int icount)
    cdef void build(self)
