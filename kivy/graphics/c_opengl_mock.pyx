# XXX: remember to update c_opengl_debug.pyx and opengl.pyx with any functions
# that are added here.

include "common.pxi"
cimport kivy.graphics.c_opengl as cgl

cdef cgl.GLubyte *empty_str = ''

cdef cgl.GLenum glCheckFramebufferStatus(cgl.GLenum target) nogil:
    cdef cgl.GLuint ret = cgl.glCheckFramebufferStatus(target)
    return cgl.GL_FRAMEBUFFER_COMPLETE

cdef cgl.GLuint glCreateProgram() nogil:
    cdef cgl.GLuint ret = cgl.glCreateProgram()
    return <cgl.GLuint>1 if not <int>ret else ret

cdef cgl.GLuint glCreateShader(cgl.GLenum type) nogil:
    cdef cgl.GLuint ret = cgl.glCreateShader(type)
    return <cgl.GLuint>1 if not <int>ret else ret

#cdef int glGetAttribLocation(cgl.GLuint program,  cgl.GLchar* name) nogil

cdef cgl.GLenum glGetError() nogil:
    return cgl.GL_NO_ERROR

cdef cgl.GLubyte* glGetString(cgl.GLenum name) nogil:
    cdef cgl.GLubyte* ret = cgl.glGetString(name)
    return ret if ret else empty_str

#cdef int glGetUniformLocation(cgl.GLuint program,  cgl.GLchar* name) nogil:
#cdef cgl.GLboolean  glIsBuffer(cgl.GLuint buffer) nogil

cdef cgl.GLboolean  glIsEnabled(cgl.GLenum cap) nogil:
    return cgl.GL_TRUE

#cdef cgl.GLboolean  glIsFramebuffer(cgl.GLuint framebuffer) nogil
#cdef cgl.GLboolean  glIsProgram(cgl.GLuint program) nogil
#cdef cgl.GLboolean  glIsRenderbuffer(cgl.GLuint renderbuffer) nogil
#cdef cgl.GLboolean  glIsShader(cgl.GLuint shader) nogil
#cdef cgl.GLboolean  glIsTexture(cgl.GLuint texture) nogil
