cdef class Instruction
cdef class InstructionGroup
cdef class ContextInstruction
cdef class VertexInstruction
cdef class CanvasBase
cdef class Canvas
cdef class RenderContext

from vbo cimport *
from compiler cimport *
from shader cimport *
from texture cimport Texture
from kivy._event cimport ObjectWithUid

cdef void reset_gl_context()

cdef class Instruction
cdef class InstructionGroup(Instruction)

cdef class Instruction(ObjectWithUid):
    cdef int flags
    cdef str group
    cdef InstructionGroup parent
    cdef object __weakref__
    cdef object __proxy_ref

    cdef void apply(self)
    cdef void flag_update(self, int do_parent=?)
    cdef void flag_update_done(self)
    cdef void set_parent(self, Instruction parent)
    cdef void reload(self)

    cdef void radd(self, InstructionGroup ig)
    cdef void rinsert(self, InstructionGroup ig, int index)
    cdef void rremove(self, InstructionGroup ig)

cdef class InstructionGroup(Instruction):
    cdef public list children
    cdef InstructionGroup compiled_children
    cdef GraphicsCompiler compiler
    cdef void build(self)
    cdef void reload(self)
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
    cdef void set_state(self, str name, value) except *
    cdef void push_state(self, str name) except *
    cdef void pop_state(self, str name) except *


from context_instructions cimport BindTexture

cdef class VertexInstruction(Instruction):
    cdef BindTexture texture_binding
    cdef VertexBatch batch
    cdef float _tex_coords[8]

    cdef void radd(self, InstructionGroup ig)
    cdef void rinsert(self, InstructionGroup ig, int index)
    cdef void rremove(self, InstructionGroup ig)

    cdef void build(self)

cdef class Callback(Instruction):
    cdef Shader _shader
    cdef object func
    cdef int _reset_context
    cdef void apply(self)
    cdef void enter(self)



cdef CanvasBase getActiveCanvas()

cdef class CanvasBase(InstructionGroup):
    pass

cdef class Canvas(CanvasBase):
    cdef float _opacity
    cdef CanvasBase _before
    cdef CanvasBase _after
    cdef void reload(self)
    cpdef clear(self)
    cpdef add(self, Instruction c)
    cpdef remove(self, Instruction c)
    cpdef draw(self)
    cdef void apply(self)


cdef class RenderContext(Canvas):
    cdef Shader _shader
    cdef dict state_stacks
    cdef Texture default_texture
    cdef dict bind_texture
    cdef int _use_parent_projection
    cdef int _use_parent_modelview

    cdef void set_texture(self, int index, Texture texture)
    cdef void set_state(self, str name, value, int apply_now=?)
    cdef get_state(self, str name)
    cdef void set_states(self, dict states) except *
    cdef void push_state(self, str name) except *
    cdef void push_states(self, list names) except *
    cdef void pop_state(self, str name) except *
    cdef void pop_states(self, list names) except *
    cdef void enter(self) except *
    cdef void leave(self) except *
    cdef void apply(self) except *
    cpdef draw(self)
    cdef void reload(self)

cdef RenderContext getActiveContext()
