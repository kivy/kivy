include "../../include/config.pxi"
include "../common.pxi"

from kivy.graphics.cgl cimport *

cdef GLES2_Context g_cgl_debug
cdef GLES2_Context *cgl_debug = &g_cgl_debug
cdef GLES2_Context *cgl_native


cpdef is_backend_supported():
    return True

def gl_debug_print(*args):
    print("".join([str(x) for x in args]))

def gl_check_error():
  ret = cgl_native.glGetError()
  if ret:
      print("OpenGL Error %d / %x" % (ret, ret))

cdef void __stdcall dbgActiveTexture (GLenum texture) nogil:
    with gil:
        gil_dbgActiveTexture(texture)

cdef void __stdcall gil_dbgActiveTexture (GLenum texture) with gil:
    gl_debug_print("GL glActiveTexture( texture = ", texture, ", )")
    cgl_native.glActiveTexture ( texture)
    gl_check_error()

cdef void __stdcall dbgAttachShader (GLuint program, GLuint shader) nogil:
    with gil:
        gil_dbgAttachShader(program, shader)

cdef void __stdcall gil_dbgAttachShader (GLuint program, GLuint shader) with gil:
    gl_debug_print("GL glAttachShader( program = ", program, ", shader = ", shader, ",)")
    cgl_native.glAttachShader ( program, shader)
    gl_check_error()

cdef void __stdcall dbgBindAttribLocation (GLuint program, GLuint index, const GLchar* name) nogil:
    with gil:
        gil_dbgBindAttribLocation(program, index, name)

cdef void __stdcall gil_dbgBindAttribLocation (GLuint program, GLuint index, const GLchar* name) with gil:
    gl_debug_print("GL glBindAttribLocation( program = ", program, ", index = ", index, ", name*=", <bytes>name, ", )")
    cgl_native.glBindAttribLocation ( program, index, name)
    gl_check_error()

cdef void __stdcall dbgBindBuffer (GLenum target, GLuint buffer) nogil:
    with gil:
        gil_dbgBindBuffer(target, buffer)

cdef void __stdcall gil_dbgBindBuffer (GLenum target, GLuint buffer) with gil:
    gl_debug_print("GL glBindBuffer( target = ", target, ", buffer = ", buffer, ", )")
    cgl_native.glBindBuffer ( target, buffer)
    gl_check_error()

cdef void __stdcall dbgBindFramebuffer (GLenum target, GLuint framebuffer) nogil:
    with gil:
        gil_dbgBindFramebuffer(target, framebuffer)

cdef void __stdcall gil_dbgBindFramebuffer (GLenum target, GLuint framebuffer) with gil:
    gl_debug_print("GL glBindFramebuffer( target = ", target, ", framebuffer = ", framebuffer, ", )")
    cgl_native.glBindFramebuffer ( target, framebuffer)
    gl_check_error()

cdef void __stdcall dbgBindRenderbuffer (GLenum target, GLuint renderbuffer) nogil:
    with gil:
        gil_dbgBindRenderbuffer(target, renderbuffer)

cdef void __stdcall gil_dbgBindRenderbuffer (GLenum target, GLuint renderbuffer) with gil:
    gl_debug_print("GL glBindRenderbuffer( target = ", target, ", renderbuffer = ", renderbuffer, ", )")
    cgl_native.glBindRenderbuffer ( target, renderbuffer)
    gl_check_error()

cdef void __stdcall dbgBindTexture (GLenum target, GLuint texture) nogil:
    with gil:
        gil_dbgBindTexture(target, texture)

cdef void __stdcall gil_dbgBindTexture (GLenum target, GLuint texture) with gil:
    gl_debug_print("GL glBindTexture( target = ", target, ", texture = ", texture, ", )")
    cgl_native.glBindTexture ( target, texture)
    gl_check_error()

cdef void __stdcall dbgBlendColor (GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha) nogil:
    with gil:
        gil_dbgBlendColor(red, green, blue, alpha)

cdef void __stdcall gil_dbgBlendColor (GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha) with gil:
    gl_debug_print("GL glBlendColor( red = ", red, ", green = ", green, ", blue = ", blue, ", alpha = ", alpha, ", )")
    cgl_native.glBlendColor ( red, green, blue, alpha)
    gl_check_error()

cdef void __stdcall dbgBlendEquation (GLenum mode) nogil:
    with gil:
        gil_dbgBlendEquation(mode)

cdef void __stdcall gil_dbgBlendEquation (GLenum mode) with gil:
    gl_debug_print("GL glBlendEquation( mode = ", mode, ", )")
    cgl_native.glBlendEquation ( mode)
    gl_check_error()

cdef void __stdcall dbgBlendEquationSeparate (GLenum modeRGB, GLenum modeAlpha) nogil:
    with gil:
        gil_dbgBlendEquationSeparate(modeRGB, modeAlpha)

cdef void __stdcall gil_dbgBlendEquationSeparate (GLenum modeRGB, GLenum modeAlpha) with gil:
    gl_debug_print("GL glBlendEquationSeparate( modeRGB = ", modeRGB, ", modeAlpha = ", modeAlpha, ", )")
    cgl_native.glBlendEquationSeparate ( modeRGB, modeAlpha)
    gl_check_error()

cdef void __stdcall dbgBlendFunc (GLenum sfactor, GLenum dfactor) nogil:
    with gil:
        gil_dbgBlendFunc(sfactor, dfactor)

cdef void __stdcall gil_dbgBlendFunc (GLenum sfactor, GLenum dfactor) with gil:
    gl_debug_print("GL glBlendFunc( sfactor = ", sfactor, ", dfactor = ", dfactor, ", )")
    cgl_native.glBlendFunc ( sfactor, dfactor)
    gl_check_error()

cdef void __stdcall dbgBlendFuncSeparate (GLenum srcRGB, GLenum dstRGB, GLenum srcAlpha, GLenum dstAlpha) nogil:
    with gil:
        gil_dbgBlendFuncSeparate(srcRGB, dstRGB, srcAlpha, dstAlpha)

cdef void __stdcall gil_dbgBlendFuncSeparate (GLenum srcRGB, GLenum dstRGB, GLenum srcAlpha, GLenum dstAlpha) with gil:
    gl_debug_print("GL glBlendFuncSeparate( srcRGB = ", srcRGB, ", dstRGB = ", dstRGB, ", srcAlpha = ", srcAlpha, ", dstAlpha = ", dstAlpha, ", )")
    cgl_native.glBlendFuncSeparate ( srcRGB, dstRGB, srcAlpha, dstAlpha)
    gl_check_error()

cdef void __stdcall dbgBufferData (GLenum target, GLsizeiptr size, const GLvoid* data, GLenum usage) nogil:
    with gil:
        gil_dbgBufferData(target, size, data, usage)

cdef void __stdcall gil_dbgBufferData (GLenum target, GLsizeiptr size, const GLvoid* data, GLenum usage) with gil:
    gl_debug_print("GL glBufferData( target = ", target, ", size = ", size, ", data*=", repr(hex(<long long> data)), ", usage = ", usage, ", )")
    cgl_native.glBufferData ( target, size, data, usage)
    gl_check_error()

cdef void __stdcall dbgBufferSubData (GLenum target, GLintptr offset, GLsizeiptr size, const GLvoid* data) nogil:
    with gil:
        gil_dbgBufferSubData(target, offset, size, <GLvoid *>data)

cdef void __stdcall gil_dbgBufferSubData (GLenum target, GLintptr offset, GLsizeiptr size,  GLvoid* data) with gil:
    gl_debug_print("GL glBufferSubData( target = ", target, ", offset = ", offset, ", size = ", size, ", data*=", repr(hex(<long long> data)), ", )")
    cgl_native.glBufferSubData ( target, offset, size, data)
    gl_check_error()

cdef GLenum __stdcall dbgCheckFramebufferStatus (GLenum target) nogil:
    with gil:
        return gil_dbgCheckFramebufferStatus(target)

cdef GLenum __stdcall gil_dbgCheckFramebufferStatus (GLenum target) with gil:
    gl_debug_print("GL glCheckFramebufferStatus( target = ", target, ", )")
    ret = cgl_native.glCheckFramebufferStatus ( target)
    gl_check_error()
    return ret

cdef void __stdcall dbgClear (GLbitfield mask) nogil:
    with gil:
        gil_dbgClear(mask)

cdef void __stdcall gil_dbgClear (GLbitfield mask) with gil:
    gl_debug_print("GL glClear( mask = ", mask, ", )")
    cgl_native.glClear ( mask)
    gl_check_error()

cdef void __stdcall dbgClearColor (GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha) nogil:
    with gil:
        gil_dbgClearColor(red, green, blue, alpha)

cdef void __stdcall gil_dbgClearColor (GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha) with gil:
    gl_debug_print("GL glClearColor( red = ", red, ", green = ", green, ", blue = ", blue, ", alpha = ", alpha, ", )")
    cgl_native.glClearColor ( red, green, blue, alpha)
    gl_check_error()

#crash on android platform
#cdef void __stdcall dbgClearDepthf (GLclampf depth) nogil:
# with gil:
#     gil_dbgClearDepthf(depth)
#
#cdef void __stdgil_call dbgClearDepthf (GLclampf depth) with gil:
#    gl_debug_print("GL glClearDepthf( depth = ", depth, ", )")
#    cgl_native.glClearDepthf ( depth)
#    ret = cgl_native.glGetError()
#    if ret: print("OpenGL Error %d / %x" % (ret, ret))

cdef void __stdcall dbgClearStencil (GLint s) nogil:
    with gil:
        gil_dbgClearStencil(s)

cdef void __stdcall gil_dbgClearStencil (GLint s) with gil:
    gl_debug_print("GL glClearStencil( s = ", s, ", )")
    cgl_native.glClearStencil ( s)
    gl_check_error()

cdef void __stdcall dbgColorMask (GLboolean red, GLboolean green, GLboolean blue, GLboolean alpha) nogil:
    with gil:
        gil_dbgColorMask(red, green, blue, alpha)

cdef void __stdcall gil_dbgColorMask (GLboolean red, GLboolean green, GLboolean blue, GLboolean alpha) with gil:
    gl_debug_print("GL glColorMask( red = ", red, ", green = ", green, ", blue = ", blue, ", alpha = ", alpha, ", )")
    cgl_native.glColorMask ( red, green, blue, alpha)
    gl_check_error()

