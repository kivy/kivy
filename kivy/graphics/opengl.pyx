'''
OpenGL
======

This module is a Python wrapper for OpenGL commands.

.. warning::

    Not every OpenGL command has been wrapped and because we are using the C
    binding for higher performance, and you should rather stick to the Kivy
    Graphics API. By using OpenGL commands directly, you might change
    the OpenGL context and introduce inconsistency between the Kivy state and
    the OpenGL state.

'''

include "../include/config.pxi"
include "common.pxi"

cimport kivy.graphics.cgl as cgldef
from kivy.graphics.cgl cimport (cgl, GLvoid, GLfloat, GLuint, GLint, GLchar,
    GLubyte, cgl_init, GLboolean, GLenum, GLsizei, GLclampf, GLbitfield,
    GLintptr, GLsizeiptr)
from kivy.logger import Logger

# Utilities

cdef GLuint *_genBegin(int n):
    cdef GLuint *d
    d = <GLuint *>malloc(sizeof(GLuint) * n)
    if d == NULL:
        raise MemoryError()
    return d

cdef list _genEnd(int n, GLuint *data):
    cdef list out = []
    for x in xrange(n):
        out.append(data[x])
    free(data)
    return out

#GL_ES_VERSION_2_0 = cgldef.GL_ES_VERSION_2_0
GL_DEPTH_BUFFER_BIT = cgldef.GL_DEPTH_BUFFER_BIT
GL_STENCIL_BUFFER_BIT = cgldef.GL_STENCIL_BUFFER_BIT
GL_COLOR_BUFFER_BIT = cgldef.GL_COLOR_BUFFER_BIT
GL_FALSE = cgldef.GL_FALSE
GL_TRUE = cgldef.GL_TRUE
GL_POINTS = cgldef.GL_POINTS
GL_LINES = cgldef.GL_LINES
GL_LINE_LOOP = cgldef.GL_LINE_LOOP
GL_LINE_STRIP = cgldef.GL_LINE_STRIP
GL_TRIANGLES = cgldef.GL_TRIANGLES
GL_TRIANGLE_STRIP = cgldef.GL_TRIANGLE_STRIP
GL_TRIANGLE_FAN = cgldef.GL_TRIANGLE_FAN
GL_ZERO = cgldef.GL_ZERO
GL_ONE = cgldef.GL_ONE
GL_SRC_COLOR = cgldef.GL_SRC_COLOR
GL_ONE_MINUS_SRC_COLOR = cgldef.GL_ONE_MINUS_SRC_COLOR
GL_SRC_ALPHA = cgldef.GL_SRC_ALPHA
GL_ONE_MINUS_SRC_ALPHA = cgldef.GL_ONE_MINUS_SRC_ALPHA
GL_DST_ALPHA = cgldef.GL_DST_ALPHA
GL_ONE_MINUS_DST_ALPHA = cgldef.GL_ONE_MINUS_DST_ALPHA
GL_DST_COLOR = cgldef.GL_DST_COLOR
GL_ONE_MINUS_DST_COLOR = cgldef.GL_ONE_MINUS_DST_COLOR
GL_SRC_ALPHA_SATURATE = cgldef.GL_SRC_ALPHA_SATURATE
GL_FUNC_ADD = cgldef.GL_FUNC_ADD
GL_BLEND_EQUATION = cgldef.GL_BLEND_EQUATION
GL_BLEND_EQUATION_RGB = cgldef.GL_BLEND_EQUATION_RGB
GL_BLEND_EQUATION_ALPHA = cgldef.GL_BLEND_EQUATION_ALPHA
GL_FUNC_SUBTRACT = cgldef.GL_FUNC_SUBTRACT
GL_FUNC_REVERSE_SUBTRACT = cgldef.GL_FUNC_REVERSE_SUBTRACT
GL_BLEND_DST_RGB = cgldef.GL_BLEND_DST_RGB
GL_BLEND_SRC_RGB = cgldef.GL_BLEND_SRC_RGB
GL_BLEND_DST_ALPHA = cgldef.GL_BLEND_DST_ALPHA
GL_BLEND_SRC_ALPHA = cgldef.GL_BLEND_SRC_ALPHA
GL_SRC_COLOR = cgldef.GL_SRC_COLOR
GL_ONE_MINUS_SRC_COLOR = cgldef.GL_ONE_MINUS_SRC_COLOR
GL_SRC_ALPHA = cgldef.GL_SRC_ALPHA
GL_ONE_MINUS_SRC_ALPHA = cgldef.GL_ONE_MINUS_SRC_ALPHA
GL_BLEND_COLOR = cgldef.GL_BLEND_COLOR
GL_ARRAY_BUFFER = cgldef.GL_ARRAY_BUFFER
GL_ELEMENT_ARRAY_BUFFER = cgldef.GL_ELEMENT_ARRAY_BUFFER
GL_ARRAY_BUFFER_BINDING = cgldef.GL_ARRAY_BUFFER_BINDING
GL_ELEMENT_ARRAY_BUFFER_BINDING = cgldef.GL_ELEMENT_ARRAY_BUFFER_BINDING
GL_STREAM_DRAW = cgldef.GL_STREAM_DRAW
GL_STATIC_DRAW = cgldef.GL_STATIC_DRAW
GL_DYNAMIC_DRAW = cgldef.GL_DYNAMIC_DRAW
GL_BUFFER_SIZE = cgldef.GL_BUFFER_SIZE
GL_BUFFER_USAGE = cgldef.GL_BUFFER_USAGE
GL_CURRENT_VERTEX_ATTRIB = cgldef.GL_CURRENT_VERTEX_ATTRIB
GL_FRONT = cgldef.GL_FRONT
GL_BACK = cgldef.GL_BACK
GL_FRONT_AND_BACK = cgldef.GL_FRONT_AND_BACK
GL_TEXTURE_2D = cgldef.GL_TEXTURE_2D
GL_CULL_FACE = cgldef.GL_CULL_FACE
GL_BLEND = cgldef.GL_BLEND
GL_DITHER = cgldef.GL_DITHER
GL_STENCIL_TEST = cgldef.GL_STENCIL_TEST
GL_DEPTH_TEST = cgldef.GL_DEPTH_TEST
GL_SCISSOR_TEST = cgldef.GL_SCISSOR_TEST
GL_POLYGON_OFFSET_FILL = cgldef.GL_POLYGON_OFFSET_FILL
GL_SAMPLE_ALPHA_TO_COVERAGE = cgldef.GL_SAMPLE_ALPHA_TO_COVERAGE
GL_SAMPLE_COVERAGE = cgldef.GL_SAMPLE_COVERAGE
GL_NO_ERROR = cgldef.GL_NO_ERROR
GL_INVALID_ENUM = cgldef.GL_INVALID_ENUM
GL_INVALID_VALUE = cgldef.GL_INVALID_VALUE
GL_INVALID_OPERATION = cgldef.GL_INVALID_OPERATION
GL_OUT_OF_MEMORY = cgldef.GL_OUT_OF_MEMORY
GL_CW = cgldef.GL_CW
GL_CCW = cgldef.GL_CCW
GL_LINE_WIDTH = cgldef.GL_LINE_WIDTH
GL_ALIASED_POINT_SIZE_RANGE = cgldef.GL_ALIASED_POINT_SIZE_RANGE
GL_ALIASED_LINE_WIDTH_RANGE = cgldef.GL_ALIASED_LINE_WIDTH_RANGE
GL_CULL_FACE_MODE = cgldef.GL_CULL_FACE_MODE
GL_FRONT_FACE = cgldef.GL_FRONT_FACE
GL_DEPTH_RANGE = cgldef.GL_DEPTH_RANGE
GL_DEPTH_WRITEMASK = cgldef.GL_DEPTH_WRITEMASK
GL_DEPTH_CLEAR_VALUE = cgldef.GL_DEPTH_CLEAR_VALUE
GL_DEPTH_FUNC = cgldef.GL_DEPTH_FUNC
GL_STENCIL_CLEAR_VALUE = cgldef.GL_STENCIL_CLEAR_VALUE
GL_STENCIL_FUNC = cgldef.GL_STENCIL_FUNC
GL_STENCIL_FAIL = cgldef.GL_STENCIL_FAIL
GL_STENCIL_PASS_DEPTH_FAIL = cgldef.GL_STENCIL_PASS_DEPTH_FAIL
GL_STENCIL_PASS_DEPTH_PASS = cgldef.GL_STENCIL_PASS_DEPTH_PASS
GL_STENCIL_REF = cgldef.GL_STENCIL_REF
GL_STENCIL_VALUE_MASK = cgldef.GL_STENCIL_VALUE_MASK
GL_STENCIL_WRITEMASK = cgldef.GL_STENCIL_WRITEMASK
GL_STENCIL_BACK_FUNC = cgldef.GL_STENCIL_BACK_FUNC
GL_STENCIL_BACK_FAIL = cgldef.GL_STENCIL_BACK_FAIL
GL_STENCIL_BACK_PASS_DEPTH_FAIL = cgldef.GL_STENCIL_BACK_PASS_DEPTH_FAIL
GL_STENCIL_BACK_PASS_DEPTH_PASS = cgldef.GL_STENCIL_BACK_PASS_DEPTH_PASS
GL_STENCIL_BACK_REF = cgldef.GL_STENCIL_BACK_REF
GL_STENCIL_BACK_VALUE_MASK = cgldef.GL_STENCIL_BACK_VALUE_MASK
GL_STENCIL_BACK_WRITEMASK = cgldef.GL_STENCIL_BACK_WRITEMASK
GL_VIEWPORT = cgldef.GL_VIEWPORT
GL_SCISSOR_BOX = cgldef.GL_SCISSOR_BOX
GL_COLOR_CLEAR_VALUE = cgldef.GL_COLOR_CLEAR_VALUE
GL_COLOR_WRITEMASK = cgldef.GL_COLOR_WRITEMASK
GL_UNPACK_ALIGNMENT = cgldef.GL_UNPACK_ALIGNMENT
GL_PACK_ALIGNMENT = cgldef.GL_PACK_ALIGNMENT
GL_MAX_TEXTURE_SIZE = cgldef.GL_MAX_TEXTURE_SIZE
GL_MAX_VIEWPORT_DIMS = cgldef.GL_MAX_VIEWPORT_DIMS
GL_SUBPIXEL_BITS = cgldef.GL_SUBPIXEL_BITS
GL_RED_BITS = cgldef.GL_RED_BITS
GL_GREEN_BITS = cgldef.GL_GREEN_BITS
GL_BLUE_BITS = cgldef.GL_BLUE_BITS
GL_ALPHA_BITS = cgldef.GL_ALPHA_BITS
GL_DEPTH_BITS = cgldef.GL_DEPTH_BITS
GL_STENCIL_BITS = cgldef.GL_STENCIL_BITS
GL_POLYGON_OFFSET_UNITS = cgldef.GL_POLYGON_OFFSET_UNITS
GL_POLYGON_OFFSET_FACTOR = cgldef.GL_POLYGON_OFFSET_FACTOR
GL_TEXTURE_BINDING_2D = cgldef.GL_TEXTURE_BINDING_2D
GL_SAMPLE_BUFFERS = cgldef.GL_SAMPLE_BUFFERS
GL_SAMPLES = cgldef.GL_SAMPLES
GL_SAMPLE_COVERAGE_VALUE = cgldef.GL_SAMPLE_COVERAGE_VALUE
GL_SAMPLE_COVERAGE_INVERT = cgldef.GL_SAMPLE_COVERAGE_INVERT
GL_NUM_COMPRESSED_TEXTURE_FORMATS = cgldef.GL_NUM_COMPRESSED_TEXTURE_FORMATS
GL_COMPRESSED_TEXTURE_FORMATS = cgldef.GL_COMPRESSED_TEXTURE_FORMATS
GL_DONT_CARE = cgldef.GL_DONT_CARE
GL_FASTEST = cgldef.GL_FASTEST
GL_NICEST = cgldef.GL_NICEST
GL_GENERATE_MIPMAP_HINT = cgldef.GL_GENERATE_MIPMAP_HINT
GL_BYTE = cgldef.GL_BYTE
GL_UNSIGNED_BYTE = cgldef.GL_UNSIGNED_BYTE
GL_SHORT = cgldef.GL_SHORT
GL_UNSIGNED_SHORT = cgldef.GL_UNSIGNED_SHORT
GL_INT = cgldef.GL_INT
GL_UNSIGNED_INT = cgldef.GL_UNSIGNED_INT
GL_FLOAT = cgldef.GL_FLOAT
GL_DEPTH_COMPONENT = cgldef.GL_DEPTH_COMPONENT
GL_ALPHA = cgldef.GL_ALPHA
GL_RGB = cgldef.GL_RGB
GL_RGBA = cgldef.GL_RGBA
GL_LUMINANCE = cgldef.GL_LUMINANCE
GL_LUMINANCE_ALPHA = cgldef.GL_LUMINANCE_ALPHA
GL_UNSIGNED_SHORT_4_4_4_4 = cgldef.GL_UNSIGNED_SHORT_4_4_4_4
GL_UNSIGNED_SHORT_5_5_5_1 = cgldef.GL_UNSIGNED_SHORT_5_5_5_1
GL_UNSIGNED_SHORT_5_6_5 = cgldef.GL_UNSIGNED_SHORT_5_6_5
GL_FRAGMENT_SHADER = cgldef.GL_FRAGMENT_SHADER
GL_VERTEX_SHADER = cgldef.GL_VERTEX_SHADER
GL_MAX_VERTEX_ATTRIBS = cgldef.GL_MAX_VERTEX_ATTRIBS
GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS = cgldef.GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS
GL_MAX_VERTEX_TEXTURE_IMAGE_UNITS = cgldef.GL_MAX_VERTEX_TEXTURE_IMAGE_UNITS
GL_MAX_TEXTURE_IMAGE_UNITS = cgldef.GL_MAX_TEXTURE_IMAGE_UNITS
GL_SHADER_TYPE = cgldef.GL_SHADER_TYPE
GL_DELETE_STATUS = cgldef.GL_DELETE_STATUS
GL_LINK_STATUS = cgldef.GL_LINK_STATUS
GL_VALIDATE_STATUS = cgldef.GL_VALIDATE_STATUS
GL_ATTACHED_SHADERS = cgldef.GL_ATTACHED_SHADERS
GL_ACTIVE_UNIFORMS = cgldef.GL_ACTIVE_UNIFORMS
GL_ACTIVE_UNIFORM_MAX_LENGTH = cgldef.GL_ACTIVE_UNIFORM_MAX_LENGTH
GL_ACTIVE_ATTRIBUTES = cgldef.GL_ACTIVE_ATTRIBUTES
GL_ACTIVE_ATTRIBUTE_MAX_LENGTH = cgldef.GL_ACTIVE_ATTRIBUTE_MAX_LENGTH
GL_SHADING_LANGUAGE_VERSION = cgldef.GL_SHADING_LANGUAGE_VERSION
GL_CURRENT_PROGRAM = cgldef.GL_CURRENT_PROGRAM
GL_NEVER = cgldef.GL_NEVER
GL_LESS = cgldef.GL_LESS
GL_EQUAL = cgldef.GL_EQUAL
GL_LEQUAL = cgldef.GL_LEQUAL
GL_GREATER = cgldef.GL_GREATER
GL_NOTEQUAL = cgldef.GL_NOTEQUAL
GL_GEQUAL = cgldef.GL_GEQUAL
GL_ALWAYS = cgldef.GL_ALWAYS
GL_KEEP = cgldef.GL_KEEP
GL_REPLACE = cgldef.GL_REPLACE
GL_INCR = cgldef.GL_INCR
GL_DECR = cgldef.GL_DECR
GL_INVERT = cgldef.GL_INVERT
GL_INCR_WRAP = cgldef.GL_INCR_WRAP
GL_DECR_WRAP = cgldef.GL_DECR_WRAP
GL_VENDOR = cgldef.GL_VENDOR
GL_RENDERER = cgldef.GL_RENDERER
GL_VERSION = cgldef.GL_VERSION
GL_EXTENSIONS = cgldef.GL_EXTENSIONS
GL_NEAREST = cgldef.GL_NEAREST
GL_LINEAR = cgldef.GL_LINEAR
GL_NEAREST_MIPMAP_NEAREST = cgldef.GL_NEAREST_MIPMAP_NEAREST
GL_LINEAR_MIPMAP_NEAREST = cgldef.GL_LINEAR_MIPMAP_NEAREST
GL_NEAREST_MIPMAP_LINEAR = cgldef.GL_NEAREST_MIPMAP_LINEAR
GL_LINEAR_MIPMAP_LINEAR = cgldef.GL_LINEAR_MIPMAP_LINEAR
GL_TEXTURE_MAG_FILTER = cgldef.GL_TEXTURE_MAG_FILTER
GL_TEXTURE_MIN_FILTER = cgldef.GL_TEXTURE_MIN_FILTER
GL_TEXTURE_WRAP_S = cgldef.GL_TEXTURE_WRAP_S
GL_TEXTURE_WRAP_T = cgldef.GL_TEXTURE_WRAP_T
GL_TEXTURE = cgldef.GL_TEXTURE
GL_TEXTURE_CUBE_MAP = cgldef.GL_TEXTURE_CUBE_MAP
GL_TEXTURE_BINDING_CUBE_MAP = cgldef.GL_TEXTURE_BINDING_CUBE_MAP
GL_TEXTURE_CUBE_MAP_POSITIVE_X = cgldef.GL_TEXTURE_CUBE_MAP_POSITIVE_X
GL_TEXTURE_CUBE_MAP_NEGATIVE_X = cgldef.GL_TEXTURE_CUBE_MAP_NEGATIVE_X
GL_TEXTURE_CUBE_MAP_POSITIVE_Y = cgldef.GL_TEXTURE_CUBE_MAP_POSITIVE_Y
GL_TEXTURE_CUBE_MAP_NEGATIVE_Y = cgldef.GL_TEXTURE_CUBE_MAP_NEGATIVE_Y
GL_TEXTURE_CUBE_MAP_POSITIVE_Z = cgldef.GL_TEXTURE_CUBE_MAP_POSITIVE_Z
GL_TEXTURE_CUBE_MAP_NEGATIVE_Z = cgldef.GL_TEXTURE_CUBE_MAP_NEGATIVE_Z
GL_MAX_CUBE_MAP_TEXTURE_SIZE = cgldef.GL_MAX_CUBE_MAP_TEXTURE_SIZE
GL_TEXTURE0 = cgldef.GL_TEXTURE0
GL_TEXTURE1 = cgldef.GL_TEXTURE1
GL_TEXTURE2 = cgldef.GL_TEXTURE2
GL_TEXTURE3 = cgldef.GL_TEXTURE3
GL_TEXTURE4 = cgldef.GL_TEXTURE4
GL_TEXTURE5 = cgldef.GL_TEXTURE5
GL_TEXTURE6 = cgldef.GL_TEXTURE6
GL_TEXTURE7 = cgldef.GL_TEXTURE7
GL_TEXTURE8 = cgldef.GL_TEXTURE8
GL_TEXTURE9 = cgldef.GL_TEXTURE9
GL_TEXTURE10 = cgldef.GL_TEXTURE10
GL_TEXTURE11 = cgldef.GL_TEXTURE11
GL_TEXTURE12 = cgldef.GL_TEXTURE12
GL_TEXTURE13 = cgldef.GL_TEXTURE13
GL_TEXTURE14 = cgldef.GL_TEXTURE14
GL_TEXTURE15 = cgldef.GL_TEXTURE15
GL_TEXTURE16 = cgldef.GL_TEXTURE16
GL_TEXTURE17 = cgldef.GL_TEXTURE17
GL_TEXTURE18 = cgldef.GL_TEXTURE18
GL_TEXTURE19 = cgldef.GL_TEXTURE19
GL_TEXTURE20 = cgldef.GL_TEXTURE20
GL_TEXTURE21 = cgldef.GL_TEXTURE21
GL_TEXTURE22 = cgldef.GL_TEXTURE22
GL_TEXTURE23 = cgldef.GL_TEXTURE23
GL_TEXTURE24 = cgldef.GL_TEXTURE24
GL_TEXTURE25 = cgldef.GL_TEXTURE25
GL_TEXTURE26 = cgldef.GL_TEXTURE26
GL_TEXTURE27 = cgldef.GL_TEXTURE27
GL_TEXTURE28 = cgldef.GL_TEXTURE28
GL_TEXTURE29 = cgldef.GL_TEXTURE29
GL_TEXTURE30 = cgldef.GL_TEXTURE30
GL_TEXTURE31 = cgldef.GL_TEXTURE31
GL_ACTIVE_TEXTURE = cgldef.GL_ACTIVE_TEXTURE
GL_REPEAT = cgldef.GL_REPEAT
GL_CLAMP_TO_EDGE = cgldef.GL_CLAMP_TO_EDGE
GL_MIRRORED_REPEAT = cgldef.GL_MIRRORED_REPEAT
GL_FLOAT_VEC2 = cgldef.GL_FLOAT_VEC2
GL_FLOAT_VEC3 = cgldef.GL_FLOAT_VEC3
GL_FLOAT_VEC4 = cgldef.GL_FLOAT_VEC4
GL_INT_VEC2 = cgldef.GL_INT_VEC2
GL_INT_VEC3 = cgldef.GL_INT_VEC3
GL_INT_VEC4 = cgldef.GL_INT_VEC4
GL_BOOL = cgldef.GL_BOOL
GL_BOOL_VEC2 = cgldef.GL_BOOL_VEC2
GL_BOOL_VEC3 = cgldef.GL_BOOL_VEC3
GL_BOOL_VEC4 = cgldef.GL_BOOL_VEC4
GL_FLOAT_MAT2 = cgldef.GL_FLOAT_MAT2
GL_FLOAT_MAT3 = cgldef.GL_FLOAT_MAT3
GL_FLOAT_MAT4 = cgldef.GL_FLOAT_MAT4
GL_SAMPLER_2D = cgldef.GL_SAMPLER_2D
GL_SAMPLER_CUBE = cgldef.GL_SAMPLER_CUBE
GL_VERTEX_ATTRIB_ARRAY_ENABLED = cgldef.GL_VERTEX_ATTRIB_ARRAY_ENABLED
GL_VERTEX_ATTRIB_ARRAY_SIZE = cgldef.GL_VERTEX_ATTRIB_ARRAY_SIZE
GL_VERTEX_ATTRIB_ARRAY_STRIDE = cgldef.GL_VERTEX_ATTRIB_ARRAY_STRIDE
GL_VERTEX_ATTRIB_ARRAY_TYPE = cgldef.GL_VERTEX_ATTRIB_ARRAY_TYPE
GL_VERTEX_ATTRIB_ARRAY_NORMALIZED = cgldef.GL_VERTEX_ATTRIB_ARRAY_NORMALIZED
GL_VERTEX_ATTRIB_ARRAY_POINTER = cgldef.GL_VERTEX_ATTRIB_ARRAY_POINTER
GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING = cgldef.GL_VERTEX_ATTRIB_ARRAY_BUFFER_BINDING
GL_COMPILE_STATUS = cgldef.GL_COMPILE_STATUS
GL_INFO_LOG_LENGTH = cgldef.GL_INFO_LOG_LENGTH
GL_SHADER_SOURCE_LENGTH = cgldef.GL_SHADER_SOURCE_LENGTH
GL_FRAMEBUFFER = cgldef.GL_FRAMEBUFFER
GL_RENDERBUFFER = cgldef.GL_RENDERBUFFER
GL_RGBA4 = cgldef.GL_RGBA4
GL_RGB5_A1 = cgldef.GL_RGB5_A1
GL_DEPTH_COMPONENT16 = cgldef.GL_DEPTH_COMPONENT16
GL_STENCIL_INDEX8 = cgldef.GL_STENCIL_INDEX8
GL_RENDERBUFFER_WIDTH = cgldef.GL_RENDERBUFFER_WIDTH
GL_RENDERBUFFER_HEIGHT = cgldef.GL_RENDERBUFFER_HEIGHT
GL_RENDERBUFFER_INTERNAL_FORMAT = cgldef.GL_RENDERBUFFER_INTERNAL_FORMAT
GL_RENDERBUFFER_RED_SIZE = cgldef.GL_RENDERBUFFER_RED_SIZE
GL_RENDERBUFFER_GREEN_SIZE = cgldef.GL_RENDERBUFFER_GREEN_SIZE
GL_RENDERBUFFER_BLUE_SIZE = cgldef.GL_RENDERBUFFER_BLUE_SIZE
GL_RENDERBUFFER_ALPHA_SIZE = cgldef.GL_RENDERBUFFER_ALPHA_SIZE
GL_RENDERBUFFER_DEPTH_SIZE = cgldef.GL_RENDERBUFFER_DEPTH_SIZE
GL_RENDERBUFFER_STENCIL_SIZE = cgldef.GL_RENDERBUFFER_STENCIL_SIZE
GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE = cgldef.GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE
GL_FRAMEBUFFER_ATTACHMENT_OBJECT_NAME = cgldef.GL_FRAMEBUFFER_ATTACHMENT_OBJECT_NAME
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_LEVEL = cgldef.GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_LEVEL
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_CUBE_MAP_FACE = cgldef.GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_CUBE_MAP_FACE
GL_COLOR_ATTACHMENT0 = cgldef.GL_COLOR_ATTACHMENT0
GL_DEPTH_ATTACHMENT = cgldef.GL_DEPTH_ATTACHMENT
GL_STENCIL_ATTACHMENT = cgldef.GL_STENCIL_ATTACHMENT
GL_NONE = cgldef.GL_NONE
GL_FRAMEBUFFER_COMPLETE = cgldef.GL_FRAMEBUFFER_COMPLETE
GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT = cgldef.GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT
GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT = cgldef.GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT
GL_FRAMEBUFFER_UNSUPPORTED = cgldef.GL_FRAMEBUFFER_UNSUPPORTED
GL_FRAMEBUFFER_BINDING = cgldef.GL_FRAMEBUFFER_BINDING
GL_RENDERBUFFER_BINDING = cgldef.GL_RENDERBUFFER_BINDING
GL_MAX_RENDERBUFFER_SIZE = cgldef.GL_MAX_RENDERBUFFER_SIZE
GL_INVALID_FRAMEBUFFER_OPERATION = cgldef.GL_INVALID_FRAMEBUFFER_OPERATION

