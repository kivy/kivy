
__all__ = ('VertexFormat', 'VertexFormatException')

include "../include/config.pxi"
include "common.pxi"

from kivy.graphics.cgl cimport GL_FLOAT, GLfloat


class VertexFormatException(Exception):
    pass


cdef class VertexFormat:
    '''VertexFormat is used to describe the layout of the vertex data stored
    in vertex arrays/vbo's.

    .. versionadded:: 1.6.0
    '''
    def __cinit__(self, *fmt):
        self.vattr = NULL
        self.vattr_count = 0
        self.vsize = 0
        self.vbytesize = 0

    def __dealloc__(self):
        if self.vattr != NULL:
            free(self.vattr)
            self.vattr = NULL

    def __init__(self, *fmt):
        cdef vertex_attr_t *attr
        cdef int index, size

        if not fmt:
            raise VertexFormatException('No format specified')

        self.last_shader = None
        self.vattr_count = <long>len(fmt)
        self.vattr = <vertex_attr_t *>malloc(sizeof(vertex_attr_t) * self.vattr_count)

        if self.vattr == NULL:
            raise MemoryError()

        index = 0
        for name, size, tp in fmt:
            attr = &self.vattr[index]

            # fill the vertex format
            attr.per_vertex = 1
            attr.name = <bytes>name
            attr.index = 0 # will be set by the shader itself
            attr.size = size

            # only float is accepted as attribute format
            if tp == 'float':
                attr.type = GL_FLOAT
                attr.bytesize = sizeof(GLfloat) * size
            else:
                raise VertexFormatException('Unknown format type %r' % tp)

            # adjust the size, and prepare for the next iteration.
            index += 1
            self.vsize += attr.size
            self.vbytesize += attr.bytesize
