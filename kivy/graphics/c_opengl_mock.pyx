# XXX: remember to update c_opengl_debug.pyx and opengl.pyx with any functions
# that are added here.

include "common.pxi"
cimport kivy.graphics.c_opengl as cgl

cdef cgl.GLubyte *empty_str = ''

cdef cgl.GLenum glCheckFramebufferStatus(cgl.GLenum target) nogil:
    return cgl.GL_FRAMEBUFFER_COMPLETE
cdef cgl.GLuint glCreateProgram() nogil:
    return <cgl.GLuint>1
cdef cgl.GLuint glCreateShader(cgl.GLenum type) nogil:
    return <cgl.GLuint>1
cdef int glGetAttribLocation(cgl.GLuint program, cgl.GLchar* name) nogil:
    return 1
cdef cgl.GLenum glGetError() nogil:
    return cgl.GL_NO_ERROR
cdef cgl.GLubyte* glGetString(cgl.GLenum name) nogil:
    return empty_str
cdef int glGetUniformLocation(cgl.GLuint program,  cgl.GLchar* name) nogil:
    1
cdef cgl.GLboolean glIsBuffer(cgl.GLuint buffer) nogil:
    return cgl.GL_TRUE
cdef cgl.GLboolean  glIsEnabled(cgl.GLenum cap) nogil:
    return cgl.GL_TRUE
cdef cgl.GLboolean glIsFramebuffer(cgl.GLuint framebuffer) nogil:
    return cgl.GL_TRUE
cdef cgl.GLboolean glIsProgram(cgl.GLuint program) nogil:
    return cgl.GL_TRUE
cdef cgl.GLboolean glIsRenderbuffer(cgl.GLuint renderbuffer) nogil:
    return cgl.GL_TRUE
cdef cgl.GLboolean glIsShader(cgl.GLuint shader) nogil:
    return cgl.GL_TRUE
cdef cgl.GLboolean glIsTexture(cgl.GLuint texture) nogil:
    return cgl.GL_TRUE



cdef void glActiveTexture(cgl.GLenum texture) nogil:
    pass
cdef void glAttachShader(cgl.GLuint program, cgl.GLuint shader) nogil:
    pass
cdef void glBindAttribLocation(cgl.GLuint program, cgl.GLuint index, cgl.GLchar* name) nogil:
    pass
cdef void glBindBuffer(cgl.GLenum target, cgl.GLuint buffer) nogil:
    pass
cdef void glBindFramebuffer(cgl.GLenum target, cgl.GLuint framebuffer) nogil:
    pass
cdef void glBindRenderbuffer(cgl.GLenum target, cgl.GLuint renderbuffer) nogil:
    pass
cdef void glBindTexture(cgl.GLenum target, cgl.GLuint texture) nogil:
    pass
cdef void glBlendColor(cgl.GLclampf red, cgl.GLclampf green, cgl.GLclampf blue, cgl.GLclampf alpha) nogil:
    pass
cdef void glBlendEquation( cgl.GLenum mode ) nogil:
    pass
cdef void glBlendEquationSeparate(cgl.GLenum modeRGB, cgl.GLenum modeAlpha) nogil:
    pass
cdef void glBlendFunc(cgl.GLenum sfactor, cgl.GLenum dfactor) nogil:
    pass
cdef void glBlendFuncSeparate(cgl.GLenum srcRGB, cgl.GLenum dstRGB, cgl.GLenum srcAlpha, cgl.GLenum dstAlpha) nogil:
    pass
cdef void glBufferData(cgl.GLenum target, cgl.GLsizeiptr size, cgl.GLvoid* data, cgl.GLenum usage) nogil:
    pass
cdef void glBufferSubData(cgl.GLenum target, cgl.GLintptr offset, cgl.GLsizeiptr size, cgl.GLvoid* data) nogil:
    pass
cdef void glClear(cgl.GLbitfield mask) nogil:
    pass