cdef void __stdcall dbgCompileShader (GLuint shader) nogil:
    with gil:
        gil_dbgCompileShader(shader)

cdef void __stdcall gil_dbgCompileShader (GLuint shader) with gil:
    gl_debug_print("GL glCompileShader( shader = ", shader, ", )")
    cgl_native.glCompileShader ( shader)
    gl_check_error()

cdef void __stdcall dbgCompressedTexImage2D (GLenum target, GLint level, GLenum internalformat, GLsizei width, GLsizei height, GLint border, GLsizei imageSize, const GLvoid* data) nogil:
    with gil:
        gil_dbgCompressedTexImage2D(target, level, internalformat, width, height, border, imageSize, data)

cdef void __stdcall gil_dbgCompressedTexImage2D (GLenum target, GLint level, GLenum internalformat, GLsizei width, GLsizei height, GLint border, GLsizei imageSize, const GLvoid* data) with gil:
    gl_debug_print("GL glCompressedTexImage2D( target = ", target, ", level = ", level, ", internalformat = ", internalformat, ", width = ", width, ", height = ", height, ", border = ", border, ", imageSize = ", imageSize, ", data*=", repr(hex(<long long> data)), ", )")
    cgl_native.glCompressedTexImage2D ( target, level, internalformat, width, height, border, imageSize, data)
    gl_check_error()

cdef void __stdcall dbgCompressedTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLsizei imageSize, const GLvoid* data) nogil:
    with gil:
        gil_dbgCompressedTexSubImage2D(target, level, xoffset, yoffset, width, height, format, imageSize, <GLvoid*>data)

cdef void __stdcall gil_dbgCompressedTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLsizei imageSize,  GLvoid* data) with gil:
    gl_debug_print("GL glCompressedTexSubImage2D( target = ", target, ", level = ", level, ", xoffset = ", xoffset, ", yoffset = ", yoffset, ", width = ", width, ", height = ", height, ", format = ", format, ", imageSize = ", imageSize, ", data*=", repr(hex(<long long> data)), ", )")
    cgl_native.glCompressedTexSubImage2D ( target, level, xoffset, yoffset, width, height, format, imageSize, data)
    gl_check_error()

cdef void __stdcall dbgCopyTexImage2D (GLenum target, GLint level, GLenum internalformat, GLint x, GLint y, GLsizei width, GLsizei height, GLint border) nogil:
    with gil:
        gil_dbgCopyTexImage2D(target, level, internalformat, x, y, width, height, border)

cdef void __stdcall gil_dbgCopyTexImage2D (GLenum target, GLint level, GLenum internalformat, GLint x, GLint y, GLsizei width, GLsizei height, GLint border) with gil:
    gl_debug_print("GL glCopyTexImage2D( target = ", target, ", level = ", level, ", internalformat = ", internalformat, ", x = ", x, ", y = ", y, ", width = ", width, ", height = ", height, ", border = ", border, ", )")
    cgl_native.glCopyTexImage2D ( target, level, internalformat, x, y, width, height, border)
    gl_check_error()

cdef void __stdcall dbgCopyTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLint x, GLint y, GLsizei width, GLsizei height) nogil:
    with gil:
        gil_dbgCopyTexSubImage2D(target, level, xoffset, yoffset, x, y, width, height)

cdef void __stdcall gil_dbgCopyTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLint x, GLint y, GLsizei width, GLsizei height) with gil:
    gl_debug_print("GL glCopyTexSubImage2D( target = ", target, ", level = ", level, ", xoffset = ", xoffset, ", yoffset = ", yoffset, ", x = ", x, ", y = ", y, ", width = ", width, ", height = ", height, ", )")
    cgl_native.glCopyTexSubImage2D ( target, level, xoffset, yoffset, x, y, width, height)
    gl_check_error()

cdef GLuint __stdcall dbgCreateProgram () nogil:
    with gil:
        return gil_dbgCreateProgram()

cdef GLuint __stdcall gil_dbgCreateProgram () with gil:
    gl_debug_print("GL glCreateProgram( )")
    ret = cgl_native.glCreateProgram ()
    gl_check_error()
    return ret

cdef GLuint __stdcall dbgCreateShader (GLenum type) nogil:
    with gil:
        return gil_dbgCreateShader(type)

cdef GLuint __stdcall gil_dbgCreateShader (GLenum type) with gil:
    gl_debug_print("GL glCreateShader( type = ", type, ", )")
    ret = cgl_native.glCreateShader ( type)
    gl_check_error()
    return ret

cdef void __stdcall dbgCullFace (GLenum mode) nogil:
    with gil:
        gil_dbgCullFace(mode)

cdef void __stdcall gil_dbgCullFace (GLenum mode) with gil:
    gl_debug_print("GL glCullFace( mode = ", mode, ", )")
    cgl_native.glCullFace ( mode)
    gl_check_error()

cdef void __stdcall dbgDeleteBuffers (GLsizei n, const GLuint* buffers) nogil:
    with gil:
        gil_dbgDeleteBuffers(n, buffers)

cdef void __stdcall gil_dbgDeleteBuffers (GLsizei n, const GLuint* buffers) with gil:
    gl_debug_print("GL glDeleteBuffers( n = ", n, ", buffers*=", repr(hex(<long long> buffers)), ", )")
    cgl_native.glDeleteBuffers ( n, buffers)
    gl_check_error()

cdef void __stdcall dbgDeleteFramebuffers (GLsizei n, const GLuint* framebuffers) nogil:
    with gil:
        gil_dbgDeleteFramebuffers(n, framebuffers)

cdef void __stdcall gil_dbgDeleteFramebuffers (GLsizei n, const GLuint* framebuffers) with gil:
    gl_debug_print("GL glDeleteFramebuffers( n = ", n, ", framebuffers*=", repr(hex(<long long> framebuffers)), ", )")
    cgl_native.glDeleteFramebuffers ( n, framebuffers)
    gl_check_error()

cdef void __stdcall dbgDeleteProgram (GLuint program) nogil:
    with gil:
        gil_dbgDeleteProgram(program)

cdef void __stdcall gil_dbgDeleteProgram (GLuint program) with gil:
    gl_debug_print("GL glDeleteProgram( program = ", program, ", )")
    cgl_native.glDeleteProgram ( program)
    gl_check_error()

cdef void __stdcall dbgDeleteRenderbuffers (GLsizei n, const GLuint* renderbuffers) nogil:
    with gil:
        gil_dbgDeleteRenderbuffers(n, renderbuffers)

cdef void __stdcall gil_dbgDeleteRenderbuffers (GLsizei n, const GLuint* renderbuffers) with gil:
    gl_debug_print("GL glDeleteRenderbuffers( n = ", n, ", renderbuffers*=", repr(hex(<long long> renderbuffers)), ", )")
    cgl_native.glDeleteRenderbuffers ( n, renderbuffers)
    gl_check_error()

cdef void __stdcall dbgDeleteShader (GLuint shader) nogil:
    with gil:
        gil_dbgDeleteShader(shader)

cdef void __stdcall gil_dbgDeleteShader (GLuint shader) with gil:
    gl_debug_print("GL glDeleteShader( shader = ", shader, ", )")
    cgl_native.glDeleteShader ( shader)
    gl_check_error()

cdef void __stdcall dbgDeleteTextures (GLsizei n, const GLuint* textures) nogil:
    with gil:
        gil_dbgDeleteTextures(n, textures)

cdef void __stdcall gil_dbgDeleteTextures (GLsizei n, const GLuint* textures) with gil:
    gl_debug_print("GL glDeleteTextures( n = ", n, ", textures*=", repr(hex(<long long> textures)), ", )")
    cgl_native.glDeleteTextures ( n, textures)
    gl_check_error()

cdef void __stdcall dbgDepthFunc (GLenum func) nogil:
    with gil:
        gil_dbgDepthFunc(func)

cdef void __stdcall gil_dbgDepthFunc (GLenum func) with gil:
    gl_debug_print("GL glDepthFunc( func = ", func, ", )")
    cgl_native.glDepthFunc ( func)
    gl_check_error()

cdef void __stdcall dbgDepthMask (GLboolean flag) nogil:
    with gil:
        gil_dbgDepthMask(flag)

cdef void __stdcall gil_dbgDepthMask (GLboolean flag) with gil:
    gl_debug_print("GL glDepthMask( flag = ", flag, ", )")
    cgl_native.glDepthMask ( flag)
    gl_check_error()

#crash on android platform
#cdef void __stdcall dbgDepthRangef (GLclampf zNear, GLclampf zFar) nogil:
# with gil:
#     gil_dbgDepthRangef(GLclampf zNear, GLclampf zFar)
#cdef void __stdgil_call dbgDepthRangef (GLclampf zNear, GLclampf zFar) with gil:
#    gl_debug_print("GL glDepthRangef( zNear = ", zNear, ", zFar = ", zFar, ", )")
#    cgl_native.glDepthRangef ( zNear, zFar)
#    ret = glGetError()
#    if ret: print("ERR %d / %x" % (ret, ret))

cdef void __stdcall dbgDetachShader (GLuint program, GLuint shader) nogil:
    with gil:
        gil_dbgDetachShader(program, shader)

cdef void __stdcall gil_dbgDetachShader (GLuint program, GLuint shader) with gil:
    gl_debug_print("GL glDetachShader( program = ", program, ", shader = ", shader, ", )")
    cgl_native.glDetachShader ( program, shader)
    gl_check_error()

cdef void __stdcall dbgDisable (GLenum cap) nogil:
    with gil:
        gil_dbgDisable(cap)

cdef void __stdcall gil_dbgDisable (GLenum cap) with gil:
    gl_debug_print("GL glDisable( cap = ", cap, ", )")
    cgl_native.glDisable ( cap)
    gl_check_error()

cdef void __stdcall dbgDisableVertexAttribArray (GLuint index) nogil:
    with gil:
        gil_dbgDisableVertexAttribArray(index)

cdef void __stdcall gil_dbgDisableVertexAttribArray (GLuint index) with gil:
    gl_debug_print("GL glDisableVertexAttribArray( index = ", index, ", )")
    cgl_native.glDisableVertexAttribArray ( index)
    gl_check_error()

cdef void __stdcall dbgDrawArrays (GLenum mode, GLint first, GLsizei count) nogil:
    with gil:
        gil_dbgDrawArrays(mode, first, count)

