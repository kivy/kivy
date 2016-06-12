"""
CGL: standard C interface for OpenGL
====================================

It load dynamically a backend (either from SDL, mock, wgl, etc...), and
link all the symbols to the GLES2_Context context.
"""

include "config.pxi"

from sys import platform
from os import environ
from cgl cimport GLES2_Context
import importlib

cdef GLES2_Context g_cgl
cdef GLES2_Context *cgl = &g_cgl
cdef object cgl_name = None


def cgl_get_default_backend():
    IF USE_GLEW:
        return "glew"
    ELIF USE_SDL2:
        return "sdl2"
    ELSE:
        return "static"


cdef GLES2_Context *cgl_get_context():
    return cgl


cdef void cgl_set_context(GLES2_Context* ctx):
    global cgl
    cgl = ctx


cpdef object cgl_get_backend_name():
    return cgl_name


cdef void cgl_init():
    global cgl_name
    backend = environ.get("KIVY_GL_BACKEND")
    if not backend:
        backend = cgl_get_default_backend()

    # specific cases
    # for ANGLE, we use sdl2, and only on windows.
    if backend == "angle":
        if platform != "win32":
            raise Exception("CGL: ANGLE backend can be used only on Windows")
        backend = "sdl2"
        cgl_name = "angle"
    else:
        cgl_name = backend

    mod = importlib.import_module("kivy.graphics.cgl_{}".format(backend))
    mod.init_backend()

    use_debug = environ.get("KIVY_GL_DEBUG") == "1"
    if use_debug:
        mod = importlib.import_module("kivy.graphics.cgl_debug")
        mod.init_backend_debug()
