include "config.pxi"
include "common.pxi"
include "gl_debug_logger.pxi"

from kivy.graphics.c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from kivy.graphics.c_opengl_debug cimport *

class PBOException(Exception):
    pass


# cdef pbo_update(int _id, int data_size, char *target) nogil:
#     cdef char *ptr
#     glBindBuffer(GL_PIXEL_UNPACK_BUFFER, _id)
#     ptr = glMapBuffers(GL_PIXEL_UNPACK_BUFFER, GL_WRITE_ONLY)
#     if ptr:
#         memcpy(ptr, target, data_size * pixel_size)
#         glUnmapBuffer(GL_PIXEL_UNPACK_BUFFER)
#     else:
#         raise PBOException('unable to map PBO buffer')
#     glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0)
#

cdef class PBO:
    def __init__(self, width, height):
        cdef int data_size = width * height
        self.width = width
        self.height = height
        glGenBuffers(1, &self._id)

        if self._id <= 0:
            raise PBOException('invalid glGenBuffers result')


    cdef void release(self):
        glDeleteBuffers(1, &self._id)

    cpdef GLuint get_id(self):
        #print "get_id called", self._id
        return self._id
