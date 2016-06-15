"""
CGL: standard C interface for OpenGL
====================================

It loads dynamically a backend (either from SDL, mock, wgl, etc...), and
link all the symbols to the GLES2_Context context.
"""

include "config.pxi"

from sys import platform
from os import environ
from cgl cimport GLES2_Context
import importlib
from kivy.logger import Logger

cdef GLES2_Context g_cgl
cdef GLES2_Context *cgl = &g_cgl
cdef object cgl_name = None


cdef extern from "gl_redirect.h":
    ctypedef void (__stdcall* PFNGLBINDFRAMEBUFFERPROC) (GLenum target, GLuint framebuffer) nogil
    ctypedef void (__stdcall* PFNGLBINDRENDERBUFFERPROC) (GLenum target, GLuint renderbuffer) nogil
    ctypedef void (__stdcall* PFNGLBLITFRAMEBUFFERPROC) (GLint srcX0, GLint srcY0, GLint srcX1, GLint srcY1, GLint dstX0, GLint dstY0, GLint dstX1, GLint dstY1, GLbitfield mask, GLenum filter) nogil
    ctypedef GLenum (__stdcall* PFNGLCHECKFRAMEBUFFERSTATUSPROC) (GLenum target) nogil
    ctypedef void (__stdcall* PFNGLDELETEFRAMEBUFFERSPROC) (GLsizei n, const GLuint* framebuffers) nogil
    ctypedef void (__stdcall* PFNGLDELETERENDERBUFFERSPROC) (GLsizei n, const GLuint* renderbuffers) nogil
    ctypedef void (__stdcall* PFNGLFRAMEBUFFERRENDERBUFFERPROC) (GLenum target, GLenum attachment, GLenum renderbuffertarget, GLuint renderbuffer) nogil
    ctypedef void (__stdcall* PFNGLFRAMEBUFFERTEXTURE1DPROC) (GLenum target, GLenum attachment, GLenum textarget, GLuint texture, GLint level) nogil
    ctypedef void (__stdcall* PFNGLFRAMEBUFFERTEXTURE2DPROC) (GLenum target, GLenum attachment, GLenum textarget, GLuint texture, GLint level) nogil
    ctypedef void (__stdcall* PFNGLFRAMEBUFFERTEXTURE3DPROC) (GLenum target, GLenum attachment, GLenum textarget, GLuint texture, GLint level, GLint layer) nogil
    ctypedef void (__stdcall* PFNGLFRAMEBUFFERTEXTURELAYERPROC) (GLenum target,GLenum attachment, GLuint texture,GLint level,GLint layer) nogil
    ctypedef void (__stdcall* PFNGLGENFRAMEBUFFERSPROC) (GLsizei n, GLuint* framebuffers) nogil
    ctypedef void (__stdcall* PFNGLGENRENDERBUFFERSPROC) (GLsizei n, GLuint* renderbuffers) nogil
    ctypedef void (__stdcall* PFNGLGENERATEMIPMAPPROC) (GLenum target) nogil
    ctypedef void (__stdcall* PFNGLGETFRAMEBUFFERATTACHMENTPARAMETERIVPROC) (GLenum target, GLenum attachment, GLenum pname, GLint* params) nogil
    ctypedef void (__stdcall* PFNGLGETRENDERBUFFERPARAMETERIVPROC) (GLenum target, GLenum pname, GLint* params) nogil
    ctypedef GLboolean (__stdcall* PFNGLISFRAMEBUFFERPROC) (GLuint framebuffer) nogil
    ctypedef GLboolean (__stdcall* PFNGLISRENDERBUFFERPROC) (GLuint renderbuffer) nogil
    ctypedef void (__stdcall* PFNGLRENDERBUFFERSTORAGEPROC) (GLenum target, GLenum internalformat, GLsizei width, GLsizei height) nogil
    ctypedef void (__stdcall* PFNGLRENDERBUFFERSTORAGEMULTISAMPLEPROC) (GLenum target, GLsizei samples, GLenum internalformat, GLsizei width, GLsizei height) nogil


cpdef cgl_get_backend_name():
    if cgl_name:
        return cgl_name
    name = environ.get("KIVY_GL_BACKEND")
    if name:
        return name

    if USE_GLEW:
        return "glew"
    elif USE_ANGLE and USE_SDL2:
        return "angle"
    elif not USE_OPENGL_MOCK and USE_SDL2:
        return "sdl2"
    else:
        return "mock"


cdef GLES2_Context *cgl_get_context():
    return cgl


cdef void cgl_set_context(GLES2_Context* ctx):
    global cgl
    cgl = ctx


cdef void cgl_init() except *:
    global cgl_name
    cgl_name = backend = cgl_get_backend_name()

    # for ANGLE, currently we use sdl2, and only on windows.
    if backend == "angle":
        if platform != "win32":
            raise Exception("CGL: ANGLE backend can be used only on Windows")
        backend = "sdl2"

    if backend == 'glew':
        backend = 'static'

    if cgl_name not in {'glew', 'sdl2', 'angle', 'mock'}:
        raise ValueError('{} is not a recognized gl backend'.format(backend))

    mod = importlib.import_module("kivy.graphics.cgl_{}".format(backend))
    mod.init_backend()

    use_debug = environ.get("KIVY_GL_DEBUG") == "1"
    if use_debug:
        mod = importlib.import_module("kivy.graphics.cgl_debug")
        mod.init_backend_debug()