cdef void __stdcall gil_dbgDrawArrays (GLenum mode, GLint first, GLsizei count) with gil:
    gl_debug_print("GL glDrawArrays( mode = ", mode, ", first = ", first, ", count = ", count, ", )")
    cgl_native.glDrawArrays ( mode, first, count)
    gl_check_error()

cdef void __stdcall dbgDrawElements (GLenum mode, GLsizei count, GLenum type, const GLvoid* indices) nogil:
    with gil:
        gil_dbgDrawElements(mode, count, type, <GLvoid*>indices)

cdef void __stdcall gil_dbgDrawElements (GLenum mode, GLsizei count, GLenum type,  GLvoid* indices) with gil:
    gl_debug_print("GL glDrawElements( mode = ", mode, ", count = ", count, ", type = ", type, ", indices*=", repr(hex(<long long> indices)), ", )")
    cgl_native.glDrawElements ( mode, count, type, indices)
    gl_check_error()

cdef void __stdcall dbgEnable (GLenum cap) nogil:
    with gil:
        gil_dbgEnable(cap)

cdef void __stdcall gil_dbgEnable (GLenum cap) with gil:
    gl_debug_print("GL glEnable( cap = ", cap, ", )")
    cgl_native.glEnable ( cap)
    gl_check_error()

cdef void __stdcall dbgEnableVertexAttribArray (GLuint index) nogil:
    with gil:
        gil_dbgEnableVertexAttribArray(index)

cdef void __stdcall gil_dbgEnableVertexAttribArray (GLuint index) with gil:
    gl_debug_print("GL glEnableVertexAttribArray( index = ", index, ", )")
    cgl_native.glEnableVertexAttribArray ( index)
    gl_check_error()

cdef void __stdcall dbgFinish () nogil:
    with gil:
        gil_dbgFinish()

cdef void __stdcall gil_dbgFinish () with gil:
    gl_debug_print("GL glFinish( )")
    cgl_native.glFinish ()
    gl_check_error()

cdef void __stdcall dbgFlush () nogil:
    with gil:
        gil_dbgFlush()

cdef void __stdcall gil_dbgFlush () with gil:
    gl_debug_print("GL glFlush( )")
    cgl_native.glFlush ()
    gl_check_error()

cdef void __stdcall dbgFramebufferRenderbuffer (GLenum target, GLenum attachment, GLenum renderbuffertarget, GLuint renderbuffer) nogil:
    with gil:
        gil_dbgFramebufferRenderbuffer(target, attachment, renderbuffertarget, renderbuffer)

cdef void __stdcall gil_dbgFramebufferRenderbuffer (GLenum target, GLenum attachment, GLenum renderbuffertarget, GLuint renderbuffer) with gil:
    gl_debug_print("GL glFramebufferRenderbuffer( target = ", target, ", attachment = ", attachment, ", renderbuffertarget = ", renderbuffertarget, ", renderbuffer = ", renderbuffer, ", )")
    cgl_native.glFramebufferRenderbuffer ( target, attachment, renderbuffertarget, renderbuffer)
    gl_check_error()

cdef void __stdcall dbgFramebufferTexture2D (GLenum target, GLenum attachment, GLenum textarget, GLuint texture, GLint level) nogil:
    with gil:
        gil_dbgFramebufferTexture2D(target, attachment, textarget, texture, level)

cdef void __stdcall gil_dbgFramebufferTexture2D (GLenum target, GLenum attachment, GLenum textarget, GLuint texture, GLint level) with gil:
    gl_debug_print("GL glFramebufferTexture2D( target = ", target, ", attachment = ", attachment, ", textarget = ", textarget, ", texture = ", texture, ", level = ", level, ", )")
    cgl_native.glFramebufferTexture2D ( target, attachment, textarget, texture, level)
    gl_check_error()

cdef void __stdcall dbgFrontFace (GLenum mode) nogil:
    with gil:
        gil_dbgFrontFace(mode)

cdef void __stdcall gil_dbgFrontFace (GLenum mode) with gil:
    gl_debug_print("GL glFrontFace( mode = ", mode, ", )")
    cgl_native.glFrontFace ( mode)
    gl_check_error()

cdef void __stdcall dbgGenBuffers (GLsizei n, GLuint* buffers) nogil:
    with gil:
        gil_dbgGenBuffers(n, buffers)

cdef void __stdcall gil_dbgGenBuffers (GLsizei n, GLuint* buffers) with gil:
    gl_debug_print("GL glGenBuffers( n = ", n, ", buffers*=", repr(hex(<long long> buffers)), ", )")
    cgl_native.glGenBuffers ( n, buffers)
    gl_check_error()

cdef void __stdcall dbgGenerateMipmap (GLenum target) nogil:
    with gil:
        gil_dbgGenerateMipmap(target)

cdef void __stdcall gil_dbgGenerateMipmap (GLenum target) with gil:
    gl_debug_print("GL glGenerateMipmap( target = ", target, ", )")
    cgl_native.glGenerateMipmap ( target)
    gl_check_error()

cdef void __stdcall dbgGenFramebuffers (GLsizei n, GLuint* framebuffers) nogil:
    with gil:
        gil_dbgGenFramebuffers(n,  framebuffers)

cdef void __stdcall gil_dbgGenFramebuffers (GLsizei n, GLuint* framebuffers) with gil:
    gl_debug_print("GL glGenFramebuffers( n = ", n, ", framebuffers*=", repr(hex(<long long> framebuffers)), ", )")
    cgl_native.glGenFramebuffers ( n, framebuffers)
    gl_check_error()

cdef void __stdcall dbgGenRenderbuffers (GLsizei n, GLuint* renderbuffers) nogil:
    with gil:
        gil_dbgGenRenderbuffers(n, renderbuffers)

cdef void __stdcall gil_dbgGenRenderbuffers (GLsizei n, GLuint* renderbuffers) with gil:
    gl_debug_print("GL glGenRenderbuffers( n = ", n, ", renderbuffers*=", repr(hex(<long long> renderbuffers)), ", )")
    cgl_native.glGenRenderbuffers ( n, renderbuffers)
    gl_check_error()

cdef void __stdcall dbgGenTextures (GLsizei n, GLuint* textures) nogil:
    with gil:
        gil_dbgGenTextures(n, textures)

cdef void __stdcall gil_dbgGenTextures (GLsizei n, GLuint* textures) with gil:
    gl_debug_print("GL glGenTextures( n = ", n, ", textures*=", repr(hex(<long long> textures)), ", )")
    cgl_native.glGenTextures ( n, textures)
    gl_check_error()

cdef void __stdcall dbgGetActiveAttrib (GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name) nogil:
    with gil:
        gil_dbgGetActiveAttrib(program, index, bufsize,  length,  size,  type,  name)

cdef void __stdcall gil_dbgGetActiveAttrib (GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name) with gil:
    gl_debug_print("GL glGetActiveAttrib( program = ", program, ", index = ", index, ", bufsize = ", bufsize, ", length*=", repr(hex(<long long> length)), ", size*=", repr(hex(<long long> size)), ", type*=", repr(hex(<long long> type)), ", name*=", repr(hex(<long long> name)), ", )")
    cgl_native.glGetActiveAttrib ( program, index, bufsize, length, size, type, name)
    gl_check_error()

cdef void __stdcall dbgGetActiveUniform (GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name) nogil:
    with gil:
        gil_dbgGetActiveUniform(program, index, bufsize,  length,  size,  type,  name)

cdef void __stdcall gil_dbgGetActiveUniform (GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name) with gil:
    gl_debug_print("GL glGetActiveUniform( program = ", program, ", index = ", index, ", bufsize = ", bufsize, ", length*=", repr(hex(<long long> length)), ", size*=", repr(hex(<long long> size)), ", type*=", repr(hex(<long long> type)), ", name*=", repr(hex(<long long> name)), ", )")
    cgl_native.glGetActiveUniform ( program, index, bufsize, length, size, type, name)
    gl_check_error()

cdef void __stdcall dbgGetAttachedShaders (GLuint program, GLsizei maxcount, GLsizei* count, GLuint* shaders) nogil:
    with gil:
        gil_dbgGetAttachedShaders(program, maxcount,  count,  shaders)

cdef void __stdcall gil_dbgGetAttachedShaders (GLuint program, GLsizei maxcount, GLsizei* count, GLuint* shaders) with gil:
    gl_debug_print("GL glGetAttachedShaders( program = ", program, ", maxcount = ", maxcount, ", count*=", repr(hex(<long long> count)), ", shaders*=", repr(hex(<long long> shaders)), ", )")
    cgl_native.glGetAttachedShaders ( program, maxcount, count, shaders)
    gl_check_error()

cdef int  __stdcall dbgGetAttribLocation (GLuint program, const GLchar* name) nogil:
    with gil:
        return gil_dbgGetAttribLocation(program,  <GLchar*>name)

cdef int  __stdcall gil_dbgGetAttribLocation (GLuint program,  GLchar* name) with gil:
    gl_debug_print("GL glGetAttribLocation( program = ", program, ", name*=", repr(hex(<long long> name)), ", )")
    ret = cgl_native.glGetAttribLocation ( program, name)
    gl_check_error()
    return ret

cdef void __stdcall dbgGetBooleanv (GLenum pname, GLboolean* params) nogil:
    with gil:
        gil_dbgGetBooleanv(pname,  params)

cdef void __stdcall gil_dbgGetBooleanv (GLenum pname, GLboolean* params) with gil:
    gl_debug_print("GL glGetBooleanv( pname = ", pname, ", params*=", repr(hex(<long long> params)), ", )")
    cgl_native.glGetBooleanv ( pname, params)
    gl_check_error()

cdef void __stdcall dbgGetBufferParameteriv (GLenum target, GLenum pname, GLint* params) nogil:
    with gil:
        gil_dbgGetBufferParameteriv(target, pname,  params)

cdef void __stdcall gil_dbgGetBufferParameteriv (GLenum target, GLenum pname, GLint* params) with gil:
    gl_debug_print("GL glGetBufferParameteriv( target = ", target, ", pname = ", pname, ", params*=", repr(hex(<long long> params)), ", )")
    cgl_native.glGetBufferParameteriv ( target, pname, params)
    gl_check_error()

cdef GLenum __stdcall dbgGetError() nogil:
    with gil:
        return gil_dbgGetError()

cdef GLenum __stdcall gil_dbgGetError () with gil:
    # gl_debug_print("GL glGetError( )")
    return cgl_native.glGetError ()