# not working with GL standard include
GL_SHADER_BINARY_FORMATS = cgldef.GL_SHADER_BINARY_FORMATS
GL_RGB565 = cgldef.GL_RGB565
GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS = cgldef.GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS

# glGet*v
# Note: there are more, this is just what *my* hardware can find...
_GL_GET_SIZE = {
    GL_ACTIVE_TEXTURE: 1,
    GL_ALIASED_LINE_WIDTH_RANGE: 2,
    GL_ALIASED_POINT_SIZE_RANGE: 2,
    GL_ALPHA_BITS: 1,
    GL_ARRAY_BUFFER_BINDING: 1,
    GL_BLEND: 1,
    GL_BLEND_COLOR: 4,
    GL_BLEND_DST_ALPHA: 1,
    GL_BLEND_DST_RGB: 1,
    GL_BLEND_EQUATION_ALPHA: 1,
    GL_BLEND_EQUATION_RGB: 1,
    GL_BLEND_SRC_ALPHA: 1,
    GL_BLEND_SRC_RGB: 1,
    GL_BLUE_BITS: 1,
    GL_COLOR_CLEAR_VALUE: 4,
    GL_COLOR_WRITEMASK: 4,
    GL_COMPRESSED_TEXTURE_FORMATS: cgldef.GL_NUM_COMPRESSED_TEXTURE_FORMATS,
    GL_CULL_FACE: 1,
    GL_CULL_FACE_MODE: 1,
    GL_CURRENT_PROGRAM: 1,
    GL_DEPTH_BITS: 1,
    GL_DEPTH_CLEAR_VALUE: 1,
    GL_DEPTH_FUNC: 1,
    GL_DEPTH_RANGE: 2,
    GL_DEPTH_TEST: 1,
    GL_DEPTH_WRITEMASK: 1,
    GL_DITHER: 1,
    GL_ELEMENT_ARRAY_BUFFER_BINDING: 1,
    GL_FRAMEBUFFER_BINDING: 1,
    GL_FRONT_FACE: 1,
    GL_GENERATE_MIPMAP_HINT: 1,
    GL_GREEN_BITS: 1,
    GL_LINE_WIDTH: 1,
    GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS: 1,
    GL_MAX_CUBE_MAP_TEXTURE_SIZE: 1,
    GL_MAX_RENDERBUFFER_SIZE: 1,
    GL_MAX_TEXTURE_IMAGE_UNITS: 1,
    GL_MAX_TEXTURE_SIZE: 1,
    GL_MAX_VERTEX_ATTRIBS: 1,
    GL_MAX_VERTEX_TEXTURE_IMAGE_UNITS: 1,
    GL_MAX_VIEWPORT_DIMS: 2,
    GL_NUM_COMPRESSED_TEXTURE_FORMATS: 1,
    GL_PACK_ALIGNMENT: 1,
    GL_POLYGON_OFFSET_FACTOR: 1,
    GL_POLYGON_OFFSET_FILL: 1,
    GL_POLYGON_OFFSET_UNITS: 1,
    GL_RED_BITS: 1,
    GL_RENDERBUFFER_BINDING: 1,
    GL_SAMPLE_BUFFERS: 1,
    GL_SAMPLE_COVERAGE_INVERT: 1,
    GL_SAMPLE_COVERAGE_VALUE: 1,
    GL_SAMPLES: 1,
    GL_SCISSOR_BOX: 4,
    GL_SCISSOR_TEST: 1,
    GL_STENCIL_BACK_FAIL: 1,
    GL_STENCIL_BACK_FUNC: 1,
    GL_STENCIL_BACK_PASS_DEPTH_FAIL: 1,
    GL_STENCIL_BACK_PASS_DEPTH_PASS: 1,
    GL_STENCIL_BACK_REF: 1,
    GL_STENCIL_BACK_VALUE_MASK: 1,
    GL_STENCIL_BACK_WRITEMASK: 1,
    GL_STENCIL_BITS: 1,
    GL_STENCIL_CLEAR_VALUE: 1,
    GL_STENCIL_FAIL: 1,
    GL_STENCIL_FUNC: 1,
    GL_STENCIL_PASS_DEPTH_FAIL: 1,
    GL_STENCIL_PASS_DEPTH_PASS: 1,
    GL_STENCIL_REF: 1,
    GL_STENCIL_TEST: 1,
    GL_STENCIL_VALUE_MASK: 1,
    GL_STENCIL_WRITEMASK: 1,
    GL_SUBPIXEL_BITS: 1,
    GL_TEXTURE_BINDING_2D: 1,
    GL_TEXTURE_BINDING_CUBE_MAP: 1,
    GL_UNPACK_ALIGNMENT: 1,
    GL_VIEWPORT: 4,
}

