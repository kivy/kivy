"""
CGL/Mock: GL backend implementation by mocking functions to NOOP
"""

include "../common.pxi"

from kivy.graphics.cgl cimport *

cdef GLubyte *empty_str = ''

cpdef is_backend_supported():
    return True

cdef GLenum __stdcall mockCheckFramebufferStatus(GLenum target) nogil:
    return GL_FRAMEBUFFER_COMPLETE
cdef GLuint __stdcall mockCreateProgram() nogil:
    return <GLuint>1
cdef GLuint __stdcall mockCreateShader(GLenum type) nogil:
    return <GLuint>1
cdef int __stdcall mockGetAttribLocation(GLuint program, GLchar* name) nogil:
    return 1
cdef GLenum __stdcall mockGetError() nogil:
    return GL_NO_ERROR
cdef GLubyte* __stdcall mockGetString(GLenum name) nogil:
    return empty_str
cdef int __stdcall mockGetUniformLocation(GLuint program,  GLchar* name) nogil:
    1
cdef GLboolean __stdcall mockIsBuffer(GLuint buffer) nogil:
    return GL_TRUE
cdef GLboolean __stdcall  mockIsEnabled(GLenum cap) nogil:
    return GL_TRUE
cdef GLboolean __stdcall mockIsFramebuffer(GLuint framebuffer) nogil:
    return GL_TRUE
cdef GLboolean __stdcall mockIsProgram(GLuint program) nogil:
    return GL_TRUE
cdef GLboolean __stdcall mockIsRenderbuffer(GLuint renderbuffer) nogil:
    return GL_TRUE
cdef GLboolean __stdcall mockIsShader(GLuint shader) nogil:
    return GL_TRUE
cdef GLboolean __stdcall mockIsTexture(GLuint texture) nogil:
    return GL_TRUE

cdef void __stdcall mockActiveTexture(GLenum texture) nogil:
    pass
cdef void __stdcall mockAttachShader(GLuint program, GLuint shader) nogil:
    pass
cdef void __stdcall mockBindAttribLocation(GLuint program, GLuint index, GLchar* name) nogil:
    pass
cdef void __stdcall mockBindBuffer(GLenum target, GLuint buffer) nogil:
    pass
cdef void __stdcall mockBindFramebuffer(GLenum target, GLuint framebuffer) nogil:
    pass
cdef void __stdcall mockBindRenderbuffer(GLenum target, GLuint renderbuffer) nogil:
    pass
cdef void __stdcall mockBindTexture(GLenum target, GLuint texture) nogil:
    pass
cdef void __stdcall mockBlendColor(GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha) nogil:
    pass
cdef void __stdcall mockBlendEquation( GLenum mode ) nogil:
    pass
cdef void __stdcall mockBlendEquationSeparate(GLenum modeRGB, GLenum modeAlpha) nogil:
    pass
cdef void __stdcall mockBlendFunc(GLenum sfactor, GLenum dfactor) nogil:
    pass
cdef void __stdcall mockBlendFuncSeparate(GLenum srcRGB, GLenum dstRGB, GLenum srcAlpha, GLenum dstAlpha) nogil:
    pass
cdef void __stdcall mockBufferData(GLenum target, GLsizeiptr size, GLvoid* data, GLenum usage) nogil:
    pass
cdef void __stdcall mockBufferSubData(GLenum target, GLintptr offset, GLsizeiptr size, GLvoid* data) nogil:
    pass
cdef void __stdcall mockClear(GLbitfield mask) nogil:
    pass
cdef void __stdcall mockClearColor(GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha) nogil:
    pass
cdef void __stdcall mockClearDepthf(GLclampf depth) nogil:
    pass
cdef void __stdcall mockClearStencil(GLint s) nogil:
    pass
cdef void __stdcall mockColorMask(GLboolean red, GLboolean green, GLboolean blue, GLboolean alpha) nogil:
    pass
cdef void __stdcall mockCompileShader(GLuint shader) nogil:
    pass
cdef void __stdcall mockCompressedTexImage2D(GLenum target, GLint level, GLenum internalformat, GLsizei width, GLsizei height, GLint border, GLsizei imageSize, GLvoid* data) nogil:
    pass
