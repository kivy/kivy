from c_opengl cimport GLfloat, GL_FLOAT

cdef list VERTEX_ATTRIBUTES = [
    {'name': 'vPosition',  'index': 0, 'size': 2, 'type': GL_FLOAT,
     'bytesize': sizeof(GLfloat) * 2, 'per_vertex': True},

    {'name': 'vTexCoords0', 'index': 1, 'size': 2, 'type': GL_FLOAT,
     'bytesize': sizeof(GLfloat) * 2, 'per_vertex': True},

    {'name': 'vTexCoords1', 'index': 2, 'size': 2, 'type': GL_FLOAT,
     'bytesize': sizeof(GLfloat) * 2, 'per_vertex': True},

    {'name': 'vTexCoords2',    'index': 3, 'size': 2, 'type': GL_FLOAT,
     'bytesize': sizeof(GLfloat) * 2, 'per_vertex': True},

    {'name': 'vColor',     'index': 4, 'size': 4, 'type': GL_FLOAT,
     'bytesize': sizeof(GLfloat) * 4, 'per_vertex': False}
]


cdef double pi = 3.1415926535897931
cdef extern from "math.h":
    double cos(double)
    double sin(double)
    double sqrt(double)


'''
Insruction type bitmask. Graphic Instruction Codes
bitmask to hold various graphic intrcution codes so its
possible to set the code on any GraphicInstruction
in order to let the compiler know how to handle it best
'''

cdef int GI_NOOP         = 1 << 0
cdef int GI_IGNORE       = 1 << 1
cdef int GI_VERTEX_DATA  = 1 << 2
cdef int GI_CONTEXT_MOD  = 1 << 3
cdef int GI_COMPILER	 = 1 << 4




