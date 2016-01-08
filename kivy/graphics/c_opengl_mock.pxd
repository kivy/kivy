cimport kivy.graphics.c_opengl as cgl

cdef cgl.GLenum glCheckFramebufferStatus(cgl.GLenum target) nogil
cdef cgl.GLuint glCreateProgram() nogil
cdef cgl.GLuint glCreateShader(cgl.GLenum type) nogil
cdef int glGetAttribLocation(cgl.GLuint program, cgl.GLchar* name) nogil
cdef cgl.GLenum glGetError() nogil
cdef cgl.GLubyte* glGetString(cgl.GLenum name) nogil
cdef int glGetUniformLocation(cgl.GLuint program, cgl.GLchar* name) nogil
cdef cgl.GLboolean glIsBuffer(cgl.GLuint buffer) nogil
cdef cgl.GLboolean glIsEnabled(cgl.GLenum cap) nogil
cdef cgl.GLboolean glIsFramebuffer(cgl.GLuint framebuffer) nogil
cdef cgl.GLboolean glIsProgram(cgl.GLuint program) nogil
cdef cgl.GLboolean glIsRenderbuffer(cgl.GLuint renderbuffer) nogil
cdef cgl.GLboolean glIsShader(cgl.GLuint shader) nogil
cdef cgl.GLboolean glIsTexture(cgl.GLuint texture) nogil


