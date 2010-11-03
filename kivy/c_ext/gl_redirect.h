/**
 * Redirect the inclusion of GL file to the selected provider
 *
 * TODO: make it work on macosx platform
 */

#define __USE_GLES2		1

#if __USE_GLES2
#   warning "GL redirect is set on GLES 2 headers"
#	include <GLES2/gl2.h>
#else
#   warning "GL redirect is set on standard GL headers"
#	ifdef __APPLE__
#		include <OpenGL/gl.h>
#	else
#		include <GL/gl.h>
#		include <GL/glext.h>
#	endif
#	define GL_SHADER_BINARY_FORMATS					0x8DF8
#	define GL_RGB565								0x8D62
#	define GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS 	0x8CD9
#endif


