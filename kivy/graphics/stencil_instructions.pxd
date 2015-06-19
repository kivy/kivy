from kivy.graphics.instructions cimport Instruction

cdef class StencilPush(Instruction):
    cdef int apply(self) except -1 
cdef class StencilPop(Instruction):
    cdef int apply(self) except -1
cdef class StencilUse(Instruction):
    cdef unsigned int _op
    cdef int apply(self) except -1
cdef class StencilUnUse(Instruction):
    cdef int apply(self) except -1