# update sizes
_GL_GET_SIZE[cgldef.GL_MAX_VERTEX_UNIFORM_VECTORS] = 1
_GL_GET_SIZE[cgldef.GL_MAX_VARYING_VECTORS] = 1
_GL_GET_SIZE[cgldef.GL_MAX_FRAGMENT_UNIFORM_VECTORS] = 1
_GL_GET_SIZE[cgldef.GL_IMPLEMENTATION_COLOR_READ_FORMAT] = 1
_GL_GET_SIZE[cgldef.GL_IMPLEMENTATION_COLOR_READ_TYPE] = 1
_GL_GET_SIZE[cgldef.GL_SHADER_COMPILER] = 1
_GL_GET_SIZE[cgldef.GL_NUM_SHADER_BINARY_FORMATS] = 1
_GL_GET_SIZE[cgldef.GL_SHADER_BINARY_FORMATS] = cgldef.GL_NUM_SHADER_BINARY_FORMATS


def glActiveTexture(GLenum texture):
    '''See: `glActiveTexture() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glActiveTexture.xml>`_
    '''
    cgl.glActiveTexture(texture)

def glAttachShader(GLuint program, GLuint shader):
    '''See: `glAttachShader() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glAttachShader.xml>`_
    '''
    cgl.glAttachShader(program, shader)

