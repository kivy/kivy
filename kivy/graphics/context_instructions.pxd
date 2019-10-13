cdef class LineWidth
cdef class Color
cdef class BindTexture

from .transformation cimport Matrix
from .instructions cimport ContextInstruction
from .texture cimport Texture

cdef class PushState(ContextInstruction):
    pass

cdef class ChangeState(ContextInstruction):
    pass

cdef class PopState(ContextInstruction):
    pass

cdef class LineWidth(ContextInstruction):
    cdef int apply(self) except -1

cdef class Color(ContextInstruction):
    cdef int apply(self) except -1

cdef class BindTexture(ContextInstruction):
    cdef int _index
    cdef object _source
    cdef Texture _texture
    cdef int apply(self) except -1


cdef class LoadIdentity(ContextInstruction):
    pass

cdef class PushMatrix(ContextInstruction):
    cdef int apply(self) except -1

cdef class PopMatrix(ContextInstruction):
    cdef int apply(self) except -1

cdef class ApplyContextMatrix(ContextInstruction):
    cdef object _target_stack
    cdef object _source_stack
    cdef int apply(self) except -1

cdef class UpdateNormalMatrix(ContextInstruction):
    cdef int apply(self) except -1

cdef class MatrixInstruction(ContextInstruction):
    cdef object _stack
    cdef Matrix _matrix
    cdef int apply(self) except -1

cdef class Transform(MatrixInstruction):
    cpdef transform(self, Matrix trans)
    cpdef translate(self, float tx, float ty, float tz)
    cpdef rotate(self, float angle, float ax, float ay, float az)
    cpdef scale(self, float s)
    cpdef identity(self)

cdef class Rotate(Transform):
    cdef float _angle
    cdef tuple _axis
    cdef tuple _origin
    cdef int apply(self) except -1
    cdef void compute(self)

cdef class Scale(Transform):
    cdef tuple _origin
    cdef double _x, _y, _z
    cdef int apply(self) except -1
    cdef set_scale(self, double x, double y, double z)

cdef class Translate(Transform):
    cdef double _x, _y, _z
    cdef int apply(self) except -1
    cdef set_translate(self, double x, double y, double z)

