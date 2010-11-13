
from instructions cimport *

cdef class Canvas(GraphicsGroup):
    cpdef draw(self):
        GraphicsGroup.apply(self)
  






