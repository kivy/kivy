__all__ = ('Triangle', 'Rectangle', 'BorderImage', 'Ellipse')

include "graphics_common.pxi"

from kivy.logger import Logger
from kivy.resources import resource_find
from kivy.core.image import Image
from graphics_vertex cimport *
from c_opengl cimport *

cdef class VertexDataInstruction(GraphicInstruction):
    '''A VertexDataInstruction pushes vertices into the graphics pipeline
    this class manages a vbo, allocating a set of vertices on the vbo
    and can update the vbo data, when local changes have been made

    :Parameters:
        `source`: str
            Filename to load for the texture
        `texture`: Texture
            The texture to be bound while drawing the vertices

    '''
    def __cinit__(self):
        self._texture = None
        self.v_count = 0
        self.v_buffer = None
        self.v_data = NULL

    def __init__(self, **kwargs):
        GraphicInstruction.__init__(self, GI_VERTEX_DATA)
        self.vbo        = self.canvas.vertex_buffer
        self.v_count    = 0 #no vertices to draw until initialized
        self.source     = kwargs.get('source', None)
        self.texture    = kwargs.get('texture', None)

    cdef allocate_vertex_buffers(self, int num_verts):
        '''For allocating and initializing vertes data buffers of this
        GraphicElement both locally and on VBO.

        Allocates local vertex and index buffers to be able to hold num_verts
        vertices.  adds the vertices to the vbo associated with the elements
        canvas and sets vbo indices in i_data.

        After calling the follwoing buffers will have enough room for
        num_verts :

            self.vbo:
                num_verts are added to the canvas' VBO

            self.v_data:
                `vertex*`, vertex array with enough room for num_verts.
                pointing to start of v_buffer, so you can set data using
                indexing.  liek:  self.v_data[i] = <vertex> v

            self.i_data:
                `int*`, int array of size num_verts. Has vbo index of vertex in
                v_data.  so self.i_data[i] is vbo index of self.v_buffer[i]
        '''

        Logger.trace('GVertex: allocating vertex data: %s' % str(num_verts))

        # create vertex and index buffers
        self.v_buffer = Buffer(sizeof(vertex))
        self.i_buffer = Buffer(sizeof(GLint))

        # allocate enough room for vertex and index data
        self.v_count = num_verts
        self.v_buffer.grow(num_verts)
        self.i_buffer.grow(num_verts)

        # set data pointers to be able to index vertices and indices
        self.v_data = <vertex*>  self.v_buffer.pointer()
        self.i_data = <int*> self.i_buffer.pointer()

        # allocte on vbo and update indices with
        self.vbo.add_vertices(self.v_data, self.i_data, self.v_count)

        Logger.trace('GVertex: done allocating')


    property indices:
        '''This property is write only. It determines, which of the vertices
        from this object will be drawn by the canvas.  if e.g. the object has 4
        vertices. Then setting vdi.indices = (0,1,2 2,4,0), will draw two
        triangles corrosponding to the vertices stored in v_data this function
        automatically converts the indices from local to vbo indices.
        '''
        def __set__(self, object batch): #list or tuple..iterable?
            #create element buffer for list of vbo indices to be drawn
            self.element_buffer = Buffer(sizeof(int))
            cdef int i, e
            for i in xrange(len(batch)):
                e = batch[i]
                self.element_buffer.add(&self.i_data[e], NULL, 1)
            self.element_data = <int*> self.element_buffer.pointer()
            self.num_elements = self.element_buffer.count()
            #since we changed the list of vertices to draw, canvas must recompile
            self.canvas.update(self)


    cdef update_vbo_data(self):
        '''Updates the vertex data stored on vbo to be same as local needs to be
        called if you change v_data inside this element.
        '''
        cdef vertex* vtx = self.v_data
        cdef int* idx    = self.i_data
        cdef int i

        Logger.trace('GVertex: uploading vbo data')

        for i in range(self.v_count):
            #print idx[i], vtx[i].x, vtx[i].y, vtx[i].s0, vtx[i].t0
            self.vbo.update_vertices(idx[i], &vtx[i], 1)
        self.canvas.update(self)

    cdef trigger_texture_update(self):
        '''Called when the texture is updated
        '''
        pass

    property texture:
        '''Set/get the texture to be bound while the vertices are being drawn
        '''
        def __get__(self):
            return self._texture
        def __set__(self, tex):
            if tex == self._texture:
                return
            self._texture = tex
            self.trigger_texture_update()

    property source:
        '''Set/get the source (filename) to load for texture.
        '''
        def __get__(self):
            return self._source
        def __set__(self, bytes filename):
            if self._source == filename:
                return
            self._source = resource_find(filename)
            if self._source is None:
                Logger.warning('GVertex: unable to found <%s>' % filename)
                return
            if filename is None:
                self.texture = None
            else:
                self.texture = Image(self._source).texture


