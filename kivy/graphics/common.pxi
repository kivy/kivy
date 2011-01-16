#
# Common definition
#

from c_opengl cimport GLfloat, GL_FLOAT

cdef list VERTEX_ATTRIBUTES = [
    {'name': 'vPosition',  'index': 0, 'size': 2, 'type': GL_FLOAT,
     'bytesize': sizeof(GLfloat) * 2, 'per_vertex': True},

    {'name': 'vTexCoords0', 'index': 1, 'size': 2, 'type': GL_FLOAT,
     'bytesize': sizeof(GLfloat) * 2, 'per_vertex': True},

   # {'name': 'vTexCoords1', 'index': 2, 'size': 2, 'type': GL_FLOAT,
   #  'bytesize': sizeof(GLfloat) * 2, 'per_vertex': True},

   # {'name': 'vTexCoords2',    'index': 3, 'size': 2, 'type': GL_FLOAT,
   #  'bytesize': sizeof(GLfloat) * 2, 'per_vertex': True},

   # {'name': 'vColor',     'index': 4, 'size': 4, 'type': GL_FLOAT,
   #  'bytesize': sizeof(GLfloat) * 4, 'per_vertex': False}
]


cdef double pi = 3.1415926535897931
cdef extern from "math.h":
    double cos(double)
    double sin(double)
    double sqrt(double)

