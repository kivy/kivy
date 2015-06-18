from kivy.graphics.c_opengl cimport GLenum, glGetError
from kivy.logger import Logger
include "config.pxi"

cdef inline void log_gl_error(str note):
    IF DEBUG_GL:
        ret = glGetError()
        if ret:
            Logger.error("OpenGL Error: {note} {ret1} / {ret2}".format(
                note=note, ret1=ret, ret2=hex(ret)))