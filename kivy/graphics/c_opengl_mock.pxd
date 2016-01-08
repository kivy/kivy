cimport kivy.graphics.c_opengl as cgl

cdef cgl.GLenum glCheckFramebufferStatus(cgl.GLenum target) nogil
cdef cgl.GLuint glCreateProgram() nogil
cdef cgl.GLuint glCreateShader(cgl.GLenum type) nogil
#cdef int    glGetAttribLocation(cgl.GLuint program,  cgl.GLchar* name) nogil
cdef cgl.GLenum glGetError() nogil
cdef cgl.GLubyte* glGetString(cgl.GLenum name) nogil
#cdef int    glGetUniformLocation(cgl.GLuint program,  cgl.GLchar* name) nogil
#cdef cgl.GLboolean  glIsBuffer(cgl.GLuint buffer) nogil
cdef cgl.GLboolean  glIsEnabled(cgl.GLenum cap) nogil
#cdef cgl.GLboolean  glIsFramebuffer(cgl.GLuint framebuffer) nogil
#cdef cgl.GLboolean  glIsProgram(cgl.GLuint program) nogil
#cdef cgl.GLboolean  glIsRenderbuffer(cgl.GLuint renderbuffer) nogil
#cdef cgl.GLboolean  glIsShader(cgl.GLuint shader) nogil
#cdef cgl.GLboolean  glIsTexture(cgl.GLuint texture) nogil
