cimport c_opengl as cgl


cdef void   glActiveTexture (GLenum texture) with gil:
    print "GL glActiveTexture()"
    cgl.glActiveTexture ( texture)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glAttachShader (GLuint program, GLuint shader) with gil:
    print "GL glAttachShader()"
    cgl.glAttachShader ( program, shader)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glBindAttribLocation (GLuint program, GLuint index,  GLchar* name) with gil:
    print "GL glBindAttribLocation()"
    cgl.glBindAttribLocation ( program, index, name)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glBindBuffer (GLenum target, GLuint buffer) with gil:
    print "GL glBindBuffer()"
    cgl.glBindBuffer ( target, buffer)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glBindFramebuffer (GLenum target, GLuint framebuffer) with gil:
    print "GL glBindFramebuffer()"
    cgl.glBindFramebuffer ( target, framebuffer)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glBindRenderbuffer (GLenum target, GLuint renderbuffer) with gil:
    print "GL glBindRenderbuffer()"
    cgl.glBindRenderbuffer ( target, renderbuffer)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glBindTexture (GLenum target, GLuint texture) with gil:
    print "GL glBindTexture()"
    cgl.glBindTexture ( target, texture)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glBlendColor (GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha) with gil:
    print "GL glBlendColor()"
    cgl.glBlendColor ( red, green, blue, alpha)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glBlendEquation ( GLenum mode ) with gil:
    print "GL glBlendEquation()"
    cgl.glBlendEquation ( mode )
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glBlendEquationSeparate (GLenum modeRGB, GLenum modeAlpha) with gil:
    print "GL glBlendEquationSeparate()"
    cgl.glBlendEquationSeparate ( modeRGB, modeAlpha)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glBlendFunc (GLenum sfactor, GLenum dfactor) with gil:
    print "GL glBlendFunc()"
    cgl.glBlendFunc ( sfactor, dfactor)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glBlendFuncSeparate (GLenum srcRGB, GLenum dstRGB, GLenum srcAlpha, GLenum dstAlpha) with gil:
    print "GL glBlendFuncSeparate()"
    cgl.glBlendFuncSeparate ( srcRGB, dstRGB, srcAlpha, dstAlpha)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glBufferData (GLenum target, GLsizeiptr size,  GLvoid* data, GLenum usage) with gil:
    print "GL glBufferData()"
    cgl.glBufferData ( target, size, data, usage)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glBufferSubData (GLenum target, GLintptr offset, GLsizeiptr size,  GLvoid* data) with gil:
    print "GL glBufferSubData()"
    cgl.glBufferSubData ( target, offset, size, data)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef GLenum glCheckFramebufferStatus (GLenum target) with gil:
    print "GL glCheckFramebufferStatus()"
    return cgl.glCheckFramebufferStatus ( target)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glClear (GLbitfield mask) with gil:
    print "GL glClear()"
    cgl.glClear ( mask)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glClearColor (GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha) with gil:
    print "GL glClearColor()"
    cgl.glClearColor ( red, green, blue, alpha)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glClearDepthf (GLclampf depth) with gil:
    print "GL glClearDepthf()"
    cgl.glClearDepthf ( depth)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glClearStencil (GLint s) with gil:
    print "GL glClearStencil()"
    cgl.glClearStencil ( s)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glColorMask (GLboolean red, GLboolean green, GLboolean blue, GLboolean alpha) with gil:
    print "GL glColorMask()"
    cgl.glColorMask ( red, green, blue, alpha)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glCompileShader (GLuint shader) with gil:
    print "GL glCompileShader()"
    cgl.glCompileShader ( shader)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glCompressedTexImage2D (GLenum target, GLint level, GLenum internalformat, GLsizei width, GLsizei height, GLint border, GLsizei imageSize,  GLvoid* data) with gil:
    print "GL glCompressedTexImage2D()"
    cgl.glCompressedTexImage2D ( target, level, internalformat, width, height, border, imageSize, data)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glCompressedTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLsizei imageSize,  GLvoid* data) with gil:
    print "GL glCompressedTexSubImage2D()"
    cgl.glCompressedTexSubImage2D ( target, level, xoffset, yoffset, width, height, format, imageSize, data)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glCopyTexImage2D (GLenum target, GLint level, GLenum internalformat, GLint x, GLint y, GLsizei width, GLsizei height, GLint border) with gil:
    print "GL glCopyTexImage2D()"
    cgl.glCopyTexImage2D ( target, level, internalformat, x, y, width, height, border)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glCopyTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLint x, GLint y, GLsizei width, GLsizei height) with gil:
    print "GL glCopyTexSubImage2D()"
    cgl.glCopyTexSubImage2D ( target, level, xoffset, yoffset, x, y, width, height)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef GLuint glCreateProgram () with gil:
    print "GL glCreateProgram()"
    return cgl.glCreateProgram ()
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef GLuint glCreateShader (GLenum type) with gil:
    print "GL glCreateShader()"
    return cgl.glCreateShader ( type)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glCullFace (GLenum mode) with gil:
    print "GL glCullFace()"
    cgl.glCullFace ( mode)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glDeleteBuffers (GLsizei n,  GLuint* buffers) with gil:
    print "GL glDeleteBuffers()"
    cgl.glDeleteBuffers ( n, buffers)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glDeleteFramebuffers (GLsizei n,  GLuint* framebuffers) with gil:
    print "GL glDeleteFramebuffers()"
    cgl.glDeleteFramebuffers ( n, framebuffers)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glDeleteProgram (GLuint program) with gil:
    print "GL glDeleteProgram()"
    cgl.glDeleteProgram ( program)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glDeleteRenderbuffers (GLsizei n,  GLuint* renderbuffers) with gil:
    print "GL glDeleteRenderbuffers()"
    cgl.glDeleteRenderbuffers ( n, renderbuffers)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glDeleteShader (GLuint shader) with gil:
    print "GL glDeleteShader()"
    cgl.glDeleteShader ( shader)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glDeleteTextures (GLsizei n,  GLuint* textures) with gil:
    print "GL glDeleteTextures()"
    cgl.glDeleteTextures ( n, textures)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glDepthFunc (GLenum func) with gil:
    print "GL glDepthFunc()"
    cgl.glDepthFunc ( func)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glDepthMask (GLboolean flag) with gil:
    print "GL glDepthMask()"
    cgl.glDepthMask ( flag)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glDepthRangef (GLclampf zNear, GLclampf zFar) with gil:
    print "GL glDepthRangef()"
    cgl.glDepthRangef ( zNear, zFar)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glDetachShader (GLuint program, GLuint shader) with gil:
    print "GL glDetachShader()"
    cgl.glDetachShader ( program, shader)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glDisable (GLenum cap) with gil:
    print "GL glDisable()"
    cgl.glDisable ( cap)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glDisableVertexAttribArray (GLuint index) with gil:
    print "GL glDisableVertexAttribArray()"
    cgl.glDisableVertexAttribArray ( index)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glDrawArrays (GLenum mode, GLint first, GLsizei count) with gil:
    print "GL glDrawArrays()"
    cgl.glDrawArrays ( mode, first, count)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glDrawElements (GLenum mode, GLsizei count, GLenum type,  GLvoid* indices) with gil:
    print "GL glDrawElements()"
    cgl.glDrawElements ( mode, count, type, indices)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glEnable (GLenum cap) with gil:
    print "GL glEnable()"
    cgl.glEnable ( cap)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glEnableVertexAttribArray (GLuint index) with gil:
    print "GL glEnableVertexAttribArray()"
    cgl.glEnableVertexAttribArray ( index)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glFinish () with gil:
    print "GL glFinish()"
    cgl.glFinish ()
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glFlush () with gil:
    print "GL glFlush()"
    cgl.glFlush ()
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glFramebufferRenderbuffer (GLenum target, GLenum attachment, GLenum renderbuffertarget, GLuint renderbuffer) with gil:
    print "GL glFramebufferRenderbuffer()"
    cgl.glFramebufferRenderbuffer ( target, attachment, renderbuffertarget, renderbuffer)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glFramebufferTexture2D (GLenum target, GLenum attachment, GLenum textarget, GLuint texture, GLint level) with gil:
    print "GL glFramebufferTexture2D()"
    cgl.glFramebufferTexture2D ( target, attachment, textarget, texture, level)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glFrontFace (GLenum mode) with gil:
    print "GL glFrontFace()"
    cgl.glFrontFace ( mode)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGenBuffers (GLsizei n, GLuint* buffers) with gil:
    print "GL glGenBuffers()"
    cgl.glGenBuffers ( n, buffers)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGenerateMipmap (GLenum target) with gil:
    print "GL glGenerateMipmap()"
    cgl.glGenerateMipmap ( target)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGenFramebuffers (GLsizei n, GLuint* framebuffers) with gil:
    print "GL glGenFramebuffers()"
    cgl.glGenFramebuffers ( n, framebuffers)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGenRenderbuffers (GLsizei n, GLuint* renderbuffers) with gil:
    print "GL glGenRenderbuffers()"
    cgl.glGenRenderbuffers ( n, renderbuffers)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGenTextures (GLsizei n, GLuint* textures) with gil:
    print "GL glGenTextures()"
    cgl.glGenTextures ( n, textures)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetActiveAttrib (GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name) with gil:
    print "GL glGetActiveAttrib()"
    cgl.glGetActiveAttrib ( program, index, bufsize, length, size, type, name)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetActiveUniform (GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name) with gil:
    print "GL glGetActiveUniform()"
    cgl.glGetActiveUniform ( program, index, bufsize, length, size, type, name)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetAttachedShaders (GLuint program, GLsizei maxcount, GLsizei* count, GLuint* shaders) with gil:
    print "GL glGetAttachedShaders()"
    cgl.glGetAttachedShaders ( program, maxcount, count, shaders)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef int    glGetAttribLocation (GLuint program,  GLchar* name) with gil:
    print "GL glGetAttribLocation()"
    return cgl.glGetAttribLocation ( program, name)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetBooleanv (GLenum pname, GLboolean* params) with gil:
    print "GL glGetBooleanv()"
    cgl.glGetBooleanv ( pname, params)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetBufferParameteriv (GLenum target, GLenum pname, GLint* params) with gil:
    print "GL glGetBufferParameteriv()"
    cgl.glGetBufferParameteriv ( target, pname, params)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef GLenum glGetError () with gil:
    print "GL glGetError()"
    return cgl.glGetError ()
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetFloatv (GLenum pname, GLfloat* params) with gil:
    print "GL glGetFloatv()"
    cgl.glGetFloatv ( pname, params)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetFramebufferAttachmentParameteriv (GLenum target, GLenum attachment, GLenum pname, GLint* params) with gil:
    print "GL glGetFramebufferAttachmentParameteriv()"
    cgl.glGetFramebufferAttachmentParameteriv ( target, attachment, pname, params)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetIntegerv (GLenum pname, GLint* params) with gil:
    print "GL glGetIntegerv()"
    cgl.glGetIntegerv ( pname, params)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetProgramiv (GLuint program, GLenum pname, GLint* params) with gil:
    print "GL glGetProgramiv()"
    cgl.glGetProgramiv ( program, pname, params)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetProgramInfoLog (GLuint program, GLsizei bufsize, GLsizei* length, GLchar* infolog) with gil:
    print "GL glGetProgramInfoLog()"
    cgl.glGetProgramInfoLog ( program, bufsize, length, infolog)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetRenderbufferParameteriv (GLenum target, GLenum pname, GLint* params) with gil:
    print "GL glGetRenderbufferParameteriv()"
    cgl.glGetRenderbufferParameteriv ( target, pname, params)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetShaderiv (GLuint shader, GLenum pname, GLint* params) with gil:
    print "GL glGetShaderiv()"
    cgl.glGetShaderiv ( shader, pname, params)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetShaderInfoLog (GLuint shader, GLsizei bufsize, GLsizei* length, GLchar* infolog) with gil:
    print "GL glGetShaderInfoLog()"
    cgl.glGetShaderInfoLog ( shader, bufsize, length, infolog)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetShaderPrecisionFormat (GLenum shadertype, GLenum precisiontype, GLint* range, GLint* precision) with gil:
    print "GL glGetShaderPrecisionFormat()"
    cgl.glGetShaderPrecisionFormat ( shadertype, precisiontype, range, precision)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetShaderSource (GLuint shader, GLsizei bufsize, GLsizei* length, GLchar* source) with gil:
    print "GL glGetShaderSource()"
    cgl.glGetShaderSource ( shader, bufsize, length, source)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef   GLubyte*  glGetString (GLenum name) with gil:
    print "GL glGetString()"
    return cgl.glGetString ( name)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetTexParameterfv (GLenum target, GLenum pname, GLfloat* params) with gil:
    print "GL glGetTexParameterfv()"
    cgl.glGetTexParameterfv ( target, pname, params)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetTexParameteriv (GLenum target, GLenum pname, GLint* params) with gil:
    print "GL glGetTexParameteriv()"
    cgl.glGetTexParameteriv ( target, pname, params)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetUniformfv (GLuint program, GLint location, GLfloat* params) with gil:
    print "GL glGetUniformfv()"
    cgl.glGetUniformfv ( program, location, params)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetUniformiv (GLuint program, GLint location, GLint* params) with gil:
    print "GL glGetUniformiv()"
    cgl.glGetUniformiv ( program, location, params)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef int    glGetUniformLocation (GLuint program,  GLchar* name) with gil:
    print "GL glGetUniformLocation()"
    return cgl.glGetUniformLocation ( program, name)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetVertexAttribfv (GLuint index, GLenum pname, GLfloat* params) with gil:
    print "GL glGetVertexAttribfv()"
    cgl.glGetVertexAttribfv ( index, pname, params)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetVertexAttribiv (GLuint index, GLenum pname, GLint* params) with gil:
    print "GL glGetVertexAttribiv()"
    cgl.glGetVertexAttribiv ( index, pname, params)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glGetVertexAttribPointerv (GLuint index, GLenum pname, GLvoid** pointer) with gil:
    print "GL glGetVertexAttribPointerv()"
    cgl.glGetVertexAttribPointerv ( index, pname, pointer)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void   glHint (GLenum target, GLenum mode) with gil:
    print "GL glHint()"
    cgl.glHint ( target, mode)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef GLboolean  glIsBuffer (GLuint buffer) with gil:
    print "GL glIsBuffer()"
    return cgl.glIsBuffer ( buffer)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef GLboolean  glIsEnabled (GLenum cap) with gil:
    print "GL glIsEnabled()"
    return cgl.glIsEnabled ( cap)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef GLboolean  glIsFramebuffer (GLuint framebuffer) with gil:
    print "GL glIsFramebuffer()"
    return cgl.glIsFramebuffer ( framebuffer)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef GLboolean  glIsProgram (GLuint program) with gil:
    print "GL glIsProgram()"
    return cgl.glIsProgram ( program)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef GLboolean  glIsRenderbuffer (GLuint renderbuffer) with gil:
    print "GL glIsRenderbuffer()"
    return cgl.glIsRenderbuffer ( renderbuffer)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef GLboolean  glIsShader (GLuint shader) with gil:
    print "GL glIsShader()"
    return cgl.glIsShader ( shader)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef GLboolean  glIsTexture (GLuint texture) with gil:
    print "GL glIsTexture()"
    return cgl.glIsTexture ( texture)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glLineWidth (GLfloat width) with gil:
    print "GL glLineWidth()"
    cgl.glLineWidth ( width)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glLinkProgram (GLuint program) with gil:
    print "GL glLinkProgram()"
    cgl.glLinkProgram ( program)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glPixelStorei (GLenum pname, GLint param) with gil:
    print "GL glPixelStorei()"
    cgl.glPixelStorei ( pname, param)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glPolygonOffset (GLfloat factor, GLfloat units) with gil:
    print "GL glPolygonOffset()"
    cgl.glPolygonOffset ( factor, units)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glReadPixels (GLint x, GLint y, GLsizei width, GLsizei height, GLenum format, GLenum type, GLvoid* pixels) with gil:
    print "GL glReadPixels()"
    cgl.glReadPixels ( x, y, width, height, format, type, pixels)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glReleaseShaderCompiler () with gil:
    print "GL glReleaseShaderCompiler()"
    cgl.glReleaseShaderCompiler ()
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glRenderbufferStorage (GLenum target, GLenum internalformat, GLsizei width, GLsizei height) with gil:
    print "GL glRenderbufferStorage()"
    cgl.glRenderbufferStorage ( target, internalformat, width, height)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glSampleCoverage (GLclampf value, GLboolean invert) with gil:
    print "GL glSampleCoverage()"
    cgl.glSampleCoverage ( value, invert)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glScissor (GLint x, GLint y, GLsizei width, GLsizei height) with gil:
    print "GL glScissor()"
    cgl.glScissor ( x, y, width, height)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glShaderBinary (GLsizei n,  GLuint* shaders, GLenum binaryformat,  GLvoid* binary, GLsizei length) with gil:
    print "GL glShaderBinary()"
    cgl.glShaderBinary ( n, shaders, binaryformat, binary, length)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glShaderSource (GLuint shader, GLsizei count,  GLchar** string,  GLint* length) with gil:
    print "GL glShaderSource()"
    cgl.glShaderSource ( shader, count, string, length)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glStencilFunc (GLenum func, GLint ref, GLuint mask) with gil:
    print "GL glStencilFunc()"
    cgl.glStencilFunc ( func, ref, mask)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glStencilFuncSeparate (GLenum face, GLenum func, GLint ref, GLuint mask) with gil:
    print "GL glStencilFuncSeparate()"
    cgl.glStencilFuncSeparate ( face, func, ref, mask)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glStencilMask (GLuint mask) with gil:
    print "GL glStencilMask()"
    cgl.glStencilMask ( mask)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glStencilMaskSeparate (GLenum face, GLuint mask) with gil:
    print "GL glStencilMaskSeparate()"
    cgl.glStencilMaskSeparate ( face, mask)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glStencilOp (GLenum fail, GLenum zfail, GLenum zpass) with gil:
    print "GL glStencilOp()"
    cgl.glStencilOp ( fail, zfail, zpass)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glStencilOpSeparate (GLenum face, GLenum fail, GLenum zfail, GLenum zpass) with gil:
    print "GL glStencilOpSeparate()"
    cgl.glStencilOpSeparate ( face, fail, zfail, zpass)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glTexImage2D (GLenum target, GLint level, GLint internalformat, GLsizei width, GLsizei height, GLint border, GLenum format, GLenum type,  GLvoid* pixels) with gil:
    print "GL glTexImage2D()"
    cgl.glTexImage2D ( target, level, internalformat, width, height, border, format, type, pixels)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glTexParameterf (GLenum target, GLenum pname, GLfloat param) with gil:
    print "GL glTexParameterf()"
    cgl.glTexParameterf ( target, pname, param)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glTexParameterfv (GLenum target, GLenum pname,  GLfloat* params) with gil:
    print "GL glTexParameterfv()"
    cgl.glTexParameterfv ( target, pname, params)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glTexParameteri (GLenum target, GLenum pname, GLint param) with gil:
    print "GL glTexParameteri()"
    cgl.glTexParameteri ( target, pname, param)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glTexParameteriv (GLenum target, GLenum pname,  GLint* params) with gil:
    print "GL glTexParameteriv()"
    cgl.glTexParameteriv ( target, pname, params)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLenum type,  GLvoid* pixels) with gil:
    print "GL glTexSubImage2D()"
    cgl.glTexSubImage2D ( target, level, xoffset, yoffset, width, height, format, type, pixels)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniform1f (GLint location, GLfloat x) with gil:
    print "GL glUniform1f()"
    cgl.glUniform1f ( location, x)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniform1fv (GLint location, GLsizei count,  GLfloat* v) with gil:
    print "GL glUniform1fv()"
    cgl.glUniform1fv ( location, count, v)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniform1i (GLint location, GLint x) with gil:
    print "GL glUniform1i()"
    cgl.glUniform1i ( location, x)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniform1iv (GLint location, GLsizei count,  GLint* v) with gil:
    print "GL glUniform1iv()"
    cgl.glUniform1iv ( location, count, v)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniform2f (GLint location, GLfloat x, GLfloat y) with gil:
    print "GL glUniform2f()"
    cgl.glUniform2f ( location, x, y)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniform2fv (GLint location, GLsizei count,  GLfloat* v) with gil:
    print "GL glUniform2fv()"
    cgl.glUniform2fv ( location, count, v)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniform2i (GLint location, GLint x, GLint y) with gil:
    print "GL glUniform2i()"
    cgl.glUniform2i ( location, x, y)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniform2iv (GLint location, GLsizei count,  GLint* v) with gil:
    print "GL glUniform2iv()"
    cgl.glUniform2iv ( location, count, v)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniform3f (GLint location, GLfloat x, GLfloat y, GLfloat z) with gil:
    print "GL glUniform3f()"
    cgl.glUniform3f ( location, x, y, z)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniform3fv (GLint location, GLsizei count,  GLfloat* v) with gil:
    print "GL glUniform3fv()"
    cgl.glUniform3fv ( location, count, v)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniform3i (GLint location, GLint x, GLint y, GLint z) with gil:
    print "GL glUniform3i()"
    cgl.glUniform3i ( location, x, y, z)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniform3iv (GLint location, GLsizei count,  GLint* v) with gil:
    print "GL glUniform3iv()"
    cgl.glUniform3iv ( location, count, v)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniform4f (GLint location, GLfloat x, GLfloat y, GLfloat z, GLfloat w) with gil:
    print "GL glUniform4f()"
    cgl.glUniform4f ( location, x, y, z, w)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniform4fv (GLint location, GLsizei count,  GLfloat* v) with gil:
    print "GL glUniform4fv()"
    cgl.glUniform4fv ( location, count, v)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniform4i (GLint location, GLint x, GLint y, GLint z, GLint w) with gil:
    print "GL glUniform4i()"
    cgl.glUniform4i ( location, x, y, z, w)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniform4iv (GLint location, GLsizei count,  GLint* v) with gil:
    print "GL glUniform4iv()"
    cgl.glUniform4iv ( location, count, v)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniformMatrix2fv (GLint location, GLsizei count, GLboolean transpose,  GLfloat* value) with gil:
    print "GL glUniformMatrix2fv()"
    cgl.glUniformMatrix2fv ( location, count, transpose, value)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniformMatrix3fv (GLint location, GLsizei count, GLboolean transpose,  GLfloat* value) with gil:
    print "GL glUniformMatrix3fv()"
    cgl.glUniformMatrix3fv ( location, count, transpose, value)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUniformMatrix4fv (GLint location, GLsizei count, GLboolean transpose,  GLfloat* value) with gil:
    print "GL glUniformMatrix4fv()"
    cgl.glUniformMatrix4fv ( location, count, transpose, value)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glUseProgram (GLuint program) with gil:
    print "GL glUseProgram()"
    cgl.glUseProgram ( program)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glValidateProgram (GLuint program) with gil:
    print "GL glValidateProgram()"
    cgl.glValidateProgram ( program)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glVertexAttrib1f (GLuint indx, GLfloat x) with gil:
    print "GL glVertexAttrib1f()"
    cgl.glVertexAttrib1f ( indx, x)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glVertexAttrib1fv (GLuint indx,  GLfloat* values) with gil:
    print "GL glVertexAttrib1fv()"
    cgl.glVertexAttrib1fv ( indx, values)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glVertexAttrib2f (GLuint indx, GLfloat x, GLfloat y) with gil:
    print "GL glVertexAttrib2f()"
    cgl.glVertexAttrib2f ( indx, x, y)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glVertexAttrib2fv (GLuint indx,  GLfloat* values) with gil:
    print "GL glVertexAttrib2fv()"
    cgl.glVertexAttrib2fv ( indx, values)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glVertexAttrib3f (GLuint indx, GLfloat x, GLfloat y, GLfloat z) with gil:
    print "GL glVertexAttrib3f()"
    cgl.glVertexAttrib3f ( indx, x, y, z)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glVertexAttrib3fv (GLuint indx,  GLfloat* values) with gil:
    print "GL glVertexAttrib3fv()"
    cgl.glVertexAttrib3fv ( indx, values)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glVertexAttrib4f (GLuint indx, GLfloat x, GLfloat y, GLfloat z, GLfloat w) with gil:
    print "GL glVertexAttrib4f()"
    cgl.glVertexAttrib4f ( indx, x, y, z, w)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glVertexAttrib4fv (GLuint indx,  GLfloat* values) with gil:
    print "GL glVertexAttrib4fv()"
    cgl.glVertexAttrib4fv ( indx, values)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glVertexAttribPointer (GLuint indx, GLint size, GLenum type, GLboolean normalized, GLsizei stride,  GLvoid* ptr) with gil:
    print "GL glVertexAttribPointer()"
    cgl.glVertexAttribPointer ( indx, size, type, normalized, stride, ptr)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
cdef void  glViewport (GLint x, GLint y, GLsizei width, GLsizei height) with gil:
    print "GL glViewport()"
    cgl.glViewport ( x, y, width, height)
    ret = glGetError()
    if ret: print "ERR %d / %x" % (ret, ret)
