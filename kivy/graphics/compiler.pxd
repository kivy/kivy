cdef class GraphicsCompiler

from .instructions cimport InstructionGroup

cdef class GraphicsCompiler:
    cdef InstructionGroup compile(self, InstructionGroup group)
