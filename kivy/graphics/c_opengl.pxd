cdef extern from "gl_redirect.h":

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

    #FIXME: figure out correct cross platform tydefs
    #ctypedef khronos_float_t  GLfloat
    #ctypedef khronos_float_t  GLclampf
    #ctypedef khronos_int32_t  GLfixed
    #ctypedef khronos_intptr_t GLintptr
    #ctypedef khronos_ssize_t  GLsizeiptr
    ctypedef signed char        GLbyte
    ctypedef unsigned char      GLubyte
    ctypedef float              GLfloat
    ctypedef float              GLclampf
    ctypedef int                GLfixed
    ctypedef signed long int    GLintptr
    ctypedef signed long int    GLsizeiptr


    #int GL_ES_VERSION_2_0

    int __USE_GLES20

    int GL_DEPTH_BUFFER_BIT
    int GL_STENCIL_BUFFER_BIT
    int GL_COLOR_BUFFER_BIT

    int GL_FALSE
    int GL_TRUE

    int GL_POINTS
    int GL_LINES
    int GL_LINE_LOOP
    int GL_LINE_STRIP
    int GL_TRIANGLES
    int GL_TRIANGLE_STRIP
    int GL_TRIANGLE_FAN

    int GL_ZERO
    int GL_ONE
    int GL_SRC_COLOR
    int GL_ONE_MINUS_SRC_COLOR
    int GL_SRC_ALPHA
    int GL_ONE_MINUS_SRC_ALPHA
    int GL_DST_ALPHA
    int GL_ONE_MINUS_DST_ALPHA

    int GL_DST_COLOR
    int GL_ONE_MINUS_DST_COLOR
    int GL_SRC_ALPHA_SATURATE

    int GL_FUNC_ADD
    int GL_BLEND_EQUATION
    int GL_BLEND_EQUATION_RGB
    int GL_BLEND_EQUATION_ALPHA

    int GL_FUNC_SUBTRACT
    int GL_FUNC_REVERSE_SUBTRACT

    int GL_BLEND_DST_RGB
    int GL_BLEND_SRC_RGB
    int GL_BLEND_DST_ALPHA
    int GL_BLEND_SRC_ALPHA
    int GL_ANT_COLOR
    int GL_ONE_MINUS_ANT_COLOR
    int GL_ANT_ALPHA
    int GL_ONE_MINUS_ANT_ALPHA
    int GL_BLEND_COLOR

    int GL_ARRAY_BUFFER
    int GL_ELEMENT_ARRAY_BUFFER
    int GL_ARRAY_BUFFER_BINDING
    int GL_ELEMENT_ARRAY_BUFFER_BINDING

    int GL_STREAM_DRAW
    int GL_STATIC_DRAW
    int GL_DYNAMIC_DRAW

    int GL_BUFFER_SIZE
    int GL_BUFFER_USAGE

    int GL_CURRENT_VERTEX_ATTRIB

    int GL_FRONT
    int GL_BACK
    int GL_FRONT_AND_BACK

    int GL_TEXTURE_2D
    int GL_CULL_FACE
    int GL_BLEND
    int GL_DITHER
    int GL_STENCIL_TEST
    int GL_DEPTH_TEST
    int GL_SCISSOR_TEST
    int GL_POLYGON_OFFSET_FILL
    int GL_SAMPLE_ALPHA_TO_COVERAGE
    int GL_SAMPLE_COVERAGE

    int GL_NO_ERROR
    int GL_INVALID_ENUM
    int GL_INVALID_VALUE
    int GL_INVALID_OPERATION
    int GL_OUT_OF_MEMORY

    int GL_CW
    int GL_CCW

    int GL_LINE_WIDTH
    int GL_ALIASED_POINT_SIZE_RANGE
    int GL_ALIASED_LINE_WIDTH_RANGE
    int GL_CULL_FACE_MODE
    int GL_FRONT_FACE
    int GL_DEPTH_RANGE
    int GL_DEPTH_WRITEMASK
    int GL_DEPTH_CLEAR_VALUE
    int GL_DEPTH_FUNC
    int GL_STENCIL_CLEAR_VALUE
    int GL_STENCIL_FUNC
    int GL_STENCIL_FAIL
    int GL_STENCIL_PASS_DEPTH_FAIL
    int GL_STENCIL_PASS_DEPTH_PASS
    int GL_STENCIL_REF
    int GL_STENCIL_VALUE_MASK
    int GL_STENCIL_WRITEMASK
    int GL_STENCIL_BACK_FUNC
    int GL_STENCIL_BACK_FAIL
    int GL_STENCIL_BACK_PASS_DEPTH_FAIL
    int GL_STENCIL_BACK_PASS_DEPTH_PASS
    int GL_STENCIL_BACK_REF
    int GL_STENCIL_BACK_VALUE_MASK
    int GL_STENCIL_BACK_WRITEMASK
    int GL_VIEWPORT
    int GL_SCISSOR_BOX

    int GL_COLOR_CLEAR_VALUE
    int GL_COLOR_WRITEMASK
    int GL_UNPACK_ALIGNMENT
    int GL_PACK_ALIGNMENT
    int GL_MAX_TEXTURE_SIZE
    int GL_MAX_VIEWPORT_DIMS
    int GL_SUBPIXEL_BITS
    int GL_RED_BITS
    int GL_GREEN_BITS
    int GL_BLUE_BITS
    int GL_ALPHA_BITS
    int GL_DEPTH_BITS
    int GL_STENCIL_BITS
    int GL_POLYGON_OFFSET_UNITS

    int GL_POLYGON_OFFSET_FACTOR
    int GL_TEXTURE_BINDING_2D
    int GL_SAMPLE_BUFFERS
    int GL_SAMPLES
    int GL_SAMPLE_COVERAGE_VALUE
    int GL_SAMPLE_COVERAGE_INVERT

    int GL_NUM_COMPRESSED_TEXTURE_FORMATS
    int GL_COMPRESSED_TEXTURE_FORMATS

    int GL_DONT_CARE
    int GL_FASTEST
    int GL_NICEST

    int GL_GENERATE_MIPMAP_HINT

    int GL_BYTE
    int GL_UNSIGNED_BYTE
    int GL_SHORT
    int GL_UNSIGNED_SHORT
    int GL_INT
    int GL_UNSIGNED_INT
    int GL_FLOAT
    int GL_FIXED

    int GL_DEPTH_COMPONENT
    int GL_ALPHA
    int GL_RGB
    int GL_RGBA
    int GL_LUMINANCE
    int GL_LUMINANCE_ALPHA

    int GL_UNSIGNED_SHORT_4_4_4_4
    int GL_UNSIGNED_SHORT_5_5_5_1
    int GL_UNSIGNED_SHORT_5_6_5

    int GL_FRAGMENT_SHADER
    int GL_VERTEX_SHADER
    int GL_MAX_VERTEX_ATTRIBS
    int GL_MAX_VERTEX_UNIFORM_VECTORS
    int GL_MAX_VARYING_VECTORS
    int GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS
    int GL_MAX_VERTEX_TEXTURE_IMAGE_UNITS
    int GL_MAX_TEXTURE_IMAGE_UNITS
    int GL_MAX_FRAGMENT_UNIFORM_VECTORS
    int GL_SHADER_TYPE
    int GL_DELETE_STATUS
    int GL_LINK_STATUS
    int GL_VALIDATE_STATUS
    int GL_ATTACHED_SHADERS
    int GL_ACTIVE_UNIFORMS
    int GL_ACTIVE_UNIFORM_MAX_LENGTH
    int GL_ACTIVE_ATTRIBUTES
    int GL_ACTIVE_ATTRIBUTE_MAX_LENGTH
    int GL_SHADING_LANGUAGE_VERSION
    int GL_CURRENT_PROGRAM

    int GL_NEVER
    int GL_LESS
    int GL_EQUAL
    int GL_LEQUAL
    int GL_GREATER
    int GL_NOTEQUAL
    int GL_GEQUAL
    int GL_ALWAYS

    int GL_KEEP
    int GL_REPLACE
    int GL_INCR
    int GL_DECR
    int GL_INVERT
    int GL_INCR_WRAP
    int GL_DECR_WRAP

    int GL_VENDOR
    int GL_RENDERER
    int GL_VERSION
    int GL_EXTENSIONS

    int GL_NEAREST
    int GL_LINEAR

    int GL_NEAREST_MIPMAP_NEAREST
    int GL_LINEAR_MIPMAP_NEAREST
    int GL_NEAREST_MIPMAP_LINEAR
    int GL_LINEAR_MIPMAP_LINEAR

    int GL_TEXTURE_MAG_FILTER
    int GL_TEXTURE_MIN_FILTER
    int GL_TEXTURE_WRAP_S
    int GL_TEXTURE_WRAP_T

    int GL_TEXTURE

    int GL_TEXTURE_CUBE_MAP
    int GL_TEXTURE_BINDING_CUBE_MAP
    int GL_TEXTURE_CUBE_MAP_POSITIVE_X
    int GL_TEXTURE_CUBE_MAP_NEGATIVE_X
    int GL_TEXTURE_CUBE_MAP_POSITIVE_Y
    int GL_TEXTURE_CUBE_MAP_NEGATIVE_Y
    int GL_TEXTURE_CUBE_MAP_POSITIVE_Z
    int GL_TEXTURE_CUBE_MAP_NEGATIVE_Z
    int GL_MAX_CUBE_MAP_TEXTURE_SIZE

    int GL_TEXTURE0
    int GL_TEXTURE1
    int GL_TEXTURE2
    int GL_TEXTURE3
    int GL_TEXTURE4
    int GL_TEXTURE5
    int GL_TEXTURE6
    int GL_TEXTURE7
    int GL_TEXTURE8
    int GL_TEXTURE9
    int GL_TEXTURE10
    int GL_TEXTURE11
    int GL_TEXTURE12
    int GL_TEXTURE13
    int GL_TEXTURE14
    int GL_TEXTURE15
    int GL_TEXTURE16
    int GL_TEXTURE17
    int GL_TEXTURE18
    int GL_TEXTURE19
    int GL_TEXTURE20
    int GL_TEXTURE21
    int GL_TEXTURE22
    int GL_TEXTURE23
    int GL_TEXTURE24
    int GL_TEXTURE25
    int GL_TEXTURE26
    int GL_TEXTURE27
    int GL_TEXTURE28
    int GL_TEXTURE29
    int GL_TEXTURE30
    int GL_TEXTURE31
    int GL_ACTIVE_TEXTURE


    int GL_REPEAT
    int GL_CLAMP_TO_EDGE
    int GL_MIRRORED_REPEAT

    int GL_FLOAT_VEC2
    int GL_FLOAT_VEC3
    int GL_FLOAT_VEC4
    int GL_INT_VEC2
    int GL_INT_VEC3
    int GL_INT_VEC4
    int GL_BOOL
    int GL_BOOL_VEC2
    int GL_BOOL_VEC3
    int GL_BOOL_VEC4
    int GL_FLOAT_MAT2
    int GL_FLOAT_MAT3
    int GL_FLOAT_MAT4
    int GL_SAMPLER_2D
    int GL_SAMPLER_CUBE

    int GL_VERTEX_ATTRIB_ARRAY_ENABLED
    int GL_VERTEX_ATTRIB_ARRAY_SIZE
    int GL_VERTEX_ATTRIB_ARRAY_STRIDE
    int GL_VERTEX_ATTRIB_ARRAY_TYPE
    int GL_VERTEX_ATTRIB_ARRAY_NORMALIZED
    int GL_VERTEX_ATTRIB_ARRAY_POINTER
    int GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING

    int GL_IMPLEMENTATION_COLOR_READ_TYPE
    int GL_IMPLEMENTATION_COLOR_READ_FORMAT

    int GL_COMPILE_STATUS
    int GL_INFO_LOG_LENGTH
    int GL_SHADER_SOURCE_LENGTH
    int GL_SHADER_COMPILER

    int GL_SHADER_BINARY_FORMATS
    int GL_NUM_SHADER_BINARY_FORMATS

    int GL_LOW_FLOAT
    int GL_MEDIUM_FLOAT
    int GL_HIGH_FLOAT
    int GL_LOW_INT
    int GL_MEDIUM_INT
    int GL_HIGH_INT

    int GL_FRAMEBUFFER
    int GL_RENDERBUFFER

    int GL_RGBA4
    int GL_RGB5_A1
    int GL_RGB565
    int GL_DEPTH_COMPONENT16
    int GL_STENCIL_INDEX
    int GL_STENCIL_INDEX8

    int GL_RENDERBUFFER_WIDTH
    int GL_RENDERBUFFER_HEIGHT
    int GL_RENDERBUFFER_INTERNAL_FORMAT
    int GL_RENDERBUFFER_RED_SIZE
    int GL_RENDERBUFFER_GREEN_SIZE
    int GL_RENDERBUFFER_BLUE_SIZE
    int GL_RENDERBUFFER_ALPHA_SIZE
    int GL_RENDERBUFFER_DEPTH_SIZE
    int GL_RENDERBUFFER_STENCIL_SIZE

    int GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE
    int GL_FRAMEBUFFER_ATTACHMENT_OBJECT_NAME
    int GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_LEVEL
    int GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_CUBE_MAP_FACE

    int GL_COLOR_ATTACHMENT0
    int GL_DEPTH_ATTACHMENT
    int GL_STENCIL_ATTACHMENT

    int GL_NONE

    int GL_FRAMEBUFFER_COMPLETE
    int GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT
    int GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT
    int GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS
    int GL_FRAMEBUFFER_UNSUPPORTED

    int GL_FRAMEBUFFER_BINDING
    int GL_RENDERBUFFER_BINDING
    int GL_MAX_RENDERBUFFER_SIZE

    int GL_INVALID_FRAMEBUFFER_OPERATION




    cdef void   glActiveTexture (GLenum texture)
    cdef void   glAttachShader (GLuint program, GLuint shader)
    cdef void   glBindAttribLocation (GLuint program, GLuint index,  GLchar* name)
    cdef void   glBindBuffer (GLenum target, GLuint buffer)
    cdef void   glBindFramebuffer (GLenum target, GLuint framebuffer)
    cdef void   glBindRenderbuffer (GLenum target, GLuint renderbuffer)
    cdef void   glBindTexture (GLenum target, GLuint texture)
    cdef void   glBlendColor (GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha)
    cdef void   glBlendEquation ( GLenum mode )
    cdef void   glBlendEquationSeparate (GLenum modeRGB, GLenum modeAlpha)
    cdef void   glBlendFunc (GLenum sfactor, GLenum dfactor)
    cdef void   glBlendFuncSeparate (GLenum srcRGB, GLenum dstRGB, GLenum srcAlpha, GLenum dstAlpha)
    cdef void   glBufferData (GLenum target, GLsizeiptr size,  GLvoid* data, GLenum usage)
    cdef void   glBufferSubData (GLenum target, GLintptr offset, GLsizeiptr size,  GLvoid* data)
    cdef GLenum glCheckFramebufferStatus (GLenum target)
    cdef void   glClear (GLbitfield mask)
    cdef void   glClearColor (GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha)
    cdef void   glClearDepthf (GLclampf depth)
    cdef void   glClearStencil (GLint s)
    cdef void   glColorMask (GLboolean red, GLboolean green, GLboolean blue, GLboolean alpha)
    cdef void   glCompileShader (GLuint shader)
    cdef void   glCompressedTexImage2D (GLenum target, GLint level, GLenum internalformat, GLsizei width, GLsizei height, GLint border, GLsizei imageSize,  GLvoid* data)
    cdef void   glCompressedTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLsizei imageSize,  GLvoid* data)
    cdef void   glCopyTexImage2D (GLenum target, GLint level, GLenum internalformat, GLint x, GLint y, GLsizei width, GLsizei height, GLint border)
    cdef void   glCopyTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLint x, GLint y, GLsizei width, GLsizei height)
    cdef GLuint glCreateProgram ()
    cdef GLuint glCreateShader (GLenum type)
    cdef void   glCullFace (GLenum mode)
    cdef void   glDeleteBuffers (GLsizei n,  GLuint* buffers)
    cdef void   glDeleteFramebuffers (GLsizei n,  GLuint* framebuffers)
    cdef void   glDeleteProgram (GLuint program)
    cdef void   glDeleteRenderbuffers (GLsizei n,  GLuint* renderbuffers)
    cdef void   glDeleteShader (GLuint shader)
    cdef void   glDeleteTextures (GLsizei n,  GLuint* textures)
    cdef void   glDepthFunc (GLenum func)
    cdef void   glDepthMask (GLboolean flag)
    cdef void   glDepthRangef (GLclampf zNear, GLclampf zFar)
    cdef void   glDetachShader (GLuint program, GLuint shader)
    cdef void   glDisable (GLenum cap)
    cdef void   glDisableVertexAttribArray (GLuint index)
    cdef void   glDrawArrays (GLenum mode, GLint first, GLsizei count)
    cdef void   glDrawElements (GLenum mode, GLsizei count, GLenum type,  GLvoid* indices)
    cdef void   glEnable (GLenum cap)
    cdef void   glEnableVertexAttribArray (GLuint index)
    cdef void   glFinish ()
    cdef void   glFlush ()
    cdef void   glFramebufferRenderbuffer (GLenum target, GLenum attachment, GLenum renderbuffertarget, GLuint renderbuffer)
    cdef void   glFramebufferTexture2D (GLenum target, GLenum attachment, GLenum textarget, GLuint texture, GLint level)
    cdef void   glFrontFace (GLenum mode)
    cdef void   glGenBuffers (GLsizei n, GLuint* buffers)
    cdef void   glGenerateMipmap (GLenum target)
    cdef void   glGenFramebuffers (GLsizei n, GLuint* framebuffers)
    cdef void   glGenRenderbuffers (GLsizei n, GLuint* renderbuffers)
    cdef void   glGenTextures (GLsizei n, GLuint* textures)
    cdef void   glGetActiveAttrib (GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name)
    cdef void   glGetActiveUniform (GLuint program, GLuint index, GLsizei bufsize, GLsizei* length, GLint* size, GLenum* type, GLchar* name)
    cdef void   glGetAttachedShaders (GLuint program, GLsizei maxcount, GLsizei* count, GLuint* shaders)
    cdef int    glGetAttribLocation (GLuint program,  GLchar* name)
    cdef void   glGetBooleanv (GLenum pname, GLboolean* params)
    cdef void   glGetBufferParameteriv (GLenum target, GLenum pname, GLint* params)
    cdef GLenum glGetError ()
    cdef void   glGetFloatv (GLenum pname, GLfloat* params)
    cdef void   glGetFramebufferAttachmentParameteriv (GLenum target, GLenum attachment, GLenum pname, GLint* params)
    cdef void   glGetIntegerv (GLenum pname, GLint* params)
    cdef void   glGetProgramiv (GLuint program, GLenum pname, GLint* params)
    cdef void   glGetProgramInfoLog (GLuint program, GLsizei bufsize, GLsizei* length, GLchar* infolog)
    cdef void   glGetRenderbufferParameteriv (GLenum target, GLenum pname, GLint* params)
    cdef void   glGetShaderiv (GLuint shader, GLenum pname, GLint* params)
    cdef void   glGetShaderInfoLog (GLuint shader, GLsizei bufsize, GLsizei* length, GLchar* infolog)
    cdef void   glGetShaderPrecisionFormat (GLenum shadertype, GLenum precisiontype, GLint* range, GLint* precision)
    cdef void   glGetShaderSource (GLuint shader, GLsizei bufsize, GLsizei* length, GLchar* source)
    cdef   GLubyte*  glGetString (GLenum name)
    cdef void   glGetTexParameterfv (GLenum target, GLenum pname, GLfloat* params)
    cdef void   glGetTexParameteriv (GLenum target, GLenum pname, GLint* params)
    cdef void   glGetUniformfv (GLuint program, GLint location, GLfloat* params)
    cdef void   glGetUniformiv (GLuint program, GLint location, GLint* params)
    cdef int    glGetUniformLocation (GLuint program,  GLchar* name)
    cdef void   glGetVertexAttribfv (GLuint index, GLenum pname, GLfloat* params)
    cdef void   glGetVertexAttribiv (GLuint index, GLenum pname, GLint* params)
    cdef void   glGetVertexAttribPointerv (GLuint index, GLenum pname, GLvoid** pointer)
    cdef void   glHint (GLenum target, GLenum mode)
    cdef GLboolean  glIsBuffer (GLuint buffer)
    cdef GLboolean  glIsEnabled (GLenum cap)
    cdef GLboolean  glIsFramebuffer (GLuint framebuffer)
    cdef GLboolean  glIsProgram (GLuint program)
    cdef GLboolean  glIsRenderbuffer (GLuint renderbuffer)
    cdef GLboolean  glIsShader (GLuint shader)
    cdef GLboolean  glIsTexture (GLuint texture)
    cdef void  glLineWidth (GLfloat width)
    cdef void  glLinkProgram (GLuint program)
    cdef void  glPixelStorei (GLenum pname, GLint param)
    cdef void  glPolygonOffset (GLfloat factor, GLfloat units)
    cdef void  glReadPixels (GLint x, GLint y, GLsizei width, GLsizei height, GLenum format, GLenum type, GLvoid* pixels)
    cdef void  glReleaseShaderCompiler ()
    cdef void  glRenderbufferStorage (GLenum target, GLenum internalformat, GLsizei width, GLsizei height)
    cdef void  glSampleCoverage (GLclampf value, GLboolean invert)
    cdef void  glScissor (GLint x, GLint y, GLsizei width, GLsizei height)
    cdef void  glShaderBinary (GLsizei n,  GLuint* shaders, GLenum binaryformat,  GLvoid* binary, GLsizei length)
    cdef void  glShaderSource (GLuint shader, GLsizei count,  GLchar** string,  GLint* length)
    cdef void  glStencilFunc (GLenum func, GLint ref, GLuint mask)
    cdef void  glStencilFuncSeparate (GLenum face, GLenum func, GLint ref, GLuint mask)
    cdef void  glStencilMask (GLuint mask)
    cdef void  glStencilMaskSeparate (GLenum face, GLuint mask)
    cdef void  glStencilOp (GLenum fail, GLenum zfail, GLenum zpass)
    cdef void  glStencilOpSeparate (GLenum face, GLenum fail, GLenum zfail, GLenum zpass)
    cdef void  glTexImage2D (GLenum target, GLint level, GLint internalformat, GLsizei width, GLsizei height, GLint border, GLenum format, GLenum type,  GLvoid* pixels)
    cdef void  glTexParameterf (GLenum target, GLenum pname, GLfloat param)
    cdef void  glTexParameterfv (GLenum target, GLenum pname,  GLfloat* params)
    cdef void  glTexParameteri (GLenum target, GLenum pname, GLint param)
    cdef void  glTexParameteriv (GLenum target, GLenum pname,  GLint* params)
    cdef void  glTexSubImage2D (GLenum target, GLint level, GLint xoffset, GLint yoffset, GLsizei width, GLsizei height, GLenum format, GLenum type,  GLvoid* pixels)
    cdef void  glUniform1f (GLint location, GLfloat x)
    cdef void  glUniform1fv (GLint location, GLsizei count,  GLfloat* v)
    cdef void  glUniform1i (GLint location, GLint x)
    cdef void  glUniform1iv (GLint location, GLsizei count,  GLint* v)
    cdef void  glUniform2f (GLint location, GLfloat x, GLfloat y)
    cdef void  glUniform2fv (GLint location, GLsizei count,  GLfloat* v)
    cdef void  glUniform2i (GLint location, GLint x, GLint y)
    cdef void  glUniform2iv (GLint location, GLsizei count,  GLint* v)
    cdef void  glUniform3f (GLint location, GLfloat x, GLfloat y, GLfloat z)
    cdef void  glUniform3fv (GLint location, GLsizei count,  GLfloat* v)
    cdef void  glUniform3i (GLint location, GLint x, GLint y, GLint z)
    cdef void  glUniform3iv (GLint location, GLsizei count,  GLint* v)
    cdef void  glUniform4f (GLint location, GLfloat x, GLfloat y, GLfloat z, GLfloat w)
    cdef void  glUniform4fv (GLint location, GLsizei count,  GLfloat* v)
    cdef void  glUniform4i (GLint location, GLint x, GLint y, GLint z, GLint w)
    cdef void  glUniform4iv (GLint location, GLsizei count,  GLint* v)
    cdef void  glUniformMatrix2fv (GLint location, GLsizei count, GLboolean transpose,  GLfloat* value)
    cdef void  glUniformMatrix3fv (GLint location, GLsizei count, GLboolean transpose,  GLfloat* value)
    cdef void  glUniformMatrix4fv (GLint location, GLsizei count, GLboolean transpose,  GLfloat* value)
    cdef void  glUseProgram (GLuint program)
    cdef void  glValidateProgram (GLuint program)
    cdef void  glVertexAttrib1f (GLuint indx, GLfloat x)
    cdef void  glVertexAttrib1fv (GLuint indx,  GLfloat* values)
    cdef void  glVertexAttrib2f (GLuint indx, GLfloat x, GLfloat y)
    cdef void  glVertexAttrib2fv (GLuint indx,  GLfloat* values)
    cdef void  glVertexAttrib3f (GLuint indx, GLfloat x, GLfloat y, GLfloat z)
    cdef void  glVertexAttrib3fv (GLuint indx,  GLfloat* values)
    cdef void  glVertexAttrib4f (GLuint indx, GLfloat x, GLfloat y, GLfloat z, GLfloat w)
    cdef void  glVertexAttrib4fv (GLuint indx,  GLfloat* values)
    cdef void  glVertexAttribPointer (GLuint indx, GLint size, GLenum type, GLboolean normalized, GLsizei stride,  GLvoid* ptr)
    cdef void  glViewport (GLint x, GLint y, GLsizei width, GLsizei height)