cdef void __stdcall dbgGetFloatv (GLenum pname, GLfloat* params) nogil:
    with gil:
        gil_dbgGetFloatv(pname,  params)

cdef void __stdcall gil_dbgGetFloatv (GLenum pname, GLfloat* params) with gil:
    gl_debug_print("GL glGetFloatv( pname = ", pname, ", params*=", repr(hex(<long long> params)), ", )")
    cgl_native.glGetFloatv ( pname, params)
    gl_check_error()

cdef void __stdcall dbgGetFramebufferAttachmentParameteriv (GLenum target, GLenum attachment, GLenum pname, GLint* params) nogil:
    with gil:
        gil_dbgGetFramebufferAttachmentParameteriv(target, attachment, pname,  params)

cdef void __stdcall gil_dbgGetFramebufferAttachmentParameteriv (GLenum target, GLenum attachment, GLenum pname, GLint* params) with gil:
    gl_debug_print("GL glGetFramebufferAttachmentParameteriv( target = ", target, ", attachment = ", attachment, ", pname = ", pname, ", params*=", repr(hex(<long long> params)), ", )")
    cgl_native.glGetFramebufferAttachmentParameteriv ( target, attachment, pname, params)
    gl_check_error()

cdef void __stdcall dbgGetIntegerv (GLenum pname, GLint* params) nogil:
    with gil:
        gil_dbgGetIntegerv(pname,  params)

cdef void __stdcall gil_dbgGetIntegerv (GLenum pname, GLint* params) with gil:
    gl_debug_print("GL glGetIntegerv( pname = ", pname, ", params*=", repr(hex(<long long> params)), ", )")
    cgl_native.glGetIntegerv ( pname, params)
    gl_check_error()

cdef void __stdcall dbgGetProgramiv (GLuint program, GLenum pname, GLint* params) nogil:
    with gil:
        gil_dbgGetProgramiv(program, pname,  params)

cdef void __stdcall gil_dbgGetProgramiv (GLuint program, GLenum pname, GLint* params) with gil:
    gl_debug_print("GL glGetProgramiv( program = ", program, ", pname = ", pname, ", params*=", repr(hex(<long long> params)), ", )")
    cgl_native.glGetProgramiv ( program, pname, params)
    gl_check_error()

cdef void __stdcall dbgGetProgramInfoLog (GLuint program, GLsizei bufsize, GLsizei* length, GLchar* infolog) nogil:
    with gil:
        gil_dbgGetProgramInfoLog(program, bufsize,  length,  infolog)

cdef void __stdcall gil_dbgGetProgramInfoLog (GLuint program, GLsizei bufsize, GLsizei* length, GLchar* infolog) with gil:
    gl_debug_print("GL glGetProgramInfoLog( program = ", program, ", bufsize = ", bufsize, ", length*=", repr(hex(<long long> length)), ", infolog*=", repr(hex(<long long> infolog)), ", )")
    cgl_native.glGetProgramInfoLog ( program, bufsize, length, infolog)
    gl_check_error()

cdef void __stdcall dbgGetRenderbufferParameteriv (GLenum target, GLenum pname, GLint* params) nogil:
    with gil:
        gil_dbgGetRenderbufferParameteriv(target, pname,  params)

cdef void __stdcall gil_dbgGetRenderbufferParameteriv (GLenum target, GLenum pname, GLint* params) with gil:
    gl_debug_print("GL glGetRenderbufferParameteriv( target = ", target, ", pname = ", pname, ", params*=", repr(hex(<long long> params)), ", )")
    cgl_native.glGetRenderbufferParameteriv ( target, pname, params)
    gl_check_error()

cdef void __stdcall dbgGetShaderiv (GLuint shader, GLenum pname, GLint* params) nogil:
    with gil:
        gil_dbgGetShaderiv(shader, pname,  params)

cdef void __stdcall gil_dbgGetShaderiv (GLuint shader, GLenum pname, GLint* params) with gil:
    gl_debug_print("GL glGetShaderiv( shader = ", shader, ", pname = ", pname, ", params*=", repr(hex(<long long> params)), ", )")
    cgl_native.glGetShaderiv ( shader, pname, params)
    gl_check_error()

cdef void __stdcall dbgGetShaderInfoLog (GLuint shader, GLsizei bufsize, GLsizei* length, GLchar* infolog) nogil:
    with gil:
        gil_dbgGetShaderInfoLog(shader, bufsize,  length,  infolog)

cdef void __stdcall gil_dbgGetShaderInfoLog (GLuint shader, GLsizei bufsize, GLsizei* length, GLchar* infolog) with gil:
    gl_debug_print("GL glGetShaderInfoLog( shader = ", shader, ", bufsize = ", bufsize, ", length*=", repr(hex(<long long> length)), ", infolog*=", repr(hex(<long long> infolog)), ", )")
    cgl_native.glGetShaderInfoLog ( shader, bufsize, length, infolog)
    gl_check_error()
# Skipping generation of: "#cdef void __stdcall dbgGetShaderPrecisionFormat (cgl_native.GLenum shadertype, cgl_native.GLenum precisiontype, cgl_native.GLint* range, cgl_native.GLint* precision)"

cdef void __stdcall dbgGetShaderSource (GLuint shader, GLsizei bufsize, GLsizei* length, GLchar* source) nogil:
    with gil:
        gil_dbgGetShaderSource(shader, bufsize,  length,  source)

cdef void __stdcall gil_dbgGetShaderSource (GLuint shader, GLsizei bufsize, GLsizei* length, GLchar* source) with gil:
    gl_debug_print("GL glGetShaderSource( shader = ", shader, ", bufsize = ", bufsize, ", length*=", repr(hex(<long long> length)), ", source*=", repr(hex(<long long> source)), ", )")
    cgl_native.glGetShaderSource ( shader, bufsize, length, source)
    gl_check_error()

cdef  const GLubyte* __stdcall dbgGetString (GLenum name) nogil:
    with gil:
        return gil_dbgGetString(name)

cdef  const GLubyte* __stdcall gil_dbgGetString (GLenum name) with gil:
    gl_debug_print("GL glGetString( name = ", name, ", )")
    return <const GLubyte*><const char*>cgl_native.glGetString ( name)

cdef void __stdcall dbgGetTexParameterfv (GLenum target, GLenum pname, GLfloat* params) nogil:
    with gil:
        gil_dbgGetTexParameterfv(target, pname,  params)

cdef void __stdcall gil_dbgGetTexParameterfv (GLenum target, GLenum pname, GLfloat* params) with gil:
    gl_debug_print("GL glGetTexParameterfv( target = ", target, ", pname = ", pname, ", params*=", repr(hex(<long long> params)), ", )")
    cgl_native.glGetTexParameterfv ( target, pname, params)
    gl_check_error()

cdef void __stdcall dbgGetTexParameteriv (GLenum target, GLenum pname, GLint* params) nogil:
    with gil:
        gil_dbgGetTexParameteriv(target, pname,  params)

cdef void __stdcall gil_dbgGetTexParameteriv (GLenum target, GLenum pname, GLint* params) with gil:
    gl_debug_print("GL glGetTexParameteriv( target = ", target, ", pname = ", pname, ", params*=", repr(hex(<long long> params)), ", )")
    cgl_native.glGetTexParameteriv ( target, pname, params)
    gl_check_error()

cdef void __stdcall dbgGetUniformfv (GLuint program, GLint location, GLfloat* params) nogil:
    with gil:
        gil_dbgGetUniformfv(program, location,  params)

cdef void __stdcall gil_dbgGetUniformfv (GLuint program, GLint location, GLfloat* params) with gil:
    gl_debug_print("GL glGetUniformfv( program = ", program, ", location = ", location, ", params*=", repr(hex(<long long> params)), ", )")
    cgl_native.glGetUniformfv ( program, location, params)
    gl_check_error()

cdef void __stdcall dbgGetUniformiv (GLuint program, GLint location, GLint* params) nogil:
    with gil:
        gil_dbgGetUniformiv(program, location,  params)

cdef void __stdcall gil_dbgGetUniformiv (GLuint program, GLint location, GLint* params) with gil:
    gl_debug_print("GL glGetUniformiv( program = ", program, ", location = ", location, ", params*=", repr(hex(<long long> params)), ", )")
    cgl_native.glGetUniformiv ( program, location, params)
    gl_check_error()

cdef int  __stdcall dbgGetUniformLocation (GLuint program, const GLchar* name) nogil:
    with gil:
        return gil_dbgGetUniformLocation(program,   <bytes>name)

cdef int  __stdcall gil_dbgGetUniformLocation (GLuint program,  GLchar* name) with gil:
    gl_debug_print("GL glGetUniformLocation( program = ", program, ", name*=", <bytes>name, ", )")
    gl_check_error()
    return cgl_native.glGetUniformLocation ( program, name)

cdef void __stdcall dbgGetVertexAttribfv (GLuint index, GLenum pname, GLfloat* params) nogil:
    with gil:
        gil_dbgGetVertexAttribfv(index, pname, params)

cdef void __stdcall gil_dbgGetVertexAttribfv (GLuint index, GLenum pname, GLfloat* params) with gil:
    gl_debug_print("GL glGetVertexAttribfv( index = ", index, ", pname = ", pname, ", params*=", repr(hex(<long long> params)), ", )")
    cgl_native.glGetVertexAttribfv ( index, pname, params)
    gl_check_error()

cdef void __stdcall dbgGetVertexAttribiv (GLuint index, GLenum pname, GLint* params) nogil:
    with gil:
        gil_dbgGetVertexAttribiv(index, pname,  params)

cdef void __stdcall gil_dbgGetVertexAttribiv (GLuint index, GLenum pname, GLint* params) with gil:
    gl_debug_print("GL glGetVertexAttribiv( index = ", index, ", pname = ", pname, ", params*=", repr(hex(<long long> params)), ", )")
    cgl_native.glGetVertexAttribiv ( index, pname, params)
    gl_check_error()

# cdef void __stdcall dbgGetVertexAttribPointerv (GLuint index, GLenum pname, GLvoid** pointer) nogil:
#     with gil:
#         gil_dbgGetVertexAttribPointerv(index, pname, pointer)
#
# cdef void __stdcall gil_dbgGetVertexAttribPointerv (GLuint index, GLenum pname, GLvoid** pointer) with gil:
#     gl_debug_print("GL glGetVertexAttribPointerv( index = ", index, ", pname = ", pname, ", pointer**=", repr(hex(<long long> pointer)), ", )")
#     cgl_native.glGetVertexAttribPointerv ( index, pname, pointer)
#     ret = cgl_native.glGetError()
#     if ret: print("OpenGL Error %d / %x" % (ret, ret))

