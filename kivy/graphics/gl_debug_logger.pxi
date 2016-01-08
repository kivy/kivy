from kivy.logger import Logger
include "config.pxi"

IF USE_OPENGL_DEBUG:
    cimport kivy.graphics.c_opengl_debug as c_opengl
ELIF USE_OPENGL_MOCK:
    cimport kivy.graphics.c_opengl_mock as c_opengl
ELSE:
    cimport kivy.graphics.c_opengl as c_opengl

cdef inline void log_gl_error(str note):
    IF DEBUG_GL:
        ret = c_opengl.glGetError()
        if ret:
            Logger.error("OpenGL Error: {note} {ret1} / {ret2}".format(
                note=note, ret1=ret, ret2=hex(ret)))
