
from shader cimport *
from instructions cimport *

cdef class RenderContext(InstructionGroup):
    cdef Shader shader
    cdef set_state(self, str name, value)
    cdef set_states(self, dict states)
    cdef enter(self)
    cdef apply(self)

cdef RenderContext getActiveContext()

