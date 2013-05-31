
# This file was automatically generated with kivy/tools/stub-gl-debug.py
include "common.pxi"
cimport kivy.graphics.c_opengl as cgl


cdef void   glActiveTexture (GLenum texture) with gil:
    print("GL glActiveTexture( texture = ", texture, ", )")
    cgl.glActiveTexture ( texture)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glAttachShader (GLuint program, GLuint shader) with gil:
    print("GL glAttachShader( program = ", program, ", shader = ", shader, ",)")
    cgl.glAttachShader ( program, shader)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glBindAttribLocation (GLuint program, GLuint index,  GLchar* name) with gil:
    print("GL glBindAttribLocation( program = ", program, ", index = ", index, ", name*=", repr(hex(<long> name)), ", )")
    cgl.glBindAttribLocation ( program, index, name)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glBindBuffer (GLenum target, GLuint buffer) with gil:
    print("GL glBindBuffer( target = ", target, ", buffer = ", buffer, ", )")
    cgl.glBindBuffer ( target, buffer)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glBindFramebuffer (GLenum target, GLuint framebuffer) with gil:
    print("GL glBindFramebuffer( target = ", target, ", framebuffer = ", framebuffer, ", )")
    cgl.glBindFramebuffer ( target, framebuffer)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glBindRenderbuffer (GLenum target, GLuint renderbuffer) with gil:
    print("GL glBindRenderbuffer( target = ", target, ", renderbuffer = ", renderbuffer, ", )")
    cgl.glBindRenderbuffer ( target, renderbuffer)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glBindTexture (GLenum target, GLuint texture) with gil:
    print("GL glBindTexture( target = ", target, ", texture = ", texture, ", )")
    cgl.glBindTexture ( target, texture)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glBlendColor (GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha) with gil:
    print("GL glBlendColor( red = ", red, ", green = ", green, ", blue = ", blue, ", alpha = ", alpha, ", )")
    cgl.glBlendColor ( red, green, blue, alpha)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glBlendEquation (GLenum mode) with gil:
    print("GL glBlendEquation( mode = ", mode, ", )")
    cgl.glBlendEquation ( mode)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glBlendEquationSeparate (GLenum modeRGB, GLenum modeAlpha) with gil:
    print("GL glBlendEquationSeparate( modeRGB = ", modeRGB, ", modeAlpha = ", modeAlpha, ", )")
    cgl.glBlendEquationSeparate ( modeRGB, modeAlpha)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glBlendFunc (GLenum sfactor, GLenum dfactor) with gil:
    print("GL glBlendFunc( sfactor = ", sfactor, ", dfactor = ", dfactor, ", )")
    cgl.glBlendFunc ( sfactor, dfactor)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glBlendFuncSeparate (GLenum srcRGB, GLenum dstRGB, GLenum srcAlpha, GLenum dstAlpha) with gil:
    print("GL glBlendFuncSeparate( srcRGB = ", srcRGB, ", dstRGB = ", dstRGB, ", srcAlpha = ", srcAlpha, ", dstAlpha = ", dstAlpha, ", )")
    cgl.glBlendFuncSeparate ( srcRGB, dstRGB, srcAlpha, dstAlpha)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glBufferData (GLenum target, GLsizeiptr size,  GLvoid* data, GLenum usage) with gil:
    print("GL glBufferData( target = ", target, ", size = ", size, ", data*=", repr(hex(<long> data)), ", usage = ", usage, ", )")
    cgl.glBufferData ( target, size, data, usage)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glBufferSubData (GLenum target, GLintptr offset, GLsizeiptr size,  GLvoid* data) with gil:
    print("GL glBufferSubData( target = ", target, ", offset = ", offset, ", size = ", size, ", data*=", repr(hex(<long> data)), ", )")
    cgl.glBufferSubData ( target, offset, size, data)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef GLenum glCheckFramebufferStatus (GLenum target) with gil:
    print("GL glCheckFramebufferStatus( target = ", target, ", )")
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
    return cgl.glCheckFramebufferStatus ( target)
cdef void   glClear (GLbitfield mask) with gil:
    print("GL glClear( mask = ", mask, ", )")
    cgl.glClear ( mask)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glClearColor (GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha) with gil:
    print("GL glClearColor( red = ", red, ", green = ", green, ", blue = ", blue, ", alpha = ", alpha, ", )")
    cgl.glClearColor ( red, green, blue, alpha)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