def glBindAttribLocation(GLuint program, GLuint index, bytes name):
    '''See: `glBindAttribLocation() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glBindAttribLocation.xml>`_
    '''
    cgl.glBindAttribLocation(program, index, <char *>name)

def glBindBuffer(GLenum target, GLuint buffer):
    '''See: `glBindBuffer() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glBindBuffer.xml>`_
    '''
    cgl.glBindBuffer(target, buffer)

def glBindFramebuffer(GLenum target, GLuint framebuffer):
    '''See: `glBindFramebuffer() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glBindFramebuffer.xml>`_
    '''
    cgl.glBindFramebuffer(target, framebuffer)

def glBindRenderbuffer(GLenum target, GLuint renderbuffer):
    '''See: `glBindRenderbuffer() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glBindRenderbuffer.xml>`_
    '''
    cgl.glBindRenderbuffer(target, renderbuffer)

def glBindTexture(GLenum target, GLuint texture):
    '''See: `glBindTexture() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glBindTexture.xml>`_
    '''
    cgl.glBindTexture(target, texture)

def glBlendColor(GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha):
    '''See: `glBlendColor() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glBlendColor.xml>`_
    '''
    cgl.glBlendColor(red, green, blue, alpha)

def glBlendEquation(GLenum mode):
    '''See: `glBlendEquation() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glBlendEquation.xml>`_
    '''
    cgl.glBlendEquation(mode)

def glBlendEquationSeparate(GLenum modeRGB, GLenum modeAlpha):
    '''See: `glBlendEquationSeparate() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glBlendEquationSeparate.xml>`_
    '''
    cgl.glBlendEquationSeparate(modeRGB, modeAlpha)

def glBlendFunc(GLenum sfactor, GLenum dfactor):
    '''See: `glBlendFunc() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glBlendFunc.xml>`_
    '''
    cgl.glBlendFunc(sfactor, dfactor)

def glBlendFuncSeparate(GLenum srcRGB, GLenum dstRGB, GLenum srcAlpha, GLenum dstAlpha):
    '''See: `glBlendFuncSeparate() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glBlendFuncSeparate.xml>`_
    '''
    cgl.glBlendFuncSeparate(srcRGB, dstRGB, srcAlpha, dstAlpha)

def glBufferData(GLenum target, GLsizeiptr size, bytes data, GLenum usage):
    '''See: `glBufferData() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glBufferData.xml>`_
    '''
    cgl.glBufferData(target, size, <char *>data, usage)

def glBufferSubData(GLenum target, GLintptr offset, GLsizeiptr size, bytes data):
    '''See: `glBufferSubData() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glBufferSubData.xml>`_
    '''
    cgl.glBufferSubData(target, offset, size, <char *>data)

def glCheckFramebufferStatus(GLenum target):
    '''See: `glCheckFramebufferStatus() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glCheckFramebufferStatus.xml>`_
    '''
    cdef GLenum result
    result = cgl.glCheckFramebufferStatus(target)
    return result

