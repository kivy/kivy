cdef class BindTexture

from graphics_instruction cimport ContextInstruction
from graphics_canvas cimport Canvas

cdef class LineWidth(ContextInstruction):
    cdef float lw
    cdef apply(self)

cdef class Color(ContextInstruction):
    cdef list color
    cdef apply(self)

cdef class CanvasDraw(ContextInstruction):
    cdef Canvas obj
    cdef apply(self)

cdef class BindTexture(ContextInstruction):
    cdef object _texture
    cdef apply(self)

cdef class PushMatrix(ContextInstruction):
    cdef apply(self)

cdef class PopMatrix(ContextInstruction):
    cdef apply(self)

cdef class MatrixInstruction(ContextInstruction):
    cdef object mat
    cdef apply(self)

cdef class Transform(MatrixInstruction):
    cpdef transform(self, object trans)
    cpdef translate(self, float tx, float ty, float tz)
    cpdef rotate(self, float angle, float ax, float ay, float az)
    cpdef scale(self, float s)
    cpdef identity(self)

cdef class Rotate(Transform):
    cdef float _angle
    cdef tuple _axis

cdef class Scale(Transform):
    cdef float s

cdef class Translate(Transform):
    cdef float _x, _y, _z

