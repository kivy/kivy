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
#ifndef __GLEW_DYNAMIC_BINDING
#define __GLEW_DYNAMIC_BINDING

#include <windows.h>
#include <string.h>
void glew_dynamic_binding() {
    const char *gl_extensions = glGetString(GL_EXTENSIONS);

    /* If the current opengl driver don't have framebuffers methods,
     * Check if an extension exist
     */
    if (glGenFramebuffers == NULL) {
        printf("GL: glGenFramebuffers is NULL, try to detect an extension\n");
        printf("GL: available extensions: %s\n", gl_extensions);
        if (strstr(gl_extensions, "ARB_framebuffer_object")) {
            printf("GL: ARB_framebuffer_object is supported\n");

            glIsRenderbuffer = (PFNGLISRENDERBUFFERPROC) wglGetProcAddress("glIsRenderbuffer");
            glBindRenderbuffer = (PFNGLBINDRENDERBUFFERPROC) wglGetProcAddress("glBindRenderbuffer");
            glDeleteRenderbuffers = (PFNGLDELETERENDERBUFFERSPROC) wglGetProcAddress("glDeleteRenderbuffers");
            glGenRenderbuffers = (PFNGLGENRENDERBUFFERSPROC) wglGetProcAddress("glGenRenderbuffers");
            glRenderbufferStorage = (PFNGLRENDERBUFFERSTORAGEPROC) wglGetProcAddress("glRenderbufferStorage");
            glGetRenderbufferParameteriv = (PFNGLGETRENDERBUFFERPARAMETERIVPROC) wglGetProcAddress("glGetRenderbufferParameteriv");
            glIsFramebuffer = (PFNGLISFRAMEBUFFERPROC) wglGetProcAddress("glIsFramebuffer");
            glBindFramebuffer = (PFNGLBINDFRAMEBUFFERPROC) wglGetProcAddress("glBindFramebuffer");
            glDeleteFramebuffers = (PFNGLDELETEFRAMEBUFFERSPROC) wglGetProcAddress("glDeleteFramebuffers");
            glGenFramebuffers = (PFNGLGENFRAMEBUFFERSPROC) wglGetProcAddress("glGenFramebuffers");
            glCheckFramebufferStatus = (PFNGLCHECKFRAMEBUFFERSTATUSPROC) wglGetProcAddress("glCheckFramebufferStatus");
            glFramebufferTexture1D = (PFNGLFRAMEBUFFERTEXTURE1DPROC) wglGetProcAddress("glFramebufferTexture1D");
            glFramebufferTexture2D = (PFNGLFRAMEBUFFERTEXTURE2DPROC) wglGetProcAddress("glFramebufferTexture2D");
            glFramebufferTexture3D = (PFNGLFRAMEBUFFERTEXTURE3DPROC) wglGetProcAddress("glFramebufferTexture3D");
            glFramebufferRenderbuffer = (PFNGLFRAMEBUFFERRENDERBUFFERPROC) wglGetProcAddress("glFramebufferRenderbuffer");
            glGetFramebufferAttachmentParameteriv = (PFNGLGETFRAMEBUFFERATTACHMENTPARAMETERIVPROC) wglGetProcAddress("glGetFramebufferAttachmentParameteriv");
            glGenerateMipmap = (PFNGLGENERATEMIPMAPPROC) wglGetProcAddress("glGenerateMipmap");
        } else if (strstr(gl_extensions, "EXT_framebuffer_object")) {
            printf("GL: EXT_framebuffer_object is supported\n");
            glIsRenderbuffer = (PFNGLISRENDERBUFFERPROC) wglGetProcAddress("glIsRenderbufferEXT");
            glBindRenderbuffer = (PFNGLBINDRENDERBUFFERPROC) wglGetProcAddress("glBindRenderbufferEXT");
            glDeleteRenderbuffers = (PFNGLDELETERENDERBUFFERSPROC) wglGetProcAddress("glDeleteRenderbuffersEXT");
            glGenRenderbuffers = (PFNGLGENRENDERBUFFERSPROC) wglGetProcAddress("glGenRenderbuffersEXT");
            glRenderbufferStorage = (PFNGLRENDERBUFFERSTORAGEPROC) wglGetProcAddress("glRenderbufferStorageEXT");
            glGetRenderbufferParameteriv = (PFNGLGETRENDERBUFFERPARAMETERIVPROC) wglGetProcAddress("glGetRenderbufferParameterivEXT");
            glIsFramebuffer = (PFNGLISFRAMEBUFFERPROC) wglGetProcAddress("glIsFramebufferEXT");
            glBindFramebuffer = (PFNGLBINDFRAMEBUFFERPROC) wglGetProcAddress("glBindFramebufferEXT");
            glDeleteFramebuffers = (PFNGLDELETEFRAMEBUFFERSPROC) wglGetProcAddress("glDeleteFramebuffersEXT");
            glGenFramebuffers = (PFNGLGENFRAMEBUFFERSPROC) wglGetProcAddress("glGenFramebuffersEXT");
            glCheckFramebufferStatus = (PFNGLCHECKFRAMEBUFFERSTATUSPROC) wglGetProcAddress("glCheckFramebufferStatusEXT");
            glFramebufferTexture1D = (PFNGLFRAMEBUFFERTEXTURE1DPROC) wglGetProcAddress("glFramebufferTexture1DEXT");
            glFramebufferTexture2D = (PFNGLFRAMEBUFFERTEXTURE2DPROC) wglGetProcAddress("glFramebufferTexture2DEXT");
            glFramebufferTexture3D = (PFNGLFRAMEBUFFERTEXTURE3DPROC) wglGetProcAddress("glFramebufferTexture3DEXT");
            glFramebufferRenderbuffer = (PFNGLFRAMEBUFFERRENDERBUFFERPROC) wglGetProcAddress("glFramebufferRenderbufferEXT");
            glGetFramebufferAttachmentParameteriv = (PFNGLGETFRAMEBUFFERATTACHMENTPARAMETERIVPROC) wglGetProcAddress("glGetFramebufferAttachmentParameterivEXT");
            glGenerateMipmap = (PFNGLGENERATEMIPMAPPROC) wglGetProcAddress("glGenerateMipmapEXT");
        } else {
            printf("GL: No framebuffers extension is supported\n");
            printf("GL: Any call to Fbo will crash !\n");
        }
    }
}

#endif /* __GLEW_DYNAMIC_BINDING */
#endif /* __USE_GLEW */
#endif /* __USE_OPENGL_MOCK */

#endif /* __gl2platform_h_ */