cdef class Triangle(VertexDataInstruction):
    def __init__(self, **kwargs):
        VertexDataInstruction.__init__(self, **kwargs)
        self.allocate_vertex_buffers(3)
        self.points  = kwargs.get('points', (0,0,  100,0,  50,100))
        self.tex_coords  = kwargs.get('tex_coords', self.points)
        self.indices = (0,1,2)
        self.canvas.add(self)

    cdef build(self):
        cdef float *vc, *tc
        vc = self._points;  tc = self._tex_coords
        self.v_data[0] = vertex4f(vc[0], vc[1], tc[0], tc[1])
        self.v_data[1] = vertex4f(vc[2], vc[3], tc[2], tc[3])
        self.v_data[2] = vertex4f(vc[4], vc[5], tc[4], tc[5])
        self.update_vbo_data()

    property points:
        def __set__(self, points):
            cdef int i
            for i in range(6):
                self._points[i] = points[i]
            self.build()

        def __get__(self):
            cdef float *p = self._points
            return (p[0],p[1],p[2],p[3],p[4],p[5])

    property tex_coords:
        def __set__(self, coords):
            cdef int i
            for i in range(6):
                self._tex_coords[i] = coords[i]
            self.build()

        def __get__(self):
            cdef float *p = self._tex_coords
            return (p[0],p[1],p[2],p[3],p[4],p[5])


cdef class Rectangle(VertexDataInstruction):
    def __init__(self, **kwargs):
        self._user_texcoords = 0
        self._is_init = 0
        VertexDataInstruction.__init__(self, **kwargs)
        self.allocate_vertex_buffers(4)
        self.indices = (0,1,2, 2,3,0)

        # get keyword args for configuring rectangle
        self.x, self.y  = kwargs.get('pos',  (0,0))
        self.w, self.h  = kwargs.get('size', (100,100))
        if 'tex_coords' in kwargs:
            self.tex_coords = kwargs['tex_coords']
        else:
            self.tex_coords = (0.0,0.0, 1.0,0.0, 1.0,1.0, 0.0,1.0)
            self._user_texcoords = 0


        # tell VBO which triangles to draw using our vertices
        self.canvas.add(self)

        # trigger the tx coords + rebuild only now
        self._is_init = 1
        self.trigger_texture_update()
        Logger.trace("rectangle: tex_coords"+str(self.tex_coords))

    cdef build(self):
        cdef float* tc = self._tex_coords
        cdef float x,y,w,h
        x = self.x; y=self.y; w = self.w; h = self.h
        self.v_data[0] = vertex4f(x,    y, tc[0], tc[1])
        self.v_data[1] = vertex4f(x+w,  y, tc[2], tc[3])
        self.v_data[2] = vertex4f(x+w, y+h, tc[4], tc[5])
        self.v_data[3] = vertex4f(x,   y+h, tc[6], tc[7])
        self.update_vbo_data()

    cdef trigger_texture_update(self):
        if not self._is_init:
            return
        if self._texture is None or self._user_texcoords == 1:
            return
        self.set_tex_coords(self._texture.tex_coords)

    cdef set_tex_coords(self, coords):
        for i in range(8):
            self._tex_coords[i] = coords[i]
        self.build()

    property pos:
        def __get__(self):
            return (self.x, self.y)
        def __set__(self, pos):
            self.x = pos[0]
            self.y = pos[1]
            self.build()

    property size:
        def __get__(self):
            return (self.w, self.h)
        def __set__(self, size):
            self.w = size[0]
            self.h = size[1]
            self.build()

    property tex_coords:
        def __get__(self):
            cdef float *p = self._tex_coords
            return (p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7])
        def __set__(self, coords):
            self._user_texcoords = 1
            self.set_tex_coords(coords)


