cdef class GraphicsInstruction
cdef class InstructionGroup
cdef class ContextInstruction
cdef class VertexInstruction

cdef class Canvas
cdef class RenderContext



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
    cpdef remove(self, GraphicsInstruction c)

cdef class ContextInstruction(GraphicsInstruction):
    cdef dict context_state
    cdef set_state(self, str name, value)

cdef class VertexInstruction(GraphicsInstruction):
    cdef VertexBatch batch
    cdef list vertices
    cdef list indices

    cdef update_batch(self)
    cdef build(self)




cdef Canvas getActiveCanvas()
cdef class Canvas(InstructionGroup):
    cpdef draw(self)



cdef class RenderContext(InstructionGroup):
    cdef Shader shader
    cdef set_state(self, str name, value)
    cdef set_states(self, dict states)
    cdef enter(self)
    cdef apply(self)
    cpdef draw(self)