def glClear(GLbitfield mask):
    '''See: `glClear() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glClear.xml>`_
    '''
    cgl.glClear(mask)

def glClearColor(GLclampf red, GLclampf green, GLclampf blue, GLclampf alpha):
    '''See: `glClearColor() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glClearColor.xml>`_
    '''
    cgl.glClearColor(red, green, blue, alpha)

# We don't use this symbol yet, but if we activate it, android platform crash
# >_<
#def glClearDepthf(GLclampf depth):
#    '''See: `glClearDepthf() on Kronos website
#    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glClearDepthf.xml>`_
#    '''
#    cgl.glClearDepthf(depth)

def glClearStencil(GLint s):
    '''See: `glClearStencil() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glClearStencil.xml>`_
    '''
    cgl.glClearStencil(s)

def glColorMask(GLboolean red, GLboolean green, GLboolean blue, GLboolean alpha):
    '''See: `glColorMask() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glColorMask.xml>`_
    '''
    cgl.glColorMask(red, green, blue, alpha)

def glCompileShader(GLuint shader):
    '''See: `glCompileShader() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glCompileShader.xml>`_
    '''
    cgl.glCompileShader(shader)

def glCompressedTexImage2D(GLenum target, GLint level, GLenum internalformat,
                           GLsizei width, GLsizei height, GLint border, GLsizei
                           imageSize,  bytes data):
    '''See: `glCompressedTexImage2D() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glCompressedTexImage2D.xml>`_
    '''
    cgl.glCompressedTexImage2D(target, level, internalformat, width,
                                    height, border, imageSize, <char *>data)

def glCompressedTexSubImage2D(GLenum target, GLint level, GLint xoffset, GLint
                              yoffset, GLsizei width, GLsizei height, GLenum
                              format, GLsizei imageSize,  bytes data):
    '''See: `glCompressedTexSubImage2D() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glCompressedTexSubImage2D.xml>`_
    '''
    cgl.glCompressedTexSubImage2D(target, level, xoffset, yoffset, width,
                                       height, format, imageSize, <char *>data)

def glCopyTexImage2D(GLenum target, GLint level, GLenum internalformat, GLint x, GLint y, GLsizei width, GLsizei height, GLint border):
    '''See: `glCopyTexImage2D() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glCopyTexImage2D.xml>`_
    '''
    cgl.glCopyTexImage2D(target, level, internalformat, x, y, width, height, border)

def glCopyTexSubImage2D(GLenum target, GLint level, GLint xoffset, GLint yoffset, GLint x, GLint y, GLsizei width, GLsizei height):
    '''See: `glCopyTexSubImage2D() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glCopyTexSubImage2D.xml>`_
    '''
    cgl.glCopyTexSubImage2D(target, level, xoffset, yoffset, x, y, width, height)

def glCreateProgram():
    '''See: `glCreateProgram() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glCreateProgram.xml>`_
    '''
    cdef GLuint id
    id = cgl.glCreateProgram()
    return id

def glCreateShader(GLenum type):
    '''See: `glCreateShader() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glCreateShader.xml>`_
    '''
    cdef GLuint id
    id = cgl.glCreateShader(type)
    return id

def glCullFace(GLenum mode):
    '''See: `glCullFace() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glCullFace.xml>`_
    '''
    cgl.glCullFace(mode)

def glDeleteBuffers(GLsizei n, bytes buffers):
    '''See: `glDeleteBuffers() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glDeleteBuffers.xml>`_
    '''
    cgl.glDeleteBuffers(n, <GLuint *><char *>buffers)

def glDeleteFramebuffers(GLsizei n, bytes framebuffers):
    '''See: `glDeleteFramebuffers() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glDeleteFramebuffers.xml>`_
    '''
    cgl.glDeleteFramebuffers(n, <GLuint *><char *>framebuffers)

def glDeleteProgram(GLuint program):
    '''See: `glDeleteProgram() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glDeleteProgram.xml>`_
    '''
    cgl.glDeleteProgram(program)

def glDeleteRenderbuffers(GLsizei n, bytes renderbuffers):
    '''See: `glDeleteRenderbuffers() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glDeleteRenderbuffers.xml>`_
    '''
    cgl.glDeleteRenderbuffers(n, <GLuint *><char *>renderbuffers)

def glDeleteShader(GLuint shader):
    '''See: `glDeleteShader() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glDeleteShader.xml>`_
    '''
    cgl.glDeleteShader(shader)

def glDeleteTextures(GLsizei n, bytes textures):
    '''See: `glDeleteTextures() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glDeleteTextures.xml>`_
    '''
    cgl.glDeleteTextures(n, <GLuint *><char *>textures)

def glDepthFunc(GLenum func):
    '''See: `glDepthFunc() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glDepthFunc.xml>`_
    '''
    cgl.glDepthFunc(func)

def glDepthMask(GLboolean flag):
    '''See: `glDepthMask() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glDepthMask.xml>`_
    '''
    cgl.glDepthMask(flag)

#def glDepthRangef(GLclampf zNear, GLclampf zFar):
#    '''See: `glDepthRangef() on Kronos website
#    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glDepthRangef.xml>`_
#    '''
#    cgl.glDepthRangef(zNear, zFar)

def glDetachShader(GLuint program, GLuint shader):
    '''See: `glDetachShader() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glDetachShader.xml>`_
    '''
    cgl.glDetachShader(program, shader)

def glDisable(GLenum cap):
    '''See: `glDisable() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glDisable.xml>`_
    '''
    cgl.glDisable(cap)

def glDisableVertexAttribArray(GLuint index):
    '''See: `glDisableVertexAttribArray() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glDisableVertexAttribArray.xml>`_
    '''
    cgl.glDisableVertexAttribArray(index)

def glDrawArrays(GLenum mode, GLint first, GLsizei count):
    '''See: `glDrawArrays() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glDrawArrays.xml>`_
    '''
    cgl.glDrawArrays(mode, first, count)

def glDrawElements(GLenum mode, GLsizei count, GLenum type, indices):
    '''See: `glDrawElements() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glDrawElements.xml>`_
    '''
    cdef void *ptr = NULL
    if isinstance(indices, bytes):
        ptr = <void *>(<char *>(<bytes>indices))
    elif isinstance(indices, (long, int)):
        ptr = <void *>(<long>indices)
    else:
        raise TypeError("Argument 'indices' has incorrect type (expected bytes or int).")
    cgl.glDrawElements(mode, count, type, ptr)

def glEnable(GLenum cap):
    '''See: `glEnable() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glEnable.xml>`_
    '''
    cgl.glEnable(cap)

def glEnableVertexAttribArray(GLuint index):
    '''See: `glEnableVertexAttribArray() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glEnableVertexAttribArray.xml>`_
    '''
    cgl.glEnableVertexAttribArray(index)

def glFinish():
    '''See: `glFinish() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glFinish.xml>`_
    '''
    cgl.glFinish()

def glFlush():
    '''See: `glFlush() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glFlush.xml>`_
    '''
    cgl.glFlush()

def glFramebufferRenderbuffer(GLenum target, GLenum attachment, GLenum renderbuffertarget, GLuint renderbuffer):
    '''See: `glFramebufferRenderbuffer() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glFramebufferRenderbuffer.xml>`_
    '''
    cgl.glFramebufferRenderbuffer(target, attachment, renderbuffertarget, renderbuffer)

def glFramebufferTexture2D(GLenum target, GLenum attachment, GLenum textarget, GLuint texture, GLint level):
    '''See: `glFramebufferTexture2D() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glFramebufferTexture2D.xml>`_
    '''
    cgl.glFramebufferTexture2D(target, attachment, textarget, texture, level)

def glFrontFace(GLenum mode):
    '''See: `glFrontFace() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glFrontFace.xml>`_
    '''
    cgl.glFrontFace(mode)

def glGenBuffers(GLsizei n):
    '''See: `glGenBuffers() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGenBuffers.xml>`_

    Unlike the C specification, the value will be the result of call.
    '''
    cdef GLuint *d = _genBegin(n)
    cgl.glGenBuffers(n, d)
    return _genEnd(n, d)

def glGenerateMipmap(GLenum target):
    '''See: `glGenerateMipmap() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGenerateMipmap.xml>`_
    '''
    cgl.glGenerateMipmap(target)

def glGenFramebuffers(GLsizei n):
    '''See: `glGenFramebuffers() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGenFramebuffers.xml>`_

    Unlike the C specification, the value will be the result of call.
    '''
    cdef GLuint *d = _genBegin(n)
    cgl.glGenFramebuffers(n, d)
    return _genEnd(n, d)

def glGenRenderbuffers(GLsizei n):
    '''See: `glGenRenderbuffers() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGenRenderbuffers.xml>`_

    Unlike the C specification, the value will be the result of call.
    '''
    cdef GLuint *d = _genBegin(n)
    cgl.glGenRenderbuffers(n, d)
    return _genEnd(n, d)

