cdef extern from "tesselator.h":
    ctypedef struct TESStesselator:
        pass
    ctypedef struct TESSalloc
    TESStesselator *tessNewTess(TESSalloc *alloc)
    void tessDeleteTess(TESStesselator *tess)

cdef class Tesselator:
    cdef TESStesselator *tess
