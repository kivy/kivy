cdef class Tesselator:
    cdef void *tess
    cdef int element_type
    cdef int polysize
    cdef void add_contour_data(self, void *cdata, int count)
    cdef iterate_vertices(self, int mode)
