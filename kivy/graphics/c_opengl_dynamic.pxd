include "common.pxi"
include "config.pxi"

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

ctypedef const GLubyte* (__stdcall *GLGETSTRINGPTR)(GLenum) nogil
ctypedef GLboolean (__stdcall *GLISBUFFERPTR)(GLuint buffer) nogil
ctypedef GLboolean (__stdcall *GLISENABLEDPTR)(GLenum cap) nogil
ctypedef GLboolean (__stdcall *GLISFRAMEBUFFERPTR)(GLuint framebuffer) nogil
ctypedef GLboolean (__stdcall *GLISPROGRAMPTR)(GLuint program) nogil
ctypedef GLboolean (__stdcall *GLISRENDERBUFFERPTR)(GLuint renderbuffer) nogil
ctypedef GLboolean (__stdcall *GLISSHADERPTR)(GLuint shader) nogil
ctypedef GLboolean (__stdcall *GLISTEXTUREPTR)(GLuint texture) nogil
ctypedef GLenum (__stdcall *GLCHECKFRAMEBUFFERSTATUSPTR)(GLenum) nogil
ctypedef GLenum (__stdcall *GLGETERRORPTR)() nogil
ctypedef GLint (__stdcall *GLGETATTRIBLOCATIONPTR)(GLuint, const GLchar *) nogil
ctypedef GLint (__stdcall *GLGETUNIFORMLOCATIONPTR)(GLuint, const char *) nogil
ctypedef GLuint (__stdcall *GLCREATEPROGRAMPTR)() nogil
ctypedef GLuint (__stdcall *GLCREATESHADERPTR)(GLenum) nogil
ctypedef void (__stdcall *GLACTIVETEXTUREPTR)(GLenum) nogil
ctypedef void (__stdcall *GLATTACHSHADERPTR)(GLuint, GLuint) nogil
ctypedef void (__stdcall *GLBINDATTRIBLOCATIONPTR)(GLuint, GLuint, const char *) nogil
ctypedef void (__stdcall *GLBINDBUFFERPTR)(GLenum, GLuint) nogil
ctypedef void (__stdcall *GLBINDFRAMEBUFFERPTR)(GLenum, GLuint) nogil
ctypedef void (__stdcall *GLBINDRENDERBUFFERPTR)(GLenum target, GLuint renderbuffer) nogil
ctypedef void (__stdcall *GLBINDTEXTUREPTR)(GLenum, GLuint) nogil
ctypedef void (__stdcall *GLBLENDCOLORPTR)(GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha) nogil
ctypedef void (__stdcall *GLBLENDEQUATIONPTR)( GLenum mode ) nogil
ctypedef void (__stdcall *GLBLENDEQUATIONSEPARATEPTR)(GLenum modeRGB, GLenum modeAlpha) nogil
ctypedef void (__stdcall *GLBLENDFUNCPTR)(GLenum sfactor, GLenum dfactor) nogil
ctypedef void (__stdcall *GLBLENDFUNCSEPARATEPTR)(GLenum, GLenum, GLenum, GLenum) nogil
ctypedef void (__stdcall *GLBUFFERDATAPTR)(GLenum, GLsizeiptr, const GLvoid *, GLenum) nogil
ctypedef void (__stdcall *GLBUFFERSUBDATAPTR)(GLenum, GLintptr, GLsizeiptr, const GLvoid *) nogil
ctypedef void (__stdcall *GLCLEARCOLORPTR)(GLclampf, GLclampf, GLclampf, GLclampf) nogil
ctypedef void (__stdcall *GLCLEARPTR)(GLbitfield) nogil
ctypedef void (__stdcall *GLCLEARSTENCILPTR)(GLint s) nogil
ctypedef void (__stdcall *GLCOLORMASKPTR)(GLboolean red, GLboolean green, GLboolean blue, GLboolean alpha) nogil
ctypedef void (__stdcall *GLCOMPILESHADERPTR)(GLuint) nogil
ctypedef void (__stdcall *GLCOMPRESSEDTEXIMAGE2DPTR)(GLenum target, GLint level, GLenum internalformat, GLsizei width, GLsizei height, GLint border, GLsizei imageSize, const GLvoid* data) nogil
ctypedef void (__stdcall *GLCOMPRESSEDTEXSUBIMAGE2DPTR)(GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLsizei imageSize, const GLvoid* data) nogil
ctypedef void (__stdcall *GLCOPYTEXIMAGE2DPTR)(GLenum target, GLint level, GLenum internalformat, GLint x, GLint y, GLsizei width, GLsizei height, GLint border) nogil
ctypedef void (__stdcall *GLCOPYTEXSUBIMAGE2DPTR)(GLenum target, GLint level, GLint xoffset, GLint yoffset, GLint x, GLint y, GLsizei width, GLsizei height) nogil
ctypedef void (__stdcall *GLCULLFACEPTR)(GLenum mode) nogil
ctypedef void (__stdcall *GLDELETEBUFFERSPTR)(GLsizei n, const GLuint* buffers) nogil
ctypedef void (__stdcall *GLDELETEFRAMEBUFFERSPTR)(GLsizei, const GLuint *) nogil
ctypedef void (__stdcall *GLDELETEPROGRAMPTR)(GLuint) nogil
ctypedef void (__stdcall *GLDELETERENDERBUFFERSPTR)(GLsizei n, const GLuint* renderbuffers) nogil
ctypedef void (__stdcall *GLDELETESHADERPTR)(GLuint) nogil
ctypedef void (__stdcall *GLDELETETEXTURESPTR)(GLsizei, const GLuint *) nogil
ctypedef void (__stdcall *GLDEPTHFUNCPTR)(GLenum func) nogil
ctypedef void (__stdcall *GLDEPTHMASKPTR)(GLboolean flag) nogil
ctypedef void (__stdcall *GLDETACHSHADERPTR)(GLuint program, GLuint shader) nogil
ctypedef void (__stdcall *GLDISABLEPTR)(GLenum) nogil
ctypedef void (__stdcall *GLDISABLEVERTEXATTRIBARRAYPTR)(GLuint) nogil
ctypedef void (__stdcall *GLDRAWARRAYSPTR)(GLenum, GLint, GLsizei) nogil
ctypedef void (__stdcall *GLDRAWELEMENTSPTR)(GLenum mode, GLsizei count, GLenum type, const GLvoid* indices) nogil
ctypedef void (__stdcall *GLENABLEPTR)(GLenum) nogil
ctypedef void (__stdcall *GLENABLEVERTEXATTRIBARRAYPTR)(GLuint) nogil
ctypedef void (__stdcall *GLFINISHPTR)() nogil
ctypedef void (__stdcall *GLFLUSHPTR)() nogil
ctypedef void (__stdcall *GLFRAMEBUFFERRENDERBUFFERPTR)(GLenum target, GLenum attachment, GLenum renderbuffertarget, GLuint renderbuffer) nogil
ctypedef void (__stdcall *GLFRAMEBUFFERTEXTURE2DPTR)(GLenum, GLenum, GLenum, GLuint, GLint) nogil
ctypedef void (__stdcall *GLFRONTFACEPTR)(GLenum mode) nogil
ctypedef void (__stdcall *GLGENBUFFERSPTR)(GLsizei, GLuint *) nogil
ctypedef void (__stdcall *GLGENERATEMIPMAPPTR)(GLenum target) nogil
ctypedef void (__stdcall *GLGENFRAMEBUFFERSPTR)(GLsizei, GLuint *) nogil
ctypedef void (__stdcall *GLGENRENDERBUFFERSPTR)(GLsizei n, GLuint* renderbuffers) nogil
ctypedef void (__stdcall *GLGENTEXTURESPTR)(GLsizei, GLuint *) nogil
ctypedef void (__stdcall *GLGETACTIVEATTRIBPTR)(GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name) nogil
ctypedef void (__stdcall *GLGETACTIVEUNIFORMPTR)(GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name) nogil
ctypedef void (__stdcall *GLGETATTACHEDSHADERSPTR)(GLuint program, GLsizei maxcount, GLsizei* count, GLuint* shaders) nogil
ctypedef void (__stdcall *GLGETBOOLEANVPTR)(GLenum, GLboolean *) nogil
ctypedef void (__stdcall *GLGETBUFFERPARAMETERIVPTR)(GLenum target, GLenum pname, GLint* params) nogil
ctypedef void (__stdcall *GLGETFLOATVPTR)(GLenum pname, GLfloat* params) nogil
ctypedef void (__stdcall *GLGETFRAMEBUFFERATTACHMENTPARAMETERIVPTR)(GLenum target, GLenum attachment, GLenum pname, GLint* params) nogil
ctypedef void (__stdcall *GLGETINTEGERVPTR)(GLenum, GLint *) nogil
ctypedef void (__stdcall *GLGETPROGRAMINFOLOGPTR)(GLuint, GLsizei, GLsizei*, GLchar*) nogil
ctypedef void (__stdcall *GLGETPROGRAMIVPTR)(GLuint, GLenum, GLint *) nogil
ctypedef void (__stdcall *GLGETRENDERBUFFERPARAMETERIVPTR)(GLenum target, GLenum pname, GLint* params) nogil
ctypedef void (__stdcall *GLGETSHADERINFOLOGPTR)(GLuint, GLsizei, GLsizei *, char *) nogil
ctypedef void (__stdcall *GLGETSHADERIVPTR)(GLuint, GLenum, GLint *) nogil
ctypedef void (__stdcall *GLGETSHADERSOURCEPTR)(GLuint shader, GLsizei bufsize, GLsizei* length, GLchar* source) nogil
ctypedef void (__stdcall *GLGETTEXPARAMETERFVPTR)(GLenum target, GLenum pname, GLfloat* params) nogil
ctypedef void (__stdcall *GLGETTEXPARAMETERIVPTR)(GLenum target, GLenum pname, GLint* params) nogil
ctypedef void (__stdcall *GLGETUNIFORMFVPTR)(GLuint program, GLint location, GLfloat* params) nogil
ctypedef void (__stdcall *GLGETUNIFORMIVPTR)(GLuint program, GLint location, GLint* params) nogil
ctypedef void (__stdcall *GLGETVERTEXATTRIBFVPTR)(GLuint index, GLenum pname, GLfloat* params) nogil
ctypedef void (__stdcall *GLGETVERTEXATTRIBIVPTR)(GLuint index, GLenum pname, GLint* params) nogil
ctypedef void (__stdcall *GLHINTPTR)(GLenum target, GLenum mode) nogil
ctypedef void (__stdcall *GLLINEWIDTHPTR)(GLfloat width) nogil
ctypedef void (__stdcall *GLLINKPROGRAMPTR)(GLuint) nogil
ctypedef void (__stdcall *GLPIXELSTOREIPTR)(GLenum, GLint) nogil
ctypedef void (__stdcall *GLPOLYGONOFFSETPTR)(GLfloat factor, GLfloat units) nogil
ctypedef void (__stdcall *GLREADPIXELSPTR)(GLint, GLint, GLsizei, GLsizei, GLenum, GLenum, GLvoid*) nogil
ctypedef void (__stdcall *GLRENDERBUFFERSTORAGEPTR)(GLenum target, GLenum internalformat, GLsizei width, GLsizei height) nogil
ctypedef void (__stdcall *GLSAMPLECOVERAGEPTR)(GLclampf value, GLboolean invert) nogil
ctypedef void (__stdcall *GLSCISSORPTR)(GLint, GLint, GLsizei, GLsizei) nogil
ctypedef void (__stdcall *GLSHADERBINARYPTR)(GLsizei, const GLuint *, GLenum, const void *, GLsizei) nogil
ctypedef void (__stdcall *GLSHADERSOURCEPTR)(GLuint, GLsizei, const GLchar* const*, const GLint *) nogil
ctypedef void (__stdcall *GLSTENCILFUNCPTR)(GLenum func, GLint ref, GLuint mask) nogil
ctypedef void (__stdcall *GLSTENCILFUNCSEPARATEPTR)(GLenum face, GLenum func, GLint ref, GLuint mask) nogil
ctypedef void (__stdcall *GLSTENCILMASKPTR)(GLuint mask) nogil
ctypedef void (__stdcall *GLSTENCILMASKSEPARATEPTR)(GLenum face, GLuint mask) nogil
ctypedef void (__stdcall *GLSTENCILOPPTR)(GLenum fail, GLenum zfail, GLenum zpass) nogil
ctypedef void (__stdcall *GLSTENCILOPSEPARATEPTR)(GLenum face, GLenum fail, GLenum zfail, GLenum zpass) nogil
ctypedef void (__stdcall *GLTEXIMAGE2DPTR)(GLenum, GLint, GLint, GLsizei, GLsizei, GLint, GLenum, GLenum, const void *) nogil
ctypedef void (__stdcall *GLTEXPARAMETERFPTR)(GLenum target, GLenum pname, GLfloat param) nogil
ctypedef void (__stdcall *GLTEXPARAMETERIPTR)(GLenum, GLenum, GLint) nogil
ctypedef void (__stdcall *GLTEXSUBIMAGE2DPTR)(GLenum, GLint, GLint, GLint, GLsizei, GLsizei, GLenum, GLenum, const GLvoid *) nogil
ctypedef void (__stdcall *GLUNIFORM1FPTR)(GLint location, GLfloat x) nogil
ctypedef void (__stdcall *GLUNIFORM1FVPTR)(GLint location, GLsizei count, const GLfloat* v) nogil
ctypedef void (__stdcall *GLUNIFORM1IPTR)(GLint, GLint) nogil
ctypedef void (__stdcall *GLUNIFORM1IVPTR)(GLint location, GLsizei count, const GLint* v) nogil
ctypedef void (__stdcall *GLUNIFORM2FPTR)(GLint location, GLfloat x, GLfloat y) nogil
ctypedef void (__stdcall *GLUNIFORM2FVPTR)(GLint location, GLsizei count, const GLfloat* v) nogil
ctypedef void (__stdcall *GLUNIFORM2IPTR)(GLint location, GLint x, GLint y) nogil
ctypedef void (__stdcall *GLUNIFORM2IVPTR)(GLint location, GLsizei count, const GLint* v) nogil
ctypedef void (__stdcall *GLUNIFORM3FPTR)(GLint location, GLfloat x, GLfloat y, GLfloat z) nogil
ctypedef void (__stdcall *GLUNIFORM3FVPTR)(GLint location, GLsizei count, const GLfloat* v) nogil
ctypedef void (__stdcall *GLUNIFORM3IPTR)(GLint location, GLint x, GLint y, GLint z) nogil
ctypedef void (__stdcall *GLUNIFORM3IVPTR)(GLint location, GLsizei count, const GLint* v) nogil
ctypedef void (__stdcall *GLUNIFORM4FPTR)(GLint, GLfloat, GLfloat, GLfloat, GLfloat) nogil
ctypedef void (__stdcall *GLUNIFORM4FVPTR)(GLint location, GLsizei count, const GLfloat* v) nogil
ctypedef void (__stdcall *GLUNIFORM4IPTR)(GLint location, GLint x, GLint y, GLint z, GLint w) nogil
ctypedef void (__stdcall *GLUNIFORM4IVPTR)(GLint location, GLsizei count, const GLint* v) nogil
ctypedef void (__stdcall *GLUNIFORMMATRIX4FVPTR)(GLint, GLsizei, GLboolean, const GLfloat *) nogil
ctypedef void (__stdcall *GLUSEPROGRAMPTR)(GLuint) nogil
ctypedef void (__stdcall *GLVALIDATEPROGRAMPTR)(GLuint program) nogil
ctypedef void (__stdcall *GLVERTEXATTRIB1FPTR)(GLuint indx, GLfloat x) nogil
ctypedef void (__stdcall *GLVERTEXATTRIB2FPTR)(GLuint indx, GLfloat x, GLfloat y) nogil
ctypedef void (__stdcall *GLVERTEXATTRIB3FPTR)(GLuint indx, GLfloat x, GLfloat y, GLfloat z) nogil
ctypedef void (__stdcall *GLVERTEXATTRIB4FPTR)(GLuint indx, GLfloat x, GLfloat y, GLfloat z, GLfloat w) nogil
ctypedef void (__stdcall *GLVERTEXATTRIBPOINTERPTR)(GLuint, GLint, GLenum, GLboolean, GLsizei, const void *) nogil
ctypedef void (__stdcall *GLVIEWPORTPTR)(GLint, GLint, GLsizei, GLsizei) nogil

ctypedef struct GLES2_Context:
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
    void (__stdcall *glShaderSource)(GLuint, GLsizei, const GLchar* const*, const GLint *) nogil
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

cdef GLES2_Context *cgl
cdef void gl_dyn_load_context()