cdef void __stdcall dbgHint (GLenum target, GLenum mode) nogil:
    with gil:
        gil_dbgHint(target, mode)

cdef void __stdcall gil_dbgHint (GLenum target, GLenum mode) with gil:
    gl_debug_print("GL glHint( target = ", target, ", mode = ", mode, ", )")
    cgl_native.glHint ( target, mode)
    gl_check_error()

cdef GLboolean __stdcall dbgIsBuffer (GLuint buffer) nogil:
    with gil:
        return gil_dbgIsBuffer(buffer)

cdef GLboolean __stdcall gil_dbgIsBuffer (GLuint buffer) with gil:
    gl_debug_print("GL glIsBuffer( buffer = ", buffer, ", )")
    gl_check_error()
    return cgl_native.glIsBuffer ( buffer)

cdef GLboolean __stdcall dbgIsEnabled (GLenum cap) nogil:
    with gil:
        return gil_dbgIsEnabled(cap)

cdef GLboolean __stdcall gil_dbgIsEnabled (GLenum cap) with gil:
    gl_debug_print("GL glIsEnabled( cap = ", cap, ", )")
    gl_check_error()
    return cgl_native.glIsEnabled ( cap)

cdef GLboolean __stdcall dbgIsFramebuffer (GLuint framebuffer) nogil:
    with gil:
        return gil_dbgIsFramebuffer(framebuffer)

cdef GLboolean __stdcall gil_dbgIsFramebuffer (GLuint framebuffer) with gil:
    gl_debug_print("GL glIsFramebuffer( framebuffer = ", framebuffer, ", )")
    gl_check_error()
    return cgl_native.glIsFramebuffer ( framebuffer)

cdef GLboolean __stdcall dbgIsProgram (GLuint program) nogil:
    with gil:
        return gil_dbgIsProgram(program)

cdef GLboolean __stdcall gil_dbgIsProgram (GLuint program) with gil:
    gl_debug_print("GL glIsProgram( program = ", program, ", )")
    gl_check_error()
    return cgl_native.glIsProgram ( program)

cdef GLboolean __stdcall dbgIsRenderbuffer (GLuint renderbuffer) nogil:
    with gil:
        return gil_dbgIsRenderbuffer(renderbuffer)

cdef GLboolean __stdcall gil_dbgIsRenderbuffer (GLuint renderbuffer) with gil:
    gl_debug_print("GL glIsRenderbuffer( renderbuffer = ", renderbuffer, ", )")
    gl_check_error()
    return cgl_native.glIsRenderbuffer ( renderbuffer)

cdef GLboolean __stdcall dbgIsShader (GLuint shader) nogil:
    with gil:
        return gil_dbgIsShader(shader)

cdef GLboolean __stdcall gil_dbgIsShader (GLuint shader) with gil:
    gl_debug_print("GL glIsShader( shader = ", shader, ", )")
    gl_check_error()
    return cgl_native.glIsShader ( shader)

cdef GLboolean __stdcall dbgIsTexture (GLuint texture) nogil:
    with gil:
        return gil_dbgIsTexture(texture)

cdef GLboolean __stdcall gil_dbgIsTexture (GLuint texture) with gil:
    gl_debug_print("GL glIsTexture( texture = ", texture, ", )")
    gl_check_error()
    return cgl_native.glIsTexture ( texture)

cdef void __stdcall dbgLineWidth (GLfloat width) nogil:
    with gil:
        gil_dbgLineWidth(width)

cdef void __stdcall gil_dbgLineWidth (GLfloat width) with gil:
    gl_debug_print("GL glLineWidth( width = ", width, ", )")
    cgl_native.glLineWidth ( width)
    gl_check_error()

cdef void __stdcall dbgLinkProgram (GLuint program) nogil:
    with gil:
        gil_dbgLinkProgram(program)

cdef void __stdcall gil_dbgLinkProgram (GLuint program) with gil:
    gl_debug_print("GL glLinkProgram( program = ", program, ", )")
    cgl_native.glLinkProgram ( program)
    gl_check_error()

cdef void __stdcall dbgPixelStorei (GLenum pname, GLint param) nogil:
    with gil:
        gil_dbgPixelStorei(pname, param)

cdef void __stdcall gil_dbgPixelStorei (GLenum pname, GLint param) with gil:
    gl_debug_print("GL glPixelStorei( pname = ", pname, ", param = ", param, ", )")
    cgl_native.glPixelStorei ( pname, param)
    gl_check_error()

cdef void __stdcall dbgPolygonOffset (GLfloat factor, GLfloat units) nogil:
    with gil:
        gil_dbgPolygonOffset(factor, units)

cdef void __stdcall gil_dbgPolygonOffset (GLfloat factor, GLfloat units) with gil:
    gl_debug_print("GL glPolygonOffset( factor = ", factor, ", units = ", units, ", )")
    cgl_native.glPolygonOffset ( factor, units)
    gl_check_error()

cdef void __stdcall dbgReadPixels (GLint x, GLint y, GLsizei width, GLsizei height, GLenum format, GLenum type, GLvoid* pixels) nogil:
    with gil:
        gil_dbgReadPixels(x, y, width, height, format, type,  pixels)

cdef void __stdcall gil_dbgReadPixels (GLint x, GLint y, GLsizei width, GLsizei height, GLenum format, GLenum type, GLvoid* pixels) with gil:
    gl_debug_print("GL glReadPixels( x = ", x, ", y = ", y, ", width = ", width, ", height = ", height, ", format = ", format, ", type = ", type, ", pixels*=", repr(hex(<long long> pixels)), ", )")
    cgl_native.glReadPixels ( x, y, width, height, format, type, pixels)
    gl_check_error()
# Skipping generation of: "#cdef void __stdcall dbgReleaseShaderCompiler ()"

cdef void __stdcall dbgRenderbufferStorage (GLenum target, GLenum internalformat, GLsizei width, GLsizei height) nogil:
    with gil:
        gil_dbgRenderbufferStorage(target, internalformat, width, height)

cdef void __stdcall gil_dbgRenderbufferStorage (GLenum target, GLenum internalformat, GLsizei width, GLsizei height) with gil:
    gl_debug_print("GL glRenderbufferStorage( target = ", target, ", internalformat = ", internalformat, ", width = ", width, ", height = ", height, ", )")
    cgl_native.glRenderbufferStorage ( target, internalformat, width, height)
    gl_check_error()

cdef void __stdcall dbgSampleCoverage (GLclampf value, GLboolean invert) nogil:
    with gil:
        gil_dbgSampleCoverage(value, invert)

cdef void __stdcall gil_dbgSampleCoverage (GLclampf value, GLboolean invert) with gil:
    gl_debug_print("GL glSampleCoverage( value = ", value, ", invert = ", invert, ", )")
    cgl_native.glSampleCoverage ( value, invert)
    gl_check_error()

cdef void __stdcall dbgScissor (GLint x, GLint y, GLsizei width, GLsizei height) nogil:
    with gil:
        gil_dbgScissor(x, y, width, height)

cdef void __stdcall gil_dbgScissor (GLint x, GLint y, GLsizei width, GLsizei height) with gil:
    gl_debug_print("GL glScissor( x = ", x, ", y = ", y, ", width = ", width, ", height = ", height, ", )")
    cgl_native.glScissor ( x, y, width, height)
    gl_check_error()
# Skipping generation of: "#cdef void __stdcall dbgShaderBinary (cgl_native.GLsizei n,  cgl_native.GLuint* shaders, cgl_native.GLenum binaryformat,  cgl_native.GLvoid* binary, cgl_native.GLsizei length)"

cdef void __stdcall dbgShaderSource (GLuint shader, GLsizei count, const GLchar** string, const GLint* length) nogil:
    with gil:
        gil_dbgShaderSource(shader, count, string, length)

cdef void __stdcall gil_dbgShaderSource (GLuint shader, GLsizei count,  const GLchar** string, const GLint* length) with gil:
    gl_debug_print("GL glShaderSource( shader = ", shader, ", count = ", count, ", string**=", repr(hex(<long long> string)), ", length*=", repr(hex(<long long> length)), ", )")
    cgl_native.glShaderSource ( shader, count, <const_char_ptr*>string, length)
    gl_check_error()

cdef void __stdcall dbgStencilFunc (GLenum func, GLint ref, GLuint mask) nogil:
    with gil:
        gil_dbgStencilFunc(func, ref, mask)

cdef void __stdcall gil_dbgStencilFunc (GLenum func, GLint ref, GLuint mask) with gil:
    gl_debug_print("GL glStencilFunc( func = ", func, ", ref = ", ref, ", mask = ", mask, ", )")
    cgl_native.glStencilFunc ( func, ref, mask)
    gl_check_error()

cdef void __stdcall dbgStencilFuncSeparate (GLenum face, GLenum func, GLint ref, GLuint mask) nogil:
    with gil:
        gil_dbgStencilFuncSeparate(face, func, ref, mask)

cdef void __stdcall gil_dbgStencilFuncSeparate (GLenum face, GLenum func, GLint ref, GLuint mask) with gil:
    gl_debug_print("GL glStencilFuncSeparate( face = ", face, ", func = ", func, ", ref = ", ref, ", mask = ", mask, ", )")
    cgl_native.glStencilFuncSeparate ( face, func, ref, mask)
    gl_check_error()

cdef void __stdcall dbgStencilMask (GLuint mask) nogil:
    with gil:
        gil_dbgStencilMask(mask)

cdef void __stdcall gil_dbgStencilMask (GLuint mask) with gil:
    gl_debug_print("GL glStencilMask( mask = ", mask, ", )")
    cgl_native.glStencilMask ( mask)
    gl_check_error()

cdef void __stdcall dbgStencilMaskSeparate (GLenum face, GLuint mask) nogil:
    with gil:
        gil_dbgStencilMaskSeparate(face, mask)

cdef void __stdcall gil_dbgStencilMaskSeparate (GLenum face, GLuint mask) with gil:
    gl_debug_print("GL glStencilMaskSeparate( face = ", face, ", mask = ", mask, ", )")
    cgl_native.glStencilMaskSeparate ( face, mask)
    gl_check_error()

