
__all__ = ('VBO', )

include "common.pxi"

from buffer cimport Buffer
from c_opengl cimport *
from vertex cimport *

cdef class VBO:
    def __cinit__(self):
        self.usage  = GL_DYNAMIC_DRAW
        self.target = GL_ARRAY_BUFFER
        self.format = VERTEX_ATTRIBUTES
        self.need_upload = 1
        self.vbo_size = 0

    def __init__(self, **kwargs):
        self.format = kwargs.get('format', self.format)
        self.data = Buffer(sizeof(vertex))
        self.create_buffer()

    cdef create_buffer(self):
        glGenBuffers(1, &self.id)
        self.allocate_buffer()

    cdef allocate_buffer(self):
        self.vbo_size = self.data.size()
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        glBufferData(GL_ARRAY_BUFFER, self.vbo_size, self.data.pointer(), self.usage)
        self.need_upload = 0

    cdef update_buffer(self):
        if self.vbo_size < self.data.size():
            self.allocate_buffer()
        elif self.need_upload:
            glBindBuffer(GL_ARRAY_BUFFER, self.id)
            glBufferSubData(GL_ARRAY_BUFFER, 0, self.data.size(), self.data.pointer())
            self.need_upload  = 0

    cdef bind(self):
        cdef int offset = 0
        self.update_buffer()
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        for attr in self.format:
            if not attr['per_vertex']:
                continue
            glVertexAttribPointer(attr['index'], attr['size'], attr['type'],
                                  GL_FALSE, sizeof(vertex), <GLvoid*>offset)
            offset += attr['bytesize']

    cdef unbind(self):
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    cdef add_vertices(self, void *v, int* indices, int count):
        self.need_upload = 1
        self.data.add(v, indices, count)

    cdef update_vertices(self, int index, vertex* v, int count):
        self.need_upload = 1
        self.data.update(index, v, count)

    cdef remove_vertices(self, int* indices, int count):
        self.data.remove(indices, count)

