"""
Tesselator
==========

Tesselator is a library for tesselate polygon, based on
`libtess2 <https://github.com/memononen/libtess2>`_
"""

include "common.pxi"
cimport cpython.array
from array import array
from cython cimport view

WINDING_ODD = TESS_WINDING_ODD
WINDING_NONZERO = TESS_WINDING_NONZERO
WINDING_POSITIVE = TESS_WINDING_POSITIVE
WINDING_NEGATIVE = TESS_WINDING_NEGATIVE
WINDING_ABS_GEQ_TWO = TESS_WINDING_ABS_GEQ_TWO
TYPE_POLYGONS = TESS_POLYGONS
TYPE_CONNECTED_POLYGONS = TESS_CONNECTED_POLYGONS
TYPE_BOUNDARY_CONTOURS = TESS_BOUNDARY_CONTOURS


cdef class Tesselator:
    def __cinit__(self):
        self.tess = tessNewTess(NULL)

    def __dealloc__(self):
        tessDeleteTess(self.tess)
        self.tess = NULL

    def add_contour(self, points):
        cdef float [:] float_view
        cdef char *cdata
        cdef long datasize
        cdef long count

        if isinstance(points, (tuple, list)):
            float_view = array("f", points)
        else:
            # must be a memory view or a buffer type
            float_view = points

        cdata = <char *>&float_view[0]
        datasize = float_view.nbytes
        self.add_contour_data(cdata, len(points) / 2)

    cdef void add_contour_data(self, void *cdata, int count):
        tessAddContour(self.tess, 2, <void *>cdata, sizeof(float) * 2, count)

    def tesselate(self, int winding_rule, int element_type, int polysize=65535):
        self.element_type = element_type
        self.polysize = polysize
        return tessTesselate(self.tess, winding_rule, element_type,
                             polysize, 2, NULL)

    @property
    def vertex_count(self):
        return tessGetVertexCount(self.tess)

    @property
    def element_count(self):
        return tessGetElementCount(self.tess)

    @property
    def meshes(self):
        cdef int nelems, *elems, *poly, i, j, count
        cdef float *verts = tessGetVertices(self.tess)
        cdef view.array mesh
        ret = []
        if self.element_type == TYPE_POLYGONS:
            nelems = tessGetElementCount(self.tess)
            elems = tessGetElements(self.tess)
            for i in range(nelems):
                poly = &elems[i * self.polysize]

                # first, count the number of vertices in this polygon
                count = 0
                for j in range(self.polysize):
                    if poly[j] == ~(<int>0):
                        break
                    count += 1

                # second, wrote it
                if count:
                    mesh = view.array(shape=(count * 4, ), itemsize=sizeof(float), format="f")
                    for j in range(count):
                        mesh[j * 4] = verts[poly[j] * 2]
                        mesh[j * 4 + 1] = verts[poly[j] * 2 + 1]
                        mesh[j * 4 + 2] = 0
                        mesh[j * 4 + 3] = 0
                    ret.append(mesh.memview)
                    #print "->", count, mesh.memview, list(mesh.memview)
        return ret
