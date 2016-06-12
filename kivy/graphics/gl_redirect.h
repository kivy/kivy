/**
 * Redirect the inclusion of GL file to the selected provider
 */
#ifndef __gl_redirect_h_
#define __gl_redirect_h_

#include "config.h"
#define GL_GLEXT_PROTOTYPES
#include "GLES2/gl2.h"
#include "GLES2/gl2ext.h"

#if 0
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
#endif

#endif /* __gl2platform_h_ */
