from instructions cimport *

cdef class Canvas(InstructionGroup):
    cpdef draw(self)

cdef Canvas getActiveCanvas()

