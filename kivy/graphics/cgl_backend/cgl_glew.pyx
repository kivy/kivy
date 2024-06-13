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

cpdef is_backend_supported():
    return not USE_OPENGL_MOCK and (PLATFORM == "win32" or PLATFORM == "linux")


def init_backend():
    IF USE_OPENGL_MOCK or (PLATFORM != "win32" and PLATFORM != "linux"):
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