cdef void __stdcall dbgStencilOp (GLenum fail, GLenum zfail, GLenum zpass) nogil:
    with gil:
        gil_dbgStencilOp(fail, zfail, zpass)

cdef void __stdcall gil_dbgStencilOp (GLenum fail, GLenum zfail, GLenum zpass) with gil:
    gl_debug_print("GL glStencilOp( fail = ", fail, ", zfail = ", zfail, ", zpass = ", zpass, ", )")
    cgl_native.glStencilOp ( fail, zfail, zpass)
    gl_check_error()

cdef void __stdcall dbgStencilOpSeparate (GLenum face, GLenum fail, GLenum zfail, GLenum zpass) nogil:
    with gil:
        gil_dbgStencilOpSeparate(face, fail, zfail, zpass)

cdef void __stdcall gil_dbgStencilOpSeparate (GLenum face, GLenum fail, GLenum zfail, GLenum zpass) with gil:
    gl_debug_print("GL glStencilOpSeparate( face = ", face, ", fail = ", fail, ", zfail = ", zfail, ", zpass = ", zpass, ", )")
    cgl_native.glStencilOpSeparate ( face, fail, zfail, zpass)
    gl_check_error()

cdef void __stdcall dbgTexImage2D (GLenum target, GLint level, GLint internalformat, GLsizei width, GLsizei height, GLint border, GLenum format, GLenum type, const GLvoid* pixels) nogil:
    with gil:
        gil_dbgTexImage2D(target, level, internalformat, width, height, border, format, type,   pixels)

cdef void __stdcall gil_dbgTexImage2D (GLenum target, GLint level, GLint internalformat, GLsizei width, GLsizei height, GLint border, GLenum format, GLenum type, const GLvoid* pixels) with gil:
    gl_debug_print("GL glTexImage2D( target = ", target, ", level = ", level, ", internalformat = ", internalformat, ", width = ", width, ", height = ", height, ", border = ", border, ", format = ", format, ", type = ", type, ", pixels*=", repr(hex(<long long> pixels)), ", )")
    cgl_native.glTexImage2D ( target, level, internalformat, width, height, border, format, type, pixels)
    gl_check_error()

cdef void __stdcall dbgTexParameterf (GLenum target, GLenum pname, GLfloat param) nogil:
    with gil:
        gil_dbgTexParameterf(target, pname, param)

cdef void __stdcall gil_dbgTexParameterf (GLenum target, GLenum pname, GLfloat param) with gil:
    gl_debug_print("GL glTexParameterf( target = ", target, ", pname = ", pname, ", param = ", param, ", )")
    cgl_native.glTexParameterf ( target, pname, param)
    gl_check_error()

# cdef void __stdcall dbgTexParameterfv (GLenum target, GLenum pname,  GLfloat* params) nogil:
#     with gil:
#         gil_dbgTexParameterfv(target, pname,   params)
#
# cdef void __stdcall gil_dbgTexParameterfv (GLenum target, GLenum pname,  GLfloat* params) with gil:
#     gl_debug_print("GL glTexParameterfv( target = ", target, ", pname = ", pname, ", params*=", repr(hex(<long long> params)), ", )")
#     cgl_native.glTexParameterfv ( target, pname, params)
#     ret = cgl_native.glGetError()
#     if ret: print("OpenGL Error %d / %x" % (ret, ret))
#
cdef void __stdcall dbgTexParameteri (GLenum target, GLenum pname, GLint param) nogil:
    with gil:
        gil_dbgTexParameteri(target, pname, param)

cdef void __stdcall gil_dbgTexParameteri (GLenum target, GLenum pname, GLint param) with gil:
    gl_debug_print("GL glTexParameteri( target = ", target, ", pname = ", pname, ", param = ", param, ", )")
    cgl_native.glTexParameteri ( target, pname, param)
    gl_check_error()

# cdef void __stdcall dbgTexParameteriv (GLenum target, GLenum pname,  GLint* params) nogil:
#     with gil:
#         gil_dbgTexParameteriv(target, pname,   params)
#
# cdef void __stdcall gil_dbgTexParameteriv (GLenum target, GLenum pname,  GLint* params) with gil:
#     gl_debug_print("GL glTexParameteriv( target = ", target, ", pname = ", pname, ", params*=", repr(hex(<long long> params)), ", )")
#     cgl_native.glTexParameteriv ( target, pname, params)
#     ret = cgl_native.glGetError()
#     if ret: print("OpenGL Error %d / %x" % (ret, ret))
#
cdef void __stdcall dbgTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLenum type, const GLvoid* pixels) nogil:
    with gil:
        gil_dbgTexSubImage2D(target, level, xoffset, yoffset, width, height, format, type,   pixels)

cdef void __stdcall gil_dbgTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLenum type, const GLvoid* pixels) with gil:
    gl_debug_print("GL glTexSubImage2D( target = ", target, ", level = ", level, ", xoffset = ", xoffset, ", yoffset = ", yoffset, ", width = ", width, ", height = ", height, ", format = ", format, ", type = ", type, ", pixels*=", repr(hex(<long long> pixels)), ", )")
    cgl_native.glTexSubImage2D ( target, level, xoffset, yoffset, width, height, format, type, pixels)
    gl_check_error()

cdef void __stdcall dbgUniform1f (GLint location, GLfloat x) nogil:
    with gil:
        gil_dbgUniform1f(location, x)

cdef void __stdcall gil_dbgUniform1f (GLint location, GLfloat x) with gil:
    gl_debug_print("GL glUniform1f( location = ", location, ", x = ", x, ", )")
    cgl_native.glUniform1f ( location, x)
    gl_check_error()

cdef void __stdcall dbgUniform1fv (GLint location, GLsizei count, const GLfloat* v) nogil:
    with gil:
        gil_dbgUniform1fv(location, count,   v)

cdef void __stdcall gil_dbgUniform1fv (GLint location, GLsizei count, const GLfloat* v) with gil:
    gl_debug_print("GL glUniform1fv( location = ", location, ", count = ", count, ", v*=", repr(hex(<long long> v)), ", )")
    cgl_native.glUniform1fv ( location, count, v)
    gl_check_error()

cdef void __stdcall dbgUniform1i (GLint location, GLint x) nogil:
    with gil:
        gil_dbgUniform1i(location, x)

cdef void __stdcall gil_dbgUniform1i (GLint location, GLint x) with gil:
    gl_debug_print("GL glUniform1i( location = ", location, ", x = ", x, ", )")
    cgl_native.glUniform1i ( location, x)
    gl_check_error()

cdef void __stdcall dbgUniform1iv (GLint location, GLsizei count, const GLint* v) nogil:
    with gil:
        gil_dbgUniform1iv(location, count,   v)

cdef void __stdcall gil_dbgUniform1iv (GLint location, GLsizei count, const GLint* v) with gil:
    gl_debug_print("GL glUniform1iv( location = ", location, ", count = ", count, ", v*=", repr(hex(<long long> v)), ", )")
    cgl_native.glUniform1iv ( location, count, v)
    gl_check_error()

cdef void __stdcall dbgUniform2f (GLint location, GLfloat x, GLfloat y) nogil:
    with gil:
        gil_dbgUniform2f(location, x, y)

cdef void __stdcall gil_dbgUniform2f (GLint location, GLfloat x, GLfloat y) with gil:
    gl_debug_print("GL glUniform2f( location = ", location, ", x = ", x, ", y = ", y, ", )")
    cgl_native.glUniform2f ( location, x, y)
    gl_check_error()

cdef void __stdcall dbgUniform2fv (GLint location, GLsizei count, const GLfloat* v) nogil:
    with gil:
        gil_dbgUniform2fv(location, count,   v)

cdef void __stdcall gil_dbgUniform2fv (GLint location, GLsizei count, const GLfloat* v) with gil:
    gl_debug_print("GL glUniform2fv( location = ", location, ", count = ", count, ", v*=", repr(hex(<long long> v)), ", )")
    cgl_native.glUniform2fv ( location, count, v)
    gl_check_error()

cdef void __stdcall dbgUniform2i (GLint location, GLint x, GLint y) nogil:
    with gil:
        gil_dbgUniform2i(location, x, y)

cdef void __stdcall gil_dbgUniform2i (GLint location, GLint x, GLint y) with gil:
    gl_debug_print("GL glUniform2i( location = ", location, ", x = ", x, ", y = ", y, ", )")
    cgl_native.glUniform2i ( location, x, y)
    gl_check_error()

cdef void __stdcall dbgUniform2iv (GLint location, GLsizei count, const GLint* v) nogil:
    with gil:
        gil_dbgUniform2iv(location, count,   v)

cdef void __stdcall gil_dbgUniform2iv (GLint location, GLsizei count, const GLint* v) with gil:
    gl_debug_print("GL glUniform2iv( location = ", location, ", count = ", count, ", v*=", repr(hex(<long long> v)), ", )")
    cgl_native.glUniform2iv ( location, count, v)
    gl_check_error()

cdef void __stdcall dbgUniform3f (GLint location, GLfloat x, GLfloat y, GLfloat z) nogil:
    with gil:
        gil_dbgUniform3f(location, x, y, z)

cdef void __stdcall gil_dbgUniform3f (GLint location, GLfloat x, GLfloat y, GLfloat z) with gil:
    gl_debug_print("GL glUniform3f( location = ", location, ", x = ", x, ", y = ", y, ", z = ", z, ", )")
    cgl_native.glUniform3f ( location, x, y, z)
    gl_check_error()

cdef void __stdcall dbgUniform3fv (GLint location, GLsizei count, const GLfloat* v) nogil:
    with gil:
        gil_dbgUniform3fv(location, count,   v)

cdef void __stdcall gil_dbgUniform3fv (GLint location, GLsizei count, const GLfloat* v) with gil:
    gl_debug_print("GL glUniform3fv( location = ", location, ", count = ", count, ", v*=", repr(hex(<long long> v)), ", )")
    cgl_native.glUniform3fv ( location, count, v)
    gl_check_error()

cdef void __stdcall dbgUniform3i (GLint location, GLint x, GLint y, GLint z) nogil:
    with gil:
        gil_dbgUniform3i(location, x, y, z)

cdef void __stdcall gil_dbgUniform3i (GLint location, GLint x, GLint y, GLint z) with gil:
    gl_debug_print("GL glUniform3i( location = ", location, ", x = ", x, ", y = ", y, ", z = ", z, ", )")
    cgl_native.glUniform3i ( location, x, y, z)
    gl_check_error()

