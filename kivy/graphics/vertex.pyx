
cdef class Vertex:

    def __init__(self, x, y, s0=0,t0=0, s1=0,t1=0, s2=0,t2=0):
        self.data.x = x
        self.data.y = y
        self.data.s0 = s0
        self.data.t0 = t0
        self.data.s1 = s1
        self.data.t1 = t1
        self.data.s2 = s2
        self.data.t2 = t2

    def __repr__(self):
        return "vertex: x=%.2f, y=%.2f, s0=%.2f, t0=%.2f" %(self.data.x, self.data.y, self.data.s0, self.data.t0)
