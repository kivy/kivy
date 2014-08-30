cdef extern from "tesselator.h":
    ctypedef struct TESStesselator:
        pass
    ctypedef struct TESSalloc:
        pass
    ctypedef enum TessElementType:
        TESS_POLYGONS
        TESS_CONNECTED_POLYGONS
        TESS_BOUNDARY_CONTOURS
    ctypedef enum TessWindingRule:
        TESS_WINDING_ODD
        TESS_WINDING_NONZERO
        TESS_WINDING_POSITIVE
        TESS_WINDING_NEGATIVE
        TESS_WINDING_ABS_GEQ_TWO
    TESStesselator *tessNewTess(TESSalloc *)
    void tessDeleteTess(TESStesselator *)
    void tessAddContour(TESStesselator *, int, void *, int, int)
    int tessTesselate(TESStesselator *, int, int, int, int, float *)
    int tessGetVertexCount(TESStesselator *)
    int tessGetElementCount(TESStesselator *)
    float *tessGetVertices(TESStesselator *)
    float *tessGetVertexIndices(TESStesselator *)
    int *tessGetVertexIndices(TESStesselator *)
    int *tessGetElements(TESStesselator *)


cdef class Tesselator:
    cdef TESStesselator *tess
    cdef int element_type
    cdef int polysize
    cdef void add_contour_data(self, void *cdata, int count)