cdef void __stdcall dbgUniform3iv (GLint location, GLsizei count, const GLint* v) nogil:
    with gil:
        gil_dbgUniform3iv(location, count,   v)

cdef void __stdcall gil_dbgUniform3iv (GLint location, GLsizei count, const GLint* v) with gil:
    gl_debug_print("GL glUniform3iv( location = ", location, ", count = ", count, ", v*=", repr(hex(<long long> v)), ", )")
    cgl_native.glUniform3iv ( location, count, v)
    gl_check_error()

cdef void __stdcall dbgUniform4f (GLint location, GLfloat x, GLfloat y, GLfloat z, GLfloat w) nogil:
    with gil:
        gil_dbgUniform4f(location, x, y, z, w)

cdef void __stdcall gil_dbgUniform4f (GLint location, GLfloat x, GLfloat y, GLfloat z, GLfloat w) with gil:
    gl_debug_print("GL glUniform4f( location = ", location, ", x = ", x, ", y = ", y, ", z = ", z, ", w = ", w, ", )")
    cgl_native.glUniform4f ( location, x, y, z, w)
    gl_check_error()

cdef void __stdcall dbgUniform4fv (GLint location, GLsizei count, const GLfloat* v) nogil:
    with gil:
        gil_dbgUniform4fv(location, count,   v)

cdef void __stdcall gil_dbgUniform4fv (GLint location, GLsizei count, const GLfloat* v) with gil:
    gl_debug_print("GL glUniform4fv( location = ", location, ", count = ", count, ", v*=", repr(hex(<long long> v)), ", )")
    cgl_native.glUniform4fv ( location, count, v)
    gl_check_error()

cdef void __stdcall dbgUniform4i (GLint location, GLint x, GLint y, GLint z, GLint w) nogil:
    with gil:
        gil_dbgUniform4i(location, x, y, z, w)

cdef void __stdcall gil_dbgUniform4i (GLint location, GLint x, GLint y, GLint z, GLint w) with gil:
    gl_debug_print("GL glUniform4i( location = ", location, ", x = ", x, ", y = ", y, ", z = ", z, ", w = ", w, ", )")
    cgl_native.glUniform4i ( location, x, y, z, w)
    gl_check_error()

cdef void __stdcall dbgUniform4iv (GLint location, GLsizei count, const GLint* v) nogil:
    with gil:
        gil_dbgUniform4iv(location, count,   v)

cdef void __stdcall gil_dbgUniform4iv (GLint location, GLsizei count, const GLint* v) with gil:
    gl_debug_print("GL glUniform4iv( location = ", location, ", count = ", count, ", v*=", repr(hex(<long long> v)), ", )")
    cgl_native.glUniform4iv ( location, count, v)
    gl_check_error()

# cdef void __stdcall dbgUniformMatrix2fv (GLint location, GLsizei count, GLboolean transpose,  GLfloat* value) nogil:
#     with gil:
#         gil_dbgUniformMatrix2fv(location, count, transpose,   value)
#
# cdef void __stdcall gil_dbgUniformMatrix2fv (GLint location, GLsizei count, GLboolean transpose,  GLfloat* value) with gil:
#     gl_debug_print("GL glUniformMatrix2fv( location = ", location, ", count = ", count, ", transpose = ", transpose, ", value*=", repr(hex(<long long> value)), ", )")
#     cgl_native.glUniformMatrix2fv ( location, count, transpose, value)
#     ret = cgl_native.glGetError()
#     if ret: print("OpenGL Error %d / %x" % (ret, ret))

# cdef void __stdcall dbgUniformMatrix3fv (GLint location, GLsizei count, GLboolean transpose,  GLfloat* value) nogil:
#     with gil:
#         gil_dbgUniformMatrix3fv(location, count, transpose,   value)
#
# cdef void __stdcall gil_dbgUniformMatrix3fv (GLint location, GLsizei count, GLboolean transpose,  GLfloat* value) with gil:
#     gl_debug_print("GL glUniformMatrix3fv( location = ", location, ", count = ", count, ", transpose = ", transpose, ", value*=", repr(hex(<long long> value)), ", )")
#     cgl_native.glUniformMatrix3fv ( location, count, transpose, value)
#     ret = cgl_native.glGetError()
#     if ret: print("OpenGL Error %d / %x" % (ret, ret))

cdef void __stdcall dbgUniformMatrix4fv (GLint location, GLsizei count, GLboolean transpose, const GLfloat* value) nogil:
    with gil:
        gil_dbgUniformMatrix4fv(location, count, transpose,   value)

cdef void __stdcall gil_dbgUniformMatrix4fv (GLint location, GLsizei count, GLboolean transpose, const GLfloat* value) with gil:
    gl_debug_print("GL glUniformMatrix4fv( location = ", location, ", count = ", count, ", transpose = ", transpose, ", value*=", repr(hex(<long long> value)), ", )")
    cgl_native.glUniformMatrix4fv ( location, count, transpose, value)
    gl_check_error()

cdef void __stdcall dbgUseProgram (GLuint program) nogil:
    with gil:
        gil_dbgUseProgram(program)

cdef void __stdcall gil_dbgUseProgram (GLuint program) with gil:
    gl_debug_print("GL glUseProgram( program = ", program, ", )")
    cgl_native.glUseProgram ( program)
    gl_check_error()

cdef void __stdcall dbgValidateProgram (GLuint program) nogil:
    with gil:
        gil_dbgValidateProgram(program)

cdef void __stdcall gil_dbgValidateProgram (GLuint program) with gil:
    gl_debug_print("GL glValidateProgram( program = ", program, ", )")
    cgl_native.glValidateProgram ( program)
    gl_check_error()

cdef void __stdcall dbgVertexAttrib1f (GLuint indx, GLfloat x) nogil:
    with gil:
        gil_dbgVertexAttrib1f(indx, x)

cdef void __stdcall gil_dbgVertexAttrib1f (GLuint indx, GLfloat x) with gil:
    gl_debug_print("GL glVertexAttrib1f( indx = ", indx, ", x = ", x, ", )")
    cgl_native.glVertexAttrib1f ( indx, x)
    gl_check_error()

# cdef void __stdcall dbgVertexAttrib1fv (GLuint indx,  GLfloat* values) nogil:
#     with gil:
#         gil_dbgVertexAttrib1fv(indx,   values)
#
# cdef void __stdcall gil_dbgVertexAttrib1fv (GLuint indx,  GLfloat* values) with gil:
#     gl_debug_print("GL glVertexAttrib1fv( indx = ", indx, ", values*=", repr(hex(<long long> values)), ", )")
#     cgl_native.glVertexAttrib1fv ( indx, values)
#     ret = cgl_native.glGetError()
#     if ret: print("OpenGL Error %d / %x" % (ret, ret))
#
cdef void __stdcall dbgVertexAttrib2f (GLuint indx, GLfloat x, GLfloat y) nogil:
    with gil:
        gil_dbgVertexAttrib2f(indx, x, y)

cdef void __stdcall gil_dbgVertexAttrib2f (GLuint indx, GLfloat x, GLfloat y) with gil:
    gl_debug_print("GL glVertexAttrib2f( indx = ", indx, ", x = ", x, ", y = ", y, ", )")
    cgl_native.glVertexAttrib2f ( indx, x, y)
    gl_check_error()

# cdef void __stdcall dbgVertexAttrib2fv (GLuint indx,  GLfloat* values) nogil:
#     with gil:
#         gil_dbgVertexAttrib2fv(indx,   values)
#
# cdef void __stdcall gil_dbgVertexAttrib2fv (GLuint indx,  GLfloat* values) with gil:
#     gl_debug_print("GL glVertexAttrib2fv( indx = ", indx, ", values*=", repr(hex(<long long> values)), ", )")
#     cgl_native.glVertexAttrib2fv ( indx, values)
#     ret = cgl_native.glGetError()
#     if ret: print("OpenGL Error %d / %x" % (ret, ret))
#
cdef void __stdcall dbgVertexAttrib3f (GLuint indx, GLfloat x, GLfloat y, GLfloat z) nogil:
    with gil:
        gil_dbgVertexAttrib3f(indx, x, y, z)

cdef void __stdcall gil_dbgVertexAttrib3f (GLuint indx, GLfloat x, GLfloat y, GLfloat z) with gil:
    gl_debug_print("GL glVertexAttrib3f( indx = ", indx, ", x = ", x, ", y = ", y, ", z = ", z, ", )")
    cgl_native.glVertexAttrib3f ( indx, x, y, z)
    gl_check_error()

# cdef void __stdcall dbgVertexAttrib3fv (GLuint indx,  GLfloat* values) nogil:
#     with gil:
#         gil_dbgVertexAttrib3fv(indx,   values)
#
# cdef void __stdcall gil_dbgVertexAttrib3fv (GLuint indx,  GLfloat* values) with gil:
#     gl_debug_print("GL glVertexAttrib3fv( indx = ", indx, ", values*=", repr(hex(<long long> values)), ", )")
#     cgl_native.glVertexAttrib3fv ( indx, values)
#     ret = cgl_native.glGetError()
#     if ret: print("OpenGL Error %d / %x" % (ret, ret))
#
cdef void __stdcall dbgVertexAttrib4f (GLuint indx, GLfloat x, GLfloat y, GLfloat z, GLfloat w) nogil:
    with gil:
        gil_dbgVertexAttrib4f(indx, x, y, z, w)

cdef void __stdcall gil_dbgVertexAttrib4f (GLuint indx, GLfloat x, GLfloat y, GLfloat z, GLfloat w) with gil:
    gl_debug_print("GL glVertexAttrib4f( indx = ", indx, ", x = ", x, ", y = ", y, ", z = ", z, ", w = ", w, ", )")
    cgl_native.glVertexAttrib4f ( indx, x, y, z, w)
    gl_check_error()

# cdef void __stdcall dbgVertexAttrib4fv (GLuint indx,  GLfloat* values) nogil:
#     with gil:
#         gil_dbgVertexAttrib4fv(indx,   values)
#
# cdef void __stdcall gil_dbgVertexAttrib4fv (GLuint indx,  GLfloat* values) with gil:
#     gl_debug_print("GL glVertexAttrib4fv( indx = ", indx, ", values*=", repr(hex(<long long> values)), ", )")
#     cgl_native.glVertexAttrib4fv ( indx, values)
#     ret = cgl_native.glGetError()
#     if ret: print("OpenGL Error %d / %x" % (ret, ret))
#
cdef void __stdcall dbgVertexAttribPointer (GLuint indx, GLint size, GLenum type, GLboolean normalized, GLsizei stride, const GLvoid* ptr) nogil:
    with gil:
        gil_dbgVertexAttribPointer(indx, size, type, normalized, stride, <GLvoid*>ptr)

