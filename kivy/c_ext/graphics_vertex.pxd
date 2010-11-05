from c_opengl cimport GLfloat, GL_FLOAT

#: Vertex data struct
cdef struct vertex:
    GLfloat x, y
    GLfloat s0, t0 
    GLfloat s1, t1
    GLfloat s2, t2

cdef vertex vertex8f(GLfloat x, GLfloat y, GLfloat s0, GLfloat t0,
                     GLfloat s1, GLfloat t1, GLfloat s2, GLfloat t2)

cdef vertex vertex6f(GLfloat x, GLfloat y, GLfloat s0, GLfloat t0,
                     GLfloat s1, GLfloat t1)

cdef vertex vertex4f(GLfloat x, GLfloat y, GLfloat s0, GLfloat t0)
    
cdef vertex vertex2f(GLfloat x, GLfloat y)


