include "common.pxi"
include "../include/config.pxi"


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
    ctypedef signed char        GLbyte
    ctypedef unsigned char      GLubyte
    ctypedef float              GLfloat
    ctypedef float              GLclampf
    ctypedef int                GLfixed
    ctypedef signed long int    GLintptr
    ctypedef signed long int    GLsizeiptr


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
    int GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS
    int GL_MAX_VERTEX_TEXTURE_IMAGE_UNITS
    int GL_MAX_TEXTURE_IMAGE_UNITS
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

    int GL_COMPILE_STATUS
    int GL_INFO_LOG_LENGTH
    int GL_SHADER_SOURCE_LENGTH

    int GL_SHADER_BINARY_FORMATS

    int GL_FRAMEBUFFER
    int GL_RENDERBUFFER

    int GL_RGBA4
    int GL_RGB5_A1
    int GL_RGB565
    int GL_DEPTH_COMPONENT16
    int GL_STENCIL_INDEX8
    int GL_DEPTH24_STENCIL8_OES

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

    int GL_FIXED
    int GL_MAX_VERTEX_UNIFORM_VECTORS
    int GL_MAX_VARYING_VECTORS
    int GL_MAX_FRAGMENT_UNIFORM_VECTORS
    int GL_IMPLEMENTATION_COLOR_READ_TYPE
    int GL_IMPLEMENTATION_COLOR_READ_FORMAT
    int GL_SHADER_COMPILER
    int GL_NUM_SHADER_BINARY_FORMATS
    int GL_LOW_FLOAT
    int GL_MEDIUM_FLOAT
    int GL_HIGH_FLOAT
    int GL_LOW_INT
    int GL_MEDIUM_INT
    int GL_HIGH_INT

    int GL_FRAMEBUFFER_UNDEFINED_OES

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
ctypedef void (__stdcall *GLSHADERSOURCEPTR)(GLuint, GLsizei, const GLchar**, const GLint *) nogil
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

cdef GLES2_Context *cgl
cdef int kivy_opengl_es2
cdef unsigned long initialized_tid
cdef public int verify_gl_main_thread
cpdef cgl_init(allowed=*, ignored=*)
cdef GLES2_Context *cgl_get_context()
cdef void cgl_set_context(GLES2_Context* ctx)
cpdef cgl_get_backend_name(allowed=*, ignored=*)
cpdef cgl_get_initialized_backend_name()
