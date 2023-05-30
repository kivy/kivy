"""
CGL/Glew: GL backend implementation using Glew
"""

include "../common.pxi"
include "../../include/config.pxi"

from kivy.graphics.cgl cimport *
from kivy.graphics.cgl_backend.cgl_gl import link_static
from kivy.logger import Logger

cdef extern from "gl_redirect.h":
    int glewInit() nogil
    int GLEW_OK
    char *glewGetErrorString(int) nogil

IF PLATFORM == "win32":
    cdef extern from *:
        void* wglGetProcAddress(const char* proc)

cpdef is_backend_supported():
    return not USE_OPENGL_MOCK and PLATFORM == "win32"


def init_backend():
    IF USE_OPENGL_MOCK or PLATFORM != "win32":
        raise TypeError('Glew is not available. Recompile with USE_OPENGL_MOCK=0')
    ELSE:
        cdef int result
        cdef bytes error
        result = glewInit()
        if result != GLEW_OK:
            error = glewGetErrorString(result)
            Logger.error('GL: GLEW initialization error {}'.format(error))
        else:
            Logger.info('GL: GLEW initialization succeeded')
        link_static()
        gl_dynamic_binding(<void *(__stdcall *)(const char *)>wglGetProcAddress)

IF not USE_OPENGL_MOCK and PLATFORM == "win32":
    cdef void gl_dynamic_binding(void *(__stdcall * f)(const char *)) except *:
        cdef bytes gl_extensions
        if cgl.glGetString == NULL:
            Logger.error('glGetString is unavailable, skipping Fbo detection')
            return
        gl_extensions = cgl.glGetString(GL_EXTENSIONS)

        # If the current opengl driver don't have framebuffers methods,
        # Check if an extension exist
        Logger.debug("GL: available extensions: {}".format(gl_extensions))
        if cgl.glGenFramebuffers != NULL:
            return

        Logger.debug("GL: glGenFramebuffers is NULL, try to detect an extension")
        if b"ARB_framebuffer_object" in gl_extensions:
            Logger.debug("GL: ARB_framebuffer_object is supported")

            cgl.glIsRenderbuffer = <GLISRENDERBUFFERPTR> f("glIsRenderbuffer")
            cgl.glBindRenderbuffer = <GLBINDRENDERBUFFERPTR> f("glBindRenderbuffer")
            cgl.glDeleteRenderbuffers = <GLDELETERENDERBUFFERSPTR> f("glDeleteRenderbuffers")
            cgl.glGenRenderbuffers = <GLGENRENDERBUFFERSPTR> f("glGenRenderbuffers")
            cgl.glRenderbufferStorage = <GLRENDERBUFFERSTORAGEPTR> f("glRenderbufferStorage")
            cgl.glGetRenderbufferParameteriv = <GLGETRENDERBUFFERPARAMETERIVPTR> f("glGetRenderbufferParameteriv")
            cgl.glIsFramebuffer = <GLISFRAMEBUFFERPTR> f("glIsFramebuffer")
            cgl.glBindFramebuffer = <GLBINDFRAMEBUFFERPTR> f("glBindFramebuffer")
            cgl.glDeleteFramebuffers = <GLDELETEFRAMEBUFFERSPTR> f("glDeleteFramebuffers")
            cgl.glGenFramebuffers = <GLGENFRAMEBUFFERSPTR> f("glGenFramebuffers")
            cgl.glCheckFramebufferStatus = <GLCHECKFRAMEBUFFERSTATUSPTR> f("glCheckFramebufferStatus")
            #cgl.glFramebufferTexture1D = <GLFRAMEBUFFERTEXTURE1DPTR> f("glFramebufferTexture1D")
            cgl.glFramebufferTexture2D = <GLFRAMEBUFFERTEXTURE2DPTR> f("glFramebufferTexture2D")
            #cgl.glFramebufferTexture3D = <GLFRAMEBUFFERTEXTURE3DPTR> f("glFramebufferTexture3D")
            cgl.glFramebufferRenderbuffer = <GLFRAMEBUFFERRENDERBUFFERPTR> f("glFramebufferRenderbuffer")
            cgl.glGetFramebufferAttachmentParameteriv = <GLGETFRAMEBUFFERATTACHMENTPARAMETERIVPTR> f("glGetFramebufferAttachmentParameteriv")
            cgl.glGenerateMipmap = <GLGENERATEMIPMAPPTR> f("glGenerateMipmap")
        elif b"EXT_framebuffer_object" in gl_extensions:
            Logger.debug("GL: EXT_framebuffer_object is supported\n")

            cgl.glIsRenderbuffer = <GLISRENDERBUFFERPTR> f("glIsRenderbufferEXT")
            cgl.glBindRenderbuffer = <GLBINDRENDERBUFFERPTR> f("glBindRenderbufferEXT")
            cgl.glDeleteRenderbuffers = <GLDELETERENDERBUFFERSPTR> f("glDeleteRenderbuffersEXT")
            cgl.glGenRenderbuffers = <GLGENRENDERBUFFERSPTR> f("glGenRenderbuffersEXT")
            cgl.glRenderbufferStorage = <GLRENDERBUFFERSTORAGEPTR> f("glRenderbufferStorageEXT")
            cgl.glGetRenderbufferParameteriv = <GLGETRENDERBUFFERPARAMETERIVPTR> f("glGetRenderbufferParameterivEXT")
            cgl.glIsFramebuffer = <GLISFRAMEBUFFERPTR> f("glIsFramebufferEXT")
            cgl.glBindFramebuffer = <GLBINDFRAMEBUFFERPTR> f("glBindFramebufferEXT")
            cgl.glDeleteFramebuffers = <GLDELETEFRAMEBUFFERSPTR> f("glDeleteFramebuffersEXT")
            cgl.glGenFramebuffers = <GLGENFRAMEBUFFERSPTR> f("glGenFramebuffersEXT")
            cgl.glCheckFramebufferStatus = <GLCHECKFRAMEBUFFERSTATUSPTR> f("glCheckFramebufferStatusEXT")
            #cgl.glFramebufferTexture1D = <GLFRAMEBUFFERTEXTURE1DPTR> f("glFramebufferTexture1DEXT")
            cgl.glFramebufferTexture2D = <GLFRAMEBUFFERTEXTURE2DPTR> f("glFramebufferTexture2DEXT")
            #cgl.glFramebufferTexture3D = <GLFRAMEBUFFERTEXTURE3DPTR> f("glFramebufferTexture3DEXT")
            cgl.glFramebufferRenderbuffer = <GLFRAMEBUFFERRENDERBUFFERPTR> f("glFramebufferRenderbufferEXT")
            cgl.glGetFramebufferAttachmentParameteriv = <GLGETFRAMEBUFFERATTACHMENTPARAMETERIVPTR> f("glGetFramebufferAttachmentParameterivEXT")
        else:
            Logger.info("GL: No framebuffers extension is supported")
            Logger.debug("GL: Any call to Fbo will crash!")
