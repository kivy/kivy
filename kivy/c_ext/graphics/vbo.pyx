
__all__ = ('VBO', )

include "common.pxi"

from buffer cimport Buffer
from c_opengl cimport *
from vertex cimport *
from pprint import pprint
from kivy.logger import Logger

cdef class VBO:
    def __cinit__(self, **kwargs):
        self.usage  = GL_DYNAMIC_DRAW
        self.target = GL_ARRAY_BUFFER
        self.format = VERTEX_ATTRIBUTES
        self.need_upload = 1
        self.vbo_size = 0
        glGenBuffers(1, &self.id)

    def __dealloc__(self):
        glDeleteBuffers(1, &self.id)

    def __init__(self, **kwargs):
        self.format = kwargs.get('format', self.format)
        self.data = Buffer(sizeof(vertex))

    cdef allocate_buffer(self):
        Logger.trace("VBO:allocating VBO " + str(self.data.size()))
        self.vbo_size = self.data.size()
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        glBufferData(GL_ARRAY_BUFFER, self.vbo_size, self.data.pointer(), self.usage)
        self.need_upload = 0

    cdef update_buffer(self):
        cdef vertex* data = <vertex*>self.data.pointer()
        if self.vbo_size < self.data.size():
            self.allocate_buffer()
        elif self.need_upload:
            Logger.trace("VBO:uploading VBO " + str(self.data.size()))
            for i in range(self.data.count()):
                Logger.trace("VBO: uploading, v[%d]  x=%d, y=%d" % (i, data[i].x, data[i].y))
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
            Logger.trace("VBO: binding buffer %d  attr %s  index %d" % (self.id, attr, attr['index']))
            glVertexAttribPointer(attr['index'], attr['size'], attr['type'],
                                  GL_FALSE, sizeof(vertex), <GLvoid*>offset)
            offset += attr['bytesize']

    cdef unbind(self):
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    cdef add_vertex_data(self, void *v, int* indices, int count):
        self.need_upload = 1
        self.data.add(v, indices, count)

    cdef update_vertex_data(self, int index, vertex* v, int count):
        self.need_upload = 1
        self.data.update(index, v, count)

    cdef remove_vertex_data(self, int* indices, int count):
        self.data.remove(indices, count)

    """
    cdef list add_vertices(self, list vertices):
        self.need_upload = 1
        self.data.add(v, indices, count)

    cdef update_vertices(self, list indices, list ):
        self.need_upload = 1
        self.data.update(index, v, count)

    cdef remove_vertices(self, int* indices, int count):
        self.data.remove(indices, count)
    """


cdef class VertexBatch:
    
    def __init__(self, **kwargs):
        self.vbo = kwargs.get('vbo', VBO())
        self.vbo_index = Buffer(sizeof(int)) #index of every vertex in the vbo
        self.elements = Buffer(sizeof(int)) #indices translated to vbo indices
        
        vertices = kwargs.get('vertices', [])
        indices  = kwargs.get('indices' , [])
        self.set_data(vertices, indices)

    cdef set_data(self, list vertices, list indices):
        self.vertices = vertices
        self.indices  = indices
        self.build()

    cdef build(self):
        Logger.trace("VB: start build  vbo size=%d"%self.vbo.data.count())
        cdef int  num_verts = len(self.vertices)

        #clear vbo, and reset index buffer
        Logger.trace("VB: removing %d verts from vbo"%self.vbo_index.count())
        self.vbo.remove_vertex_data(<int*>self.vbo_index.pointer(), self.vbo_index.count())
        self.vbo.data.pack()
        self.vbo_index = Buffer(sizeof(int))
        Logger.trace("VB:  vbo size=%d"%self.vbo.data.count())
        
        #add vertex data to vbo and get index for every vertex added
        cdef Vertex v
        cdef int vi
        pprint(self.vertices)
        for i in range(num_verts):
            v = self.vertices[i]
            self.vbo.add_vertex_data(&(v.data), &vi, 1)
            self.vbo_index.add(&vi, NULL, 1)
            Logger.trace("VB: building  v[%d]->vbo[%d]  x=%d, y=%d" %(i, vi, v.data.x, v.data.y))

        #build element list for DrawElements using vbo indices
        cdef int local_index
        cdef int * vbi = <int*>self.vbo_index.pointer()
        cdef vertex* data = <vertex*>self.vbo.data.pointer()
        cdef vertex vert
        self.elements = Buffer(sizeof(int))
        for i in range(len(self.indices)):
            local_index = self.indices[i]
            self.elements.add(&vbi[local_index], NULL, 1)
            vert = data[vbi[local_index]]
            Logger.trace("VB: elements  i[%d]->e[%d]  x=%d, y=%d" %(i, vbi[local_index],vert.x, vert.y))

    cdef draw(self):
        self.vbo.bind()
        Logger.trace("VB: drawing" + str(self.elements.count()))
        glDrawElements(GL_TRIANGLES,    self.elements.count(), 
                       GL_UNSIGNED_INT, self.elements.pointer())

