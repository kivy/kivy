from kivy.graphics.instructions cimport Instruction

cdef class StencilPush(Instruction):
    cdef void apply(self)
cdef class StencilPop(Instruction):
    cdef void apply(self)
cdef class StencilUse(Instruction):
    cdef unsigned int _op
    cdef void apply(self)
cdef class StencilUnUse(Instruction):
    cdef void apply(self)
