
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

    cdef set_pos(self, float x, float y):
        self.data.x = x
        self.data.y = y

    cdef set_tc0(self, float s, float t):
        self.data.s0 = s
        self.data.t0 = t

    cdef set_tc1(self, float s, float t):
        self.data.s1 = s
        self.data.t1 = t

    cdef set_tc2(self, float s, float t):
        self.data.s2 = s
        self.data.t2 = t


    def __repr__(self):
        return "vertex: x=%d, y=%d" %(self.data.x, self.data.y)