cdef void __stdcall mockCompressedTexSubImage2D(GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLsizei imageSize, GLvoid* data) nogil:
    pass
cdef void __stdcall mockCopyTexImage2D(GLenum target, GLint level, GLenum internalformat, GLint x, GLint y, GLsizei width, GLsizei height, GLint border) nogil:
    pass
cdef void __stdcall mockCopyTexSubImage2D(GLenum target, GLint level, GLint xoffset, GLint yoffset, GLint x, GLint y, GLsizei width, GLsizei height) nogil:
    pass
cdef void __stdcall mockCullFace(GLenum mode) nogil:
    pass
cdef void __stdcall mockDeleteBuffers(GLsizei n, GLuint* buffers) nogil:
    pass
cdef void __stdcall mockDeleteFramebuffers(GLsizei n, GLuint* framebuffers) nogil:
    pass
cdef void __stdcall mockDeleteProgram(GLuint program) nogil:
    pass
cdef void __stdcall mockDeleteRenderbuffers(GLsizei n, GLuint* renderbuffers) nogil:
    pass
cdef void __stdcall mockDeleteShader(GLuint shader) nogil:
    pass
cdef void __stdcall mockDeleteTextures(GLsizei n, GLuint* textures) nogil:
    pass
cdef void __stdcall mockDepthFunc(GLenum func) nogil:
    pass
cdef void __stdcall mockDepthMask(GLboolean flag) nogil:
    pass
cdef void __stdcall mockDepthRangef(GLclampf zNear, GLclampf zFar) nogil:
    pass
cdef void __stdcall mockDetachShader(GLuint program, GLuint shader) nogil:
    pass
cdef void __stdcall mockDisable(GLenum cap) nogil:
    pass
cdef void __stdcall mockDisableVertexAttribArray(GLuint index) nogil:
    pass
cdef void __stdcall mockDrawArrays(GLenum mode, GLint first, GLsizei count) nogil:
    pass
cdef void __stdcall mockDrawElements(GLenum mode, GLsizei count, GLenum type, GLvoid* indices) nogil:
    pass
cdef void __stdcall mockEnable(GLenum cap) nogil:
    pass
cdef void __stdcall mockEnableVertexAttribArray(GLuint index) nogil:
    pass
cdef void __stdcall mockFinish() nogil:
    pass
cdef void __stdcall mockFlush() nogil:
    pass
cdef void __stdcall mockFramebufferRenderbuffer(GLenum target, GLenum attachment, GLenum renderbuffertarget, GLuint renderbuffer) nogil:
    pass
cdef void __stdcall mockFramebufferTexture2D(GLenum target, GLenum attachment, GLenum textarget, GLuint texture, GLint level) nogil:
    pass
cdef void __stdcall mockFrontFace(GLenum mode) nogil:
    pass
cdef void __stdcall mockGenBuffers(GLsizei n, GLuint* buffers) nogil:
    pass
cdef void __stdcall mockGenerateMipmap(GLenum target) nogil:
    pass
cdef void __stdcall mockGenFramebuffers(GLsizei n, GLuint* framebuffers) nogil:
    pass
cdef void __stdcall mockGenRenderbuffers(GLsizei n, GLuint* renderbuffers) nogil:
    pass
cdef void __stdcall mockGenTextures(GLsizei n, GLuint* textures) nogil:
    pass
cdef void __stdcall mockGetActiveAttrib(GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name) nogil:
    pass
cdef void __stdcall mockGetActiveUniform(GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name) nogil:
    pass
cdef void __stdcall mockGetAttachedShaders(GLuint program, GLsizei maxcount, GLsizei* count, GLuint* shaders) nogil:
    pass
cdef void __stdcall mockGetBooleanv(GLenum pname, GLboolean* params) nogil:
    pass
cdef void __stdcall mockGetBufferParameteriv(GLenum target, GLenum pname, GLint* params) nogil:
    pass
cdef void __stdcall mockGetFloatv(GLenum pname, GLfloat* params) nogil:
    pass
