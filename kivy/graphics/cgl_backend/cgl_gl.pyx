"""
CGL/GL: GL backend implementation using GL directly
"""

include "../common.pxi"
include "../../include/config.pxi"

from kivy.graphics.cgl cimport *
from kivy.logger import Logger

cdef extern from "gl_redirect.h":
    const GLubyte* (__stdcall *glGetString)(GLenum) nogil
    GLboolean (__stdcall *glIsBuffer)(GLuint buffer) nogil
    GLboolean (__stdcall *glIsEnabled)(GLenum cap) nogil
    GLboolean (__stdcall *glIsFramebuffer)(GLuint framebuffer) nogil
    GLboolean (__stdcall *glIsProgram)(GLuint program) nogil
    GLboolean (__stdcall *glIsRenderbuffer)(GLuint renderbuffer) nogil
    GLboolean (__stdcall *glIsShader)(GLuint shader) nogil
    GLboolean (__stdcall *glIsTexture)(GLuint texture) nogil
    GLenum (__stdcall *glCheckFramebufferStatus)(GLenum) nogil
    GLenum (__stdcall *glGetError)() nogil
    GLint (__stdcall *glGetAttribLocation)(GLuint, const GLchar *) nogil
    GLint (__stdcall *glGetUniformLocation)(GLuint, const char *) nogil
    GLuint (__stdcall *glCreateProgram)() nogil
    GLuint (__stdcall *glCreateShader)(GLenum) nogil
    void (__stdcall *glActiveTexture)(GLenum) nogil
    void (__stdcall *glAttachShader)(GLuint, GLuint) nogil
    void (__stdcall *glBindAttribLocation)(GLuint, GLuint, const char *) nogil
    void (__stdcall *glBindBuffer)(GLenum, GLuint) nogil
    void (__stdcall *glBindFramebuffer)(GLenum, GLuint) nogil
    void (__stdcall *glBindRenderbuffer)(GLenum target, GLuint renderbuffer) nogil
    void (__stdcall *glBindTexture)(GLenum, GLuint) nogil
    void (__stdcall *glBlendColor)(GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha) nogil
    void (__stdcall *glBlendEquation)( GLenum mode ) nogil
    void (__stdcall *glBlendEquationSeparate)(GLenum modeRGB, GLenum modeAlpha) nogil
    void (__stdcall *glBlendFunc)(GLenum sfactor, GLenum dfactor) nogil
    void (__stdcall *glBlendFuncSeparate)(GLenum, GLenum, GLenum, GLenum) nogil
    void (__stdcall *glBufferData)(GLenum, GLsizeiptr, const GLvoid *, GLenum) nogil
    void (__stdcall *glBufferSubData)(GLenum, GLintptr, GLsizeiptr, const GLvoid *) nogil
    void (__stdcall *glClear)(GLbitfield) nogil
    void (__stdcall *glClearColor)(GLclampf, GLclampf, GLclampf, GLclampf) nogil
    void (__stdcall *glClearStencil)(GLint s) nogil
    void (__stdcall *glColorMask)(GLboolean red, GLboolean green, GLboolean blue, GLboolean alpha) nogil
    void (__stdcall *glCompileShader)(GLuint) nogil
    void (__stdcall *glCompressedTexImage2D)(GLenum target, GLint level, GLenum internalformat, GLsizei width, GLsizei height, GLint border, GLsizei imageSize, const GLvoid* data) nogil
    void (__stdcall *glCompressedTexSubImage2D)(GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLsizei imageSize, const GLvoid* data) nogil
    void (__stdcall *glCopyTexImage2D)(GLenum target, GLint level, GLenum internalformat, GLint x, GLint y, GLsizei width, GLsizei height, GLint border) nogil
    void (__stdcall *glCopyTexSubImage2D)(GLenum target, GLint level, GLint xoffset, GLint yoffset, GLint x, GLint y, GLsizei width, GLsizei height) nogil
    void (__stdcall *glCullFace)(GLenum mode) nogil
    void (__stdcall *glDeleteBuffers)(GLsizei n, const GLuint* buffers) nogil
    void (__stdcall *glDeleteFramebuffers)(GLsizei, const GLuint *) nogil
    void (__stdcall *glDeleteProgram)(GLuint) nogil
    void (__stdcall *glDeleteRenderbuffers)(GLsizei n, const GLuint* renderbuffers) nogil
    void (__stdcall *glDeleteShader)(GLuint) nogil
    void (__stdcall *glDeleteTextures)(GLsizei, const GLuint *) nogil
    void (__stdcall *glDepthFunc)(GLenum func) nogil
    void (__stdcall *glDepthMask)(GLboolean flag) nogil
    void (__stdcall *glDetachShader)(GLuint program, GLuint shader) nogil
    void (__stdcall *glDisable)(GLenum) nogil
    void (__stdcall *glDisableVertexAttribArray)(GLuint) nogil
    void (__stdcall *glDrawArrays)(GLenum, GLint, GLsizei) nogil
    void (__stdcall *glDrawElements)(GLenum mode, GLsizei count, GLenum type, const GLvoid* indices) nogil
    void (__stdcall *glEnable)(GLenum) nogil
    void (__stdcall *glEnableVertexAttribArray)(GLuint) nogil
    void (__stdcall *glFinish)() nogil
    void (__stdcall *glFlush)() nogil
    void (__stdcall *glFramebufferRenderbuffer)(GLenum target, GLenum attachment, GLenum renderbuffertarget, GLuint renderbuffer) nogil
    void (__stdcall *glFramebufferTexture2D)(GLenum, GLenum, GLenum, GLuint, GLint) nogil
    void (__stdcall *glFrontFace)(GLenum mode) nogil
    void (__stdcall *glGenBuffers)(GLsizei, GLuint *) nogil
    void (__stdcall *glGenerateMipmap)(GLenum target) nogil
    void (__stdcall *glGenFramebuffers)(GLsizei, GLuint *) nogil
    void (__stdcall *glGenRenderbuffers)(GLsizei n, GLuint* renderbuffers) nogil
    void (__stdcall *glGenTextures)(GLsizei, GLuint *) nogil
    void (__stdcall *glGetActiveAttrib)(GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name) nogil
    void (__stdcall *glGetActiveUniform)(GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name) nogil
    void (__stdcall *glGetAttachedShaders)(GLuint program, GLsizei maxcount, GLsizei* count, GLuint* shaders) nogil
    void (__stdcall *glGetBooleanv)(GLenum, GLboolean *) nogil
    void (__stdcall *glGetBufferParameteriv)(GLenum target, GLenum pname, GLint* params) nogil
    void (__stdcall *glGetFloatv)(GLenum pname, GLfloat* params) nogil
    void (__stdcall *glGetFramebufferAttachmentParameteriv)(GLenum target, GLenum attachment, GLenum pname, GLint* params) nogil
    void (__stdcall *glGetIntegerv)(GLenum, GLint *) nogil
    void (__stdcall *glGetProgramInfoLog)(GLuint, GLsizei, GLsizei*, GLchar*) nogil
    void (__stdcall *glGetProgramiv)(GLuint, GLenum, GLint *) nogil
    void (__stdcall *glGetRenderbufferParameteriv)(GLenum target, GLenum pname, GLint* params) nogil
    void (__stdcall *glGetShaderInfoLog)(GLuint, GLsizei, GLsizei *, char *) nogil
    void (__stdcall *glGetShaderiv)(GLuint, GLenum, GLint *) nogil
    void (__stdcall *glGetShaderSource)(GLuint shader, GLsizei bufsize, GLsizei* length, GLchar* source) nogil
    void (__stdcall *glGetTexParameterfv)(GLenum target, GLenum pname, GLfloat* params) nogil
    void (__stdcall *glGetTexParameteriv)(GLenum target, GLenum pname, GLint* params) nogil
    void (__stdcall *glGetUniformfv)(GLuint program, GLint location, GLfloat* params) nogil
    void (__stdcall *glGetUniformiv)(GLuint program, GLint location, GLint* params) nogil
    void (__stdcall *glGetVertexAttribfv)(GLuint index, GLenum pname, GLfloat* params) nogil
    void (__stdcall *glGetVertexAttribiv)(GLuint index, GLenum pname, GLint* params) nogil
    void (__stdcall *glHint)(GLenum target, GLenum mode) nogil
    void (__stdcall *glLineWidth)(GLfloat width) nogil
    void (__stdcall *glLinkProgram)(GLuint) nogil
    void (__stdcall *glPixelStorei)(GLenum, GLint) nogil
    void (__stdcall *glPolygonOffset)(GLfloat factor, GLfloat units) nogil
    void (__stdcall *glReadPixels)(GLint, GLint, GLsizei, GLsizei, GLenum, GLenum, GLvoid*) nogil
    void (__stdcall *glRenderbufferStorage)(GLenum target, GLenum internalformat, GLsizei width, GLsizei height) nogil
    void (__stdcall *glSampleCoverage)(GLclampf value, GLboolean invert) nogil
    void (__stdcall *glScissor)(GLint, GLint, GLsizei, GLsizei) nogil
    void (__stdcall *glShaderBinary)(GLsizei, const GLuint *, GLenum, const void *, GLsizei) nogil
    void (__stdcall *glShaderSource)(GLuint, GLsizei, const GLchar**, const GLint *) nogil
    void (__stdcall *glStencilFunc)(GLenum func, GLint ref, GLuint mask) nogil
    void (__stdcall *glStencilFuncSeparate)(GLenum face, GLenum func, GLint ref, GLuint mask) nogil
    void (__stdcall *glStencilMask)(GLuint mask) nogil
    void (__stdcall *glStencilMaskSeparate)(GLenum face, GLuint mask) nogil
    void (__stdcall *glStencilOp)(GLenum fail, GLenum zfail, GLenum zpass) nogil
    void (__stdcall *glStencilOpSeparate)(GLenum face, GLenum fail, GLenum zfail, GLenum zpass) nogil
    void (__stdcall *glTexImage2D)(GLenum, GLint, GLint, GLsizei, GLsizei, GLint, GLenum, GLenum, const void *) nogil
    void (__stdcall *glTexParameterf)(GLenum target, GLenum pname, GLfloat param) nogil
    void (__stdcall *glTexParameteri)(GLenum, GLenum, GLint) nogil
    void (__stdcall *glTexSubImage2D)(GLenum, GLint, GLint, GLint, GLsizei, GLsizei, GLenum, GLenum, const GLvoid *) nogil
    void (__stdcall *glUniform1f)(GLint location, GLfloat x) nogil
    void (__stdcall *glUniform1fv)(GLint location, GLsizei count, const GLfloat* v) nogil
    void (__stdcall *glUniform1i)(GLint, GLint) nogil
    void (__stdcall *glUniform1iv)(GLint location, GLsizei count, const GLint* v) nogil
    void (__stdcall *glUniform2f)(GLint location, GLfloat x, GLfloat y) nogil
    void (__stdcall *glUniform2fv)(GLint location, GLsizei count, const GLfloat* v) nogil
    void (__stdcall *glUniform2i)(GLint location, GLint x, GLint y) nogil
    void (__stdcall *glUniform2iv)(GLint location, GLsizei count, const GLint* v) nogil
    void (__stdcall *glUniform3f)(GLint location, GLfloat x, GLfloat y, GLfloat z) nogil
    void (__stdcall *glUniform3fv)(GLint location, GLsizei count, const GLfloat* v) nogil
    void (__stdcall *glUniform3i)(GLint location, GLint x, GLint y, GLint z) nogil
    void (__stdcall *glUniform3iv)(GLint location, GLsizei count, const GLint* v) nogil
    void (__stdcall *glUniform4f)(GLint, GLfloat, GLfloat, GLfloat, GLfloat) nogil
    void (__stdcall *glUniform4fv)(GLint location, GLsizei count, const GLfloat* v) nogil
    void (__stdcall *glUniform4i)(GLint location, GLint x, GLint y, GLint z, GLint w) nogil
    void (__stdcall *glUniform4iv)(GLint location, GLsizei count, const GLint* v) nogil
    void (__stdcall *glUniformMatrix4fv)(GLint, GLsizei, GLboolean, const GLfloat *) nogil
    void (__stdcall *glUseProgram)(GLuint) nogil
    void (__stdcall *glValidateProgram)(GLuint program) nogil
    void (__stdcall *glVertexAttrib1f)(GLuint indx, GLfloat x) nogil
    void (__stdcall *glVertexAttrib2f)(GLuint indx, GLfloat x, GLfloat y) nogil
    void (__stdcall *glVertexAttrib3f)(GLuint indx, GLfloat x, GLfloat y, GLfloat z) nogil
    void (__stdcall *glVertexAttrib4f)(GLuint indx, GLfloat x, GLfloat y, GLfloat z, GLfloat w) nogil
    void (__stdcall *glVertexAttribPointer)(GLuint, GLint, GLenum, GLboolean, GLsizei, const void *) nogil
    void (__stdcall *glViewport)(GLint, GLint, GLsizei, GLsizei) nogil