cdef class BorderImage(VertexDataInstruction):
    def __init__(self, **kwargs):
        # we have 16 vertices in BorderImage
        VertexDataInstruction.__init__(self, **kwargs)
        self.allocate_vertex_buffers(16)

        # get keyword args for configuring rectangle
        cdef tuple s = kwargs.get('size', (100, 100))
        cdef tuple p = kwargs.get('pos', (0,0))
        cdef tuple bv = kwargs.get('border', (5,5,5,5))
        cdef float* b = self._border
        b[0] = bv[0];  b[1]=bv[1];  b[2]=bv[2];  b[3]=bv[3];
        self.x = p[0]; self.y = p[1]
        self.w = s[0]; self.h = s[1]

        # setting the texture or filename will rebuild the border rectangle
        self.source = kwargs.get('source', None)
        self.texture = kwargs.get('texture', None)

        # tell VBO which triangles to draw using our vertices
        # two triangles per quad
        '''
            v9---v8------v7----v6
            |        b2        |
           v10  v15------v14   v5
            |    |        |    |
            |-b4-|        |-b1-|
            |    |        |    |
           v11  v12------v13   v4
            |        b0        |
            v0---v1------v2----v3
        '''
        self.indices = (
             0,  1, 12,    12, 11,  0,  # bottom left
             1,  2, 13,    13, 12,  1,  # bottom middle
             2,  3,  4,     4, 13,  2,  # bottom right
            13,  4,  5,     5, 14, 13,  # center right
            14,  5,  6,     6,  7, 14,  # top right
            15, 14,  7,     7,  8, 15,  # top middle
            10, 15,  8,     8,  9, 10,  # top left
            11, 12, 15,    15, 10, 11,  # center left
            12, 13, 14,    14, 15, 12)  # center middel
        self.canvas.add(self)

    cdef build(self):
        if not self.texture:
            Logger.trace('GBorderImage: texture missing')
            return

        #pos and size of border rectangle
        cdef float x,y,w,h
        x=self.x;  y=self.y; w=self.w;  h=self.h

        # width and heigth of texture in pixels, and tex coord space
        cdef float tw, th, tcw, tch
        cdef float* tc = self._tex_coords
        tsize  = self.texture.size
        tw  = tsize[0]
        th  = tsize[1]
        tcw = tc[2] - tc[0]  #right - left
        tch = tc[7] - tc[1]  #top - bottom

        # calculate border offset in texture coord space
        # border width(px)/texture width(px) *  tcoord width
        cdef float *b = self._border
        cdef float tb[4] # border offset in texture coordinate space
        tb[0] = b[0] / th*tch
        tb[1] = b[1] / tw*tcw
        tb[2] = b[2] / th*tch
        tb[3] = b[3] / tw*tcw


        # horizontal and vertical sections
        cdef float hs[4]
        cdef float vs[4]
        hs[0] = x;            vs[0] = y
        hs[1] = x + b[3];     vs[1] = y + b[0]
        hs[2] = x + w - b[1]; vs[2] = y + h - b[2]
        hs[3] = x + w;        vs[3] = y + h

        cdef float ths[4]
        cdef float tvs[4]
        ths[0] = tc[0];              tvs[0] = tc[1]
        ths[1] = tc[0] + tb[3];      tvs[1] = tc[1] + tb[0]
        ths[2] = tc[0] + tcw-tb[1];  tvs[2] = tc[1] + tch - tb[2]
        ths[3] = tc[0] + tcw;        tvs[3] = tc[1] + tch

        # set the vertex data
        cdef vertex* v = self.v_data
        # bottom row
        v[0] = vertex4f(hs[0], vs[0], ths[0], tvs[0])
        v[1] = vertex4f(hs[1], vs[0], ths[1], tvs[0])
        v[2] = vertex4f(hs[2], vs[0], ths[2], tvs[0])
        v[3] = vertex4f(hs[3], vs[0], ths[3], tvs[0])

        # bottom inner border row
        v[11] = vertex4f(hs[0], vs[1], ths[0], tvs[1])
        v[12] = vertex4f(hs[1], vs[1], ths[1], tvs[1])
        v[13] = vertex4f(hs[2], vs[1], ths[2], tvs[1])
        v[4]  = vertex4f(hs[3], vs[1], ths[3], tvs[1])

        # top inner border row
        v[10] = vertex4f(hs[0], vs[2], ths[0], tvs[2])
        v[15] = vertex4f(hs[1], vs[2], ths[1], tvs[2])
        v[14] = vertex4f(hs[2], vs[2], ths[2], tvs[2])
        v[5]  = vertex4f(hs[3], vs[2], ths[3], tvs[2])

        # top row
        v[9] = vertex4f(hs[0], vs[3], ths[0], tvs[3])
        v[8] = vertex4f(hs[1], vs[3], ths[1], tvs[3])
        v[7] = vertex4f(hs[2], vs[3], ths[2], tvs[3])
        v[6] = vertex4f(hs[3], vs[3], ths[3], tvs[3])

        # phew....all done
        self.update_vbo_data()

    cdef trigger_texture_update(self):
        if self._texture is None:
            return
        tcords = self.texture.tex_coords
        for i in range(8):
            self._tex_coords[i] = tcords[i]
        self.build()

    property pos:
        def __get__(self):
            return (self.x, self.y)
        def __set__(self, pos):
            self.x = pos[0]
            self.y = pos[1]
            self.build()

    property size:
        def __get__(self):
            return (self.w, self.h)
        def __set__(self, size):
            self.w = size[0]
            self.h = size[1]
            self.build()

    property border:
        def __get__(self):
            cdef float* b = self._border
            return (b[0], b[1], b[2], b[3])
        def __set__(self, b):
            cdef int i
            for i in xrange(4):
                self._border[i] = b[0]
            self.build()


