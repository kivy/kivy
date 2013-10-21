'''
Vertex Buffer
=============

The :class:`VBO` class handle the creation and update of Vertex Buffer Object in
OpenGL.

.. versionadded:: 1.6.0
    VertexFormat class added.  VertexFormat is used to describe the layout
    of the vertex data stored in vertex arrays/vbo.  The default vertex format
    is:
        VertexFormat(('vPosition', 2, 'float'), ('vTexCoords0', 2, 'float'))

.. versionchanged:: 1.6.0
    VBO now no longer has a fixed vertex format, if no VertexFormat is given
    at initialization, the default vertex format is used.
'''

__all__ = ('VBO', 'VertexBatch', 'VertexFormat')

include "config.pxi"
include "common.pxi"

from os import environ
from kivy.graphics.buffer cimport Buffer
from kivy.graphics.c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from kivy.graphics.c_opengl_debug cimport *
from kivy.graphics.vertex cimport *
from kivy.logger import Logger
from kivy.graphics.context cimport Context, get_context
from kivy.graphics.instructions cimport getActiveContext
from kivy.graphics.shader cimport Shader

cdef VertexFormat default_vertex = VertexFormat( (b'vPosition', 2, 'float'),
        (b'vTexCoords0', 2, 'float'))

cdef short V_NEEDGEN = 1 << 0
cdef short V_NEEDUPLOAD = 1 << 1
cdef short V_HAVEID = 1 << 2

cdef class VBO:
    '''
    .. versionchanged:: 1.6.0
        VBO now no longer has a fixed vertex format, if no VertexFormat is given
        at initialization, the default vertex format is used.
    '''
    def __cinit__(self, VertexFormat vertex_format=None):
        self.usage  = GL_DYNAMIC_DRAW
        self.target = GL_ARRAY_BUFFER
        if vertex_format is None:
            vertex_format = default_vertex
        self.vertex_format = vertex_format
        self.format = vertex_format.vattr
        self.format_count = vertex_format.vattr_count
        self.format_size = vertex_format.vbytesize
        self.flags = V_NEEDGEN | V_NEEDUPLOAD
        self.vbo_size = 0

    def __dealloc__(self):
        get_context().dealloc_vbo(self)

    def __init__(self, VertexFormat vertex_format=None):
        get_context().register_vbo(self)
        self.data = Buffer(self.format_size)

    cdef int have_id(self):
        return self.flags & V_HAVEID

    cdef void update_buffer(self):
        # generate VBO if not done yet
        if self.flags & V_NEEDGEN:
            glGenBuffers(1, &self.id)
            self.flags &= ~V_NEEDGEN
            self.flags |= V_HAVEID

        # if the size doesn't match, we need to reupload the whole data
        if self.vbo_size < self.data.size():
            self.vbo_size = self.data.size()
            glBindBuffer(GL_ARRAY_BUFFER, self.id)
            glBufferData(GL_ARRAY_BUFFER, self.vbo_size, self.data.pointer(), self.usage)
            self.flags &= ~V_NEEDUPLOAD

        # if size match, update only what is needed
        elif self.flags & V_NEEDUPLOAD:
            glBindBuffer(GL_ARRAY_BUFFER, self.id)
            glBufferSubData(GL_ARRAY_BUFFER, 0, self.data.size(), self.data.pointer())
            self.flags &= ~V_NEEDUPLOAD

    cdef void bind(self):
        cdef Shader shader = getActiveContext()._shader
        cdef vertex_attr_t *attr
        cdef int offset = 0, i
        self.update_buffer()
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        shader.bind_vertex_format(self.vertex_format)
        for i in xrange(self.format_count):
            attr = &self.format[i]
            if attr.per_vertex == 0:
                continue
            glVertexAttribPointer(attr.index, attr.size, attr.type,
                    GL_FALSE, <GLsizei>self.format_size, <GLvoid*><long>offset)
            offset += attr.bytesize

    cdef void unbind(self):
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    cdef void add_vertex_data(self, void *v, unsigned short* indices, int count):
        self.flags |= V_NEEDUPLOAD
        self.data.add(v, indices, count)

    cdef void update_vertex_data(self, int index, void* v, int count):
        self.flags |= V_NEEDUPLOAD
        self.data.update(index, v, count)

    cdef void remove_vertex_data(self, unsigned short* indices, int count):
        self.data.remove(indices, count)

    cdef void reload(self):
        self.flags = V_NEEDUPLOAD | V_NEEDGEN
        self.vbo_size = 0

    def __repr__(self):
        return '<VBO at %x id=%r count=%d size=%d>' % (
                id(self), self.id if self.flags & V_HAVEID else None,
                self.data.count(), self.data.size())

cdef class VertexBatch:
    def __init__(self, **kwargs):
        get_context().register_vertexbatch(self)
        self.usage  = GL_DYNAMIC_DRAW
        cdef object lushort = sizeof(unsigned short)
        self.vbo = kwargs.get('vbo')
        if self.vbo is None:
            self.vbo = VBO()
        self.vbo_index = Buffer(lushort) #index of every vertex in the vbo
        self.elements = Buffer(lushort) #indices translated to vbo indices
        self.elements_size = 0
        self.flags = V_NEEDGEN | V_NEEDUPLOAD

        self.set_data(NULL, 0, NULL, 0)
        self.set_mode(kwargs.get('mode'))

    def __dealloc__(self):
        get_context().dealloc_vertexbatch(self)

    cdef int have_id(self):
        return self.flags & V_HAVEID

    cdef void reload(self):
        self.flags = V_NEEDGEN | V_NEEDUPLOAD
        self.elements_size = 0

    cdef void clear_data(self):
        # clear old vertices from vbo and then reset index buffer
        self.vbo.remove_vertex_data(<unsigned short*>self.vbo_index.pointer(),
                                    self.vbo_index.count())
        self.vbo_index.clear()
        self.elements.clear()

    cdef void set_data(self, void *vertices, int vertices_count,
                       unsigned short *indices, int indices_count):
        #clear old vertices first
        self.clear_data()
        self.elements.grow(indices_count)

        # now append the vertices and indices to vbo
        #vsize = self.vbo.vertex_format.vsize
        self.append_data(vertices, vertices_count, indices, indices_count)
        self.flags |= V_NEEDUPLOAD

    cdef void append_data(self, void *vertices, int vertices_count,
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
        self.flags |= V_NEEDUPLOAD

    cdef void draw(self):
        cdef int count = self.elements.count()
        if count == 0:
            return

        # create when needed
        if self.flags & V_NEEDGEN:
            glGenBuffers(1, &self.id)
            self.flags &= ~V_NEEDGEN
            self.flags |= V_HAVEID

        # bind to the current id
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.id)

        # cache indices in a gpu buffer too
        if self.flags & V_NEEDUPLOAD:
            if self.elements_size == self.elements.size():
                glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, self.elements_size,
                    self.elements.pointer())
            else:
                glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.elements.size(),
                    self.elements.pointer(), self.usage)
                self.elements_size = self.elements.size()
            self.flags &= ~V_NEEDUPLOAD

        self.vbo.bind()

        # draw the elements pointed by indices in ELEMENT ARRAY BUFFER.
        glDrawElements(self.mode, count, GL_UNSIGNED_SHORT, NULL)

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

    def __repr__(self):
        return '<VertexBatch at %x id=%r vertex=%d size=%d mode=%s vbo=%x>' % (
                id(self), self.id if self.flags & V_HAVEID else None,
                self.elements.count(), self.elements.size(), self.get_mode(),
                id(self.vbo))