cdef void glClearColor(cgl.GLclampf red, cgl.GLclampf green, cgl.GLclampf blue, cgl.GLclampf alpha) nogil:
    pass
cdef void glClearDepthf(cgl.GLclampf depth) nogil:
    pass
cdef void glClearStencil(cgl.GLint s) nogil:
    pass
cdef void glColorMask(cgl.GLboolean red, cgl.GLboolean green, cgl.GLboolean blue, cgl.GLboolean alpha) nogil:
    pass
cdef void glCompileShader(cgl.GLuint shader) nogil:
    pass
cdef void glCompressedTexImage2D(cgl.GLenum target, cgl.GLint level, cgl.GLenum internalformat, cgl.GLsizei width, cgl.GLsizei height, cgl.GLint border, cgl.GLsizei imageSize, cgl.GLvoid* data) nogil:
    pass
cdef void glCompressedTexSubImage2D(cgl.GLenum target, cgl.GLint level, cgl.GLint xoffset, cgl.GLint yoffset, cgl.GLsizei width, cgl.GLsizei height, cgl.GLenum format, cgl.GLsizei imageSize, cgl.GLvoid* data) nogil:
    pass
cdef void glCopyTexImage2D(cgl.GLenum target, cgl.GLint level, cgl.GLenum internalformat, cgl.GLint x, cgl.GLint y, cgl.GLsizei width, cgl.GLsizei height, cgl.GLint border) nogil:
    pass
cdef void glCopyTexSubImage2D(cgl.GLenum target, cgl.GLint level, cgl.GLint xoffset, cgl.GLint yoffset, cgl.GLint x, cgl.GLint y, cgl.GLsizei width, cgl.GLsizei height) nogil:
    pass
cdef void glCullFace(cgl.GLenum mode) nogil:
    pass
cdef void glDeleteBuffers(cgl.GLsizei n, cgl.GLuint* buffers) nogil:
    pass
cdef void glDeleteFramebuffers(cgl.GLsizei n, cgl.GLuint* framebuffers) nogil:
    pass
cdef void glDeleteProgram(cgl.GLuint program) nogil:
    pass
cdef void glDeleteRenderbuffers(cgl.GLsizei n, cgl.GLuint* renderbuffers) nogil:
    pass
cdef void glDeleteShader(cgl.GLuint shader) nogil:
    pass
cdef void glDeleteTextures(cgl.GLsizei n, cgl.GLuint* textures) nogil:
    pass
cdef void glDepthFunc(cgl.GLenum func) nogil:
    pass
cdef void glDepthMask(cgl.GLboolean flag) nogil:
    pass
cdef void glDepthRangef(cgl.GLclampf zNear, cgl.GLclampf zFar) nogil:
    pass
cdef void glDetachShader(cgl.GLuint program, cgl.GLuint shader) nogil:
    pass
cdef void glDisable(cgl.GLenum cap) nogil:
    pass
cdef void glDisableVertexAttribArray(cgl.GLuint index) nogil:
    pass
cdef void glDrawArrays(cgl.GLenum mode, cgl.GLint first, cgl.GLsizei count) nogil:
    pass
cdef void glDrawElements(cgl.GLenum mode, cgl.GLsizei count, cgl.GLenum type, cgl.GLvoid* indices) nogil:
    pass
cdef void glEnable(cgl.GLenum cap) nogil:
    pass
cdef void glEnableVertexAttribArray(cgl.GLuint index) nogil:
    pass
cdef void glFinish() nogil:
    pass
cdef void glFlush() nogil:
    pass
cdef void glFramebufferRenderbuffer(cgl.GLenum target, cgl.GLenum attachment, cgl.GLenum renderbuffertarget, cgl.GLuint renderbuffer) nogil:
    pass
cdef void glFramebufferTexture2D(cgl.GLenum target, cgl.GLenum attachment, cgl.GLenum textarget, cgl.GLuint texture, cgl.GLint level) nogil:
    pass
cdef void glFrontFace(cgl.GLenum mode) nogil:
    pass