#crash on android platform
#cdef void   glClearDepthf (GLclampf depth) with gil:
#    print("GL glClearDepthf( depth = ", depth, ", )")
#    cgl.glClearDepthf ( depth)
#    ret = cgl.glGetError()
#    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glClearStencil (GLint s) with gil:
    print("GL glClearStencil( s = ", s, ", )")
    cgl.glClearStencil ( s)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glColorMask (GLboolean red, GLboolean green, GLboolean blue, GLboolean alpha) with gil:
    print("GL glColorMask( red = ", red, ", green = ", green, ", blue = ", blue, ", alpha = ", alpha, ", )")
    cgl.glColorMask ( red, green, blue, alpha)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glCompileShader (GLuint shader) with gil:
    print("GL glCompileShader( shader = ", shader, ", )")
    cgl.glCompileShader ( shader)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glCompressedTexImage2D (GLenum target, GLint level, GLenum internalformat, GLsizei width, GLsizei height, GLint border, GLsizei imageSize,  GLvoid* data) with gil:
    print("GL glCompressedTexImage2D( target = ", target, ", level = ", level, ", internalformat = ", internalformat, ", width = ", width, ", height = ", height, ", border = ", border, ", imageSize = ", imageSize, ", data*=", repr(hex(<long> data)), ", )")
    cgl.glCompressedTexImage2D ( target, level, internalformat, width, height, border, imageSize, data)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glCompressedTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLsizei imageSize,  GLvoid* data) with gil:
    print("GL glCompressedTexSubImage2D( target = ", target, ", level = ", level, ", xoffset = ", xoffset, ", yoffset = ", yoffset, ", width = ", width, ", height = ", height, ", format = ", format, ", imageSize = ", imageSize, ", data*=", repr(hex(<long> data)), ", )")
    cgl.glCompressedTexSubImage2D ( target, level, xoffset, yoffset, width, height, format, imageSize, data)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glCopyTexImage2D (GLenum target, GLint level, GLenum internalformat, GLint x, GLint y, GLsizei width, GLsizei height, GLint border) with gil:
    print("GL glCopyTexImage2D( target = ", target, ", level = ", level, ", internalformat = ", internalformat, ", x = ", x, ", y = ", y, ", width = ", width, ", height = ", height, ", border = ", border, ", )")
    cgl.glCopyTexImage2D ( target, level, internalformat, x, y, width, height, border)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glCopyTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLint x, GLint y, GLsizei width, GLsizei height) with gil:
    print("GL glCopyTexSubImage2D( target = ", target, ", level = ", level, ", xoffset = ", xoffset, ", yoffset = ", yoffset, ", x = ", x, ", y = ", y, ", width = ", width, ", height = ", height, ", )")
    cgl.glCopyTexSubImage2D ( target, level, xoffset, yoffset, x, y, width, height)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef GLuint glCreateProgram () with gil:
    print("GL glCreateProgram( )")
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
    return cgl.glCreateProgram ()
cdef GLuint glCreateShader (GLenum type) with gil:
    print("GL glCreateShader( type = ", type, ", )")
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
    return cgl.glCreateShader ( type)
cdef void   glCullFace (GLenum mode) with gil:
    print("GL glCullFace( mode = ", mode, ", )")
    cgl.glCullFace ( mode)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glDeleteBuffers (GLsizei n,  GLuint* buffers) with gil:
    print("GL glDeleteBuffers( n = ", n, ", buffers*=", repr(hex(<long> buffers)), ", )")
    cgl.glDeleteBuffers ( n, buffers)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glDeleteFramebuffers (GLsizei n,  GLuint* framebuffers) with gil:
    print("GL glDeleteFramebuffers( n = ", n, ", framebuffers*=", repr(hex(<long> framebuffers)), ", )")
    cgl.glDeleteFramebuffers ( n, framebuffers)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glDeleteProgram (GLuint program) with gil:
    print("GL glDeleteProgram( program = ", program, ", )")
    cgl.glDeleteProgram ( program)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glDeleteRenderbuffers (GLsizei n,  GLuint* renderbuffers) with gil:
    print("GL glDeleteRenderbuffers( n = ", n, ", renderbuffers*=", repr(hex(<long> renderbuffers)), ", )")
    cgl.glDeleteRenderbuffers ( n, renderbuffers)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glDeleteShader (GLuint shader) with gil:
    print("GL glDeleteShader( shader = ", shader, ", )")
    cgl.glDeleteShader ( shader)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glDeleteTextures (GLsizei n,  GLuint* textures) with gil:
    print("GL glDeleteTextures( n = ", n, ", textures*=", repr(hex(<long> textures)), ", )")
    cgl.glDeleteTextures ( n, textures)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glDepthFunc (GLenum func) with gil:
    print("GL glDepthFunc( func = ", func, ", )")
    cgl.glDepthFunc ( func)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glDepthMask (GLboolean flag) with gil:
    print("GL glDepthMask( flag = ", flag, ", )")
    cgl.glDepthMask ( flag)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