cdef void __stdcall mockGetFramebufferAttachmentParameteriv(GLenum target, GLenum attachment, GLenum pname, GLint* params) nogil:
    pass
cdef void __stdcall mockGetIntegerv(GLenum pname, GLint* params) nogil:
    pass
cdef void __stdcall mockGetProgramiv(GLuint program, GLenum pname, GLint* params) nogil:
    pass
cdef void __stdcall mockGetProgramInfoLog(GLuint program, GLsizei bufsize, GLsizei* length, GLchar* infolog) nogil:
    pass
cdef void __stdcall mockGetRenderbufferParameteriv(GLenum target, GLenum pname, GLint* params) nogil:
    pass
cdef void __stdcall mockGetShaderiv(GLuint shader, GLenum pname, GLint* params) nogil:
    pass
cdef void __stdcall mockGetShaderInfoLog(GLuint shader, GLsizei bufsize, GLsizei* length, GLchar* infolog) nogil:
    pass
cdef void __stdcall mockGetShaderPrecisionFormat(GLenum shadertype, GLenum precisiontype, GLint* range, GLint* precision) nogil:
    pass
cdef void __stdcall mockGetShaderSource(GLuint shader, GLsizei bufsize, GLsizei* length, GLchar* source) nogil:
    pass
cdef void __stdcall mockGetTexParameterfv(GLenum target, GLenum pname, GLfloat* params) nogil:
    pass
cdef void __stdcall mockGetTexParameteriv(GLenum target, GLenum pname, GLint* params) nogil:
    pass
cdef void __stdcall mockGetUniformfv(GLuint program, GLint location, GLfloat* params) nogil:
    pass
cdef void __stdcall mockGetUniformiv(GLuint program, GLint location, GLint* params) nogil:
    pass
cdef void __stdcall mockGetVertexAttribfv(GLuint index, GLenum pname, GLfloat* params) nogil:
    pass
cdef void __stdcall mockGetVertexAttribiv(GLuint index, GLenum pname, GLint* params) nogil:
    pass
cdef void __stdcall mockGetVertexAttribPointerv(GLuint index, GLenum pname, GLvoid** pointer) nogil:
    pass
cdef void __stdcall mockHint(GLenum target, GLenum mode) nogil:
    pass
cdef void __stdcall mockLineWidth(GLfloat width) nogil:
    pass
cdef void __stdcall mockLinkProgram(GLuint program) nogil:
    pass
cdef void __stdcall mockPixelStorei(GLenum pname, GLint param) nogil:
    pass
cdef void __stdcall mockPolygonOffset(GLfloat factor, GLfloat units) nogil:
    pass
cdef void __stdcall mockReadPixels(GLint x, GLint y, GLsizei width, GLsizei height, GLenum format, GLenum type, GLvoid* pixels) nogil:
    pass
cdef void __stdcall mockReleaseShaderCompiler() nogil:
    pass
cdef void __stdcall mockRenderbufferStorage(GLenum target, GLenum internalformat, GLsizei width, GLsizei height) nogil:
    pass
cdef void __stdcall mockSampleCoverage(GLclampf value, GLboolean invert) nogil:
    pass
cdef void __stdcall mockScissor(GLint x, GLint y, GLsizei width, GLsizei height) nogil:
    pass
cdef void __stdcall mockShaderBinary(GLsizei n, GLuint* shaders, GLenum binaryformat, GLvoid* binary, GLsizei length) nogil:
    pass
cdef void __stdcall mockShaderSource(GLuint shader, GLsizei count, GLchar** string, GLint* length) nogil:
    pass
cdef void __stdcall mockStencilFunc(GLenum func, GLint ref, GLuint mask) nogil:
    pass
cdef void __stdcall mockStencilFuncSeparate(GLenum face, GLenum func, GLint ref, GLuint mask) nogil:
    pass
cdef void __stdcall mockStencilMask(GLuint mask) nogil:
    pass
cdef void __stdcall mockStencilMaskSeparate(GLenum face, GLuint mask) nogil:
    pass
cdef void __stdcall mockStencilOp(GLenum fail, GLenum zfail, GLenum zpass) nogil:
    pass
