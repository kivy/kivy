include "graphics_common.pxi"

from graphics_canvas cimport Canvas

cdef class GraphicInstruction:
    def __init__(self, int code):
        self.code = code
        self.canvas = Canvas.active()

cdef class ContextInstruction(GraphicInstruction):
    '''Abstract Base class for GraphicInstructions that modidifies the
    context. (so that canvas/compiler can know about how to optimize).
    '''

    def __init__(self, *args, **kwargs):
        GraphicInstruction.__init__(self, GI_CONTEXT_MOD)
        self.context = self.canvas.context
        self.canvas.add(self)

    cdef apply(self):
        pass