#crash on android platform
#cdef void   glDepthRangef (GLclampf zNear, GLclampf zFar) with gil:
#    print("GL glDepthRangef( zNear = ", zNear, ", zFar = ", zFar, ", )")
#    cgl.glDepthRangef ( zNear, zFar)
#    ret = glGetError()
#    if ret: print("ERR %d / %x" % (ret, ret))
cdef void   glDetachShader (GLuint program, GLuint shader) with gil:
    print("GL glDetachShader( program = ", program, ", shader = ", shader, ", )")
    cgl.glDetachShader ( program, shader)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glDisable (GLenum cap) with gil:
    print("GL glDisable( cap = ", cap, ", )")
    cgl.glDisable ( cap)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glDisableVertexAttribArray (GLuint index) with gil:
    print("GL glDisableVertexAttribArray( index = ", index, ", )")
    cgl.glDisableVertexAttribArray ( index)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glDrawArrays (GLenum mode, GLint first, GLsizei count) with gil:
    print("GL glDrawArrays( mode = ", mode, ", first = ", first, ", count = ", count, ", )")
    cgl.glDrawArrays ( mode, first, count)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glDrawElements (GLenum mode, GLsizei count, GLenum type,  GLvoid* indices) with gil:
    print("GL glDrawElements( mode = ", mode, ", count = ", count, ", type = ", type, ", indices*=", repr(hex(<long> indices)), ", )")
    cgl.glDrawElements ( mode, count, type, indices)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glEnable (GLenum cap) with gil:
    print("GL glEnable( cap = ", cap, ", )")
    cgl.glEnable ( cap)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glEnableVertexAttribArray (GLuint index) with gil:
    print("GL glEnableVertexAttribArray( index = ", index, ", )")
    cgl.glEnableVertexAttribArray ( index)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glFinish () with gil:
    print("GL glFinish( )")
    cgl.glFinish ()
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glFlush () with gil:
    print("GL glFlush( )")
    cgl.glFlush ()
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glFramebufferRenderbuffer (GLenum target, GLenum attachment, GLenum renderbuffertarget, GLuint renderbuffer) with gil:
    print("GL glFramebufferRenderbuffer( target = ", target, ", attachment = ", attachment, ", renderbuffertarget = ", renderbuffertarget, ", renderbuffer = ", renderbuffer, ", )")
    cgl.glFramebufferRenderbuffer ( target, attachment, renderbuffertarget, renderbuffer)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glFramebufferTexture2D (GLenum target, GLenum attachment, GLenum textarget, GLuint texture, GLint level) with gil:
    print("GL glFramebufferTexture2D( target = ", target, ", attachment = ", attachment, ", textarget = ", textarget, ", texture = ", texture, ", level = ", level, ", )")
    cgl.glFramebufferTexture2D ( target, attachment, textarget, texture, level)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glFrontFace (GLenum mode) with gil:
    print("GL glFrontFace( mode = ", mode, ", )")
    cgl.glFrontFace ( mode)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGenBuffers (GLsizei n, GLuint* buffers) with gil:
    print("GL glGenBuffers( n = ", n, ", buffers*=", repr(hex(<long> buffers)), ", )")
    cgl.glGenBuffers ( n, buffers)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGenerateMipmap (GLenum target) with gil:
    print("GL glGenerateMipmap( target = ", target, ", )")
    cgl.glGenerateMipmap ( target)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGenFramebuffers (GLsizei n, GLuint* framebuffers) with gil:
    print("GL glGenFramebuffers( n = ", n, ", framebuffers*=", repr(hex(<long> framebuffers)), ", )")
    cgl.glGenFramebuffers ( n, framebuffers)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGenRenderbuffers (GLsizei n, GLuint* renderbuffers) with gil:
    print("GL glGenRenderbuffers( n = ", n, ", renderbuffers*=", repr(hex(<long> renderbuffers)), ", )")
    cgl.glGenRenderbuffers ( n, renderbuffers)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGenTextures (GLsizei n, GLuint* textures) with gil:
    print("GL glGenTextures( n = ", n, ", textures*=", repr(hex(<long> textures)), ", )")
    cgl.glGenTextures ( n, textures)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGetActiveAttrib (GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name) with gil:
    print("GL glGetActiveAttrib( program = ", program, ", index = ", index, ", bufsize = ", bufsize, ", length*=", repr(hex(<long> length)), ", size*=", repr(hex(<long> size)), ", type*=", repr(hex(<long> type)), ", name*=", repr(hex(<long> name)), ", )")
    cgl.glGetActiveAttrib ( program, index, bufsize, length, size, type, name)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGetActiveUniform (GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name) with gil:
    print("GL glGetActiveUniform( program = ", program, ", index = ", index, ", bufsize = ", bufsize, ", length*=", repr(hex(<long> length)), ", size*=", repr(hex(<long> size)), ", type*=", repr(hex(<long> type)), ", name*=", repr(hex(<long> name)), ", )")
    cgl.glGetActiveUniform ( program, index, bufsize, length, size, type, name)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGetAttachedShaders (GLuint program, GLsizei maxcount, GLsizei* count, GLuint* shaders) with gil:
    print("GL glGetAttachedShaders( program = ", program, ", maxcount = ", maxcount, ", count*=", repr(hex(<long> count)), ", shaders*=", repr(hex(<long> shaders)), ", )")
    cgl.glGetAttachedShaders ( program, maxcount, count, shaders)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef int    glGetAttribLocation (GLuint program,  GLchar* name) with gil:
    print("GL glGetAttribLocation( program = ", program, ", name*=", repr(hex(<long> name)), ", )")
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
    return cgl.glGetAttribLocation ( program, name)
