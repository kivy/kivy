from instructions cimport *

cdef class GraphicsCompiler:

    cdef GraphicsGroup compile(self, InstructionGroup group):
        #instead return an optimized group with only needed elements
        #which has state changes  and vertex batches grouped into
        #as few elements as possible
        return group
