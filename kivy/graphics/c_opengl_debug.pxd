ctypedef void               GLvoid
ctypedef char               GLchar
ctypedef unsigned int       GLenum
ctypedef unsigned char      GLboolean
ctypedef unsigned int       GLbitfield
ctypedef short              GLshort
ctypedef int                GLint
ctypedef int                GLsizei
ctypedef unsigned short     GLushort
ctypedef unsigned int       GLuint
ctypedef signed char        GLbyte
ctypedef unsigned char      GLubyte
ctypedef float              GLfloat
ctypedef float              GLclampf
ctypedef int                GLfixed
ctypedef signed long int    GLintptr
ctypedef signed long int    GLsizeiptr

cdef void   glActiveTexture (GLenum texture) with gil
cdef void   glAttachShader (GLuint program, GLuint shader) with gil
cdef void   glBindAttribLocation (GLuint program, GLuint index,  GLchar* name) with gil
cdef void   glBindBuffer (GLenum target, GLuint buffer) with gil
cdef void   glBindFramebuffer (GLenum target, GLuint framebuffer) with gil
cdef void   glBindRenderbuffer (GLenum target, GLuint renderbuffer) with gil
cdef void   glBindTexture (GLenum target, GLuint texture) with gil
cdef void   glBlendColor (GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha) with gil
cdef void   glBlendEquation ( GLenum mode ) with gil
cdef void   glBlendEquationSeparate (GLenum modeRGB, GLenum modeAlpha) with gil
cdef void   glBlendFunc (GLenum sfactor, GLenum dfactor) with gil
cdef void   glBlendFuncSeparate (GLenum srcRGB, GLenum dstRGB, GLenum srcAlpha, GLenum dstAlpha) with gil
cdef void   glBufferData (GLenum target, GLsizeiptr size,  GLvoid* data, GLenum usage) with gil
cdef void   glBufferSubData (GLenum target, GLintptr offset, GLsizeiptr size,  GLvoid* data) with gil
cdef GLenum glCheckFramebufferStatus (GLenum target) with gil
cdef void   glClear (GLbitfield mask) with gil
cdef void   glClearColor (GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha) with gil
# crash on android platform
#cdef void   glClearDepthf (GLclampf depth) with gil
cdef void   glClearStencil (GLint s) with gil
cdef void   glColorMask (GLboolean red, GLboolean green, GLboolean blue, GLboolean alpha) with gil
cdef void   glCompileShader (GLuint shader) with gil
cdef void   glCompressedTexImage2D (GLenum target, GLint level, GLenum internalformat, GLsizei width, GLsizei height, GLint border, GLsizei imageSize,  GLvoid* data) with gil
cdef void   glCompressedTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLsizei imageSize,  GLvoid* data) with gil
cdef void   glCopyTexImage2D (GLenum target, GLint level, GLenum internalformat, GLint x, GLint y, GLsizei width, GLsizei height, GLint border) with gil
cdef void   glCopyTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLint x, GLint y, GLsizei width, GLsizei height) with gil
cdef GLuint glCreateProgram () with gil
cdef GLuint glCreateShader (GLenum type) with gil
cdef void   glCullFace (GLenum mode) with gil
cdef void   glDeleteBuffers (GLsizei n,  GLuint* buffers) with gil
cdef void   glDeleteFramebuffers (GLsizei n,  GLuint* framebuffers) with gil
cdef void   glDeleteProgram (GLuint program) with gil
cdef void   glDeleteRenderbuffers (GLsizei n,  GLuint* renderbuffers) with gil
cdef void   glDeleteShader (GLuint shader) with gil
cdef void   glDeleteTextures (GLsizei n,  GLuint* textures) with gil
cdef void   glDepthFunc (GLenum func) with gil
cdef void   glDepthMask (GLboolean flag) with gil
# crash on android platform
#cdef void   glDepthRangef (GLclampf zNear, GLclampf zFar) with gil
cdef void   glDetachShader (GLuint program, GLuint shader) with gil
cdef void   glDisable (GLenum cap) with gil
cdef void   glDisableVertexAttribArray (GLuint index) with gil
cdef void   glDrawArrays (GLenum mode, GLint first, GLsizei count) with gil
cdef void   glDrawElements (GLenum mode, GLsizei count, GLenum type,  GLvoid* indices) with gil
cdef void   glEnable (GLenum cap) with gil
cdef void   glEnableVertexAttribArray (GLuint index) with gil
cdef void   glFinish () with gil
cdef void   glFlush () with gil
cdef void   glFramebufferRenderbuffer (GLenum target, GLenum attachment, GLenum renderbuffertarget, GLuint renderbuffer) with gil
cdef void   glFramebufferTexture2D (GLenum target, GLenum attachment, GLenum textarget, GLuint texture, GLint level) with gil
cdef void   glFrontFace (GLenum mode) with gil
cdef void   glGenBuffers (GLsizei n, GLuint* buffers) with gil
cdef void   glGenerateMipmap (GLenum target) with gil
cdef void   glGenFramebuffers (GLsizei n, GLuint* framebuffers) with gil
cdef void   glGenRenderbuffers (GLsizei n, GLuint* renderbuffers) with gil
cdef void   glGenTextures (GLsizei n, GLuint* textures) with gil
cdef void   glGetActiveAttrib (GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name) with gil
cdef void   glGetActiveUniform (GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name) with gil
cdef void   glGetAttachedShaders (GLuint program, GLsizei maxcount, GLsizei* count, GLuint* shaders) with gil
cdef int    glGetAttribLocation (GLuint program,  GLchar* name) with gil
cdef void   glGetBooleanv (GLenum pname, GLboolean* params) with gil
cdef void   glGetBufferParameteriv (GLenum target, GLenum pname, GLint* params) with gil
cdef GLenum glGetError () with gil
cdef void   glGetFloatv (GLenum pname, GLfloat* params) with gil
cdef void   glGetFramebufferAttachmentParameteriv (GLenum target, GLenum attachment, GLenum pname, GLint* params) with gil
cdef void   glGetIntegerv (GLenum pname, GLint* params) with gil
cdef void   glGetProgramiv (GLuint program, GLenum pname, GLint* params) with gil
cdef void   glGetProgramInfoLog (GLuint program, GLsizei bufsize, GLsizei* length, GLchar* infolog) with gil
cdef void   glGetRenderbufferParameteriv (GLenum target, GLenum pname, GLint* params) with gil
cdef void   glGetShaderiv (GLuint shader, GLenum pname, GLint* params) with gil
cdef void   glGetShaderInfoLog (GLuint shader, GLsizei bufsize, GLsizei* length, GLchar* infolog) with gil
#cdef void   glGetShaderPrecisionFormat (GLenum shadertype, GLenum precisiontype, GLint* range, GLint* precision) with gil
cdef void   glGetShaderSource (GLuint shader, GLsizei bufsize, GLsizei* length, GLchar* source) with gil
cdef   GLubyte*  glGetString (GLenum name) with gil
cdef void   glGetTexParameterfv (GLenum target, GLenum pname, GLfloat* params) with gil
cdef void   glGetTexParameteriv (GLenum target, GLenum pname, GLint* params) with gil
cdef void   glGetUniformfv (GLuint program, GLint location, GLfloat* params) with gil
cdef void   glGetUniformiv (GLuint program, GLint location, GLint* params) with gil
cdef int    glGetUniformLocation (GLuint program,  GLchar* name) with gil
cdef void   glGetVertexAttribfv (GLuint index, GLenum pname, GLfloat* params) with gil
cdef void   glGetVertexAttribiv (GLuint index, GLenum pname, GLint* params) with gil
cdef void   glGetVertexAttribPointerv (GLuint index, GLenum pname, GLvoid** pointer) with gil
cdef void   glHint (GLenum target, GLenum mode) with gil
cdef GLboolean  glIsBuffer (GLuint buffer) with gil
cdef GLboolean  glIsEnabled (GLenum cap) with gil
cdef GLboolean  glIsFramebuffer (GLuint framebuffer) with gil
cdef GLboolean  glIsProgram (GLuint program) with gil
cdef GLboolean  glIsRenderbuffer (GLuint renderbuffer) with gil
cdef GLboolean  glIsShader (GLuint shader) with gil
cdef GLboolean  glIsTexture (GLuint texture) with gil
cdef void  glLineWidth (GLfloat width) with gil
cdef void  glLinkProgram (GLuint program) with gil
cdef void  glPixelStorei (GLenum pname, GLint param) with gil
cdef void  glPolygonOffset (GLfloat factor, GLfloat units) with gil
cdef void  glReadPixels (GLint x, GLint y, GLsizei width, GLsizei height, GLenum format, GLenum type, GLvoid* pixels) with gil
# XXX This one is commented out because a) it's not necessary and
#	    				b) it's breaking on OSX for some reason
#cdef void  glReleaseShaderCompiler () with gil
cdef void  glRenderbufferStorage (GLenum target, GLenum internalformat, GLsizei width, GLsizei height) with gil
cdef void  glSampleCoverage (GLclampf value, GLboolean invert) with gil
cdef void  glScissor (GLint x, GLint y, GLsizei width, GLsizei height) with gil
#cdef void  glShaderBinary (GLsizei n,  GLuint* shaders, GLenum binaryformat,  GLvoid* binary, GLsizei length) with gil
cdef void  glShaderSource (GLuint shader, GLsizei count,  GLchar** string,  GLint* length) with gil
cdef void  glStencilFunc (GLenum func, GLint ref, GLuint mask) with gil
cdef void  glStencilFuncSeparate (GLenum face, GLenum func, GLint ref, GLuint mask) with gil
cdef void  glStencilMask (GLuint mask) with gil
cdef void  glStencilMaskSeparate (GLenum face, GLuint mask) with gil
cdef void  glStencilOp (GLenum fail, GLenum zfail, GLenum zpass) with gil
cdef void  glStencilOpSeparate (GLenum face, GLenum fail, GLenum zfail, GLenum zpass) with gil
cdef void  glTexImage2D (GLenum target, GLint level, GLint internalformat, GLsizei width, GLsizei height, GLint border, GLenum format, GLenum type,  GLvoid* pixels) with gil
cdef void  glTexParameterf (GLenum target, GLenum pname, GLfloat param) with gil
cdef void  glTexParameterfv (GLenum target, GLenum pname,  GLfloat* params) with gil
cdef void  glTexParameteri (GLenum target, GLenum pname, GLint param) with gil
cdef void  glTexParameteriv (GLenum target, GLenum pname,  GLint* params) with gil
cdef void  glTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLenum type,  GLvoid* pixels) with gil
cdef void  glUniform1f (GLint location, GLfloat x) with gil
cdef void  glUniform1fv (GLint location, GLsizei count,  GLfloat* v) with gil
cdef void  glUniform1i (GLint location, GLint x) with gil
cdef void  glUniform1iv (GLint location, GLsizei count,  GLint* v) with gil
cdef void  glUniform2f (GLint location, GLfloat x, GLfloat y) with gil
cdef void  glUniform2fv (GLint location, GLsizei count,  GLfloat* v) with gil
cdef void  glUniform2i (GLint location, GLint x, GLint y) with gil
cdef void  glUniform2iv (GLint location, GLsizei count,  GLint* v) with gil
cdef void  glUniform3f (GLint location, GLfloat x, GLfloat y, GLfloat z) with gil
cdef void  glUniform3fv (GLint location, GLsizei count,  GLfloat* v) with gil
cdef void  glUniform3i (GLint location, GLint x, GLint y, GLint z) with gil
cdef void  glUniform3iv (GLint location, GLsizei count,  GLint* v) with gil
cdef void  glUniform4f (GLint location, GLfloat x, GLfloat y, GLfloat z, GLfloat w) with gil
cdef void  glUniform4fv (GLint location, GLsizei count,  GLfloat* v) with gil
cdef void  glUniform4i (GLint location, GLint x, GLint y, GLint z, GLint w) with gil
cdef void  glUniform4iv (GLint location, GLsizei count,  GLint* v) with gil
cdef void  glUniformMatrix2fv (GLint location, GLsizei count, GLboolean transpose,  GLfloat* value) with gil
cdef void  glUniformMatrix3fv (GLint location, GLsizei count, GLboolean transpose,  GLfloat* value) with gil
cdef void  glUniformMatrix4fv (GLint location, GLsizei count, GLboolean transpose,  GLfloat* value) with gil
cdef void  glUseProgram (GLuint program) with gil
cdef void  glValidateProgram (GLuint program) with gil
cdef void  glVertexAttrib1f (GLuint indx, GLfloat x) with gil
cdef void  glVertexAttrib1fv (GLuint indx,  GLfloat* values) with gil
cdef void  glVertexAttrib2f (GLuint indx, GLfloat x, GLfloat y) with gil
cdef void  glVertexAttrib2fv (GLuint indx,  GLfloat* values) with gil
cdef void  glVertexAttrib3f (GLuint indx, GLfloat x, GLfloat y, GLfloat z) with gil
cdef void  glVertexAttrib3fv (GLuint indx,  GLfloat* values) with gil
cdef void  glVertexAttrib4f (GLuint indx, GLfloat x, GLfloat y, GLfloat z, GLfloat w) with gil
cdef void  glVertexAttrib4fv (GLuint indx,  GLfloat* values) with gil
cdef void  glVertexAttribPointer (GLuint indx, GLint size, GLenum type, GLboolean normalized, GLsizei stride,  GLvoid* ptr) with gil
cdef void  glViewport (GLint x, GLint y, GLsizei width, GLsizei height) with gil
