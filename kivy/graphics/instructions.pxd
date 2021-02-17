include "../include/config.pxi"

cdef class Instruction
cdef class InstructionGroup
cdef class ContextInstruction
cdef class VertexInstruction
cdef class CanvasBase
cdef class Canvas
cdef class RenderContext

from .vbo cimport *
from .compiler cimport *
from .shader cimport *
from .texture cimport Texture
from kivy._event cimport ObjectWithUid

cdef void reset_gl_context()

cdef class Instruction
cdef class InstructionGroup(Instruction)

cdef class Instruction(ObjectWithUid):
    cdef int flags
    cdef public str group
    cdef InstructionGroup parent
    cdef object __weakref__
    cdef object __proxy_ref

    cdef int apply(self) except -1
    IF DEBUG:
        cpdef flag_update(self, int do_parent=?, list _instrs=?)
    ELSE:
        cpdef flag_update(self, int do_parent=?)
    cpdef flag_data_update(self)
    cdef void flag_update_done(self)
    cdef void set_parent(self, Instruction parent)
    cdef void reload(self) except *

    cdef void radd(self, InstructionGroup ig)
    cdef void rinsert(self, InstructionGroup ig, int index)
    cdef void rremove(self, InstructionGroup ig)

cdef class InstructionGroup(Instruction):
    cdef public list children
    cdef InstructionGroup compiled_children
    cdef GraphicsCompiler compiler
    cdef void build(self)
    cdef void reload(self) except *
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
    cdef int set_state(self, str name, value) except -1
    cdef int push_state(self, str name) except -1
    cdef int pop_state(self, str name) except -1


from .context_instructions cimport BindTexture

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
    cdef int apply(self) except -1
    cdef int enter(self) except -1



cdef CanvasBase getActiveCanvas()

cdef class CanvasBase(InstructionGroup):
    pass

cdef class Canvas(CanvasBase):
    cdef float _opacity
    cdef CanvasBase _before
    cdef CanvasBase _after
    cdef void reload(self) except *
    cpdef clear(self)
    cpdef add(self, Instruction c)
    cpdef remove(self, Instruction c)
    cpdef draw(self)
    cdef int apply(self) except -1


cdef class RenderContext(Canvas):
    cdef Shader _shader
    cdef dict state_stacks
    cdef Texture default_texture
    cdef dict bind_texture
    cdef int _use_parent_projection
    cdef int _use_parent_modelview
    cdef int _use_parent_frag_modelview

    cdef void set_texture(self, int index, Texture texture)
    cdef void set_state(self, str name, value, int apply_now=?)
    cdef get_state(self, str name)
    cdef int set_states(self, dict states) except -1
    cdef int push_state(self, str name) except -1
    cdef int push_states(self, list names) except -1
    cdef int pop_state(self, str name) except -1
    cdef int pop_states(self, list names) except -1
    cdef int enter(self) except -1
    cdef int leave(self) except -1
    cdef int apply(self) except -1
    cpdef draw(self)
    cdef void reload(self) except *

cdef RenderContext getActiveContext()