def glGenTextures(GLsizei n):
    '''See: `glGenTextures() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGenTextures.xml>`_

    Unlike the C specification, the value will be the result of call.
    '''
    cdef GLuint *d = _genBegin(n)
    cgl.glGenTextures(n, d)
    return _genEnd(n, d)

def glGetActiveAttrib(GLuint program, GLuint index):
    '''See: `glGetActiveAttrib() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetActiveAttrib.xml>`_

    Unlike the C specification, the value will be the result of call.
    '''
    cdef GLint size = 0
    cdef GLenum gl_type = 0
    cdef GLchar *name
    cdef bytes p_name
    name = <GLchar *>malloc(sizeof(GLchar) * 255)
    if name == NULL:
        raise MemoryError('glGetActiveAttrib()')
    cgl.glGetActiveAttrib(program, index, 255, NULL, &size, &gl_type, name)
    p_name = <char *>name
    free(name)
    return p_name, size, gl_type

def glGetActiveUniform(GLuint program, GLuint index):
    '''See: `glGetActiveUniform() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetActiveUniform.xml>`_

    Unlike the C specification, the value will be the result of call.
    '''
    cdef GLint size = 0
    cdef GLenum gl_type = 0
    cdef GLchar *name
    cdef bytes p_name
    name = <GLchar *>malloc(sizeof(GLchar) * 255)
    if name == NULL:
        raise MemoryError('glGetActiveUniform()')
    cgl.glGetActiveUniform(program, index, 255, NULL, &size, &gl_type, name)
    p_name = <char *>name
    free(name)
    return p_name, size, gl_type

def glGetAttachedShaders(GLuint program, GLsizei maxcount):
    '''See: `glGetAttachedShaders() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetAttachedShaders.xml>`_

    Unlike the C specification, the value will be the result of call.
    '''
    cdef GLsizei count = 1024
    cdef GLuint *shaders = _genBegin(count)
    cgl.glGetAttachedShaders(program, count, &count, shaders)
    return _genEnd(count, shaders)

def glGetAttribLocation(GLuint program,  bytes name):
    '''See: `glGetAttribLocation() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetAttribLocation.xml>`_

    Unlike the C specification, the value will be the result of call.
    '''
    return cgl.glGetAttribLocation(program, <char *>name)

def glGetBooleanv(GLenum pname):
    '''See: `glGetBooleanv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetBooleanv.xml>`_

    Unlike the C specification, the value will be the result of call.
    '''
    cdef GLboolean *params = <GLboolean *>malloc(_GL_GET_SIZE[pname] * sizeof(GLboolean))
    if params == NULL:
        raise MemoryError('glGetBooleanv()')
    cgl.glGetBooleanv(pname, params)
    cdef out = [params[i] for i in xrange(_GL_GET_SIZE[pname])]
    free(params)
    return out

def glGetBufferParameteriv(GLenum target, GLenum pname):
    '''See: `glGetBufferParameteriv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetBufferParameteriv.xml>`_

    Unlike the C specification, the value will be the result of call.
    '''
    cdef GLint *params = <GLint *>malloc(_GL_GET_SIZE[pname] * sizeof(GLint))
    if params == NULL:
        raise MemoryError('glGetBufferParameteriv()')
    cgl.glGetBufferParameteriv(target, pname, params)
    cdef out = [params[i] for i in xrange(_GL_GET_SIZE[pname])]
    free(params)
    return out

def glGetError():
    '''See: `glGetError() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetError.xml>`_

    Unlike the C specification, the value will be the result of call.
    '''
    return cgl.glGetError()

def glGetFloatv(GLenum pname):
    '''See: `glGetFloatv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetFloatv.xml>`_

    Unlike the C specification, the value will be the result of call.
    '''
    cdef GLfloat *params = <GLfloat *>malloc(_GL_GET_SIZE[pname] * sizeof(GLfloat))
    if params == NULL:
        raise MemoryError('glGetFloatv()')
    cgl.glGetFloatv(pname, params)
    cdef out = [params[i] for i in xrange(_GL_GET_SIZE[pname])]
    free(params)
    return out

def glGetFramebufferAttachmentParameteriv(GLenum target, GLenum attachment, GLenum pname):
    '''See: `glGetFramebufferAttachmentParameteriv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetFramebufferAttachmentParameteriv.xml>`_

    Unlike the C specification, the value will be the result of call.
    '''
    cdef GLint *params = <GLint *>malloc(_GL_GET_SIZE[pname] * sizeof(GLint))
    if params == NULL:
        raise MemoryError('glGetFramebufferAttachmentParameteriv()')
    cgl.glGetFramebufferAttachmentParameteriv(target, attachment, pname, params)
    cdef out = [params[i] for i in xrange(_GL_GET_SIZE[pname])]
    free(params)
    return out

def glGetIntegerv(GLenum pname):
    '''See: `glGetIntegerv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetIntegerv.xml>`_

    Unlike the C specification, the value(s) will be the result of the call
    '''
    cdef GLint *params = <GLint *>malloc(_GL_GET_SIZE[pname] * sizeof(GLint) * 2)
    if params == NULL:
        raise MemoryError('glGetIntegerv()')
    cgl.glGetIntegerv(pname, params)
    cdef out = [params[i] for i in xrange(_GL_GET_SIZE[pname])]
    free(params)
    return out

def glGetProgramiv(GLuint program, GLenum pname):
    '''See: `glGetProgramiv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetProgramiv.xml>`_

    Unlike the C specification, the value(s) will be the result of the call
    '''
    cdef GLint params = 0
    cgl.glGetProgramiv(program, pname, &params)
    return params

def glGetProgramInfoLog(GLuint program, GLsizei bufsize):
    '''See: `glGetProgramInfoLog() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetProgramInfoLog.xml>`_

    Unlike the C specification, the source code will be returned as a string.
    '''
    cdef GLint size = 0
    cdef GLchar *infolog
    cdef bytes p_infolog
    infolog = <GLchar *>malloc(sizeof(GLchar) * 2048)
    if infolog == NULL:
        raise MemoryError('glGetProgramInfoLog()')
    cgl.glGetProgramInfoLog(program, 2048, &size, infolog)
    p_infolog = <char *>infolog
    free(infolog)
    return p_infolog

def glGetRenderbufferParameteriv(GLenum target, GLenum pname):
    '''See: `glGetRenderbufferParameteriv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetRenderbufferParameteriv.xml>`_

    Unlike the C specification, the value will be the result of call.
    '''
    cdef GLint params = 0
    cgl.glGetRenderbufferParameteriv(target, pname, &params)
    return params

def glGetShaderiv(GLuint shader, GLenum pname):
    '''See: `glGetShaderiv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetShaderiv.xml>`_

    Unlike the C specification, the value will be the result of call.
    '''
    cdef GLint params = 0
    cgl.glGetShaderiv(shader, pname, &params)
    return params

def glGetShaderInfoLog(GLuint shader, GLsizei bufsize):
    '''See: `glGetShaderInfoLog() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetShaderInfoLog.xml>`_

    Unlike the C specification, the source code will be returned as a string.
    '''
    cdef GLint size = 0
    cdef GLchar *infolog
    cdef bytes p_infolog
    infolog = <GLchar *>malloc(sizeof(GLchar) * 2048)
    if infolog == NULL:
        raise MemoryError('glGetShaderInfoLog()')
    cgl.glGetShaderInfoLog(shader, 2048, &size, infolog)
    p_infolog = <char *>infolog
    free(infolog)
    return p_infolog

def glGetShaderPrecisionFormat(GLenum shadertype, GLenum precisiontype): #, GLint* range, GLint* precision):
    '''See: `glGetShaderPrecisionFormat() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetShaderPrecisionFormat.xml>`_

    .. warning:: Not implemented yet.
    '''
    raise NotImplemented()
    #cgl.glGetShaderPrecisionFormat(shadertype, precisiontype, range, precision)

def glGetShaderSource(GLuint shader):
    '''See: `glGetShaderSource() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetShaderSource.xml>`_

    Unlike the C specification, the source code will be returned as a string.
    '''
    cdef GLint size = 0
    cdef GLchar *source
    cdef bytes p_source
    source = <GLchar *>malloc(sizeof(GLchar) * 65535)
    if source == NULL:
        raise MemoryError('glGetShaderInfoLog()')
    cgl.glGetShaderSource(shader, 65535, &size, source)
    p_source = <char *>source
    free(source)
    return p_source

def glGetString(GLenum name):
    '''See: `glGetString() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetString.xml>`_

    Unlike the C specification, the value will be returned as a string.
    '''
    cdef bytes p_string
    p_string = <char *>cgl.glGetString(name)
    return p_string

def glGetTexParameterfv(GLenum target, GLenum pname):
    '''See: `glGetTexParameterfv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetTexParameterfv.xml>`_
    '''
    cdef GLfloat params = 0
    cgl.glGetTexParameterfv(target, pname, &params)
    return params

