
cdef int GI_NOOP         = 1 << 0
cdef int GI_IGNORE       = 1 << 1
cdef int GI_GROUP        = 1 << 2
cdef int GI_VERTEX_DATA  = 1 << 3
cdef int GI_CONTEXT_MOD  = 1 << 4
cdef int GI_COMPILER	 = 1 << 5



cdef class GraphicsInstruction:
    def __cinit__(self):
        self.flags = 0
        self.parent = None

    cdef apply(self):
        pass



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



cdef class ContextInstruction(GraphicsInstruction):
    def __init__(self):
        self.flags &= GI_CONTEXT_MOD
        self.context_state = dict()

    cdef apply(self):
        pass
        #for key, val in self.context_state:
        #    self.shader.set_uniform(key, val)



cdef class VertexInstruction:
    def __init__(self):
        self.flags &= GI_VERTEX_DATA
        self.vertices = list()
        self.indices = list()

    cdef build(self):
        pass
