cdef class GraphicInstruction
cdef class ContextInstruction

from graphics_canvas cimport Canvas
from graphics_context cimport GraphicContext

cdef class GraphicInstruction:

    #: Graphic instruction op code
    cdef int code

    #: Canvas on which to operate
    cdef Canvas canvas

cdef class ContextInstruction(GraphicInstruction):
    cdef GraphicContext context

    cdef apply(self)