cdef void   glGetBooleanv (GLenum pname, GLboolean* params) with gil:
    print("GL glGetBooleanv( pname = ", pname, ", params*=", repr(hex(<long> params)), ", )")
    cgl.glGetBooleanv ( pname, params)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGetBufferParameteriv (GLenum target, GLenum pname, GLint* params) with gil:
    print("GL glGetBufferParameteriv( target = ", target, ", pname = ", pname, ", params*=", repr(hex(<long> params)), ", )")
    cgl.glGetBufferParameteriv ( target, pname, params)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef GLenum glGetError () with gil:
    print("GL glGetError( )")
    return cgl.glGetError ()
cdef void   glGetFloatv (GLenum pname, GLfloat* params) with gil:
    print("GL glGetFloatv( pname = ", pname, ", params*=", repr(hex(<long> params)), ", )")
    cgl.glGetFloatv ( pname, params)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGetFramebufferAttachmentParameteriv (GLenum target, GLenum attachment, GLenum pname, GLint* params) with gil:
    print("GL glGetFramebufferAttachmentParameteriv( target = ", target, ", attachment = ", attachment, ", pname = ", pname, ", params*=", repr(hex(<long> params)), ", )")
    cgl.glGetFramebufferAttachmentParameteriv ( target, attachment, pname, params)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGetIntegerv (GLenum pname, GLint* params) with gil:
    print("GL glGetIntegerv( pname = ", pname, ", params*=", repr(hex(<long> params)), ", )")
    cgl.glGetIntegerv ( pname, params)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGetProgramiv (GLuint program, GLenum pname, GLint* params) with gil:
    print("GL glGetProgramiv( program = ", program, ", pname = ", pname, ", params*=", repr(hex(<long> params)), ", )")
    cgl.glGetProgramiv ( program, pname, params)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGetProgramInfoLog (GLuint program, GLsizei bufsize, GLsizei* length, GLchar* infolog) with gil:
    print("GL glGetProgramInfoLog( program = ", program, ", bufsize = ", bufsize, ", length*=", repr(hex(<long> length)), ", infolog*=", repr(hex(<long> infolog)), ", )")
    cgl.glGetProgramInfoLog ( program, bufsize, length, infolog)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGetRenderbufferParameteriv (GLenum target, GLenum pname, GLint* params) with gil:
    print("GL glGetRenderbufferParameteriv( target = ", target, ", pname = ", pname, ", params*=", repr(hex(<long> params)), ", )")
    cgl.glGetRenderbufferParameteriv ( target, pname, params)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGetShaderiv (GLuint shader, GLenum pname, GLint* params) with gil:
    print("GL glGetShaderiv( shader = ", shader, ", pname = ", pname, ", params*=", repr(hex(<long> params)), ", )")
    cgl.glGetShaderiv ( shader, pname, params)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGetShaderInfoLog (GLuint shader, GLsizei bufsize, GLsizei* length, GLchar* infolog) with gil:
    print("GL glGetShaderInfoLog( shader = ", shader, ", bufsize = ", bufsize, ", length*=", repr(hex(<long> length)), ", infolog*=", repr(hex(<long> infolog)), ", )")
    cgl.glGetShaderInfoLog ( shader, bufsize, length, infolog)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
# Skipping generation of: "#cdef void   glGetShaderPrecisionFormat (cgl.GLenum shadertype, cgl.GLenum precisiontype, cgl.GLint* range, cgl.GLint* precision)"
cdef void   glGetShaderSource (GLuint shader, GLsizei bufsize, GLsizei* length, GLchar* source) with gil:
    print("GL glGetShaderSource( shader = ", shader, ", bufsize = ", bufsize, ", length*=", repr(hex(<long> length)), ", source*=", repr(hex(<long> source)), ", )")
    cgl.glGetShaderSource ( shader, bufsize, length, source)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef   GLubyte*  glGetString (GLenum name) with gil:
    print("GL glGetString( name = ", name, ", )")
    return <GLubyte*><char*>cgl.glGetString ( name)
