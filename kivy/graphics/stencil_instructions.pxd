from kivy.graphics.instructions cimport Instruction

cdef get_stencil_state()
cdef void restore_stencil_state(dict state)
cdef void reset_stencil_state()

cdef class StencilPush(Instruction):
    cdef int apply(self) except -1

cdef class StencilPop(Instruction):
    cdef int apply(self) except -1

cdef class StencilUse(Instruction):
    cdef int _op
    cdef int apply(self) except -1

cdef class StencilUnUse(Instruction):
    cdef int apply(self) except -1
