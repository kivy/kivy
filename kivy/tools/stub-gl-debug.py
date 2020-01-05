# flake8: noqa
from __future__ import print_function

a = '''cdef void   glActiveTexture (cgl.GLenum texture)
cdef void   glAttachShader (cgl.GLuint program, cgl.GLuint shader)
cdef void   glBindAttribLocation (cgl.GLuint program, cgl.GLuint index,  cgl.GLchar* name)
cdef void   glBindBuffer (cgl.GLenum target, cgl.GLuint buffer)
cdef void   glBindFramebuffer (cgl.GLenum target, cgl.GLuint framebuffer)
cdef void   glBindRenderbuffer (cgl.GLenum target, cgl.GLuint renderbuffer)
cdef void   glBindTexture (cgl.GLenum target, cgl.GLuint texture)
cdef void   glBlendColor (cgl.GLclampf red, cgl.GLclampf green, cgl.GLclampf blue, cgl.GLclampf alpha)
cdef void   glBlendEquation (cgl.GLenum mode)
cdef void   glBlendEquationSeparate (cgl.GLenum modeRGB, cgl.GLenum modeAlpha)
cdef void   glBlendFunc (cgl.GLenum sfactor, cgl.GLenum dfactor)
cdef void   glBlendFuncSeparate (cgl.GLenum srcRGB, cgl.GLenum dstRGB, cgl.GLenum srcAlpha, cgl.GLenum dstAlpha)
cdef void   glBufferData (cgl.GLenum target, cgl.GLsizeiptr size,  cgl.GLvoid* data, cgl.GLenum usage)
cdef void   glBufferSubData (cgl.GLenum target, cgl.GLintptr offset, cgl.GLsizeiptr size,  cgl.GLvoid* data)
cdef cgl.GLenum glCheckFramebufferStatus (cgl.GLenum target)
cdef void   glClear (cgl.GLbitfield mask)
cdef void   glClearColor (cgl.GLclampf red, cgl.GLclampf green, cgl.GLclampf blue, cgl.GLclampf alpha)
cdef void   glClearDepthf (cgl.GLclampf depth)
cdef void   glClearStencil (cgl.GLint s)
cdef void   glColorMask (cgl.GLboolean red, cgl.GLboolean green, cgl.GLboolean blue, cgl.GLboolean alpha)
cdef void   glCompileShader (cgl.GLuint shader)
cdef void   glCompressedTexImage2D (cgl.GLenum target, cgl.GLint level, cgl.GLenum internalformat, cgl.GLsizei width, cgl.GLsizei height, cgl.GLint border, cgl.GLsizei imageSize,  cgl.GLvoid* data)
cdef void   glCompressedTexSubImage2D (cgl.GLenum target, cgl.GLint level, cgl.GLint xoffset, cgl.GLint yoffset, cgl.GLsizei width, cgl.GLsizei height, cgl.GLenum format, cgl.GLsizei imageSize,  cgl.GLvoid* data)
cdef void   glCopyTexImage2D (cgl.GLenum target, cgl.GLint level, cgl.GLenum internalformat, cgl.GLint x, cgl.GLint y, cgl.GLsizei width, cgl.GLsizei height, cgl.GLint border)
cdef void   glCopyTexSubImage2D (cgl.GLenum target, cgl.GLint level, cgl.GLint xoffset, cgl.GLint yoffset, cgl.GLint x, cgl.GLint y, cgl.GLsizei width, cgl.GLsizei height)
cdef cgl.GLuint glCreateProgram ()
cdef cgl.GLuint glCreateShader (cgl.GLenum type)
cdef void   glCullFace (cgl.GLenum mode)
cdef void   glDeleteBuffers (cgl.GLsizei n,  cgl.GLuint* buffers)
cdef void   glDeleteFramebuffers (cgl.GLsizei n,  cgl.GLuint* framebuffers)
cdef void   glDeleteProgram (cgl.GLuint program)
cdef void   glDeleteRenderbuffers (cgl.GLsizei n,  cgl.GLuint* renderbuffers)
cdef void   glDeleteShader (cgl.GLuint shader)
cdef void   glDeleteTextures (cgl.GLsizei n,  cgl.GLuint* textures)
cdef void   glDepthFunc (cgl.GLenum func)
cdef void   glDepthMask (cgl.GLboolean flag)
cdef void   glDepthRangef (cgl.GLclampf zNear, cgl.GLclampf zFar)
cdef void   glDetachShader (cgl.GLuint program, cgl.GLuint shader)
cdef void   glDisable (cgl.GLenum cap)
cdef void   glDisableVertexAttribArray (cgl.GLuint index)
cdef void   glDrawArrays (cgl.GLenum mode, cgl.GLint first, cgl.GLsizei count)
cdef void   glDrawElements (cgl.GLenum mode, cgl.GLsizei count, cgl.GLenum type,  cgl.GLvoid* indices)
cdef void   glEnable (cgl.GLenum cap)
cdef void   glEnableVertexAttribArray (cgl.GLuint index)
cdef void   glFinish ()
cdef void   glFlush ()
cdef void   glFramebufferRenderbuffer (cgl.GLenum target, cgl.GLenum attachment, cgl.GLenum renderbuffertarget, cgl.GLuint renderbuffer)
cdef void   glFramebufferTexture2D (cgl.GLenum target, cgl.GLenum attachment, cgl.GLenum textarget, cgl.GLuint texture, cgl.GLint level)
cdef void   glFrontFace (cgl.GLenum mode)
cdef void   glGenBuffers (cgl.GLsizei n, cgl.GLuint* buffers)
cdef void   glGenerateMipmap (cgl.GLenum target)
cdef void   glGenFramebuffers (cgl.GLsizei n, cgl.GLuint* framebuffers)
cdef void   glGenRenderbuffers (cgl.GLsizei n, cgl.GLuint* renderbuffers)
cdef void   glGenTextures (cgl.GLsizei n, cgl.GLuint* textures)
cdef void   glGetActiveAttrib (cgl.GLuint program, cgl.GLuint index, cgl.GLsizei bufsize, cgl.GLsizei* length, cgl.GLint* size, cgl.GLenum* type, cgl.GLchar* name)
cdef void   glGetActiveUniform (cgl.GLuint program, cgl.GLuint index, cgl.GLsizei bufsize, cgl.GLsizei* length, cgl.GLint* size, cgl.GLenum* type, cgl.GLchar* name)
cdef void   glGetAttachedShaders (cgl.GLuint program, cgl.GLsizei maxcount, cgl.GLsizei* count, cgl.GLuint* shaders)
cdef int    glGetAttribLocation (cgl.GLuint program,  cgl.GLchar* name)
cdef void   glGetBooleanv (cgl.GLenum pname, cgl.GLboolean* params)
cdef void   glGetBufferParameteriv (cgl.GLenum target, cgl.GLenum pname, cgl.GLint* params)
cdef cgl.GLenum glGetError ()
cdef void   glGetFloatv (cgl.GLenum pname, cgl.GLfloat* params)
cdef void   glGetFramebufferAttachmentParameteriv (cgl.GLenum target, cgl.GLenum attachment, cgl.GLenum pname, cgl.GLint* params)
cdef void   glGetIntegerv (cgl.GLenum pname, cgl.GLint* params)
cdef void   glGetProgramiv (cgl.GLuint program, cgl.GLenum pname, cgl.GLint* params)
cdef void   glGetProgramInfoLog (cgl.GLuint program, cgl.GLsizei bufsize, cgl.GLsizei* length, cgl.GLchar* infolog)
cdef void   glGetRenderbufferParameteriv (cgl.GLenum target, cgl.GLenum pname, cgl.GLint* params)
cdef void   glGetShaderiv (cgl.GLuint shader, cgl.GLenum pname, cgl.GLint* params)
cdef void   glGetShaderInfoLog (cgl.GLuint shader, cgl.GLsizei bufsize, cgl.GLsizei* length, cgl.GLchar* infolog)
#cdef void   glGetShaderPrecisionFormat (cgl.GLenum shadertype, cgl.GLenum precisiontype, cgl.GLint* range, cgl.GLint* precision)
cdef void   glGetShaderSource (cgl.GLuint shader, cgl.GLsizei bufsize, cgl.GLsizei* length, cgl.GLchar* source)
cdef   cgl.GLubyte*  glGetString (cgl.GLenum name)
cdef void   glGetTexParameterfv (cgl.GLenum target, cgl.GLenum pname, cgl.GLfloat* params)
cdef void   glGetTexParameteriv (cgl.GLenum target, cgl.GLenum pname, cgl.GLint* params)
cdef void   glGetUniformfv (cgl.GLuint program, cgl.GLint location, cgl.GLfloat* params)
cdef void   glGetUniformiv (cgl.GLuint program, cgl.GLint location, cgl.GLint* params)
cdef int    glGetUniformLocation (cgl.GLuint program,  cgl.GLchar* name)
cdef void   glGetVertexAttribfv (cgl.GLuint index, cgl.GLenum pname, cgl.GLfloat* params)
cdef void   glGetVertexAttribiv (cgl.GLuint index, cgl.GLenum pname, cgl.GLint* params)
cdef void   glGetVertexAttribPointerv (cgl.GLuint index, cgl.GLenum pname, cgl.GLvoid** pointer)
cdef void   glHint (cgl.GLenum target, cgl.GLenum mode)
cdef cgl.GLboolean  glIsBuffer (cgl.GLuint buffer)
cdef cgl.GLboolean  glIsEnabled (cgl.GLenum cap)
cdef cgl.GLboolean  glIsFramebuffer (cgl.GLuint framebuffer)
cdef cgl.GLboolean  glIsProgram (cgl.GLuint program)
cdef cgl.GLboolean  glIsRenderbuffer (cgl.GLuint renderbuffer)
cdef cgl.GLboolean  glIsShader (cgl.GLuint shader)
cdef cgl.GLboolean  glIsTexture (cgl.GLuint texture)
cdef void  glLineWidth (cgl.GLfloat width)
cdef void  glLinkProgram (cgl.GLuint program)
cdef void  glPixelStorei (cgl.GLenum pname, cgl.GLint param)
cdef void  glPolygonOffset (cgl.GLfloat factor, cgl.GLfloat units)
cdef void  glReadPixels (cgl.GLint x, cgl.GLint y, cgl.GLsizei width, cgl.GLsizei height, cgl.GLenum format, cgl.GLenum type, cgl.GLvoid* pixels)
#cdef void  glReleaseShaderCompiler ()
cdef void  glRenderbufferStorage (cgl.GLenum target, cgl.GLenum internalformat, cgl.GLsizei width, cgl.GLsizei height)
cdef void  glSampleCoverage (cgl.GLclampf value, cgl.GLboolean invert)
cdef void  glScissor (cgl.GLint x, cgl.GLint y, cgl.GLsizei width, cgl.GLsizei height)
#cdef void  glShaderBinary (cgl.GLsizei n,  cgl.GLuint* shaders, cgl.GLenum binaryformat,  cgl.GLvoid* binary, cgl.GLsizei length)
cdef void  glShaderSource (cgl.GLuint shader, cgl.GLsizei count,  cgl.GLchar** string,  cgl.GLint* length)
cdef void  glStencilFunc (cgl.GLenum func, cgl.GLint ref, cgl.GLuint mask)
cdef void  glStencilFuncSeparate (cgl.GLenum face, cgl.GLenum func, cgl.GLint ref, cgl.GLuint mask)
cdef void  glStencilMask (cgl.GLuint mask)
cdef void  glStencilMaskSeparate (cgl.GLenum face, cgl.GLuint mask)
cdef void  glStencilOp (cgl.GLenum fail, cgl.GLenum zfail, cgl.GLenum zpass)
cdef void  glStencilOpSeparate (cgl.GLenum face, cgl.GLenum fail, cgl.GLenum zfail, cgl.GLenum zpass)
cdef void  glTexImage2D (cgl.GLenum target, cgl.GLint level, cgl.GLint internalformat, cgl.GLsizei width, cgl.GLsizei height, cgl.GLint border, cgl.GLenum format, cgl.GLenum type,  cgl.GLvoid* pixels)
cdef void  glTexParameterf (cgl.GLenum target, cgl.GLenum pname, cgl.GLfloat param)
cdef void  glTexParameterfv (cgl.GLenum target, cgl.GLenum pname,  cgl.GLfloat* params)
cdef void  glTexParameteri (cgl.GLenum target, cgl.GLenum pname, cgl.GLint param)
cdef void  glTexParameteriv (cgl.GLenum target, cgl.GLenum pname,  cgl.GLint* params)
cdef void  glTexSubImage2D (cgl.GLenum target, cgl.GLint level, cgl.GLint xoffset, cgl.GLint yoffset, cgl.GLsizei width, cgl.GLsizei height, cgl.GLenum format, cgl.GLenum type,  cgl.GLvoid* pixels)
cdef void  glUniform1f (cgl.GLint location, cgl.GLfloat x)
cdef void  glUniform1fv (cgl.GLint location, cgl.GLsizei count,  cgl.GLfloat* v)
cdef void  glUniform1i (cgl.GLint location, cgl.GLint x)
cdef void  glUniform1iv (cgl.GLint location, cgl.GLsizei count,  cgl.GLint* v)
cdef void  glUniform2f (cgl.GLint location, cgl.GLfloat x, cgl.GLfloat y)
cdef void  glUniform2fv (cgl.GLint location, cgl.GLsizei count,  cgl.GLfloat* v)
cdef void  glUniform2i (cgl.GLint location, cgl.GLint x, cgl.GLint y)
cdef void  glUniform2iv (cgl.GLint location, cgl.GLsizei count,  cgl.GLint* v)
cdef void  glUniform3f (cgl.GLint location, cgl.GLfloat x, cgl.GLfloat y, cgl.GLfloat z)
cdef void  glUniform3fv (cgl.GLint location, cgl.GLsizei count,  cgl.GLfloat* v)
cdef void  glUniform3i (cgl.GLint location, cgl.GLint x, cgl.GLint y, cgl.GLint z)
cdef void  glUniform3iv (cgl.GLint location, cgl.GLsizei count,  cgl.GLint* v)
cdef void  glUniform4f (cgl.GLint location, cgl.GLfloat x, cgl.GLfloat y, cgl.GLfloat z, cgl.GLfloat w)
cdef void  glUniform4fv (cgl.GLint location, cgl.GLsizei count,  cgl.GLfloat* v)
cdef void  glUniform4i (cgl.GLint location, cgl.GLint x, cgl.GLint y, cgl.GLint z, cgl.GLint w)
cdef void  glUniform4iv (cgl.GLint location, cgl.GLsizei count,  cgl.GLint* v)
cdef void  glUniformMatrix2fv (cgl.GLint location, cgl.GLsizei count, cgl.GLboolean transpose,  cgl.GLfloat* value)
cdef void  glUniformMatrix3fv (cgl.GLint location, cgl.GLsizei count, cgl.GLboolean transpose,  cgl.GLfloat* value)
cdef void  glUniformMatrix4fv (cgl.GLint location, cgl.GLsizei count, cgl.GLboolean transpose,  cgl.GLfloat* value)
cdef void  glUseProgram (cgl.GLuint program)
cdef void  glValidateProgram (cgl.GLuint program)
cdef void  glVertexAttrib1f (cgl.GLuint indx, cgl.GLfloat x)
cdef void  glVertexAttrib1fv (cgl.GLuint indx,  cgl.GLfloat* values)
cdef void  glVertexAttrib2f (cgl.GLuint indx, cgl.GLfloat x, cgl.GLfloat y)
cdef void  glVertexAttrib2fv (cgl.GLuint indx,  cgl.GLfloat* values)
cdef void  glVertexAttrib3f (cgl.GLuint indx, cgl.GLfloat x, cgl.GLfloat y, cgl.GLfloat z)
cdef void  glVertexAttrib3fv (cgl.GLuint indx,  cgl.GLfloat* values)
cdef void  glVertexAttrib4f (cgl.GLuint indx, cgl.GLfloat x, cgl.GLfloat y, cgl.GLfloat z, cgl.GLfloat w)
cdef void  glVertexAttrib4fv (cgl.GLuint indx,  cgl.GLfloat* values)
cdef void  glVertexAttribPointer (cgl.GLuint indx, cgl.GLint size, cgl.GLenum type, cgl.GLboolean normalized, cgl.GLsizei stride,  cgl.GLvoid* ptr)
cdef void  glViewport (cgl.GLint x, cgl.GLint y, cgl.GLsizei width, cgl.GLsizei height)'''