cdef void   glGetTexParameterfv (GLenum target, GLenum pname, GLfloat* params) with gil:
    print("GL glGetTexParameterfv( target = ", target, ", pname = ", pname, ", params*=", repr(hex(<long> params)), ", )")
    cgl.glGetTexParameterfv ( target, pname, params)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGetTexParameteriv (GLenum target, GLenum pname, GLint* params) with gil:
    print("GL glGetTexParameteriv( target = ", target, ", pname = ", pname, ", params*=", repr(hex(<long> params)), ", )")
    cgl.glGetTexParameteriv ( target, pname, params)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGetUniformfv (GLuint program, GLint location, GLfloat* params) with gil:
    print("GL glGetUniformfv( program = ", program, ", location = ", location, ", params*=", repr(hex(<long> params)), ", )")
    cgl.glGetUniformfv ( program, location, params)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGetUniformiv (GLuint program, GLint location, GLint* params) with gil:
    print("GL glGetUniformiv( program = ", program, ", location = ", location, ", params*=", repr(hex(<long> params)), ", )")
    cgl.glGetUniformiv ( program, location, params)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef int    glGetUniformLocation (GLuint program,  GLchar* name) with gil:
    print("GL glGetUniformLocation( program = ", program, ", name*=", repr(hex(<long> name)), ", )")
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
    return cgl.glGetUniformLocation ( program, name)
cdef void   glGetVertexAttribfv (GLuint index, GLenum pname, GLfloat* params) with gil:
    print("GL glGetVertexAttribfv( index = ", index, ", pname = ", pname, ", params*=", repr(hex(<long> params)), ", )")
    cgl.glGetVertexAttribfv ( index, pname, params)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGetVertexAttribiv (GLuint index, GLenum pname, GLint* params) with gil:
    print("GL glGetVertexAttribiv( index = ", index, ", pname = ", pname, ", params*=", repr(hex(<long> params)), ", )")
    cgl.glGetVertexAttribiv ( index, pname, params)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glGetVertexAttribPointerv (GLuint index, GLenum pname, GLvoid** pointer) with gil:
    print("GL glGetVertexAttribPointerv( index = ", index, ", pname = ", pname, ", pointer**=", repr(hex(<long> pointer)), ", )")
    cgl.glGetVertexAttribPointerv ( index, pname, pointer)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void   glHint (GLenum target, GLenum mode) with gil:
    print("GL glHint( target = ", target, ", mode = ", mode, ", )")
    cgl.glHint ( target, mode)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef GLboolean  glIsBuffer (GLuint buffer) with gil:
    print("GL glIsBuffer( buffer = ", buffer, ", )")
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
    return cgl.glIsBuffer ( buffer)
cdef GLboolean  glIsEnabled (GLenum cap) with gil:
    print("GL glIsEnabled( cap = ", cap, ", )")
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
    return cgl.glIsEnabled ( cap)
cdef GLboolean  glIsFramebuffer (GLuint framebuffer) with gil:
    print("GL glIsFramebuffer( framebuffer = ", framebuffer, ", )")
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
    return cgl.glIsFramebuffer ( framebuffer)
cdef GLboolean  glIsProgram (GLuint program) with gil:
    print("GL glIsProgram( program = ", program, ", )")
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
    return cgl.glIsProgram ( program)
cdef GLboolean  glIsRenderbuffer (GLuint renderbuffer) with gil:
    print("GL glIsRenderbuffer( renderbuffer = ", renderbuffer, ", )")
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
    return cgl.glIsRenderbuffer ( renderbuffer)
cdef GLboolean  glIsShader (GLuint shader) with gil:
    print("GL glIsShader( shader = ", shader, ", )")
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
    return cgl.glIsShader ( shader)
cdef GLboolean  glIsTexture (GLuint texture) with gil:
    print("GL glIsTexture( texture = ", texture, ", )")
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
    return cgl.glIsTexture ( texture)