cdef void gl_dynamic_binding(void *(*f)(const char *)) except *:
    cdef bytes gl_extensions = cgl.glGetString(GL_EXTENSIONS)

    # If the current opengl driver don't have framebuffers methods,
    # Check if an extension exist
    Logger.debug("GL: available extensions: {}".format(gl_extensions))
    if cgl.glGenFramebuffers != NULL:
        return

    Logger.debug("GL: glGenFramebuffers is NULL, try to detect an extension")
    if b"ARB_framebuffer_object" in gl_extensions:
        Logger.debug("GL: ARB_framebuffer_object is supported")

        cgl.glIsRenderbuffer = <PFNGLISRENDERBUFFERPROC> f("glIsRenderbuffer")
        cgl.glBindRenderbuffer = <PFNGLBINDRENDERBUFFERPROC> f("glBindRenderbuffer")
        cgl.glDeleteRenderbuffers = <PFNGLDELETERENDERBUFFERSPROC> f("glDeleteRenderbuffers")
        cgl.glGenRenderbuffers = <PFNGLGENRENDERBUFFERSPROC> f("glGenRenderbuffers")
        cgl.glRenderbufferStorage = <PFNGLRENDERBUFFERSTORAGEPROC> f("glRenderbufferStorage")
        cgl.glGetRenderbufferParameteriv = <PFNGLGETRENDERBUFFERPARAMETERIVPROC> f("glGetRenderbufferParameteriv")
        cgl.glIsFramebuffer = <PFNGLISFRAMEBUFFERPROC> f("glIsFramebuffer")
        cgl.glBindFramebuffer = <PFNGLBINDFRAMEBUFFERPROC> f("glBindFramebuffer")
        cgl.glDeleteFramebuffers = <PFNGLDELETEFRAMEBUFFERSPROC> f("glDeleteFramebuffers")
        cgl.glGenFramebuffers = <PFNGLGENFRAMEBUFFERSPROC> f("glGenFramebuffers")
        cgl.glCheckFramebufferStatus = <PFNGLCHECKFRAMEBUFFERSTATUSPROC> f("glCheckFramebufferStatus")
        #cgl.glFramebufferTexture1D = <PFNGLFRAMEBUFFERTEXTURE1DPROC> f("glFramebufferTexture1D")
        cgl.glFramebufferTexture2D = <PFNGLFRAMEBUFFERTEXTURE2DPROC> f("glFramebufferTexture2D")
        #cgl.glFramebufferTexture3D = <PFNGLFRAMEBUFFERTEXTURE3DPROC> f("glFramebufferTexture3D")
        cgl.glFramebufferRenderbuffer = <PFNGLFRAMEBUFFERRENDERBUFFERPROC> f("glFramebufferRenderbuffer")
        cgl.glGetFramebufferAttachmentParameteriv = <PFNGLGETFRAMEBUFFERATTACHMENTPARAMETERIVPROC> f("glGetFramebufferAttachmentParameteriv")
        cgl.glGenerateMipmap = <PFNGLGENERATEMIPMAPPROC> f("glGenerateMipmap")
    elif b"EXT_framebuffer_object" in gl_extensions:
        Logger.debug("GL: EXT_framebuffer_object is supported\n")

        cgl.glIsRenderbuffer = <PFNGLISRENDERBUFFERPROC> f("glIsRenderbufferEXT")
        cgl.glBindRenderbuffer = <PFNGLBINDRENDERBUFFERPROC> f("glBindRenderbufferEXT")
        cgl.glDeleteRenderbuffers = <PFNGLDELETERENDERBUFFERSPROC> f("glDeleteRenderbuffersEXT")
        cgl.glGenRenderbuffers = <PFNGLGENRENDERBUFFERSPROC> f("glGenRenderbuffersEXT")
        cgl.glRenderbufferStorage = <PFNGLRENDERBUFFERSTORAGEPROC> f("glRenderbufferStorageEXT")
        cgl.glGetRenderbufferParameteriv = <PFNGLGETRENDERBUFFERPARAMETERIVPROC> f("glGetRenderbufferParameterivEXT")
        cgl.glIsFramebuffer = <PFNGLISFRAMEBUFFERPROC> f("glIsFramebufferEXT")
        cgl.glBindFramebuffer = <PFNGLBINDFRAMEBUFFERPROC> f("glBindFramebufferEXT")
        cgl.glDeleteFramebuffers = <PFNGLDELETEFRAMEBUFFERSPROC> f("glDeleteFramebuffersEXT")
        cgl.glGenFramebuffers = <PFNGLGENFRAMEBUFFERSPROC> f("glGenFramebuffersEXT")
        cgl.glCheckFramebufferStatus = <PFNGLCHECKFRAMEBUFFERSTATUSPROC> f("glCheckFramebufferStatusEXT")
        #cgl.glFramebufferTexture1D = <PFNGLFRAMEBUFFERTEXTURE1DPROC> f("glFramebufferTexture1DEXT")
        cgl.glFramebufferTexture2D = <PFNGLFRAMEBUFFERTEXTURE2DPROC> f("glFramebufferTexture2DEXT")
        #cgl.glFramebufferTexture3D = <PFNGLFRAMEBUFFERTEXTURE3DPROC> f("glFramebufferTexture3DEXT")
        cgl.glFramebufferRenderbuffer = <PFNGLFRAMEBUFFERRENDERBUFFERPROC> f("glFramebufferRenderbufferEXT")
        cgl.glGetFramebufferAttachmentParameteriv = <PFNGLGETFRAMEBUFFERATTACHMENTPARAMETERIVPROC> f("glGetFramebufferAttachmentParameterivEXT")
    else:
        Logger.info("GL: No framebuffers extension is supported")
        Logger.debug("GL: Any call to Fbo will crash!")