def glGetTexParameteriv(GLenum target, GLenum pname):
    '''See: `glGetTexParameteriv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetTexParameteriv.xml>`_
    '''
    cdef GLint params = 0
    cgl.glGetTexParameteriv(target, pname, &params)
    return params

def glGetUniformfv(GLuint program, GLint location):
    '''See: `glGetUniformfv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetUniformfv.xml>`_
    '''
    cdef GLfloat params = 0
    cgl.glGetUniformfv(program, location, &params)
    return params

def glGetUniformiv(GLuint program, GLint location):
    '''See: `glGetUniformiv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetUniformiv.xml>`_
    '''
    cdef GLint params = 0
    cgl.glGetUniformiv(program, location, &params)
    return params

def glGetUniformLocation(GLuint program, bytes name):
    '''See: `glGetUniformLocation() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetUniformLocation.xml>`_
    '''
    return cgl.glGetUniformLocation(program, <char *>name)

def glGetVertexAttribfv(GLuint index, GLenum pname):
    '''See: `glGetVertexAttribfv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetVertexAttribfv.xml>`_
    '''
    cdef GLfloat params = 0
    cgl.glGetVertexAttribfv(index, pname, &params)
    return params

def glGetVertexAttribiv(GLuint index, GLenum pname):
    '''See: `glGetVertexAttribiv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetVertexAttribiv.xml>`_
    '''
    cdef GLint params = 0
    cgl.glGetVertexAttribiv(index, pname, &params)
    return params

def glGetVertexAttribPointerv(GLuint index, GLenum pname):#, GLvoid** pointer):
    '''See: `glGetVertexAttribPointerv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glGetVertexAttribPointerv.xml>`_

    .. warning:: Not implemented yet.
    '''
    raise NotImplemented()
    #cgl.glGetVertexAttribPointerv(index, pname, pointer)

def glHint(GLenum target, GLenum mode):
    '''See: `glHint() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glHint.xml>`_
    '''
    cgl.glHint(target, mode)

def glIsBuffer(GLuint buffer):
    '''See: `glIsBuffer() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glIsBuffer.xml>`_
    '''
    return cgl.glIsBuffer(buffer)

def glIsEnabled(GLenum cap):
    '''See: `glIsEnabled() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glIsEnabled.xml>`_
    '''
    return cgl.glIsEnabled(cap)

def glIsFramebuffer(GLuint framebuffer):
    '''See: `glIsFramebuffer() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glIsFramebuffer.xml>`_
    '''
    return cgl.glIsFramebuffer(framebuffer)

def glIsProgram(GLuint program):
    '''See: `glIsProgram() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glIsProgram.xml>`_
    '''
    return cgl.glIsProgram(program)

def glIsRenderbuffer(GLuint renderbuffer):
    '''See: `glIsRenderbuffer() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glIsRenderbuffer.xml>`_
    '''
    return cgl.glIsRenderbuffer(renderbuffer)

def glIsShader(GLuint shader):
    '''See: `glIsShader() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glIsShader.xml>`_
    '''
    return cgl.glIsShader(shader)

def glIsTexture(GLuint texture):
    '''See: `glIsTexture() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glIsTexture.xml>`_
    '''
    return cgl.glIsTexture(texture)

def glLineWidth(GLfloat width):
    '''See: `glLineWidth() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glLineWidth.xml>`_
    '''
    cgl.glLineWidth(width)

def glLinkProgram(GLuint program):
    '''See: `glLinkProgram() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glLinkProgram.xml>`_
    '''
    cgl.glLinkProgram(program)

def glPixelStorei(GLenum pname, GLint param):
    '''See: `glPixelStorei() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glPixelStorei.xml>`_
    '''
    cgl.glPixelStorei(pname, param)

def glPolygonOffset(GLfloat factor, GLfloat units):
    '''See: `glPolygonOffset() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glPolygonOffset.xml>`_
    '''
    cgl.glPolygonOffset(factor, units)

def glReadPixels(GLint x, GLint y, GLsizei width, GLsizei height, GLenum format,
                 GLenum type): #, GLvoid* pixels):
    '''See: `glReadPixels() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glReadPixels.xml>`_

    We support only GL_RGB/GL_RGBA as a format and GL_UNSIGNED_BYTE as a
    type.
    '''
    assert(format in (GL_RGB, GL_RGBA))
    assert(type == GL_UNSIGNED_BYTE)

    cdef object py_pixels = None
    cdef long size
    cdef char *data

    size = width * height * sizeof(GLubyte)
    if format == GL_RGB:
        size *= 3
    else:
        size *= 4
    data = <char *>malloc(size)
    if data == NULL:
        raise MemoryError('glReadPixels()')

    cgl.glPixelStorei(GL_PACK_ALIGNMENT, 1)
    cgl.glReadPixels(x, y, width, height, format, type, data)
    try:
        py_pixels = data[:size]
    finally:
        free(data)

    return py_pixels

# XXX This one is commented out because a) it's not necessary and
#                       b) it's breaking on OSX for some reason
def glReleaseShaderCompiler():
    '''See: `glReleaseShaderCompiler() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glReleaseShaderCompiler.xml>`_

    .. warning:: Not implemented yet.
    '''
    raise NotImplemented()
#    cgl.glReleaseShaderCompiler()

def glRenderbufferStorage(GLenum target, GLenum internalformat, GLsizei width, GLsizei height):
    '''See: `glRenderbufferStorage() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glRenderbufferStorage.xml>`_
    '''
    cgl.glRenderbufferStorage(target, internalformat, width, height)

def glSampleCoverage(GLclampf value, GLboolean invert):
    '''See: `glSampleCoverage() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glSampleCoverage.xml>`_
    '''
    cgl.glSampleCoverage(value, invert)

def glScissor(GLint x, GLint y, GLsizei width, GLsizei height):
    '''See: `glScissor() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glScissor.xml>`_
    '''
    cgl.glScissor(x, y, width, height)

def glShaderBinary():#GLsizei n,  GLuint* shaders, GLenum binaryformat,  bytes GLvoid* binary, GLsizei length):
    '''See: `glShaderBinary() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glShaderBinary.xml>`_

    .. warning:: Not implemented yet.
    '''
    #cgl.glShaderBinary(n, shaders, binaryformat, binary, length)
    raise NotImplemented()

def glShaderSource(GLuint shader, bytes source):
    '''See: `glShaderSource() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glShaderSource.xml>`_
    '''
    cdef const_char_ptr c_source = <const_char_ptr>source
    cgl.glShaderSource(shader, 1, &c_source, NULL)

def glStencilFunc(GLenum func, GLint ref, GLuint mask):
    '''See: `glStencilFunc() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glStencilFunc.xml>`_
    '''
    cgl.glStencilFunc(func, ref, mask)

def glStencilFuncSeparate(GLenum face, GLenum func, GLint ref, GLuint mask):
    '''See: `glStencilFuncSeparate() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glStencilFuncSeparate.xml>`_
    '''
    cgl.glStencilFuncSeparate(face, func, ref, mask)

def glStencilMask(GLuint mask):
    '''See: `glStencilMask() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glStencilMask.xml>`_
    '''
    cgl.glStencilMask(mask)

def glStencilMaskSeparate(GLenum face, GLuint mask):
    '''See: `glStencilMaskSeparate() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glStencilMaskSeparate.xml>`_
    '''
    cgl.glStencilMaskSeparate(face, mask)

def glStencilOp(GLenum fail, GLenum zfail, GLenum zpass):
    '''See: `glStencilOp() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glStencilOp.xml>`_
    '''
    cgl.glStencilOp(fail, zfail, zpass)

def glStencilOpSeparate(GLenum face, GLenum fail, GLenum zfail, GLenum zpass):
    '''See: `glStencilOpSeparate() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glStencilOpSeparate.xml>`_
    '''
    cgl.glStencilOpSeparate(face, fail, zfail, zpass)

def glTexImage2D(GLenum target, GLint level, GLint internalformat, GLsizei
                 width, GLsizei height, GLint border, GLenum format, GLenum
                 type,  bytes pixels):
    '''See: `glTexImage2D() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glTexImage2D.xml>`_
    '''
    cgl.glTexImage2D(target, level, internalformat, width, height, border,
                          format, type, <GLvoid *><char *>pixels)

def glTexParameterf(GLenum target, GLenum pname, GLfloat param):
    '''See: `glTexParameterf() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glTexParameterf.xml>`_
    '''
    cgl.glTexParameterf(target, pname, param)

def glTexParameterfv(GLenum target, GLenum pname):#,  GLfloat* params):
    '''See: `glTexParameterfv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glTexParameterfv.xml>`_

    .. warning:: Not implemented yet.
    '''
    #cgl.glTexParameterfv(target, pname, params)
    raise NotImplemented()

def glTexParameteri(GLenum target, GLenum pname, GLint param):
    '''See: `glTexParameteri() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glTexParameteri.xml>`_
    '''
    cgl.glTexParameteri(target, pname, param)

