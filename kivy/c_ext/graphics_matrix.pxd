from kivy.c_ext.graphics_context cimport GraphicContext

cdef class MatrixStack:
    cdef list stack
    cdef GraphicContext context

    cpdef apply(self, mat)