cdef void  glLineWidth (GLfloat width) with gil:
    print("GL glLineWidth( width = ", width, ", )")
    cgl.glLineWidth ( width)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glLinkProgram (GLuint program) with gil:
    print("GL glLinkProgram( program = ", program, ", )")
    cgl.glLinkProgram ( program)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glPixelStorei (GLenum pname, GLint param) with gil:
    print("GL glPixelStorei( pname = ", pname, ", param = ", param, ", )")
    cgl.glPixelStorei ( pname, param)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glPolygonOffset (GLfloat factor, GLfloat units) with gil:
    print("GL glPolygonOffset( factor = ", factor, ", units = ", units, ", )")
    cgl.glPolygonOffset ( factor, units)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glReadPixels (GLint x, GLint y, GLsizei width, GLsizei height, GLenum format, GLenum type, GLvoid* pixels) with gil:
    print("GL glReadPixels( x = ", x, ", y = ", y, ", width = ", width, ", height = ", height, ", format = ", format, ", type = ", type, ", pixels*=", repr(hex(<long> pixels)), ", )")
    cgl.glReadPixels ( x, y, width, height, format, type, pixels)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
# Skipping generation of: "#cdef void  glReleaseShaderCompiler ()"
cdef void  glRenderbufferStorage (GLenum target, GLenum internalformat, GLsizei width, GLsizei height) with gil:
    print("GL glRenderbufferStorage( target = ", target, ", internalformat = ", internalformat, ", width = ", width, ", height = ", height, ", )")
    cgl.glRenderbufferStorage ( target, internalformat, width, height)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glSampleCoverage (GLclampf value, GLboolean invert) with gil:
    print("GL glSampleCoverage( value = ", value, ", invert = ", invert, ", )")
    cgl.glSampleCoverage ( value, invert)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glScissor (GLint x, GLint y, GLsizei width, GLsizei height) with gil:
    print("GL glScissor( x = ", x, ", y = ", y, ", width = ", width, ", height = ", height, ", )")
    cgl.glScissor ( x, y, width, height)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
# Skipping generation of: "#cdef void  glShaderBinary (cgl.GLsizei n,  cgl.GLuint* shaders, cgl.GLenum binaryformat,  cgl.GLvoid* binary, cgl.GLsizei length)"
cdef void  glShaderSource (GLuint shader, GLsizei count,  GLchar** string,  GLint* length) with gil:
    print("GL glShaderSource( shader = ", shader, ", count = ", count, ", string**=", repr(hex(<long> string)), ", length*=", repr(hex(<long> length)), ", )")
    cgl.glShaderSource ( shader, count, <const_char_ptr*>string, length)
    ret = glGetError()
    if ret: print("ERR %d / %x" % (ret, ret))
