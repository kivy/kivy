cdef class Instruction
cdef class InstructionGroup
cdef class ContextInstruction
cdef class VertexInstruction
cdef class CanvasBase
cdef class Canvas
cdef class RenderContext

from vbo cimport *
from context_instructions cimport *
from compiler cimport *

cdef class Instruction:
    cdef int flags
    cdef str group
    cdef Instruction parent
    cdef apply(self)
    cdef flag_update(self)
    cdef flag_update_done(self)

cdef class InstructionGroup(Instruction):
    cdef list children
    cdef InstructionGroup compiled_children
    cdef GraphicsCompiler compiler
    cdef build(self)
    cpdef add(self, Instruction c)
    cpdef insert(self, int index, Instruction c)
    cpdef remove(self, Instruction c)
    cpdef clear(self)
    cpdef remove_group(self, str groupname)
    cpdef get_group(self, str groupname)

cdef class ContextInstruction(Instruction):
    cdef dict context_state
    cdef list context_push
    cdef list context_pop

    cdef RenderContext get_context(self)
    cdef set_state(self, str name, value)
    cdef push_state(self, str name)
    cdef pop_state(self, str name)

cdef class VertexInstruction(Instruction):
    cdef BindTexture texture_binding
    cdef VertexBatch batch
    cdef list vertices
    cdef list indices
    cdef list _tex_coords

    cdef update_batch(self)
    cdef build(self)




cdef CanvasBase getActiveCanvas()

cdef class CanvasBase(InstructionGroup):
    pass

cdef class Canvas(CanvasBase):
    cdef CanvasBase _before
    cdef CanvasBase _after
    cpdef add(self, Instruction c)
    cpdef remove(self, Instruction c)
    cpdef draw(self)


from shader cimport *
from texture cimport Texture
cdef class RenderContext(Canvas):
    cdef Shader shader
    cdef dict state_stacks
    #cdef TextureManager texture_manager
    cdef Texture default_texture

    cdef set_state(self, str name, value)
    cdef get_state(self, str name)
    cdef set_states(self, dict states)
    cdef push_state(self, str name)
    cdef push_states(self, list names)
    cdef pop_state(self, str name)
    cdef pop_states(self, list names)
    cdef enter(self)
    cdef apply(self)
    cpdef draw(self)

