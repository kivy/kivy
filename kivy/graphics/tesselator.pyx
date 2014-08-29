"""
Tesselator
==========

Tesselator is a library for tesselate polygon, based on
`libtess2 <https://github.com/memononen/libtess2>`_
"""

include "common.pxi"


cdef class Tesselator:
    def __cinit__(self):
        self.tess = tessNewTess(NULL)

    def __dealloc__(self):
        tessDeleteTess(self.tess)
        self.tess = NULL