cdef void __stdcall mockStencilOpSeparate(GLenum face, GLenum fail, GLenum zfail, GLenum zpass) nogil:
    pass
cdef void __stdcall mockTexImage2D(GLenum target, GLint level, GLint internalformat, GLsizei width, GLsizei height, GLint border, GLenum format, GLenum type, GLvoid* pixels) nogil:
    pass
cdef void __stdcall mockTexParameterf(GLenum target, GLenum pname, GLfloat param) nogil:
    pass
cdef void __stdcall mockTexParameterfv(GLenum target, GLenum pname, GLfloat* params) nogil:
    pass
cdef void __stdcall mockTexParameteri(GLenum target, GLenum pname, GLint param) nogil:
    pass
cdef void __stdcall mockTexParameteriv(GLenum target, GLenum pname, GLint* params) nogil:
    pass
cdef void __stdcall mockTexSubImage2D(GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLenum type, GLvoid* pixels) nogil:
    pass
cdef void __stdcall mockUniform1f(GLint location, GLfloat x) nogil:
    pass
cdef void __stdcall mockUniform1fv(GLint location, GLsizei count, GLfloat* v) nogil:
    pass
cdef void __stdcall mockUniform1i(GLint location, GLint x) nogil:
    pass
cdef void __stdcall mockUniform1iv(GLint location, GLsizei count, GLint* v) nogil:
    pass
cdef void __stdcall mockUniform2f(GLint location, GLfloat x, GLfloat y) nogil:
    pass
cdef void __stdcall mockUniform2fv(GLint location, GLsizei count, GLfloat* v) nogil:
    pass
cdef void __stdcall mockUniform2i(GLint location, GLint x, GLint y) nogil:
    pass
cdef void __stdcall mockUniform2iv(GLint location, GLsizei count, GLint* v) nogil:
    pass
cdef void __stdcall mockUniform3f(GLint location, GLfloat x, GLfloat y, GLfloat z) nogil:
    pass
cdef void __stdcall mockUniform3fv(GLint location, GLsizei count, GLfloat* v) nogil:
    pass
cdef void __stdcall mockUniform3i(GLint location, GLint x, GLint y, GLint z) nogil:
    pass
cdef void __stdcall mockUniform3iv(GLint location, GLsizei count, GLint* v) nogil:
    pass
cdef void __stdcall mockUniform4f(GLint location, GLfloat x, GLfloat y, GLfloat z, GLfloat w) nogil:
    pass
cdef void __stdcall mockUniform4fv(GLint location, GLsizei count, GLfloat* v) nogil:
    pass
cdef void __stdcall mockUniform4i(GLint location, GLint x, GLint y, GLint z, GLint w) nogil:
    pass
cdef void __stdcall mockUniform4iv(GLint location, GLsizei count, GLint* v) nogil:
    pass
cdef void __stdcall mockUniformMatrix2fv(GLint location, GLsizei count, GLboolean transpose, GLfloat* value) nogil:
    pass
cdef void __stdcall mockUniformMatrix3fv(GLint location, GLsizei count, GLboolean transpose, GLfloat* value) nogil:
    pass
cdef void __stdcall mockUniformMatrix4fv(GLint location, GLsizei count, GLboolean transpose, GLfloat* value) nogil:
    pass
cdef void __stdcall mockUseProgram(GLuint program) nogil:
    pass
cdef void __stdcall mockValidateProgram(GLuint program) nogil:
    pass
cdef void __stdcall mockVertexAttrib1f(GLuint indx, GLfloat x) nogil:
    pass
cdef void __stdcall mockVertexAttrib1fv(GLuint indx, GLfloat* values) nogil:
    pass
cdef void __stdcall mockVertexAttrib2f(GLuint indx, GLfloat x, GLfloat y) nogil:
    pass
cdef void __stdcall mockVertexAttrib2fv(GLuint indx, GLfloat* values) nogil:
    pass
cdef void __stdcall mockVertexAttrib3f(GLuint indx, GLfloat x, GLfloat y, GLfloat z) nogil:
    pass
cdef void __stdcall mockVertexAttrib3fv(GLuint indx, GLfloat* values) nogil:
    pass
