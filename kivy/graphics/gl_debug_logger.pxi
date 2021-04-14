from kivy.logger import Logger
include "../include/config.pxi"

from kivy.graphics.cgl cimport cgl
import os
cdef int env_debug_gl = "DEBUG_GL" in os.environ

cdef inline void log_gl_error(str note):
    if env_debug_gl:
        ret = cgl.glGetError()
        if ret:
            Logger.error("OpenGL Error: {note} {ret1} / {ret2}".format(
                note=note, ret1=ret, ret2=hex(ret)))