cpdef is_backend_supported():
    return not USE_OPENGL_MOCK and PLATFORM != "win32"


def init_backend():
    IF USE_OPENGL_MOCK or PLATFORM == "win32":
        raise TypeError('GL is not available. Recompile with USE_OPENGL_MOCK=0')
    ELSE:
        link_static()


cpdef link_static():
    IF USE_OPENGL_MOCK:
        pass
    ELSE:
        cgl.glActiveTexture = glActiveTexture
        cgl.glAttachShader = glAttachShader
        cgl.glBindAttribLocation = glBindAttribLocation
        cgl.glBindBuffer = glBindBuffer
        cgl.glBindFramebuffer = glBindFramebuffer
        cgl.glBindRenderbuffer = glBindRenderbuffer
        cgl.glBindTexture = glBindTexture
        cgl.glBlendColor = glBlendColor
        cgl.glBlendEquation = glBlendEquation
        cgl.glBlendEquationSeparate = glBlendEquationSeparate
        cgl.glBlendFunc = glBlendFunc
        cgl.glBlendFuncSeparate = glBlendFuncSeparate
        cgl.glBufferData = glBufferData
        cgl.glBufferSubData = glBufferSubData
        cgl.glCheckFramebufferStatus = glCheckFramebufferStatus
        cgl.glClear = glClear
        cgl.glClearColor = glClearColor
        cgl.glClearStencil = glClearStencil
        cgl.glColorMask = glColorMask
        cgl.glCompileShader = glCompileShader
        cgl.glCompressedTexImage2D = glCompressedTexImage2D
        cgl.glCompressedTexSubImage2D = glCompressedTexSubImage2D
        cgl.glCopyTexImage2D = glCopyTexImage2D
        cgl.glCopyTexSubImage2D = glCopyTexSubImage2D
        cgl.glCreateProgram = glCreateProgram
        cgl.glCreateShader = glCreateShader
        cgl.glCullFace = glCullFace
        cgl.glDeleteBuffers = glDeleteBuffers
        cgl.glDeleteFramebuffers = glDeleteFramebuffers
        cgl.glDeleteProgram = glDeleteProgram
        cgl.glDeleteRenderbuffers = glDeleteRenderbuffers
        cgl.glDeleteShader = glDeleteShader
        cgl.glDeleteTextures = glDeleteTextures
        cgl.glDepthFunc = glDepthFunc
        cgl.glDepthMask = glDepthMask
        cgl.glDetachShader = glDetachShader
        cgl.glDisable = glDisable
        cgl.glDisableVertexAttribArray = glDisableVertexAttribArray
        cgl.glDrawArrays = glDrawArrays
        cgl.glDrawElements = glDrawElements
        cgl.glEnable = glEnable
        cgl.glEnableVertexAttribArray = glEnableVertexAttribArray
        cgl.glFinish = glFinish
        cgl.glFlush = glFlush
        cgl.glFramebufferRenderbuffer = glFramebufferRenderbuffer
        cgl.glFramebufferTexture2D = glFramebufferTexture2D
        cgl.glFrontFace = glFrontFace
        cgl.glGenBuffers = glGenBuffers
        cgl.glGenerateMipmap = glGenerateMipmap
        cgl.glGenFramebuffers = glGenFramebuffers
        cgl.glGenRenderbuffers = glGenRenderbuffers
        cgl.glGenTextures = glGenTextures
        cgl.glGetActiveAttrib = glGetActiveAttrib
        cgl.glGetActiveUniform = glGetActiveUniform
        cgl.glGetAttachedShaders = glGetAttachedShaders
        cgl.glGetAttribLocation = glGetAttribLocation
        cgl.glGetBooleanv = glGetBooleanv
        cgl.glGetBufferParameteriv = glGetBufferParameteriv
        cgl.glGetError = glGetError
        cgl.glGetFloatv = glGetFloatv
        cgl.glGetFramebufferAttachmentParameteriv = glGetFramebufferAttachmentParameteriv
        cgl.glGetIntegerv = glGetIntegerv
        cgl.glGetProgramInfoLog = glGetProgramInfoLog
        cgl.glGetProgramiv = glGetProgramiv
        cgl.glGetRenderbufferParameteriv = glGetRenderbufferParameteriv
        cgl.glGetShaderInfoLog = glGetShaderInfoLog
        cgl.glGetShaderiv = glGetShaderiv
        cgl.glGetShaderSource = glGetShaderSource
        cgl.glGetString = glGetString
        cgl.glGetTexParameterfv = glGetTexParameterfv
        cgl.glGetTexParameteriv = glGetTexParameteriv
        cgl.glGetUniformfv = glGetUniformfv
        cgl.glGetUniformiv = glGetUniformiv
        cgl.glGetUniformLocation = glGetUniformLocation
        cgl.glGetVertexAttribfv = glGetVertexAttribfv
        cgl.glGetVertexAttribiv = glGetVertexAttribiv
        cgl.glHint = glHint
        cgl.glIsBuffer = glIsBuffer
        cgl.glIsEnabled = glIsEnabled
        cgl.glIsFramebuffer = glIsFramebuffer
        cgl.glIsProgram = glIsProgram
        cgl.glIsRenderbuffer = glIsRenderbuffer
        cgl.glIsShader = glIsShader
        cgl.glIsTexture = glIsTexture
        cgl.glLineWidth = glLineWidth
        cgl.glLinkProgram = glLinkProgram
        cgl.glPixelStorei = glPixelStorei
        cgl.glPolygonOffset = glPolygonOffset
        cgl.glReadPixels = glReadPixels
        cgl.glRenderbufferStorage = glRenderbufferStorage
        cgl.glSampleCoverage = glSampleCoverage
        cgl.glScissor = glScissor
        # cgl.glShaderBinary = glShaderBinary
        cgl.glShaderSource = glShaderSource
        cgl.glStencilFunc = glStencilFunc
        cgl.glStencilFuncSeparate = glStencilFuncSeparate
        cgl.glStencilMask = glStencilMask
        cgl.glStencilMaskSeparate = glStencilMaskSeparate
        cgl.glStencilOp = glStencilOp
        cgl.glStencilOpSeparate = glStencilOpSeparate
        cgl.glTexImage2D = glTexImage2D
        cgl.glTexParameterf = glTexParameterf
        cgl.glTexParameteri = glTexParameteri
        cgl.glTexSubImage2D = glTexSubImage2D
        cgl.glUniform1f = glUniform1f
        cgl.glUniform1fv = glUniform1fv
        cgl.glUniform1i = glUniform1i
        cgl.glUniform1iv = glUniform1iv
        cgl.glUniform2f = glUniform2f
        cgl.glUniform2fv = glUniform2fv
        cgl.glUniform2i = glUniform2i
        cgl.glUniform2iv = glUniform2iv
        cgl.glUniform3f = glUniform3f
        cgl.glUniform3fv = glUniform3fv
        cgl.glUniform3i = glUniform3i
        cgl.glUniform3iv = glUniform3iv
        cgl.glUniform4f = glUniform4f
        cgl.glUniform4fv = glUniform4fv
        cgl.glUniform4i = glUniform4i
        cgl.glUniform4iv = glUniform4iv
        cgl.glUniformMatrix4fv = glUniformMatrix4fv
        cgl.glUseProgram = glUseProgram
        cgl.glValidateProgram = glValidateProgram
        cgl.glVertexAttrib1f = glVertexAttrib1f
        cgl.glVertexAttrib2f = glVertexAttrib2f
        cgl.glVertexAttrib3f = glVertexAttrib3f
        cgl.glVertexAttrib4f = glVertexAttrib4f
        cgl.glVertexAttribPointer = glVertexAttribPointer
        cgl.glViewport = glViewport
