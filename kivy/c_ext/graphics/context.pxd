
from shader cimport *
from instructions cimport *

cdef class RenderContext(GraphicsGroup):
    cdef Shader shader