cdef class Ellipse(VertexDataInstruction):
    def __init__(self, *args, **kwargs):
        VertexDataInstruction.__init__(self, **kwargs)

        #get keyword args for configuring rectangle
        self.segments = kwargs.get('segments', 180)
        cdef tuple s = kwargs.get('size', (100, 100))
        cdef tuple p = kwargs.get('pos', (0,0))
        self.x = p[0]; self.y = p[1]
        self.w = s[0]; self.h = s[1]

        cdef tuple t_coords =  (0.0,0.0, 1.0,0.0, 1.0,1.0, 0.0,1.0)
        if self.texture:
            t_coords = self.texture.tex_coords
        self.tex_coords  = kwargs.get('tex_coords', t_coords)

        self.allocate_vertex_buffers(self.segments + 1)
        self.build()

        indices = []
        for i in range(self.segments):
            indices.extend(  (i, self.segments, (i+1)%self.segments) )
        self.indices = indices
        self.canvas.add(self)

    cdef build(self):
        cdef float x, y, angle, rx, ry, ttx, tty, tx, ty, tw, th
        cdef vertex* v = self.v_data
        cdef int i = 0
        cdef tuple tc = self.tex_coords
        tx = tc[0]; ty=tc[1];  tw=tc[4]-tx;  th=tc[5]-ty
        angle = 0.0
        rx = 0.5*(self.w)
        ry = 0.5*(self.h)
        for i in xrange(self.segments):
            # rad = deg * (pi / 180), where pi/180 = 0.0174...
            angle = i * 360.0/self.segments *0.017453292519943295
            x = (self.x+rx)+ (rx*cos(angle))
            y = (self.y+ry)+ (ry*sin(angle))
            ttx = ((x-self.x)/self.w)*tw + tx
            tty = ((y-self.y)/self.h)*th + ty
            v[i] = vertex4f(x, y, ttx, tty)
        x, y = self.x+rx, self.y+ry
        ttx = ((x-self.x)/self.w)*tw + tx
        tty = ((y-self.y)/self.h)*th + ty
        v[self.segments] = vertex4f(x,y,ttx, tty )
        self.update_vbo_data()

    property tex_coords:
        def __get__(self):
            return self._tex_coords
        def __set__(self, coords):
            self._tex_coords = coords

    property pos:
        def __get__(self):
            return (self.x, self.y)
        def __set__(self, pos):
            self.x = pos[0]
            self.y = pos[1]
            self.build()

    property size:
        def __get__(self):
            return (self.w, self.h)
        def __set__(self, size):
            self.w = size[0]
            self.h = size[1]
            self.build()

