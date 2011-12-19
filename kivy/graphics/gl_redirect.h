/**
 * Redirect the inclusion of GL file to the selected provider
 */

#include "config.h"

#if __USE_GLEW
#	include <GL/glew.h>
#	define GL_FIXED                          		0x140C
#	define GL_MAX_VERTEX_UNIFORM_VECTORS       		0x8DFB
#	define GL_MAX_VARYING_VECTORS              		0x8DFC
#	define GL_MAX_FRAGMENT_UNIFORM_VECTORS     		0x8DFD
#	define GL_IMPLEMENTATION_COLOR_READ_TYPE   		0x8B9A
#	define GL_IMPLEMENTATION_COLOR_READ_FORMAT 		0x8B9B
#	define GL_SHADER_COMPILER          			    0x8DFA
#	define GL_NUM_SHADER_BINARY_FORMATS		     	0x8DF9
#	define GL_LOW_FLOAT                		     	0x8DF0
#	define GL_MEDIUM_FLOAT             		     	0x8DF1
#	define GL_HIGH_FLOAT               		     	0x8DF2
#	define GL_LOW_INT                  		     	0x8DF3
#	define GL_MEDIUM_INT               		     	0x8DF4
#	define GL_HIGH_INT                 		     	0x8DF5
#	define GL_SHADER_BINARY_FORMATS					0x8DF8
#	define GL_RGB565								0x8D62
#	define GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS 	0x8CD9
#else
#	if __USE_OPENGL_ES2
#		if __APPLE__
#			include "common_subset.h"
#		else
#			include <GLES2/gl2.h>
#		endif
#	else
#		ifdef __APPLE__
#			include <OpenGL/gl.h>
#		else
#			define GL_GLEXT_PROTOTYPES
#			include <GL/gl.h>
#			include <GL/glext.h>
#		endif
#		define GL_SHADER_BINARY_FORMATS					0x8DF8
#		define GL_RGB565								0x8D62
#		define GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS 	0x8CD9
#endif

// In the webserver / unittest / buildbot case, we are compiling and running
// kivy in an headless env, without proper GL support.
// This is a hack to prevent to link with wrong symbol. :(
#if __USE_MESAGL
#	define glBlendEquationSeparate(x, y)
#	define glDepthRangef glDepthRange
#	define glClearDepthf glClearDepth

// C redirection to prevent warning of undeclared symbol
// (theses functions are not existing in GLES2, but if we are using GLES2
// headers with GL library, we need to declare them.)
GL_APICALL void GL_APIENTRY glDepthRange( GLclampf near_val, GLclampf far_val );
GL_APICALL void GL_APIENTRY glClearDepth( GLclampf depth );

#endif

#endif
