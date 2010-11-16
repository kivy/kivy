from vbo cimport *
from shader cimport *





cdef class GraphicsInstruction:
    cdef int flags
    cdef GraphicsInstruction parent
    cdef apply(self)
    cdef flag_update(self)
    cdef flag_update_done(self)


cdef class InstructionGroup(GraphicsInstruction):
    cdef list children
    cpdef add(self, GraphicsInstruction c)


cdef class ContextInstruction(GraphicsInstruction):
    cdef dict context_state
    cdef set_state(self, str name, value)

cdef class VertexInstruction(GraphicsInstruction):
    cdef VertexBatch batch
    cdef list vertices
    cdef list indices

    cdef update_batch(self)
    cdef build(self)