def replace(s):
    item = s.split(' ')
    rettype = item[1]
    item = item[2:]
    for x in item:
        x = x.strip()
        if not x or x.startswith('GL'):
            continue
        if x.startswith('(GL'):
            yield '('
            continue
        if x.startswith('gl'):
            prefix = ''
            if rettype != 'void':
                prefix = 'return '
            yield '%scgl.%s' % (prefix, x)
            continue
        yield x

print('''
# This file was automatically generated with kivy/tools/stub-gl-debug.py
cimport c_opengl as cgl

''')

lines = a.splitlines()
for x in lines:
    if x.startswith('#'):
        # There are some functions that either do not exist or break on OSX.
        # Just skip those.
        print('# Skipping generation of: "%s"' % x)
        continue
    x = x.replace('cgl.', '')
    y = ' '.join(replace(x))

    print('%s with gil:' % x)
    s = x.split()
    print('    print "GL %s(' % s[2], end=' ')
    pointer = 0
    for arg in s[3:]:
        arg = arg.strip()
        arg = arg.replace(',', '').replace(')', '')
        if 'GL' in arg or arg == '(':
            pointer = arg.count('*')
            continue
        pointer = '*' * pointer
        if pointer:
            print('%s%s=", repr(hex(<long> %s)), ",' % (arg, pointer, arg), end=' ')
        else:
            print('%s = ", %s, ",' % (arg, arg), end=' ')
        pointer = 0
    print(')"')
    print('    %s' % y)
    print('    ret = glGetError()')
    print('    if ret: print("ERR {} / {}".format(ret, ret))')
