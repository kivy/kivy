include "opcodes.pxi"

from context cimport *
from canvas cimport *





cdef class GraphicsInstruction:
    def __cinit__(self):
        self.flags = 0

    def __init__(self):
        self.parent = getActiveCanvas()
        if self.parent:
            self.parent.add(self)

    cdef apply(self):
        pass

    cdef flag_update(self):
        if self.parent:
            self.parent.flag_udate()
        self.flags &= GI_NEED_UPDATE

    cdef flag_update_done(self):
        self.flags &= ~GI_NEED_UPDATE



cdef class InstructionGroup(GraphicsInstruction):
    def __init__(self):
        self.children = list()

    cdef apply(self):
        cdef GraphicsInstruction c
        for c in self.children:
            c.apply()

    cpdef add(self, GraphicsInstruction c):
        c.parent = self
        self.children.append(c)
        self.flag_update()



cdef class ContextInstruction(GraphicsInstruction):
    def __init__(self):
        self.flags &= GI_CONTEXT_MOD
        self.context_state = dict()

    cdef apply(self):
        getActiveContext().set_states(self.context_state)

    cdef set_state(self, str name, value):
        self.context_state[name] = value
        self.flag_update()



cdef class VertexInstruction(GraphicsInstruction):
    def __init__(self):
        self.flags = GI_VERTEX_DATA
        self.batch = VertexBatch()
        self.vertices = list()
        self.indices = list()
        
    cdef build(self):
        pass

    cdef update_batch(self):
        self.batch.set_data(self.vertices, self.indices)
        self.flag_update_done()

    cdef apply(self):
        if self.need_build:
            self.build()
            self.update_batch()

        self.batch.draw()
        
