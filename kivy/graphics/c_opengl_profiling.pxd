ctypedef void               GLvoid
ctypedef char               GLchar
ctypedef unsigned int       GLenum
ctypedef unsigned char      GLboolean
ctypedef unsigned int       GLbitfield
ctypedef short              GLshort
ctypedef int                GLint
ctypedef int                GLsizei
ctypedef unsigned short     GLushort
ctypedef unsigned int       GLuint
ctypedef signed char        GLbyte
ctypedef unsigned char      GLubyte
ctypedef float              GLfloat
ctypedef float              GLclampf
ctypedef int                GLfixed
ctypedef signed long int    GLintptr
ctypedef signed long int    GLsizeiptr

cdef void glBindTexture(GLenum target, GLuint texture) with gil
cdef void glTexImage2D(GLenum target, GLint level, GLint internalformat, GLsizei width, GLsizei height, GLint border, GLenum format, GLenum type, GLvoid* pixels) with gil
cdef void glDeleteTextures(GLsizei n, GLuint* textures) with gil
cdef void glBindBuffer(GLenum target, GLuint buffer) with gil
cdef void glBufferData(GLenum target, GLsizeiptr size, GLvoid* data, GLenum usage) with gil
cdef void glDeleteBuffers(GLsizei n, GLuint* buffers) with gil
