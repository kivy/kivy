from kivy.logger import Logger
include "../include/config.pxi"

from kivy.graphics.cgl cimport cgl

cdef inline void log_gl_error(str note):
    IF DEBUG_GL:
        ret = cgl.glGetError()
        if ret:
            Logger.error("OpenGL Error: {note} {ret1} / {ret2}".format(
                note=note, ret1=ret, ret2=hex(ret)))
