'''
Vertex Buffer
=============

The :class:`VBO` class handle the creation and update of Vertex Buffer Object in
OpenGL. 
'''

__all__ = ('VBO', 'VertexBatch')

include "config.pxi"
include "common.pxi"

from os import environ
from buffer cimport Buffer
from c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from c_opengl_debug cimport *
from vertex cimport *
from kivy.logger import Logger

cdef int vattr_count = 2
cdef vertex_attr_t vattr[2]
vattr[0] = ['vPosition', 0, 2, GL_FLOAT, sizeof(GLfloat) * 2, 1]
vattr[1] = ['vTexCoords0', 1, 2, GL_FLOAT, sizeof(GLfloat) * 2, 1]
#vertex_attr_list[2] = ['vTexCoords1', 2, 2, GL_FLOAT, sizeof(GLfloat) * 2, 1]
#vertex_attr_list[3] = ['vTexCoords2', 3, 2, GL_FLOAT, sizeof(GLfloat) * 2, 1]
#vertex_attr_list[4] = ['vColor', 4, 2, GL_FLOAT, sizeof(GLfloat) * 4, 0]

cdef object _vbo_release_trigger = None
cdef list _vbo_release_list = []


cdef int vbo_vertex_attr_count():
    '''Return the number of vertex attributes used in VBO
    '''
    return vattr_count

cdef vertex_attr_t *vbo_vertex_attr_list():
    '''Return the list of vertex attributes used in VBO
    '''
    return vattr

cdef class VBO:
    def __cinit__(self, **kwargs):
        self.usage  = GL_DYNAMIC_DRAW
        self.target = GL_ARRAY_BUFFER
        self.format = vbo_vertex_attr_list()
        self.format_count = vbo_vertex_attr_count()
        self.need_upload = 1
        self.vbo_size = 0
        glGenBuffers(1, &self.id)

    def __dealloc__(self):
        # Add texture deletion outside GC call.
        if _vbo_release_list is not None:
            _vbo_release_list.append(self.id)
            if _vbo_release_trigger is not None:
                _vbo_release_trigger()

    def __init__(self, **kwargs):
        self.data = Buffer(sizeof(vertex_t))

    cdef void allocate_buffer(self):
        #Logger.trace("VBO:allocating VBO " + str(self.data.size()))
        self.vbo_size = self.data.size()
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        glBufferData(GL_ARRAY_BUFFER, self.vbo_size, self.data.pointer(), self.usage)
        self.need_upload = 0

    cdef void update_buffer(self):
        if self.vbo_size < self.data.size():
            self.allocate_buffer()
        elif self.need_upload:
            glBindBuffer(GL_ARRAY_BUFFER, self.id)
            glBufferSubData(GL_ARRAY_BUFFER, 0, self.data.size(), self.data.pointer())
            self.need_upload  = 0

    cdef void bind(self):
        cdef vertex_attr_t *attr
        cdef int offset = 0, i
        self.update_buffer()
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        for i in xrange(self.format_count):
            attr = &self.format[i]
            if attr.per_vertex == 0:
                continue
            glVertexAttribPointer(attr.index, attr.size, attr.type,
                    GL_FALSE, sizeof(vertex_t), <GLvoid*><long>offset)
            offset += attr.bytesize

    cdef void unbind(self):
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    cdef void add_vertex_data(self, void *v, unsigned short* indices, int count):
        self.need_upload = 1
        self.data.add(v, indices, count)

    cdef void update_vertex_data(self, int index, vertex_t* v, int count):
        self.need_upload = 1
        self.data.update(index, v, count)

    cdef void remove_vertex_data(self, unsigned short* indices, int count):
        self.data.remove(indices, count)


cdef class VertexBatch:
    def __init__(self, **kwargs):
        cdef object lushort = sizeof(unsigned short)
        self.vbo = kwargs.get('vbo')
        if self.vbo is None:
            self.vbo = VBO()
        self.vbo_index = Buffer(lushort) #index of every vertex in the vbo
        self.elements = Buffer(lushort) #indices translated to vbo indices

        self.set_data(NULL, 0, NULL, 0)
        self.set_mode(kwargs.get('mode'))

    cdef void clear_data(self):
        # clear old vertices from vbo and then reset index buffer
        self.vbo.remove_vertex_data(<unsigned short*>self.vbo_index.pointer(),
                                    self.vbo_index.count())
        self.vbo_index.clear()
        self.elements.clear()


    cdef void set_data(self, vertex_t *vertices, int vertices_count,
                       unsigned short *indices, int indices_count):
        #clear old vertices first
        self.clear_data()
        self.elements.grow(indices_count)

        # now append the vertices and indices to vbo
        self.append_data(vertices, vertices_count, indices, indices_count)

    cdef void append_data(self, vertex_t *vertices, int vertices_count,
                          unsigned short *indices, int indices_count):
        # add vertex data to vbo and get index for every vertex added
        cdef unsigned short *vi = <unsigned short *>malloc(sizeof(unsigned short) * vertices_count)
        if vi == NULL:
            raise MemoryError('vertex index allocation')
        self.vbo.add_vertex_data(vertices, vi, vertices_count)
        self.vbo_index.add(vi, NULL, vertices_count)
        free(vi)

        # build element list for DrawElements using vbo indices
        # TODO: remove buffer usage in this case, the memory is always one big
        # block. no need to use add() everytime we need to reconstruct the list.
        cdef int local_index
        cdef unsigned short *vbi = <unsigned short*>self.vbo_index.pointer()
        for i in xrange(indices_count):
            local_index = indices[i]
            self.elements.add(&vbi[local_index], NULL, 1)

    cdef void draw(self):
        self.vbo.bind()
        glDrawElements(self.mode, self.elements.count(),
                       GL_UNSIGNED_SHORT, self.elements.pointer())
        self.vbo.unbind()

    cdef void set_mode(self, str mode):
        # most common case in top;
        self.mode_str = mode
        if mode is None:
            self.mode = GL_TRIANGLES
        elif mode == 'points':
            self.mode = GL_POINTS
        elif mode == 'line_strip':
            self.mode = GL_LINE_STRIP
        elif mode == 'line_loop':
            self.mode = GL_LINE_LOOP
        elif mode == 'lines':
            self.mode = GL_LINES
        elif mode == 'triangle_strip':
            self.mode = GL_TRIANGLE_STRIP
        elif mode == 'triangle_fan':
            self.mode = GL_TRIANGLE_FAN
        else:
            self.mode = GL_TRIANGLES

    cdef str get_mode(self):
        return self.mode_str

    cdef int count(self):
        return self.elements.count()

# Releasing vbo through GC is problematic. Same as any GL deletion.
def _vbo_release(*largs):
    cdef GLuint vbo_id
    if not _vbo_release_list:
        return
    Logger.trace('VBO: releasing %d vbos' % len(_vbo_release_list))
    for vbo_id in _vbo_release_list:
        glDeleteBuffers(1, &vbo_id)
    del _vbo_release_list[:]

if 'KIVY_DOC_INCLUDE' not in environ:
    from kivy.clock import Clock
    _vbo_release_trigger = Clock.create_trigger(_vbo_release)