cdef void  glStencilFunc (GLenum func, GLint ref, GLuint mask) with gil:
    print("GL glStencilFunc( func = ", func, ", ref = ", ref, ", mask = ", mask, ", )")
    cgl.glStencilFunc ( func, ref, mask)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glStencilFuncSeparate (GLenum face, GLenum func, GLint ref, GLuint mask) with gil:
    print("GL glStencilFuncSeparate( face = ", face, ", func = ", func, ", ref = ", ref, ", mask = ", mask, ", )")
    cgl.glStencilFuncSeparate ( face, func, ref, mask)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glStencilMask (GLuint mask) with gil:
    print("GL glStencilMask( mask = ", mask, ", )")
    cgl.glStencilMask ( mask)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glStencilMaskSeparate (GLenum face, GLuint mask) with gil:
    print("GL glStencilMaskSeparate( face = ", face, ", mask = ", mask, ", )")
    cgl.glStencilMaskSeparate ( face, mask)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glStencilOp (GLenum fail, GLenum zfail, GLenum zpass) with gil:
    print("GL glStencilOp( fail = ", fail, ", zfail = ", zfail, ", zpass = ", zpass, ", )")
    cgl.glStencilOp ( fail, zfail, zpass)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glStencilOpSeparate (GLenum face, GLenum fail, GLenum zfail, GLenum zpass) with gil:
    print("GL glStencilOpSeparate( face = ", face, ", fail = ", fail, ", zfail = ", zfail, ", zpass = ", zpass, ", )")
    cgl.glStencilOpSeparate ( face, fail, zfail, zpass)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glTexImage2D (GLenum target, GLint level, GLint internalformat, GLsizei width, GLsizei height, GLint border, GLenum format, GLenum type,  GLvoid* pixels) with gil:
    print("GL glTexImage2D( target = ", target, ", level = ", level, ", internalformat = ", internalformat, ", width = ", width, ", height = ", height, ", border = ", border, ", format = ", format, ", type = ", type, ", pixels*=", repr(hex(<long> pixels)), ", )")
    cgl.glTexImage2D ( target, level, internalformat, width, height, border, format, type, pixels)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glTexParameterf (GLenum target, GLenum pname, GLfloat param) with gil:
    print("GL glTexParameterf( target = ", target, ", pname = ", pname, ", param = ", param, ", )")
    cgl.glTexParameterf ( target, pname, param)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glTexParameterfv (GLenum target, GLenum pname,  GLfloat* params) with gil:
    print("GL glTexParameterfv( target = ", target, ", pname = ", pname, ", params*=", repr(hex(<long> params)), ", )")
    cgl.glTexParameterfv ( target, pname, params)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glTexParameteri (GLenum target, GLenum pname, GLint param) with gil:
    print("GL glTexParameteri( target = ", target, ", pname = ", pname, ", param = ", param, ", )")
    cgl.glTexParameteri ( target, pname, param)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glTexParameteriv (GLenum target, GLenum pname,  GLint* params) with gil:
    print("GL glTexParameteriv( target = ", target, ", pname = ", pname, ", params*=", repr(hex(<long> params)), ", )")
    cgl.glTexParameteriv ( target, pname, params)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLenum type,  GLvoid* pixels) with gil:
    print("GL glTexSubImage2D( target = ", target, ", level = ", level, ", xoffset = ", xoffset, ", yoffset = ", yoffset, ", width = ", width, ", height = ", height, ", format = ", format, ", type = ", type, ", pixels*=", repr(hex(<long> pixels)), ", )")
    cgl.glTexSubImage2D ( target, level, xoffset, yoffset, width, height, format, type, pixels)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniform1f (GLint location, GLfloat x) with gil:
    print("GL glUniform1f( location = ", location, ", x = ", x, ", )")
    cgl.glUniform1f ( location, x)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniform1fv (GLint location, GLsizei count,  GLfloat* v) with gil:
    print("GL glUniform1fv( location = ", location, ", count = ", count, ", v*=", repr(hex(<long> v)), ", )")
    cgl.glUniform1fv ( location, count, v)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniform1i (GLint location, GLint x) with gil:
    print("GL glUniform1i( location = ", location, ", x = ", x, ", )")
    cgl.glUniform1i ( location, x)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniform1iv (GLint location, GLsizei count,  GLint* v) with gil:
    print("GL glUniform1iv( location = ", location, ", count = ", count, ", v*=", repr(hex(<long> v)), ", )")
    cgl.glUniform1iv ( location, count, v)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniform2f (GLint location, GLfloat x, GLfloat y) with gil:
    print("GL glUniform2f( location = ", location, ", x = ", x, ", y = ", y, ", )")
    cgl.glUniform2f ( location, x, y)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniform2fv (GLint location, GLsizei count,  GLfloat* v) with gil:
    print("GL glUniform2fv( location = ", location, ", count = ", count, ", v*=", repr(hex(<long> v)), ", )")
    cgl.glUniform2fv ( location, count, v)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniform2i (GLint location, GLint x, GLint y) with gil:
    print("GL glUniform2i( location = ", location, ", x = ", x, ", y = ", y, ", )")
    cgl.glUniform2i ( location, x, y)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniform2iv (GLint location, GLsizei count,  GLint* v) with gil:
    print("GL glUniform2iv( location = ", location, ", count = ", count, ", v*=", repr(hex(<long> v)), ", )")
    cgl.glUniform2iv ( location, count, v)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniform3f (GLint location, GLfloat x, GLfloat y, GLfloat z) with gil:
    print("GL glUniform3f( location = ", location, ", x = ", x, ", y = ", y, ", z = ", z, ", )")
    cgl.glUniform3f ( location, x, y, z)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniform3fv (GLint location, GLsizei count,  GLfloat* v) with gil:
    print("GL glUniform3fv( location = ", location, ", count = ", count, ", v*=", repr(hex(<long> v)), ", )")
    cgl.glUniform3fv ( location, count, v)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniform3i (GLint location, GLint x, GLint y, GLint z) with gil:
    print("GL glUniform3i( location = ", location, ", x = ", x, ", y = ", y, ", z = ", z, ", )")
    cgl.glUniform3i ( location, x, y, z)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniform3iv (GLint location, GLsizei count,  GLint* v) with gil:
    print("GL glUniform3iv( location = ", location, ", count = ", count, ", v*=", repr(hex(<long> v)), ", )")
    cgl.glUniform3iv ( location, count, v)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniform4f (GLint location, GLfloat x, GLfloat y, GLfloat z, GLfloat w) with gil:
    print("GL glUniform4f( location = ", location, ", x = ", x, ", y = ", y, ", z = ", z, ", w = ", w, ", )")
    cgl.glUniform4f ( location, x, y, z, w)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniform4fv (GLint location, GLsizei count,  GLfloat* v) with gil:
    print("GL glUniform4fv( location = ", location, ", count = ", count, ", v*=", repr(hex(<long> v)), ", )")
    cgl.glUniform4fv ( location, count, v)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniform4i (GLint location, GLint x, GLint y, GLint z, GLint w) with gil:
    print("GL glUniform4i( location = ", location, ", x = ", x, ", y = ", y, ", z = ", z, ", w = ", w, ", )")
    cgl.glUniform4i ( location, x, y, z, w)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniform4iv (GLint location, GLsizei count,  GLint* v) with gil:
    print("GL glUniform4iv( location = ", location, ", count = ", count, ", v*=", repr(hex(<long> v)), ", )")
    cgl.glUniform4iv ( location, count, v)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniformMatrix2fv (GLint location, GLsizei count, GLboolean transpose,  GLfloat* value) with gil:
    print("GL glUniformMatrix2fv( location = ", location, ", count = ", count, ", transpose = ", transpose, ", value*=", repr(hex(<long> value)), ", )")
    cgl.glUniformMatrix2fv ( location, count, transpose, value)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniformMatrix3fv (GLint location, GLsizei count, GLboolean transpose,  GLfloat* value) with gil:
    print("GL glUniformMatrix3fv( location = ", location, ", count = ", count, ", transpose = ", transpose, ", value*=", repr(hex(<long> value)), ", )")
    cgl.glUniformMatrix3fv ( location, count, transpose, value)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUniformMatrix4fv (GLint location, GLsizei count, GLboolean transpose,  GLfloat* value) with gil:
    print("GL glUniformMatrix4fv( location = ", location, ", count = ", count, ", transpose = ", transpose, ", value*=", repr(hex(<long> value)), ", )")
    cgl.glUniformMatrix4fv ( location, count, transpose, value)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glUseProgram (GLuint program) with gil:
    print("GL glUseProgram( program = ", program, ", )")
    cgl.glUseProgram ( program)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glValidateProgram (GLuint program) with gil:
    print("GL glValidateProgram( program = ", program, ", )")
    cgl.glValidateProgram ( program)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glVertexAttrib1f (GLuint indx, GLfloat x) with gil:
    print("GL glVertexAttrib1f( indx = ", indx, ", x = ", x, ", )")
    cgl.glVertexAttrib1f ( indx, x)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glVertexAttrib1fv (GLuint indx,  GLfloat* values) with gil:
    print("GL glVertexAttrib1fv( indx = ", indx, ", values*=", repr(hex(<long> values)), ", )")
    cgl.glVertexAttrib1fv ( indx, values)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glVertexAttrib2f (GLuint indx, GLfloat x, GLfloat y) with gil:
    print("GL glVertexAttrib2f( indx = ", indx, ", x = ", x, ", y = ", y, ", )")
    cgl.glVertexAttrib2f ( indx, x, y)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glVertexAttrib2fv (GLuint indx,  GLfloat* values) with gil:
    print("GL glVertexAttrib2fv( indx = ", indx, ", values*=", repr(hex(<long> values)), ", )")
    cgl.glVertexAttrib2fv ( indx, values)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glVertexAttrib3f (GLuint indx, GLfloat x, GLfloat y, GLfloat z) with gil:
    print("GL glVertexAttrib3f( indx = ", indx, ", x = ", x, ", y = ", y, ", z = ", z, ", )")
    cgl.glVertexAttrib3f ( indx, x, y, z)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glVertexAttrib3fv (GLuint indx,  GLfloat* values) with gil:
    print("GL glVertexAttrib3fv( indx = ", indx, ", values*=", repr(hex(<long> values)), ", )")
    cgl.glVertexAttrib3fv ( indx, values)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glVertexAttrib4f (GLuint indx, GLfloat x, GLfloat y, GLfloat z, GLfloat w) with gil:
    print("GL glVertexAttrib4f( indx = ", indx, ", x = ", x, ", y = ", y, ", z = ", z, ", w = ", w, ", )")
    cgl.glVertexAttrib4f ( indx, x, y, z, w)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glVertexAttrib4fv (GLuint indx,  GLfloat* values) with gil:
    print("GL glVertexAttrib4fv( indx = ", indx, ", values*=", repr(hex(<long> values)), ", )")
    cgl.glVertexAttrib4fv ( indx, values)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glVertexAttribPointer (GLuint indx, GLint size, GLenum type, GLboolean normalized, GLsizei stride,  GLvoid* ptr) with gil:
    print("GL glVertexAttribPointer( indx = ", indx, ", size = ", size, ", type = ", type, ", normalized = ", normalized, ", stride = ", stride, ", ptr*=", repr(hex(<long> ptr)), ", )")
    cgl.glVertexAttribPointer ( indx, size, type, normalized, stride, ptr)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
cdef void  glViewport (GLint x, GLint y, GLsizei width, GLsizei height) with gil:
    print("GL glViewport( x = ", x, ", y = ", y, ", width = ", width, ", height = ", height, ", )")
    cgl.glViewport ( x, y, width, height)
    ret = cgl.glGetError()
    if ret: print("OpenGL Error %d / %x" % (ret, ret))
