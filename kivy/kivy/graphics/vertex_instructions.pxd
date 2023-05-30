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
    cdef int is_built
    cdef object _vertices  # the object the user passed in
    cdef object _indices
    cdef object _fvertices  # a buffer interface passed by user, or created
    cdef object _lindices
    cdef float *_pvertices  # the pointer to the start of buffer interface data
    cdef unsigned short *_pindices
    cdef VertexFormat vertex_format
    cdef long vcount  # the length of last set _vertices
    cdef long icount  # the length of last set _indices

    cdef void build_triangle_fan(self, float *vertices, int vcount, int icount)
    cdef void build(self)