cdef void __stdcall mockVertexAttrib4f(GLuint indx, GLfloat x, GLfloat y, GLfloat z, GLfloat w) nogil:
    pass
cdef void __stdcall mockVertexAttrib4fv(GLuint indx, GLfloat* values) nogil:
    pass
cdef void __stdcall mockVertexAttribPointer(GLuint indx, GLint size, GLenum type, GLboolean normalized, GLsizei stride, GLvoid* ptr) nogil:
    pass
cdef void __stdcall mockViewport(GLint x, GLint y, GLsizei width, GLsizei height) nogil:
    pass


def init_backend():
    cgl.glActiveTexture = mockActiveTexture
    cgl.glAttachShader = mockAttachShader
    cgl.glBindAttribLocation = mockBindAttribLocation
    cgl.glBindBuffer = mockBindBuffer
    cgl.glBindFramebuffer = mockBindFramebuffer
    cgl.glBindRenderbuffer = mockBindRenderbuffer
    cgl.glBindTexture = mockBindTexture
    cgl.glBlendColor = mockBlendColor
    cgl.glBlendEquation = mockBlendEquation
    cgl.glBlendEquationSeparate = mockBlendEquationSeparate
    cgl.glBlendFunc = mockBlendFunc
    cgl.glBlendFuncSeparate = mockBlendFuncSeparate
    cgl.glBufferData = mockBufferData
    cgl.glBufferSubData = mockBufferSubData
    cgl.glCheckFramebufferStatus = mockCheckFramebufferStatus
    cgl.glClear = mockClear
    cgl.glClearColor = mockClearColor
    cgl.glClearStencil = mockClearStencil
    cgl.glColorMask = mockColorMask
    cgl.glCompileShader = mockCompileShader
    cgl.glCompressedTexImage2D = mockCompressedTexImage2D
    cgl.glCompressedTexSubImage2D = mockCompressedTexSubImage2D
    cgl.glCopyTexImage2D = mockCopyTexImage2D
    cgl.glCopyTexSubImage2D = mockCopyTexSubImage2D
    cgl.glCreateProgram = mockCreateProgram
    cgl.glCreateShader = mockCreateShader
    cgl.glCullFace = mockCullFace
    cgl.glDeleteBuffers = mockDeleteBuffers
    cgl.glDeleteFramebuffers = mockDeleteFramebuffers
    cgl.glDeleteProgram = mockDeleteProgram
    cgl.glDeleteRenderbuffers = mockDeleteRenderbuffers
    cgl.glDeleteShader = mockDeleteShader
    cgl.glDeleteTextures = mockDeleteTextures
    cgl.glDepthFunc = mockDepthFunc
    cgl.glDepthMask = mockDepthMask
    cgl.glDetachShader = mockDetachShader
    cgl.glDisable = mockDisable
    cgl.glDisableVertexAttribArray = mockDisableVertexAttribArray
    cgl.glDrawArrays = mockDrawArrays
    cgl.glDrawElements = mockDrawElements
    cgl.glEnable = mockEnable
    cgl.glEnableVertexAttribArray = mockEnableVertexAttribArray
    cgl.glFinish = mockFinish
    cgl.glFlush = mockFlush
    cgl.glFramebufferRenderbuffer = mockFramebufferRenderbuffer
    cgl.glFramebufferTexture2D = mockFramebufferTexture2D
    cgl.glFrontFace = mockFrontFace
    cgl.glGenBuffers = mockGenBuffers
    cgl.glGenerateMipmap = mockGenerateMipmap
    cgl.glGenFramebuffers = mockGenFramebuffers
    cgl.glGenRenderbuffers = mockGenRenderbuffers
    cgl.glGenTextures = mockGenTextures
    cgl.glGetActiveAttrib = mockGetActiveAttrib
    cgl.glGetActiveUniform = mockGetActiveUniform
    cgl.glGetAttachedShaders = mockGetAttachedShaders
    cgl.glGetAttribLocation = mockGetAttribLocation
    cgl.glGetBooleanv = mockGetBooleanv
    cgl.glGetBufferParameteriv = mockGetBufferParameteriv
    cgl.glGetError = mockGetError
    cgl.glGetFloatv = mockGetFloatv
    cgl.glGetFramebufferAttachmentParameteriv = mockGetFramebufferAttachmentParameteriv
    cgl.glGetIntegerv = mockGetIntegerv
    cgl.glGetProgramInfoLog = mockGetProgramInfoLog
    cgl.glGetProgramiv = mockGetProgramiv
    cgl.glGetRenderbufferParameteriv = mockGetRenderbufferParameteriv
    cgl.glGetShaderInfoLog = mockGetShaderInfoLog
    cgl.glGetShaderiv = mockGetShaderiv
    cgl.glGetShaderSource = mockGetShaderSource
    cgl.glGetString = mockGetString
    cgl.glGetTexParameterfv = mockGetTexParameterfv
    cgl.glGetTexParameteriv = mockGetTexParameteriv
    cgl.glGetUniformfv = mockGetUniformfv
    cgl.glGetUniformiv = mockGetUniformiv
    cgl.glGetUniformLocation = mockGetUniformLocation
    cgl.glGetVertexAttribfv = mockGetVertexAttribfv
    cgl.glGetVertexAttribiv = mockGetVertexAttribiv
    cgl.glHint = mockHint
    cgl.glIsBuffer = mockIsBuffer
    cgl.glIsEnabled = mockIsEnabled
    cgl.glIsFramebuffer = mockIsFramebuffer
    cgl.glIsProgram = mockIsProgram
    cgl.glIsRenderbuffer = mockIsRenderbuffer
    cgl.glIsShader = mockIsShader
    cgl.glIsTexture = mockIsTexture
    cgl.glLineWidth = mockLineWidth
    cgl.glLinkProgram = mockLinkProgram
    cgl.glPixelStorei = mockPixelStorei
    cgl.glPolygonOffset = mockPolygonOffset
    cgl.glReadPixels = mockReadPixels
    cgl.glRenderbufferStorage = mockRenderbufferStorage
    cgl.glSampleCoverage = mockSampleCoverage
    cgl.glScissor = mockScissor
    cgl.glShaderBinary = mockShaderBinary
    cgl.glShaderSource = mockShaderSource
    cgl.glStencilFunc = mockStencilFunc
    cgl.glStencilFuncSeparate = mockStencilFuncSeparate
    cgl.glStencilMask = mockStencilMask
    cgl.glStencilMaskSeparate = mockStencilMaskSeparate
    cgl.glStencilOp = mockStencilOp
    cgl.glStencilOpSeparate = mockStencilOpSeparate
    cgl.glTexImage2D = mockTexImage2D
    cgl.glTexParameterf = mockTexParameterf
    cgl.glTexParameteri = mockTexParameteri
    cgl.glTexSubImage2D = mockTexSubImage2D
    cgl.glUniform1f = mockUniform1f
    cgl.glUniform1fv = mockUniform1fv
    cgl.glUniform1i = mockUniform1i
    cgl.glUniform1iv = mockUniform1iv
    cgl.glUniform2f = mockUniform2f
    cgl.glUniform2fv = mockUniform2fv
    cgl.glUniform2i = mockUniform2i
    cgl.glUniform2iv = mockUniform2iv
    cgl.glUniform3f = mockUniform3f
    cgl.glUniform3fv = mockUniform3fv
    cgl.glUniform3i = mockUniform3i
    cgl.glUniform3iv = mockUniform3iv
    cgl.glUniform4f = mockUniform4f
    cgl.glUniform4fv = mockUniform4fv
    cgl.glUniform4i = mockUniform4i
    cgl.glUniform4iv = mockUniform4iv
    cgl.glUniformMatrix4fv = mockUniformMatrix4fv
    cgl.glUseProgram = mockUseProgram
    cgl.glValidateProgram = mockValidateProgram
    cgl.glVertexAttrib1f = mockVertexAttrib1f
    cgl.glVertexAttrib2f = mockVertexAttrib2f
    cgl.glVertexAttrib3f = mockVertexAttrib3f
    cgl.glVertexAttrib4f = mockVertexAttrib4f
    cgl.glVertexAttribPointer = mockVertexAttribPointer
    cgl.glViewport = mockViewport