cdef void glGenBuffers(cgl.GLsizei n, cgl.GLuint* buffers) nogil:
    pass
cdef void glGenerateMipmap(cgl.GLenum target) nogil:
    pass
cdef void glGenFramebuffers(cgl.GLsizei n, cgl.GLuint* framebuffers) nogil:
    pass
cdef void glGenRenderbuffers(cgl.GLsizei n, cgl.GLuint* renderbuffers) nogil:
    pass
cdef void glGenTextures(cgl.GLsizei n, cgl.GLuint* textures) nogil:
    pass
cdef void glGetActiveAttrib(cgl.GLuint program, cgl.GLuint index, cgl.GLsizei bufsize, cgl.GLsizei* length, cgl.GLint* size, cgl.GLenum* type, cgl.GLchar* name) nogil:
    pass
cdef void glGetActiveUniform(cgl.GLuint program, cgl.GLuint index, cgl.GLsizei bufsize, cgl.GLsizei* length, cgl.GLint* size, cgl.GLenum* type, cgl.GLchar* name) nogil:
    pass
cdef void glGetAttachedShaders(cgl.GLuint program, cgl.GLsizei maxcount, cgl.GLsizei* count, cgl.GLuint* shaders) nogil:
    pass
cdef void glGetBooleanv(cgl.GLenum pname, cgl.GLboolean* params) nogil:
    pass
cdef void glGetBufferParameteriv(cgl.GLenum target, cgl.GLenum pname, cgl.GLint* params) nogil:
    pass
cdef void glGetFloatv(cgl.GLenum pname, cgl.GLfloat* params) nogil:
    pass
cdef void glGetFramebufferAttachmentParameteriv(cgl.GLenum target, cgl.GLenum attachment, cgl.GLenum pname, cgl.GLint* params) nogil:
    pass
cdef void glGetIntegerv(cgl.GLenum pname, cgl.GLint* params) nogil:
    pass
cdef void glGetProgramiv(cgl.GLuint program, cgl.GLenum pname, cgl.GLint* params) nogil:
    pass
cdef void glGetProgramInfoLog(cgl.GLuint program, cgl.GLsizei bufsize, cgl.GLsizei* length, cgl.GLchar* infolog) nogil:
    pass
cdef void glGetRenderbufferParameteriv(cgl.GLenum target, cgl.GLenum pname, cgl.GLint* params) nogil:
    pass
cdef void glGetShaderiv(cgl.GLuint shader, cgl.GLenum pname, cgl.GLint* params) nogil:
    pass
cdef void glGetShaderInfoLog(cgl.GLuint shader, cgl.GLsizei bufsize, cgl.GLsizei* length, cgl.GLchar* infolog) nogil:
    pass
cdef void glGetShaderPrecisionFormat(cgl.GLenum shadertype, cgl.GLenum precisiontype, cgl.GLint* range, cgl.GLint* precision) nogil:
    pass
cdef void glGetShaderSource(cgl.GLuint shader, cgl.GLsizei bufsize, cgl.GLsizei* length, cgl.GLchar* source) nogil:
    pass
cdef void glGetTexParameterfv(cgl.GLenum target, cgl.GLenum pname, cgl.GLfloat* params) nogil:
    pass
cdef void glGetTexParameteriv(cgl.GLenum target, cgl.GLenum pname, cgl.GLint* params) nogil:
    pass
cdef void glGetUniformfv(cgl.GLuint program, cgl.GLint location, cgl.GLfloat* params) nogil:
    pass
cdef void glGetUniformiv(cgl.GLuint program, cgl.GLint location, cgl.GLint* params) nogil:
    pass
cdef void glGetVertexAttribfv(cgl.GLuint index, cgl.GLenum pname, cgl.GLfloat* params) nogil:
    pass
cdef void glGetVertexAttribiv(cgl.GLuint index, cgl.GLenum pname, cgl.GLint* params) nogil:
    pass
