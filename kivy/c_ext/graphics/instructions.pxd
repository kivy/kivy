
cdef class GraphicsInstruction:
    cdef int flags
    cdef GraphicsInstruction parent
    cdef apply(self)


cdef class InstructionGroup(GraphicsInstruction):
    cdef list children
    cpdef add(self, GraphicsInstruction c)


cdef class ContextInstruction(GraphicsInstruction):
    cdef dict context_state


cdef class VertexInstruction:
    cdef list vertices
    cdef list indices
    cdef build(self)
