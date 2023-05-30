/**
 * Includes GL headers.
 */
#ifndef __gl_redirect_h_
#define __gl_redirect_h_

#include "config.h"

#if defined(_WIN32)
    #include <windows.h>
    #include <string.h>
#endif /* _WIN32 */

#define GL_FIXED                                    0x140C
#define GL_MAX_VERTEX_UNIFORM_VECTORS               0x8DFB
#define GL_MAX_VARYING_VECTORS                      0x8DFC
#define GL_MAX_FRAGMENT_UNIFORM_VECTORS             0x8DFD
#define GL_IMPLEMENTATION_COLOR_READ_TYPE           0x8B9A
#define GL_IMPLEMENTATION_COLOR_READ_FORMAT         0x8B9B
#define GL_SHADER_COMPILER                          0x8DFA
#define GL_NUM_SHADER_BINARY_FORMATS                0x8DF9
#define GL_LOW_FLOAT                                0x8DF0
#define GL_MEDIUM_FLOAT                             0x8DF1
#define GL_HIGH_FLOAT                               0x8DF2
#define GL_LOW_INT                                  0x8DF3
#define GL_MEDIUM_INT                               0x8DF4
#define GL_HIGH_INT                                 0x8DF5
#define GL_SHADER_BINARY_FORMATS                    0x8DF8
#define GL_RGB565                                   0x8D62
#define GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS        0x8CD9
#define GL_FRAMEBUFFER_UNDEFINED_OES                0x8219
#define GL_DEPTH24_STENCIL8_OES                     0x88F0

#if __USE_OPENGL_MOCK
    #include "common_subset.h"
#elif defined(_WIN32)
    #include <GL/glew.h>
    #define GL_GLEXT_PROTOTYPES
    #define GL_APICALL
    #define GL_APIENTRY
    #ifndef GL_EXT_blend_func_extended
    #define GL_EXT_blend_func_extended
    #endif
    #define GL_EXT_disjoint_timer_query
    #ifndef GL_EXT_geometry_shader
    #define GL_EXT_geometry_shader
    #endif
    #ifndef GL_EXT_multisampled_render_to_texture
    #define GL_EXT_multisampled_render_to_texture
    #endif
    #define GL_EXT_texture_border_clamp
    #define GL_EXT_texture_buffer
    #ifndef GL_EXT_texture_storage
    #define GL_EXT_texture_storage
    #endif

#else

#	if __USE_OPENGL_ES2
#		if __APPLE__
#			include "common_subset.h"
#		else
#			include <GLES2/gl2.h>
#			include <GLES2/gl2ext.h>
#		endif
#	else
#		ifdef __APPLE__
#			include <OpenGL/gl.h>
#			include <OpenGL/glext.h>
#		else
#			define GL_GLEXT_PROTOTYPES
#			include <GL/gl.h>
#			include <GL/glext.h>
#		endif
#		define GL_SHADER_BINARY_FORMATS					0x8DF8
#		define GL_RGB565								0x8D62
#		define GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS 	0x8CD9
#   endif



#   ifndef GL_DEPTH24_STENCIL8
#       define GL_DEPTH24_STENCIL8                      GL_DEPTH24_STENCIL8_OES
#   endif

#endif /* defined(_WIN32) */

// In the webserver / unittest / buildbot case, we are compiling and running
// kivy in an headless env, without proper GL support.
// This is a hack to prevent to link with wrong symbol. :(
#if __USE_MESAGL == 1
#	define glBlendEquationSeparate(x, y)
#	define glDepthRangef glDepthRange
#	define glClearDepthf glClearDepth

// C redirection to prevent warning of undeclared symbol
// (these functions are not existing in GLES2, but if we are using GLES2
// headers with GL library, we need to declare them.)
GL_APICALL void GL_APIENTRY glDepthRange( GLclampf near_val, GLclampf far_val );
GL_APICALL void GL_APIENTRY glClearDepth( GLclampf depth );

#endif

#endif /* __gl_redirect_h_ */