cdef void __stdcall gil_dbgVertexAttribPointer (GLuint indx, GLint size, GLenum type, GLboolean normalized, GLsizei stride,  GLvoid* ptr) with gil:
    gl_debug_print("GL glVertexAttribPointer( indx = ", indx, ", size = ", size, ", type = ", type, ", normalized = ", normalized, ", stride = ", stride, ", ptr*=", repr(hex(<long long> ptr)), ", )")
    cgl_native.glVertexAttribPointer ( indx, size, type, normalized, stride, ptr)
    gl_check_error()

cdef void __stdcall dbgViewport (GLint x, GLint y, GLsizei width, GLsizei height) nogil:
    with gil:
        gil_dbgViewport(x, y, width, height)

cdef void __stdcall gil_dbgViewport (GLint x, GLint y, GLsizei width, GLsizei height) with gil:
    gl_debug_print("GL glViewport( x = ", x, ", y = ", y, ", width = ", width, ", height = ", height, ", )")
    cgl_native.glViewport ( x, y, width, height)
    gl_check_error()


def init_backend_debug():
    cgl_debug.glActiveTexture = dbgActiveTexture
    cgl_debug.glAttachShader = dbgAttachShader
    cgl_debug.glBindAttribLocation = dbgBindAttribLocation
    cgl_debug.glBindBuffer = dbgBindBuffer
    cgl_debug.glBindFramebuffer = dbgBindFramebuffer
    cgl_debug.glBindRenderbuffer = dbgBindRenderbuffer
    cgl_debug.glBindTexture = dbgBindTexture
    cgl_debug.glBlendColor = dbgBlendColor
    cgl_debug.glBlendEquation = dbgBlendEquation
    cgl_debug.glBlendEquationSeparate = dbgBlendEquationSeparate
    cgl_debug.glBlendFunc = dbgBlendFunc
    cgl_debug.glBlendFuncSeparate = dbgBlendFuncSeparate
    cgl_debug.glBufferData = dbgBufferData
    cgl_debug.glBufferSubData = dbgBufferSubData
    cgl_debug.glCheckFramebufferStatus = dbgCheckFramebufferStatus
    cgl_debug.glClear = dbgClear
    cgl_debug.glClearColor = dbgClearColor
    cgl_debug.glClearStencil = dbgClearStencil
    cgl_debug.glColorMask = dbgColorMask
    cgl_debug.glCompileShader = dbgCompileShader
    cgl_debug.glCompressedTexImage2D = dbgCompressedTexImage2D
    cgl_debug.glCompressedTexSubImage2D = dbgCompressedTexSubImage2D
    cgl_debug.glCopyTexImage2D = dbgCopyTexImage2D
    cgl_debug.glCopyTexSubImage2D = dbgCopyTexSubImage2D
    cgl_debug.glCreateProgram = dbgCreateProgram
    cgl_debug.glCreateShader = dbgCreateShader
    cgl_debug.glCullFace = dbgCullFace
    cgl_debug.glDeleteBuffers = dbgDeleteBuffers
    cgl_debug.glDeleteFramebuffers = dbgDeleteFramebuffers
    cgl_debug.glDeleteProgram = dbgDeleteProgram
    cgl_debug.glDeleteRenderbuffers = dbgDeleteRenderbuffers
    cgl_debug.glDeleteShader = dbgDeleteShader
    cgl_debug.glDeleteTextures = dbgDeleteTextures
    cgl_debug.glDepthFunc = dbgDepthFunc
    cgl_debug.glDepthMask = dbgDepthMask
    cgl_debug.glDetachShader = dbgDetachShader
    cgl_debug.glDisable = dbgDisable
    cgl_debug.glDisableVertexAttribArray = dbgDisableVertexAttribArray
    cgl_debug.glDrawArrays = dbgDrawArrays
    cgl_debug.glDrawElements = dbgDrawElements
    cgl_debug.glEnable = dbgEnable
    cgl_debug.glEnableVertexAttribArray = dbgEnableVertexAttribArray
    cgl_debug.glFinish = dbgFinish
    cgl_debug.glFlush = dbgFlush
    cgl_debug.glFramebufferRenderbuffer = dbgFramebufferRenderbuffer
    cgl_debug.glFramebufferTexture2D = dbgFramebufferTexture2D
    cgl_debug.glFrontFace = dbgFrontFace
    cgl_debug.glGenBuffers = dbgGenBuffers
    cgl_debug.glGenerateMipmap = dbgGenerateMipmap
    cgl_debug.glGenFramebuffers = dbgGenFramebuffers
    cgl_debug.glGenRenderbuffers = dbgGenRenderbuffers
    cgl_debug.glGenTextures = dbgGenTextures
    cgl_debug.glGetActiveAttrib = dbgGetActiveAttrib
    cgl_debug.glGetActiveUniform = dbgGetActiveUniform
    cgl_debug.glGetAttachedShaders = dbgGetAttachedShaders
    cgl_debug.glGetAttribLocation = dbgGetAttribLocation
    cgl_debug.glGetBooleanv = dbgGetBooleanv
    cgl_debug.glGetBufferParameteriv = dbgGetBufferParameteriv
    cgl_debug.glGetError = dbgGetError
    cgl_debug.glGetFloatv = dbgGetFloatv
    cgl_debug.glGetFramebufferAttachmentParameteriv = dbgGetFramebufferAttachmentParameteriv
    cgl_debug.glGetIntegerv = dbgGetIntegerv
    cgl_debug.glGetProgramInfoLog = dbgGetProgramInfoLog
    cgl_debug.glGetProgramiv = dbgGetProgramiv
    cgl_debug.glGetRenderbufferParameteriv = dbgGetRenderbufferParameteriv
    cgl_debug.glGetShaderInfoLog = dbgGetShaderInfoLog
    cgl_debug.glGetShaderiv = dbgGetShaderiv
    cgl_debug.glGetShaderSource = dbgGetShaderSource
    cgl_debug.glGetString = dbgGetString
    cgl_debug.glGetTexParameterfv = dbgGetTexParameterfv
    cgl_debug.glGetTexParameteriv = dbgGetTexParameteriv
    cgl_debug.glGetUniformfv = dbgGetUniformfv
    cgl_debug.glGetUniformiv = dbgGetUniformiv
    cgl_debug.glGetUniformLocation = dbgGetUniformLocation
    cgl_debug.glGetVertexAttribfv = dbgGetVertexAttribfv
    cgl_debug.glGetVertexAttribiv = dbgGetVertexAttribiv
    cgl_debug.glHint = dbgHint
    cgl_debug.glIsBuffer = dbgIsBuffer
    cgl_debug.glIsEnabled = dbgIsEnabled
    cgl_debug.glIsFramebuffer = dbgIsFramebuffer
    cgl_debug.glIsProgram = dbgIsProgram
    cgl_debug.glIsRenderbuffer = dbgIsRenderbuffer
    cgl_debug.glIsShader = dbgIsShader
    cgl_debug.glIsTexture = dbgIsTexture
    cgl_debug.glLineWidth = dbgLineWidth
    cgl_debug.glLinkProgram = dbgLinkProgram
    cgl_debug.glPixelStorei = dbgPixelStorei
    cgl_debug.glPolygonOffset = dbgPolygonOffset
    cgl_debug.glReadPixels = dbgReadPixels
    cgl_debug.glRenderbufferStorage = dbgRenderbufferStorage
    cgl_debug.glSampleCoverage = dbgSampleCoverage
    cgl_debug.glScissor = dbgScissor
    # cgl_debug.glShaderBinary = dbgShaderBinary
    cgl_debug.glShaderSource = dbgShaderSource
    cgl_debug.glStencilFunc = dbgStencilFunc
    cgl_debug.glStencilFuncSeparate = dbgStencilFuncSeparate
    cgl_debug.glStencilMask = dbgStencilMask
    cgl_debug.glStencilMaskSeparate = dbgStencilMaskSeparate
    cgl_debug.glStencilOp = dbgStencilOp
    cgl_debug.glStencilOpSeparate = dbgStencilOpSeparate
    cgl_debug.glTexImage2D = dbgTexImage2D
    cgl_debug.glTexParameterf = dbgTexParameterf
    cgl_debug.glTexParameteri = dbgTexParameteri
    cgl_debug.glTexSubImage2D = dbgTexSubImage2D
    cgl_debug.glUniform1f = dbgUniform1f
    cgl_debug.glUniform1fv = dbgUniform1fv
    cgl_debug.glUniform1i = dbgUniform1i
    cgl_debug.glUniform1iv = dbgUniform1iv
    cgl_debug.glUniform2f = dbgUniform2f
    cgl_debug.glUniform2fv = dbgUniform2fv
    cgl_debug.glUniform2i = dbgUniform2i
    cgl_debug.glUniform2iv = dbgUniform2iv
    cgl_debug.glUniform3f = dbgUniform3f
    cgl_debug.glUniform3fv = dbgUniform3fv
    cgl_debug.glUniform3i = dbgUniform3i
    cgl_debug.glUniform3iv = dbgUniform3iv
    cgl_debug.glUniform4f = dbgUniform4f
    cgl_debug.glUniform4fv = dbgUniform4fv
    cgl_debug.glUniform4i = dbgUniform4i
    cgl_debug.glUniform4iv = dbgUniform4iv
    cgl_debug.glUniformMatrix4fv = dbgUniformMatrix4fv
    cgl_debug.glUseProgram = dbgUseProgram
    cgl_debug.glValidateProgram = dbgValidateProgram
    cgl_debug.glVertexAttrib1f = dbgVertexAttrib1f
    cgl_debug.glVertexAttrib2f = dbgVertexAttrib2f
    cgl_debug.glVertexAttrib3f = dbgVertexAttrib3f
    cgl_debug.glVertexAttrib4f = dbgVertexAttrib4f
    cgl_debug.glVertexAttribPointer = dbgVertexAttribPointer
    cgl_debug.glViewport = dbgViewport

    global cgl_native
    cgl_native = cgl_get_context()
    cgl_set_context(cgl_debug)
