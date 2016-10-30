"""
CGL/Glew: GL backend implementation using Glew
"""

include "common.pxi"
include "config.pxi"

from kivy.graphics.cgl cimport *
from kivy.graphics.cgl_gl import link_static
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
        gl_dynamic_binding()


cdef void gl_dynamic_binding() except *:
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

        cgl.glIsRenderbuffer = <GLISRENDERBUFFERPTR> wglGetProcAddress("glIsRenderbuffer")
        cgl.glBindRenderbuffer = <GLBINDRENDERBUFFERPTR> wglGetProcAddress("glBindRenderbuffer")
        cgl.glDeleteRenderbuffers = <GLDELETERENDERBUFFERSPTR> wglGetProcAddress("glDeleteRenderbuffers")
        cgl.glGenRenderbuffers = <GLGENRENDERBUFFERSPTR> wglGetProcAddress("glGenRenderbuffers")
        cgl.glRenderbufferStorage = <GLRENDERBUFFERSTORAGEPTR> wglGetProcAddress("glRenderbufferStorage")
        cgl.glGetRenderbufferParameteriv = <GLGETRENDERBUFFERPARAMETERIVPTR> wglGetProcAddress("glGetRenderbufferParameteriv")
        cgl.glIsFramebuffer = <GLISFRAMEBUFFERPTR> wglGetProcAddress("glIsFramebuffer")
        cgl.glBindFramebuffer = <GLBINDFRAMEBUFFERPTR> wglGetProcAddress("glBindFramebuffer")
        cgl.glDeleteFramebuffers = <GLDELETEFRAMEBUFFERSPTR> wglGetProcAddress("glDeleteFramebuffers")
        cgl.glGenFramebuffers = <GLGENFRAMEBUFFERSPTR> wglGetProcAddress("glGenFramebuffers")
        cgl.glCheckFramebufferStatus = <GLCHECKFRAMEBUFFERSTATUSPTR> wglGetProcAddress("glCheckFramebufferStatus")
        #cgl.glFramebufferTexture1D = <GLFRAMEBUFFERTEXTURE1DPTR> wglGetProcAddress("glFramebufferTexture1D")
        cgl.glFramebufferTexture2D = <GLFRAMEBUFFERTEXTURE2DPTR> wglGetProcAddress("glFramebufferTexture2D")
        #cgl.glFramebufferTexture3D = <GLFRAMEBUFFERTEXTURE3DPTR> wglGetProcAddress("glFramebufferTexture3D")
        cgl.glFramebufferRenderbuffer = <GLFRAMEBUFFERRENDERBUFFERPTR> wglGetProcAddress("glFramebufferRenderbuffer")
        cgl.glGetFramebufferAttachmentParameteriv = <GLGETFRAMEBUFFERATTACHMENTPARAMETERIVPTR> wglGetProcAddress("glGetFramebufferAttachmentParameteriv")
        cgl.glGenerateMipmap = <GLGENERATEMIPMAPPTR> wglGetProcAddress("glGenerateMipmap")
    elif b"EXT_framebuffer_object" in gl_extensions:
        Logger.debug("GL: EXT_framebuffer_object is supported\n")

        cgl.glIsRenderbuffer = <GLISRENDERBUFFERPTR> wglGetProcAddress("glIsRenderbufferEXT")
        cgl.glBindRenderbuffer = <GLBINDRENDERBUFFERPTR> wglGetProcAddress("glBindRenderbufferEXT")
        cgl.glDeleteRenderbuffers = <GLDELETERENDERBUFFERSPTR> wglGetProcAddress("glDeleteRenderbuffersEXT")
        cgl.glGenRenderbuffers = <GLGENRENDERBUFFERSPTR> wglGetProcAddress("glGenRenderbuffersEXT")
        cgl.glRenderbufferStorage = <GLRENDERBUFFERSTORAGEPTR> wglGetProcAddress("glRenderbufferStorageEXT")
        cgl.glGetRenderbufferParameteriv = <GLGETRENDERBUFFERPARAMETERIVPTR> wglGetProcAddress("glGetRenderbufferParameterivEXT")
        cgl.glIsFramebuffer = <GLISFRAMEBUFFERPTR> wglGetProcAddress("glIsFramebufferEXT")
        cgl.glBindFramebuffer = <GLBINDFRAMEBUFFERPTR> wglGetProcAddress("glBindFramebufferEXT")
        cgl.glDeleteFramebuffers = <GLDELETEFRAMEBUFFERSPTR> wglGetProcAddress("glDeleteFramebuffersEXT")
        cgl.glGenFramebuffers = <GLGENFRAMEBUFFERSPTR> wglGetProcAddress("glGenFramebuffersEXT")
        cgl.glCheckFramebufferStatus = <GLCHECKFRAMEBUFFERSTATUSPTR> wglGetProcAddress("glCheckFramebufferStatusEXT")
        #cgl.glFramebufferTexture1D = <GLFRAMEBUFFERTEXTURE1DPTR> wglGetProcAddress("glFramebufferTexture1DEXT")
        cgl.glFramebufferTexture2D = <GLFRAMEBUFFERTEXTURE2DPTR> wglGetProcAddress("glFramebufferTexture2DEXT")
        #cgl.glFramebufferTexture3D = <GLFRAMEBUFFERTEXTURE3DPTR> wglGetProcAddress("glFramebufferTexture3DEXT")
        cgl.glFramebufferRenderbuffer = <GLFRAMEBUFFERRENDERBUFFERPTR> wglGetProcAddress("glFramebufferRenderbufferEXT")
        cgl.glGetFramebufferAttachmentParameteriv = <GLGETFRAMEBUFFERATTACHMENTPARAMETERIVPTR> wglGetProcAddress("glGetFramebufferAttachmentParameterivEXT")
    else:
        Logger.info("GL: No framebuffers extension is supported")
        Logger.debug("GL: Any call to Fbo will crash!")