cdef void glActiveTexture(cgl.GLenum texture) nogil
cdef void glAttachShader(cgl.GLuint program, cgl.GLuint shader) nogil
cdef void glBindAttribLocation(cgl.GLuint program, cgl.GLuint index, cgl.GLchar* name) nogil
cdef void glBindBuffer(cgl.GLenum target, cgl.GLuint buffer) nogil
cdef void glBindFramebuffer(cgl.GLenum target, cgl.GLuint framebuffer) nogil
cdef void glBindRenderbuffer(cgl.GLenum target, cgl.GLuint renderbuffer) nogil
cdef void glBindTexture(cgl.GLenum target, cgl.GLuint texture) nogil
cdef void glBlendColor(cgl.GLclampf red, cgl.GLclampf green, cgl.GLclampf blue, cgl.GLclampf alpha) nogil
cdef void glBlendEquation( cgl.GLenum mode ) nogil
cdef void glBlendEquationSeparate(cgl.GLenum modeRGB, cgl.GLenum modeAlpha) nogil
cdef void glBlendFunc(cgl.GLenum sfactor, cgl.GLenum dfactor) nogil
cdef void glBlendFuncSeparate(cgl.GLenum srcRGB, cgl.GLenum dstRGB, cgl.GLenum srcAlpha, cgl.GLenum dstAlpha) nogil
cdef void glBufferData(cgl.GLenum target, cgl.GLsizeiptr size, cgl.GLvoid* data, cgl.GLenum usage) nogil
cdef void glBufferSubData(cgl.GLenum target, cgl.GLintptr offset, cgl.GLsizeiptr size, cgl.GLvoid* data) nogil
cdef void glClear(cgl.GLbitfield mask) nogil
cdef void glClearColor(cgl.GLclampf red, cgl.GLclampf green, cgl.GLclampf blue, cgl.GLclampf alpha) nogil
cdef void glClearDepthf(cgl.GLclampf depth) nogil
cdef void glClearStencil(cgl.GLint s) nogil
cdef void glColorMask(cgl.GLboolean red, cgl.GLboolean green, cgl.GLboolean blue, cgl.GLboolean alpha) nogil
cdef void glCompileShader(cgl.GLuint shader) nogil
cdef void glCompressedTexImage2D(cgl.GLenum target, cgl.GLint level, cgl.GLenum internalformat, cgl.GLsizei width, cgl.GLsizei height, cgl.GLint border, cgl.GLsizei imageSize, cgl.GLvoid* data) nogil
cdef void glCompressedTexSubImage2D(cgl.GLenum target, cgl.GLint level, cgl.GLint xoffset, cgl.GLint yoffset, cgl.GLsizei width, cgl.GLsizei height, cgl.GLenum format, cgl.GLsizei imageSize, cgl.GLvoid* data) nogil
cdef void glCopyTexImage2D(cgl.GLenum target, cgl.GLint level, cgl.GLenum internalformat, cgl.GLint x, cgl.GLint y, cgl.GLsizei width, cgl.GLsizei height, cgl.GLint border) nogil
cdef void glCopyTexSubImage2D(cgl.GLenum target, cgl.GLint level, cgl.GLint xoffset, cgl.GLint yoffset, cgl.GLint x, cgl.GLint y, cgl.GLsizei width, cgl.GLsizei height) nogil
cdef void glCullFace(cgl.GLenum mode) nogil
cdef void glDeleteBuffers(cgl.GLsizei n, cgl.GLuint* buffers) nogil
cdef void glDeleteFramebuffers(cgl.GLsizei n, cgl.GLuint* framebuffers) nogil
cdef void glDeleteProgram(cgl.GLuint program) nogil
cdef void glDeleteRenderbuffers(cgl.GLsizei n, cgl.GLuint* renderbuffers) nogil
cdef void glDeleteShader(cgl.GLuint shader) nogil
cdef void glDeleteTextures(cgl.GLsizei n, cgl.GLuint* textures) nogil
cdef void glDepthFunc(cgl.GLenum func) nogil
cdef void glDepthMask(cgl.GLboolean flag) nogil
cdef void glDepthRangef(cgl.GLclampf zNear, cgl.GLclampf zFar) nogil
cdef void glDetachShader(cgl.GLuint program, cgl.GLuint shader) nogil
cdef void glDisable(cgl.GLenum cap) nogil
cdef void glDisableVertexAttribArray(cgl.GLuint index) nogil
cdef void glDrawArrays(cgl.GLenum mode, cgl.GLint first, cgl.GLsizei count) nogil
cdef void glDrawElements(cgl.GLenum mode, cgl.GLsizei count, cgl.GLenum type, cgl.GLvoid* indices) nogil
cdef void glEnable(cgl.GLenum cap) nogil
cdef void glEnableVertexAttribArray(cgl.GLuint index) nogil
cdef void glFinish() nogil
cdef void glFlush() nogil
cdef void glFramebufferRenderbuffer(cgl.GLenum target, cgl.GLenum attachment, cgl.GLenum renderbuffertarget, cgl.GLuint renderbuffer) nogil
cdef void glFramebufferTexture2D(cgl.GLenum target, cgl.GLenum attachment, cgl.GLenum textarget, cgl.GLuint texture, cgl.GLint level) nogil
cdef void glFrontFace(cgl.GLenum mode) nogil
cdef void glGenBuffers(cgl.GLsizei n, cgl.GLuint* buffers) nogil
cdef void glGenerateMipmap(cgl.GLenum target) nogil
cdef void glGenFramebuffers(cgl.GLsizei n, cgl.GLuint* framebuffers) nogil
cdef void glGenRenderbuffers(cgl.GLsizei n, cgl.GLuint* renderbuffers) nogil
cdef void glGenTextures(cgl.GLsizei n, cgl.GLuint* textures) nogil
cdef void glGetActiveAttrib(cgl.GLuint program, cgl.GLuint index, cgl.GLsizei bufsize, cgl.GLsizei* length, cgl.GLint* size, cgl.GLenum* type, cgl.GLchar* name) nogil
cdef void glGetActiveUniform(cgl.GLuint program, cgl.GLuint index, cgl.GLsizei bufsize, cgl.GLsizei* length, cgl.GLint* size, cgl.GLenum* type, cgl.GLchar* name) nogil
cdef void glGetAttachedShaders(cgl.GLuint program, cgl.GLsizei maxcount, cgl.GLsizei* count, cgl.GLuint* shaders) nogil
cdef void glGetBooleanv(cgl.GLenum pname, cgl.GLboolean* params) nogil
cdef void glGetBufferParameteriv(cgl.GLenum target, cgl.GLenum pname, cgl.GLint* params) nogil
cdef void glGetFloatv(cgl.GLenum pname, cgl.GLfloat* params) nogil
cdef void glGetFramebufferAttachmentParameteriv(cgl.GLenum target, cgl.GLenum attachment, cgl.GLenum pname, cgl.GLint* params) nogil
cdef void glGetIntegerv(cgl.GLenum pname, cgl.GLint* params) nogil
cdef void glGetProgramiv(cgl.GLuint program, cgl.GLenum pname, cgl.GLint* params) nogil
cdef void glGetProgramInfoLog(cgl.GLuint program, cgl.GLsizei bufsize, cgl.GLsizei* length, cgl.GLchar* infolog) nogil
cdef void glGetRenderbufferParameteriv(cgl.GLenum target, cgl.GLenum pname, cgl.GLint* params) nogil
cdef void glGetShaderiv(cgl.GLuint shader, cgl.GLenum pname, cgl.GLint* params) nogil
cdef void glGetShaderInfoLog(cgl.GLuint shader, cgl.GLsizei bufsize, cgl.GLsizei* length, cgl.GLchar* infolog) nogil
cdef void glGetShaderPrecisionFormat(cgl.GLenum shadertype, cgl.GLenum precisiontype, cgl.GLint* range, cgl.GLint* precision) nogil
cdef void glGetShaderSource(cgl.GLuint shader, cgl.GLsizei bufsize, cgl.GLsizei* length, cgl.GLchar* source) nogil
cdef void glGetTexParameterfv(cgl.GLenum target, cgl.GLenum pname, cgl.GLfloat* params) nogil
cdef void glGetTexParameteriv(cgl.GLenum target, cgl.GLenum pname, cgl.GLint* params) nogil
cdef void glGetUniformfv(cgl.GLuint program, cgl.GLint location, cgl.GLfloat* params) nogil
cdef void glGetUniformiv(cgl.GLuint program, cgl.GLint location, cgl.GLint* params) nogil
cdef void glGetVertexAttribfv(cgl.GLuint index, cgl.GLenum pname, cgl.GLfloat* params) nogil
cdef void glGetVertexAttribiv(cgl.GLuint index, cgl.GLenum pname, cgl.GLint* params) nogil
cdef void glGetVertexAttribPointerv(cgl.GLuint index, cgl.GLenum pname, cgl.GLvoid** pointer) nogil
cdef void glHint(cgl.GLenum target, cgl.GLenum mode) nogil
cdef void glLineWidth(cgl.GLfloat width) nogil
cdef void glLinkProgram(cgl.GLuint program) nogil
cdef void glPixelStorei(cgl.GLenum pname, cgl.GLint param) nogil
cdef void glPolygonOffset(cgl.GLfloat factor, cgl.GLfloat units) nogil
cdef void glReadPixels(cgl.GLint x, cgl.GLint y, cgl.GLsizei width, cgl.GLsizei height, cgl.GLenum format, cgl.GLenum type, cgl.GLvoid* pixels) nogil
cdef void glReleaseShaderCompiler() nogil
cdef void glRenderbufferStorage(cgl.GLenum target, cgl.GLenum internalformat, cgl.GLsizei width, cgl.GLsizei height) nogil
cdef void glSampleCoverage(cgl.GLclampf value, cgl.GLboolean invert) nogil
cdef void glScissor(cgl.GLint x, cgl.GLint y, cgl.GLsizei width, cgl.GLsizei height) nogil
cdef void glShaderBinary(cgl.GLsizei n, cgl.GLuint* shaders, cgl.GLenum binaryformat, cgl.GLvoid* binary, cgl.GLsizei length) nogil
cdef void glShaderSource(cgl.GLuint shader, cgl.GLsizei count, cgl.GLchar** string, cgl.GLint* length) nogil
cdef void glStencilFunc(cgl.GLenum func, cgl.GLint ref, cgl.GLuint mask) nogil
cdef void glStencilFuncSeparate(cgl.GLenum face, cgl.GLenum func, cgl.GLint ref, cgl.GLuint mask) nogil
cdef void glStencilMask(cgl.GLuint mask) nogil
cdef void glStencilMaskSeparate(cgl.GLenum face, cgl.GLuint mask) nogil
cdef void glStencilOp(cgl.GLenum fail, cgl.GLenum zfail, cgl.GLenum zpass) nogil
cdef void glStencilOpSeparate(cgl.GLenum face, cgl.GLenum fail, cgl.GLenum zfail, cgl.GLenum zpass) nogil
cdef void glTexImage2D(cgl.GLenum target, cgl.GLint level, cgl.GLint internalformat, cgl.GLsizei width, cgl.GLsizei height, cgl.GLint border, cgl.GLenum format, cgl.GLenum type, cgl.GLvoid* pixels) nogil
cdef void glTexParameterf(cgl.GLenum target, cgl.GLenum pname, cgl.GLfloat param) nogil
cdef void glTexParameterfv(cgl.GLenum target, cgl.GLenum pname, cgl.GLfloat* params) nogil
cdef void glTexParameteri(cgl.GLenum target, cgl.GLenum pname, cgl.GLint param) nogil
cdef void glTexParameteriv(cgl.GLenum target, cgl.GLenum pname, cgl.GLint* params) nogil
cdef void glTexSubImage2D(cgl.GLenum target, cgl.GLint level, cgl.GLint xoffset, cgl.GLint yoffset, cgl.GLsizei width, cgl.GLsizei height, cgl.GLenum format, cgl.GLenum type, cgl.GLvoid* pixels) nogil
cdef void glUniform1f(cgl.GLint location, cgl.GLfloat x) nogil
cdef void glUniform1fv(cgl.GLint location, cgl.GLsizei count, cgl.GLfloat* v) nogil
cdef void glUniform1i(cgl.GLint location, cgl.GLint x) nogil
cdef void glUniform1iv(cgl.GLint location, cgl.GLsizei count, cgl.GLint* v) nogil
cdef void glUniform2f(cgl.GLint location, cgl.GLfloat x, cgl.GLfloat y) nogil
cdef void glUniform2fv(cgl.GLint location, cgl.GLsizei count, cgl.GLfloat* v) nogil
cdef void glUniform2i(cgl.GLint location, cgl.GLint x, cgl.GLint y) nogil
cdef void glUniform2iv(cgl.GLint location, cgl.GLsizei count, cgl.GLint* v) nogil
cdef void glUniform3f(cgl.GLint location, cgl.GLfloat x, cgl.GLfloat y, cgl.GLfloat z) nogil
cdef void glUniform3fv(cgl.GLint location, cgl.GLsizei count, cgl.GLfloat* v) nogil
cdef void glUniform3i(cgl.GLint location, cgl.GLint x, cgl.GLint y, cgl.GLint z) nogil
cdef void glUniform3iv(cgl.GLint location, cgl.GLsizei count, cgl.GLint* v) nogil
cdef void glUniform4f(cgl.GLint location, cgl.GLfloat x, cgl.GLfloat y, cgl.GLfloat z, cgl.GLfloat w) nogil
cdef void glUniform4fv(cgl.GLint location, cgl.GLsizei count, cgl.GLfloat* v) nogil
cdef void glUniform4i(cgl.GLint location, cgl.GLint x, cgl.GLint y, cgl.GLint z, cgl.GLint w) nogil
cdef void glUniform4iv(cgl.GLint location, cgl.GLsizei count, cgl.GLint* v) nogil
cdef void glUniformMatrix2fv(cgl.GLint location, cgl.GLsizei count, cgl.GLboolean transpose, cgl.GLfloat* value) nogil
cdef void glUniformMatrix3fv(cgl.GLint location, cgl.GLsizei count, cgl.GLboolean transpose, cgl.GLfloat* value) nogil
cdef void glUniformMatrix4fv(cgl.GLint location, cgl.GLsizei count, cgl.GLboolean transpose, cgl.GLfloat* value) nogil
cdef void glUseProgram(cgl.GLuint program) nogil
cdef void glValidateProgram(cgl.GLuint program) nogil
cdef void glVertexAttrib1f(cgl.GLuint indx, cgl.GLfloat x) nogil
cdef void glVertexAttrib1fv(cgl.GLuint indx, cgl.GLfloat* values) nogil
cdef void glVertexAttrib2f(cgl.GLuint indx, cgl.GLfloat x, cgl.GLfloat y) nogil
cdef void glVertexAttrib2fv(cgl.GLuint indx, cgl.GLfloat* values) nogil
cdef void glVertexAttrib3f(cgl.GLuint indx, cgl.GLfloat x, cgl.GLfloat y, cgl.GLfloat z) nogil
cdef void glVertexAttrib3fv(cgl.GLuint indx, cgl.GLfloat* values) nogil
cdef void glVertexAttrib4f(cgl.GLuint indx, cgl.GLfloat x, cgl.GLfloat y, cgl.GLfloat z, cgl.GLfloat w) nogil
cdef void glVertexAttrib4fv(cgl.GLuint indx, cgl.GLfloat* values) nogil
cdef void glVertexAttribPointer(cgl.GLuint indx, cgl.GLint size, cgl.GLenum type, cgl.GLboolean normalized, cgl.GLsizei stride, cgl.GLvoid* ptr) nogil
cdef void glViewport(cgl.GLint x, cgl.GLint y, cgl.GLsizei width, cgl.GLsizei height) nogil
