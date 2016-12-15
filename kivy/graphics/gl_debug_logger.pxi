from kivy.logger import Logger
include "config.pxi"

IF USE_OPENGL_DYNAMIC:
    from kivy.graphics.c_opengl_dynamic cimport cgl
ELIF USE_OPENGL_DEBUG:
    cimport kivy.graphics.c_opengl_debug as cgl
ELIF USE_OPENGL_MOCK:
    cimport kivy.graphics.c_opengl_mock as cgl
ELSE:
    cimport kivy.graphics.c_opengl as cgl

cdef inline void log_gl_error(str note):
    IF DEBUG_GL:
        ret = cgl.glGetError()
        if ret:
            Logger.error("OpenGL Error: {note} {ret1} / {ret2}".format(
                note=note, ret1=ret, ret2=hex(ret)))
