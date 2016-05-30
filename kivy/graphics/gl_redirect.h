/**
 * Redirect the inclusion of GL file to the selected provider
 */
#ifndef __gl_redirect_h_
#define __gl_redirect_h_

#include "config.h"

#if __USE_OPENGL_MOCK
#include "gl_mock.h"
#else

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
#elif __USE_ANGLE
// #       ifndef _MSC_VER
// #       define _MSC_VER
// #       endif
#       include "SDL_opengles2.h"
// #       ifdef _MSC_VER
// #       undef _MSC_VER
// #       endif
#		ifndef GL_DEPTH24_STENCIL8
#			define GL_DEPTH24_STENCIL8                      GL_DEPTH24_STENCIL8_OES
#		endif
#else
#	if __USE_OPENGL_ES2
#		if __APPLE__
#			include "common_subset.h"
#		else
#			include <GLES2/gl2.h>
#			include <GLES2/gl2ext.h>
#		endif
#		ifndef GL_DEPTH24_STENCIL8
#			define GL_DEPTH24_STENCIL8                      GL_DEPTH24_STENCIL8_OES
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
#endif

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
#endif

// support for dynamic binding on glew
#if __USE_GLEW
#ifndef __GL_DYNAMIC_BINDING
#define __GL_DYNAMIC_BINDING

#if __USE_GLEW
#define getProcAddress(x) (wglGetProcAddress(x))
#else
#define getProcAddress(x) (SDL_GL_GetProcAddress(x))
#endif

#include <windows.h>
#include <string.h>
void gl_dynamic_binding() {
    const char *gl_extensions = glGetString(GL_EXTENSIONS);

    /* If the current opengl driver don't have framebuffers methods,
     * Check if an extension exist
     */
    if (glGenFramebuffers == NULL) {
        printf("GL: glGenFramebuffers is NULL, try to detect an extension\n");
        printf("GL: available extensions: %s\n", gl_extensions);
        if (strstr(gl_extensions, "ARB_framebuffer_object")) {
            printf("GL: ARB_framebuffer_object is supported\n");

            glIsRenderbuffer = (PFNGLISRENDERBUFFERPROC) getProcAddress("glIsRenderbuffer");
            glBindRenderbuffer = (PFNGLBINDRENDERBUFFERPROC) getProcAddress("glBindRenderbuffer");
            glDeleteRenderbuffers = (PFNGLDELETERENDERBUFFERSPROC) getProcAddress("glDeleteRenderbuffers");
            glGenRenderbuffers = (PFNGLGENRENDERBUFFERSPROC) getProcAddress("glGenRenderbuffers");
            glRenderbufferStorage = (PFNGLRENDERBUFFERSTORAGEPROC) getProcAddress("glRenderbufferStorage");
            glGetRenderbufferParameteriv = (PFNGLGETRENDERBUFFERPARAMETERIVPROC) getProcAddress("glGetRenderbufferParameteriv");
            glIsFramebuffer = (PFNGLISFRAMEBUFFERPROC) getProcAddress("glIsFramebuffer");
            glBindFramebuffer = (PFNGLBINDFRAMEBUFFERPROC) getProcAddress("glBindFramebuffer");
            glDeleteFramebuffers = (PFNGLDELETEFRAMEBUFFERSPROC) getProcAddress("glDeleteFramebuffers");
            glGenFramebuffers = (PFNGLGENFRAMEBUFFERSPROC) getProcAddress("glGenFramebuffers");
            glCheckFramebufferStatus = (PFNGLCHECKFRAMEBUFFERSTATUSPROC) getProcAddress("glCheckFramebufferStatus");
            glFramebufferTexture1D = (PFNGLFRAMEBUFFERTEXTURE1DPROC) getProcAddress("glFramebufferTexture1D");
            glFramebufferTexture2D = (PFNGLFRAMEBUFFERTEXTURE2DPROC) getProcAddress("glFramebufferTexture2D");
            glFramebufferTexture3D = (PFNGLFRAMEBUFFERTEXTURE3DPROC) getProcAddress("glFramebufferTexture3D");
            glFramebufferRenderbuffer = (PFNGLFRAMEBUFFERRENDERBUFFERPROC) getProcAddress("glFramebufferRenderbuffer");
            glGetFramebufferAttachmentParameteriv = (PFNGLGETFRAMEBUFFERATTACHMENTPARAMETERIVPROC) getProcAddress("glGetFramebufferAttachmentParameteriv");
            glGenerateMipmap = (PFNGLGENERATEMIPMAPPROC) getProcAddress("glGenerateMipmap");
        } else if (strstr(gl_extensions, "EXT_framebuffer_object")) {
            printf("GL: EXT_framebuffer_object is supported\n");
            glIsRenderbuffer = (PFNGLISRENDERBUFFERPROC) getProcAddress("glIsRenderbufferEXT");
            glBindRenderbuffer = (PFNGLBINDRENDERBUFFERPROC) getProcAddress("glBindRenderbufferEXT");
            glDeleteRenderbuffers = (PFNGLDELETERENDERBUFFERSPROC) getProcAddress("glDeleteRenderbuffersEXT");
            glGenRenderbuffers = (PFNGLGENRENDERBUFFERSPROC) getProcAddress("glGenRenderbuffersEXT");
            glRenderbufferStorage = (PFNGLRENDERBUFFERSTORAGEPROC) getProcAddress("glRenderbufferStorageEXT");
            glGetRenderbufferParameteriv = (PFNGLGETRENDERBUFFERPARAMETERIVPROC) getProcAddress("glGetRenderbufferParameterivEXT");
            glIsFramebuffer = (PFNGLISFRAMEBUFFERPROC) getProcAddress("glIsFramebufferEXT");
            glBindFramebuffer = (PFNGLBINDFRAMEBUFFERPROC) getProcAddress("glBindFramebufferEXT");
            glDeleteFramebuffers = (PFNGLDELETEFRAMEBUFFERSPROC) getProcAddress("glDeleteFramebuffersEXT");
            glGenFramebuffers = (PFNGLGENFRAMEBUFFERSPROC) getProcAddress("glGenFramebuffersEXT");
            glCheckFramebufferStatus = (PFNGLCHECKFRAMEBUFFERSTATUSPROC) getProcAddress("glCheckFramebufferStatusEXT");
            glFramebufferTexture1D = (PFNGLFRAMEBUFFERTEXTURE1DPROC) getProcAddress("glFramebufferTexture1DEXT");
            glFramebufferTexture2D = (PFNGLFRAMEBUFFERTEXTURE2DPROC) getProcAddress("glFramebufferTexture2DEXT");
            glFramebufferTexture3D = (PFNGLFRAMEBUFFERTEXTURE3DPROC) getProcAddress("glFramebufferTexture3DEXT");
            glFramebufferRenderbuffer = (PFNGLFRAMEBUFFERRENDERBUFFERPROC) getProcAddress("glFramebufferRenderbufferEXT");
            glGetFramebufferAttachmentParameteriv = (PFNGLGETFRAMEBUFFERATTACHMENTPARAMETERIVPROC) getProcAddress("glGetFramebufferAttachmentParameterivEXT");
            glGenerateMipmap = (PFNGLGENERATEMIPMAPPROC) getProcAddress("glGenerateMipmapEXT");
        } else {
            printf("GL: No framebuffers extension is supported\n");
            printf("GL: Any call to Fbo will crash !\n");
        }
    }
}

#endif /* __GL_DYNAMIC_BINDING */
#endif /* __USE_GLEW */
#endif /* __USE_OPENGL_MOCK */

#endif /* __gl2platform_h_ */