def glTexParameteriv(GLenum target, GLenum pname):#,  GLint* params):
    '''See: `glTexParameteriv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glTexParameteriv.xml>`_

    .. warning:: Not implemented yet.
    '''
    #cgl.glTexParameteriv(target, pname, params)
    raise NotImplemented()

def glTexSubImage2D(GLenum target, GLint level, GLint xoffset, GLint yoffset,
                    GLsizei width, GLsizei height, GLenum format, GLenum type,
                    bytes pixels):
    '''See: `glTexSubImage2D() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glTexSubImage2D.xml>`_
    '''
    cgl.glTexSubImage2D(target, level, xoffset, yoffset, width, height,
                             format, type, <GLvoid *><char *>pixels)

def glUniform1f(GLint location, GLfloat x):
    '''See: `glUniform1f() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniform1f.xml>`_
    '''
    cgl.glUniform1f(location, x)

def glUniform1fv(GLint location, GLsizei count):#,  GLfloat* v):
    '''See: `glUniform1fv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniform1fv.xml>`_

    .. warning:: Not implemented yet.
    '''
    #cgl.glUniform1fv(location, count, v)
    raise NotImplemented()

def glUniform1i(GLint location, GLint x):
    '''See: `glUniform1i() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniform1i.xml>`_
    '''
    cgl.glUniform1i(location, x)

def glUniform1iv(GLint location, GLsizei count):#,  GLint* v):
    '''See: `glUniform1iv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniform1iv.xml>`_

    .. warning:: Not implemented yet.
    '''
    #cgl.glUniform1iv(location, count, v)
    raise NotImplemented()

def glUniform2f(GLint location, GLfloat x, GLfloat y):
    '''See: `glUniform2f() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniform2f.xml>`_
    '''
    cgl.glUniform2f(location, x, y)

def glUniform2fv(GLint location, GLsizei count):#,  GLfloat* v):
    '''See: `glUniform2fv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniform2fv.xml>`_

    .. warning:: Not implemented yet.
    '''
    #cgl.glUniform2fv(location, count, v)
    raise NotImplemented()

def glUniform2i(GLint location, GLint x, GLint y):
    '''See: `glUniform2i() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniform2i.xml>`_
    '''
    cgl.glUniform2i(location, x, y)

def glUniform2iv(GLint location, GLsizei count):#,  GLint* v):
    '''See: `glUniform2iv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniform2iv.xml>`_

    .. warning:: Not implemented yet.
    '''
    #cgl.glUniform2iv(location, count, v)
    raise NotImplemented()

def glUniform3f(GLint location, GLfloat x, GLfloat y, GLfloat z):
    '''See: `glUniform3f() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniform3f.xml>`_
    '''
    cgl.glUniform3f(location, x, y, z)

def glUniform3fv(GLint location, GLsizei count):#,  GLfloat* v):
    '''See: `glUniform3fv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniform3fv.xml>`_

    .. warning:: Not implemented yet.
    '''
    #cgl.glUniform3fv(location, count, v)
    raise NotImplemented()

def glUniform3i(GLint location, GLint x, GLint y, GLint z):
    '''See: `glUniform3i() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniform3i.xml>`_
    '''
    cgl.glUniform3i(location, x, y, z)

def glUniform3iv(GLint location, GLsizei count):#,  GLint* v):
    '''See: `glUniform3iv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniform3iv.xml>`_

    .. warning:: Not implemented yet.
    '''
    #cgl.glUniform3iv(location, count, v)
    raise NotImplemented()

def glUniform4f(GLint location, GLfloat x, GLfloat y, GLfloat z, GLfloat w):
    '''See: `glUniform4f() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniform4f.xml>`_

    .. warning:: Not implemented yet.
    '''
    cgl.glUniform4f(location, x, y, z, w)

def glUniform4fv(GLint location, GLsizei count):#,  GLfloat* v):
    '''See: `glUniform4fv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniform4fv.xml>`_

    .. warning:: Not implemented yet.
    '''
    #cgl.glUniform4fv(location, count, v)
    raise NotImplemented()

def glUniform4i(GLint location, GLint x, GLint y, GLint z, GLint w):
    '''See: `glUniform4i() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniform4i.xml>`_
    '''
    cgl.glUniform4i(location, x, y, z, w)

def glUniform4iv(GLint location, GLsizei count):#,  GLint* v):
    '''See: `glUniform4iv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniform4iv.xml>`_

    .. warning:: Not implemented yet.
    '''
    #cgl.glUniform4iv(location, count, v)
    raise NotImplemented()

def glUniformMatrix2fv(GLint location, GLsizei count):#, GLboolean transpose, bytes values):
    '''See: `glUniformMatrix2fv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniformMatrix2fv.xml>`_

    .. warning:: Not implemented yet.
    '''
    #cgl.glUniformMatrix2fv(location, count, transpose, <GLfloat*>ptr_value)
    raise NotImplemented()

def glUniformMatrix3fv(GLint location, GLsizei count):#, GLboolean transpose,  bytes values):
    '''See: `glUniformMatrix3fv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniformMatrix3fv.xml>`_

    .. warning:: Not implemented yet.
    '''
    # cgl.glUniformMatrix3fv(location, count, transpose, <GLfloat*>ptr_value)
    raise NotImplemented()

def glUniformMatrix4fv(GLint location, GLsizei count, GLboolean transpose,  bytes value):
    '''See: `glUniformMatrix4fv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUniformMatrix4fv.xml>`_
    '''
    cgl.glUniformMatrix4fv(location, count, transpose, <GLfloat*>(<char *>value))

def glUseProgram(GLuint program):
    '''See: `glUseProgram() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glUseProgram.xml>`_
    '''
    cgl.glUseProgram(program)

def glValidateProgram(GLuint program):
    '''See: `glValidateProgram() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glValidateProgram.xml>`_
    '''
    cgl.glValidateProgram(program)

def glVertexAttrib1f(GLuint indx, GLfloat x):
    '''See: `glVertexAttrib1f() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glVertexAttrib1f.xml>`_
    '''
    cgl.glVertexAttrib1f(indx, x)

def glVertexAttrib1fv(GLuint indx, list values):
    '''See: `glVertexAttrib1fv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glVertexAttrib1fv.xml>`_

    .. warning:: Not implemented yet.
    '''
    #cgl.glVertexAttrib1fv(indx, values)
    raise NotImplemented()

def glVertexAttrib2f(GLuint indx, GLfloat x, GLfloat y):
    '''See: `glVertexAttrib2f() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glVertexAttrib2f.xml>`_
    '''
    cgl.glVertexAttrib2f(indx, x, y)

def glVertexAttrib2fv(GLuint indx, list values):
    '''See: `glVertexAttrib2fv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glVertexAttrib2fv.xml>`_

    .. warning:: Not implemented yet.
    '''
    #cgl.glVertexAttrib2fv(indx, values)
    raise NotImplemented()

def glVertexAttrib3f(GLuint indx, GLfloat x, GLfloat y, GLfloat z):
    '''See: `glVertexAttrib3f() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glVertexAttrib3f.xml>`_
    '''
    cgl.glVertexAttrib3f(indx, x, y, z)

def glVertexAttrib3fv(GLuint indx, list values):
    '''See: `glVertexAttrib3fv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glVertexAttrib3fv.xml>`_

    .. warning:: Not implemented yet.
    '''
    #cgl.glVertexAttrib3fv(indx, values)
    raise NotImplemented()

def glVertexAttrib4f(GLuint indx, GLfloat x, GLfloat y, GLfloat z, GLfloat w):
    '''See: `glVertexAttrib4f() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glVertexAttrib4f.xml>`_
    '''
    cgl.glVertexAttrib4f(indx, x, y, z, w)

def glVertexAttrib4fv(GLuint indx, list values):
    '''See: `glVertexAttrib4fv() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glVertexAttrib4fv.xml>`_

    .. warning:: Not implemented yet.
    '''
    #cgl.glVertexAttrib4fv(indx, values)
    raise NotImplemented()

def glVertexAttribPointer(GLuint index, GLint size, GLenum type, GLboolean normalized, GLsizei stride, data):
    '''See: `glVertexAttribPointer() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glVertexAttribPointer.xml>`_

    '''
    cdef void *ptr = NULL
    if isinstance(data, bytes):
        ptr = <void *>(<char *>(<bytes>data))
    elif isinstance(data, (long, int)):
        ptr = <void *>(<long>data)
    else:
        raise TypeError("Argument 'data' has incorrect type (expected bytes or int).")
    cgl.glVertexAttribPointer(index, size, type, normalized, stride, ptr)

def glViewport(GLint x, GLint y, GLsizei width, GLsizei height):
    '''See: `glViewport() on Kronos website
    <http://www.khronos.org/opengles/sdk/docs/man/xhtml/glViewport.xml>`_
    '''
    cgl.glViewport(x, y, width, height)


def gl_init_symbols(allowed=[], ignored=[]):
    cgl_init(allowed, ignored)