cdef void glGetVertexAttribPointerv(cgl.GLuint index, cgl.GLenum pname, cgl.GLvoid** pointer) nogil:
    pass
cdef void glHint(cgl.GLenum target, cgl.GLenum mode) nogil:
    pass
cdef void glLineWidth(cgl.GLfloat width) nogil:
    pass
cdef void glLinkProgram(cgl.GLuint program) nogil:
    pass
cdef void glPixelStorei(cgl.GLenum pname, cgl.GLint param) nogil:
    pass
cdef void glPolygonOffset(cgl.GLfloat factor, cgl.GLfloat units) nogil:
    pass
cdef void glReadPixels(cgl.GLint x, cgl.GLint y, cgl.GLsizei width, cgl.GLsizei height, cgl.GLenum format, cgl.GLenum type, cgl.GLvoid* pixels) nogil:
    pass
cdef void glReleaseShaderCompiler() nogil:
    pass
cdef void glRenderbufferStorage(cgl.GLenum target, cgl.GLenum internalformat, cgl.GLsizei width, cgl.GLsizei height) nogil:
    pass
cdef void glSampleCoverage(cgl.GLclampf value, cgl.GLboolean invert) nogil:
    pass
cdef void glScissor(cgl.GLint x, cgl.GLint y, cgl.GLsizei width, cgl.GLsizei height) nogil:
    pass
cdef void glShaderBinary(cgl.GLsizei n, cgl.GLuint* shaders, cgl.GLenum binaryformat, cgl.GLvoid* binary, cgl.GLsizei length) nogil:
    pass
cdef void glShaderSource(cgl.GLuint shader, cgl.GLsizei count, cgl.GLchar** string, cgl.GLint* length) nogil:
    pass
cdef void glStencilFunc(cgl.GLenum func, cgl.GLint ref, cgl.GLuint mask) nogil:
    pass
cdef void glStencilFuncSeparate(cgl.GLenum face, cgl.GLenum func, cgl.GLint ref, cgl.GLuint mask) nogil:
    pass
cdef void glStencilMask(cgl.GLuint mask) nogil:
    pass
cdef void glStencilMaskSeparate(cgl.GLenum face, cgl.GLuint mask) nogil:
    pass
cdef void glStencilOp(cgl.GLenum fail, cgl.GLenum zfail, cgl.GLenum zpass) nogil:
    pass
cdef void glStencilOpSeparate(cgl.GLenum face, cgl.GLenum fail, cgl.GLenum zfail, cgl.GLenum zpass) nogil:
    pass
cdef void glTexImage2D(cgl.GLenum target, cgl.GLint level, cgl.GLint internalformat, cgl.GLsizei width, cgl.GLsizei height, cgl.GLint border, cgl.GLenum format, cgl.GLenum type, cgl.GLvoid* pixels) nogil:
    pass
cdef void glTexParameterf(cgl.GLenum target, cgl.GLenum pname, cgl.GLfloat param) nogil:
    pass
cdef void glTexParameterfv(cgl.GLenum target, cgl.GLenum pname, cgl.GLfloat* params) nogil:
    pass
cdef void glTexParameteri(cgl.GLenum target, cgl.GLenum pname, cgl.GLint param) nogil:
    pass
cdef void glTexParameteriv(cgl.GLenum target, cgl.GLenum pname, cgl.GLint* params) nogil:
    pass
cdef void glTexSubImage2D(cgl.GLenum target, cgl.GLint level, cgl.GLint xoffset, cgl.GLint yoffset, cgl.GLsizei width, cgl.GLsizei height, cgl.GLenum format, cgl.GLenum type, cgl.GLvoid* pixels) nogil:
    pass
cdef void glUniform1f(cgl.GLint location, cgl.GLfloat x) nogil:
    pass
cdef void glUniform1fv(cgl.GLint location, cgl.GLsizei count, cgl.GLfloat* v) nogil:
    pass
cdef void glUniform1i(cgl.GLint location, cgl.GLint x) nogil:
    pass
