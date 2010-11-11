
from c_opengl cimport GLfloat, GL_FLOAT

cdef vertex vertex8f(GLfloat x, GLfloat y, GLfloat s0, GLfloat t0, GLfloat s1, GLfloat t1, GLfloat s2, GLfloat t2):
    cdef vertex v
    v.x  = x;   v.y  = y
    v.s0 = s0;  v.t0 = t0
    v.s1 = s1;  v.t1 = t1
    v.s2 = s2;  v.t2 = t2
    return v

cdef vertex vertex6f(GLfloat x, GLfloat y, GLfloat s0, GLfloat t0, GLfloat s1, GLfloat t1):
    return vertex8f(x,y,s0,t0,s1,t1,0.0,0.0)

cdef vertex vertex4f(GLfloat x, GLfloat y, GLfloat s0, GLfloat t0):
    return vertex8f(x,y,s0,t0,0.0,0.0,0.0,0.0)

cdef vertex vertex2f(GLfloat x, GLfloat y):
    return vertex8f(x,y,0.0,0.0,0.0,0.0,0.0,0.0)