cdef void glUniform1iv(cgl.GLint location, cgl.GLsizei count, cgl.GLint* v) nogil:
    pass
cdef void glUniform2f(cgl.GLint location, cgl.GLfloat x, cgl.GLfloat y) nogil:
    pass
cdef void glUniform2fv(cgl.GLint location, cgl.GLsizei count, cgl.GLfloat* v) nogil:
    pass
cdef void glUniform2i(cgl.GLint location, cgl.GLint x, cgl.GLint y) nogil:
    pass
cdef void glUniform2iv(cgl.GLint location, cgl.GLsizei count, cgl.GLint* v) nogil:
    pass
cdef void glUniform3f(cgl.GLint location, cgl.GLfloat x, cgl.GLfloat y, cgl.GLfloat z) nogil:
    pass
cdef void glUniform3fv(cgl.GLint location, cgl.GLsizei count, cgl.GLfloat* v) nogil:
    pass
cdef void glUniform3i(cgl.GLint location, cgl.GLint x, cgl.GLint y, cgl.GLint z) nogil:
    pass
cdef void glUniform3iv(cgl.GLint location, cgl.GLsizei count, cgl.GLint* v) nogil:
    pass
cdef void glUniform4f(cgl.GLint location, cgl.GLfloat x, cgl.GLfloat y, cgl.GLfloat z, cgl.GLfloat w) nogil:
    pass
cdef void glUniform4fv(cgl.GLint location, cgl.GLsizei count, cgl.GLfloat* v) nogil:
    pass
cdef void glUniform4i(cgl.GLint location, cgl.GLint x, cgl.GLint y, cgl.GLint z, cgl.GLint w) nogil:
    pass
cdef void glUniform4iv(cgl.GLint location, cgl.GLsizei count, cgl.GLint* v) nogil:
    pass
cdef void glUniformMatrix2fv(cgl.GLint location, cgl.GLsizei count, cgl.GLboolean transpose, cgl.GLfloat* value) nogil:
    pass
cdef void glUniformMatrix3fv(cgl.GLint location, cgl.GLsizei count, cgl.GLboolean transpose, cgl.GLfloat* value) nogil:
    pass
cdef void glUniformMatrix4fv(cgl.GLint location, cgl.GLsizei count, cgl.GLboolean transpose, cgl.GLfloat* value) nogil:
    pass
cdef void glUseProgram(cgl.GLuint program) nogil:
    pass
cdef void glValidateProgram(cgl.GLuint program) nogil:
    pass
cdef void glVertexAttrib1f(cgl.GLuint indx, cgl.GLfloat x) nogil:
    pass
cdef void glVertexAttrib1fv(cgl.GLuint indx, cgl.GLfloat* values) nogil:
    pass
cdef void glVertexAttrib2f(cgl.GLuint indx, cgl.GLfloat x, cgl.GLfloat y) nogil:
    pass
cdef void glVertexAttrib2fv(cgl.GLuint indx, cgl.GLfloat* values) nogil:
    pass
cdef void glVertexAttrib3f(cgl.GLuint indx, cgl.GLfloat x, cgl.GLfloat y, cgl.GLfloat z) nogil:
    pass
cdef void glVertexAttrib3fv(cgl.GLuint indx, cgl.GLfloat* values) nogil:
    pass
cdef void glVertexAttrib4f(cgl.GLuint indx, cgl.GLfloat x, cgl.GLfloat y, cgl.GLfloat z, cgl.GLfloat w) nogil:
    pass
cdef void glVertexAttrib4fv(cgl.GLuint indx, cgl.GLfloat* values) nogil:
    pass
cdef void glVertexAttribPointer(cgl.GLuint indx, cgl.GLint size, cgl.GLenum type, cgl.GLboolean normalized, cgl.GLsizei stride, cgl.GLvoid* ptr) nogil:
    pass
cdef void glViewport(cgl.GLint x, cgl.GLint y, cgl.GLsizei width, cgl.GLsizei height) nogil:
    pass
