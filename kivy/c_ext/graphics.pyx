__all__ = (
    'Canvas', 'GraphicInstruction', 'ContextInstruction',
    'PushMatrix', 'PopMatrix', 'MatrixInstruction',
    'Transform', 'Rotate', 'Scale', 'Translate', 'LineWidth',
    'Color', 'BindTexture', 'VertexDataInstruction', 'Triangle',
    'Rectangle', 'BorderImage', 'Ellipse', 'Path',
    'PathInstruction', 'PathStart', 'PathLineTo', 'PathClose',
    'PathEnd','PathStroke', 'PathFill'
)


include "graphics_common.pxi"

from buffer cimport Buffer
from c_opengl cimport *
from graphics_vertex cimport *
from graphics_vbo cimport VBO
from graphics_shader cimport Shader
from graphics_context cimport GraphicContext
from graphics_matrix cimport MatrixStack


#tesselation of complex polygons
from kivy.c_ext.p2t import CDT, Point

#TODO: write matrix transforms in c or cython
from kivy.lib.transformations import matrix_multiply, identity_matrix, \
             rotation_matrix, translation_matrix, scale_matrix

from kivy.logger import Logger
from kivy.core.image import Image
from kivy.resources import resource_find


cdef class Canvas
cdef class GraphicContext
cdef class GraphicInstruction

cdef Canvas _active_canvas = None
cdef int _active_canvas_after = 0

cdef class CanvasAfter:
    cdef Canvas canvas
    def __init__(self, canvas):
        self.canvas = canvas

    def __enter__(self):
        self.canvas.__enter__(after=1)

    def __exit__(self, extype, value, traceback):
        self.canvas.__exit__(extype, value, traceback, after=1)


cdef class Canvas:
    cdef GraphicContext _context
    cdef VBO vertex_buffer
    cdef list texture_map
    cdef list _batch
    cdef list _batch_after
    cdef list _children
    cdef CanvasAfter _canvas_after

    #move to graphics compiler?:
    cdef int _need_compile
    cdef int num_slices
    cdef list batch_slices

    def __cinit__(self):
        self._context = GraphicContext.instance()
        self._canvas_after = CanvasAfter(self)
        self.vertex_buffer = VBO()
        self.texture_map = []
        self._batch = []
        self._batch_after = []
        self._children = []

        self._need_compile = 1
        self.batch_slices = []
        self.num_slices = 0

    property need_compile:
        def __set__(self, int i):
            if i:
                self.context.post_update()
            self._need_compile = i
        def __get__(self):
            return self._need_compile

    property context:
        def __get__(self):
            return self._context

    property batch:
        def __get__(self):
            return self._batch

    property after:
        def __get__(self):
            return self._canvas_after

    cpdef trigger(self):
        self._context.trigger()

    def __enter__(self, after=0):
        global _active_canvas, _active_canvas_after
        if _active_canvas:
            raise Exception('Cannot stack canvas usage.')
        _active_canvas = self
        _active_canvas_after = after

    def __exit__(self, extype, value, traceback, after=0):
        global _active_canvas, _active_canvas_after
        _active_canvas = None
        _active_canvas_after = after

    cpdef add_canvas(self, Canvas canvas):
        if not canvas in self._children:
            self._children.append(canvas)
        self._need_compile = 1

    cpdef remove_canvas(self, Canvas canvas):
        if canvas in self._children:
            self._children.remove(canvas)
        self._need_compile = 1

    cdef add(self, GraphicInstruction instruction):
        self.need_compile = 1
        if _active_canvas_after:
            self._batch_after.append(instruction)
        else:
            self._batch.append(instruction)

    cdef remove(self, GraphicInstruction instruction):
        self.need_compile = 1
        if _active_canvas_after:
            self._batch_after.remove(instruction)
        else:
            self._batch.remove(instruction)

    cdef update(self, instruction):
        ''' called by graphic instructions taht are part of the canvas,
            when they have been changed in some way '''
        self.need_compile = 1

    cdef compile_init(self):
        self.texture_map = []
        self.batch_slices = []

        # to prevent to regenerate object from previous compilation
        # remove all the object flagged as GI_COMPILER
        self._batch = self.compile_strip_compiler(self._batch)
        self._batch_after = self.compile_strip_compiler(self._batch_after)

    cdef list compile_strip_compiler(self, list batch):
        cdef GraphicInstruction x
        return [x for x in batch if not (x.code & GI_COMPILER)]

    cdef compile(self):
        Logger.trace('GCanvas: start compilation')

        self.compile_init()
        with self:
            self.compile_batch(self._batch)
            self.compile_children()
        with self.after:
            self.compile_batch(self._batch_after)

    cdef compile_batch(self, list batch):
        cdef GraphicInstruction item
        cdef int slice_start = -1
        cdef int slice_stop  = -1
        cdef int i, code, batch_len

        # care about the batch. since we adding instruction, the size can change
        # while we are iterating.
        batch_len = len(batch)

        # always start with binding vbo
        if batch_len:
            self.batch_slices.append(('bind', None))

        for i in xrange(batch_len):
            item = batch[i]
            code = item.code
            # the instruction modifies the context, so we cant combine the drawing
            # calls before and after it
            if code & GI_CONTEXT_MOD:
                #first compile the slices we been loopiing over which we can combine
                #from slice_start to slice_stop. (using compile_slice() )
                #add the context modifying instruction to batch_slices
                #reset slice start/stop index
                self.compile_slice('draw', batch, slice_start, slice_stop)
                self.batch_slices.append(('instruction', item))
                slice_start = slice_stop = -1

            # the instruction pushes vertices to the pipeline and doesnt modify
            # the context, so we can happily combine it with any prior or follwing
            # instructions that do the same, just keep incrementing slice stop index
            # until we cant combine any more, then well call compile_slice()
            elif code & GI_VERTEX_DATA:
                slice_stop = i
                if slice_start == -1:
                    slice_start = i

        # maybe we ended on an slice of vartex data, whcih we didnt push yet
        self.compile_slice('draw', batch, slice_start, slice_stop)

    cdef compile_children(self):
        cdef Canvas child
        cdef GraphicInstruction instr
        for child in self._children:
            instr = CanvasDraw(child)
            instr.code |= GI_COMPILER
            self.batch_slices.append(('instruction', instr))

    cdef compile_slice(self, str command, list batch, slice_start, slice_end):
        Logger.trace('Canvas: compiling slice: %s' % str((
                     slice_start, slice_end, command)))
        cdef GraphicInstruction item
        cdef VertexDataInstruction vdi
        cdef Buffer b = Buffer(sizeof(GLint))
        cdef int v, i
        cdef GraphicInstruction instr

        # check if we have a valid slice
        if slice_start == -1:
            return

        # loop over all the whole slice, and combine all instructions
        for item in batch[slice_start:slice_end+1]:
            if isinstance(item, VertexDataInstruction):
                vdi = item
                # add the vertex indices to be drawn from this item
                for i in range(vdi.num_elements):
                    v = vdi.element_data[i]
                    b.add(&v, NULL, 1)

            # handle textures (should go somewhere else?,
            # maybe set GI_CONTEXT_MOD FLAG ALSO?)
            if item.texture:
                instr = BindTexture(item.texture)
            else:
                instr = BindTexture(None)

            # flags the instruction as a generated one
            instr.code |= GI_COMPILER
            self.batch_slices.append(('instruction', instr))
            self.batch_slices.append((command, b))
            b = Buffer(sizeof(GLint))

        # last slice, all done, only have to add if there is actually somethign in it
        if b.count() > 0:
            self.batch_slices.append((command, b))

    cpdef draw(self):
        # early binding to prevent some python overhead
        self._draw()

    cdef _draw(self):
        cdef int i
        cdef Buffer b
        cdef ContextInstruction ci

        if self.need_compile:
            self.compile()
            self.need_compile = 0

        for command, item in self.batch_slices:
            if command == 'bind':
                self.vertex_buffer.bind()
                attr = VERTEX_ATTRIBUTES[0]
                glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer.id)
            elif command == 'instruction':
                ci = item
                ci.apply()
            elif command == 'draw':
                b = item
                self.context.flush()
                glDrawElements(GL_TRIANGLES, b.count(), GL_UNSIGNED_INT, b.pointer())

        self.context.finish_frame()


cdef class GraphicInstruction:
    '''Base class for all Graphics Instructions

    :Parameters:
        `code`: constant
            instruction code for hinting the compiler currently a
            combination of : GI_NOOP, GI_IGNORE, GI_CONTEXT_MOD,
            GI_VERTEX_DATA, GI_COMPILER
    '''
    #: Graphic instruction op code
    cdef int code

    #: Canvas on which to operate
    cdef Canvas canvas

    def __init__(self, int code):
        self.code = code
        self.canvas = _active_canvas


cdef class ContextInstruction(GraphicInstruction):
    '''Abstract Base class for GraphicInstructions that modidifies the
    context. (so that canvas/compiler can know about how to optimize).
    '''
    #: Graphics context to use (usually equal to _default_context)
    cdef GraphicContext context

    def __init__(self, *args, **kwargs):
        GraphicInstruction.__init__(self, GI_CONTEXT_MOD)
        self.context = self.canvas.context
        self.canvas.add(self)

    cdef apply(self):
        pass


cdef class LineWidth(ContextInstruction):
    '''Instruction to set the line width of the drawing context
    '''
    cdef float lw
    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self, **kwargs)
        if len(args) == 1:
            self.lw = args[0]

    def set(self, float lw):
        self.lw = lw

    cdef apply(self):
        self.canvas.context.set('linewidth', self.lw)


cdef class Color(ContextInstruction):
    '''Instruction to set the color state for any vetices being drawn after it
    '''
    cdef list color

    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self)
        self.rgba = args

    cdef apply(self):
        self.context.set('color', (self.r, self.g, self.b, self.a))

    property rgba:
        def __get__(self):
            return self.color
        def __set__(self, rgba):
            if not rgba:
                rgba = (1.0, 1.0, 1.0, 1.0)
            self.color = list(rgba)
            self.context.post_update()

    property rgb:
        def __get__(self):
            return self.color[:-1]
        def __set__(self, rgb):
            rgba = (rgb[0], rgb[1], rgb[2], 1.0)
            self.rgba = rgba

    property r:
        def __get__(self):
            return self.color[0]
        def __set__(self, r):
            self.rgba = [r, self.g, self.b, self.a]
    property g:
        def __get__(self):
            return self.color[1]
        def __set__(self, g):
            self.rgba = [self.r, g, self.b, self.a]
    property b:
        def __get__(self):
            return self.color[2]
        def __set__(self, b):
            self.rgba = [self.r, self.g, b, self.a]
    property a:
        def __get__(self):
            return self.color[3]
        def __set__(self, a):
            self.rgba = [self.r, self.g, self.b, a]


cdef class CanvasDraw(ContextInstruction):
    cdef Canvas obj

    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self)
        self.obj = args[0]

    cdef apply(self):
        self.obj.draw()


cdef class BindTexture(ContextInstruction):
    '''BindTexture Graphic instruction.
    The BindTexture Instruction will bind a texture and enable
    GL_TEXTURE_2D for subsequent drawing.

    :Parameters:
        `texture`: Texture
            specifies the texture to bind to the given index
    '''
    cdef object _texture

    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self)
        self.texture = args[0]

    cdef apply(self):
        self.canvas.context.set('texture0', self.texture)

    def set(self, object texture):
        self.texture = texture

    property texture:
        def __get__(self):
            return self._texture
        def __set__(self, tex):
            self._texture = tex
            self.context.post_update()


cdef class PushMatrix(ContextInstruction):
    '''PushMatrix on context's matrix stack
    '''
    cdef apply(self):
        self.context.get('mvm').push()

cdef class PopMatrix(ContextInstruction):
    '''Pop Matrix from context's matrix stack onto model view
    '''
    cdef apply(self):
        self.context.get('mvm').pop()


cdef class MatrixInstruction(ContextInstruction):
    '''Base class for Matrix Instruction on canvas
    '''

    cdef object mat

    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self)

    cdef apply(self):
        '''Apply matrix to the matrix of this instance to the
        context model view matrix
        '''
        self.context.get('mvm').apply(self.mat)

    property matrix:
        ''' Matrix property. Numpy matrix from transformation module
        setting the matrix using this porperty when a change is made
        is important, becasue it will notify the context about the update
        '''
        def __get__(self):
            return self.mat
        def __set__(self, mat):
            self.mat = mat
            self.context.post_update()

cdef class Transform(MatrixInstruction):
    '''Transform class.  A matrix instruction class which
    has function to modify the transformation matrix
    '''
    cpdef transform(self, object trans):
        '''Multiply the instructions matrix by trans
        '''
        self.mat = matrix_multiply(self.mat, trans)

    cpdef translate(self, float tx, float ty, float tz):
        '''Translate the instrcutions transformation by tx, ty, tz
        '''
        self.transform( translation_matrix(tx, ty, tz) )

    cpdef rotate(self, float angle, float ax, float ay, float az):
        '''Rotate the transformation by matrix by angle degress around the
        axis defined by the vector ax, ay, az
        '''
        self.transform( rotation_matrix(angle, [ax, ay, az]) )

    cpdef scale(self, float s):
        '''Applies a uniform scaling of s to the matrix transformation
        '''
        self.transform( scale_matrix(s, s, s) )

    cpdef identity(self):
        '''Resets the transformation to the identity matrix
        '''
        self.matrix = identity_matrix()



cdef class Rotate(Transform):
    '''Rotate the coordinate space by applying a rotation transformation
    on the modelview matrix. You can set the properties of the instructions
    afterwards with e.g. ::

        rot.angle = 90
        rot.axis = (0,0,1)
    '''
    cdef float _angle
    cdef tuple _axis

    def __init__(self, *args):
        Transform.__init__(self)
        if len(args) == 4:
            self.set(args[0], args[1], args[2], args[3])
        else:
            self.set(0, 0, 0, 1)

    def set(self, float angle, float ax, float ay, float az):
        self._angle = angle
        self._axis = (ax, ay, az)
        self.matrix = rotation_matrix(self._angle, self._axis)

    property angle:
        def __get__(self):
            return self._angle
        def __set__(self, a):
            self.set(a, *self._axis)

    property axis:
        def __get__(self):
            return self._axis
        def __set__(self, axis):
           self.set(self._angle, *axis)


cdef class Scale(Transform):
    '''Instruction to perform a uniform scale transformation
    '''
    cdef float s
    def __init__(self, *args):
        Transform.__init__(self)
        if len(args) == 1:
            self.s = args[0]
            self.matrix = scale_matrix(self.s)

    property scale:
        '''Sets the scale factor for the transformation
        '''
        def __get__(self):
            return self.s
        def __set__(self, s):
            self.s = s
            self.matrix = scale_matrix(s)


cdef class  Translate(Transform):
    '''Instruction to create a translation of the model view coordinate space
    '''
    cdef float _x, _y, _z
    def __init__(self, *args):
        Transform.__init__(self)
        if len(args) == 3:
            self.matrix = translation_matrix(args)

    def set_translate(self, x, y, z):
        self.matrix = translation_matrix([x,y,z])

    property x:
        '''Sets the translation on the x axis
        '''
        def __get__(self):
            return self._x
        def __set__(self, float x):
            self.set_translate(x, self._y, self._z)

    property y:
        '''Sets the translation on the y axis
        '''
        def __get__(self):
            return self._y
        def __set__(self, float y):
            self.set_translate(self._x, y, self._z)

    property z:
        '''Sets the translation on the z axis
        '''
        def __get__(self):
            return self._z
        def __set__(self, float z):
            self.set_translate(self._x, self._y, z)

    property xy:
        '''2 tuple with translation vector in 2D for x and y axis
        '''
        def __get__(self):
            return self._x, self._y
        def __set__(self, c):
            self.set_translate(c[0], c[1], self._z)

    property xyz:
        '''3 tuple translation vector in 3D in x, y, and z axis
        '''
        def __get__(self):
            return self._x, self._y, self._z
        def __set__(self, c):
            self.set_translate(c[0], c[1], c[2])







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
    #canvas, vbo and texture to use with this element
    cdef VBO        vbo
    cdef object     _texture

    #local vertex buffers and vbo index storage
    cdef int        v_count   #vertex count
    cdef Buffer     v_buffer  #local buffer of vertex data
    cdef vertex*    v_data

    #local buffer of vertex indices on vbp
    cdef Buffer     i_buffer
    cdef int*       i_data

    #indices to draw.  e.g. [1,2,3], will draw triangle:
    #  self.v_data[0], self.v_data[1], self.v_data[2]
    cdef int*       element_data
    cdef Buffer     element_buffer
    cdef int        num_elements
    cdef bytes      _source

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
    cdef float _points[6]
    cdef float _tex_coords[6]

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
    cdef float x, y      #position
    cdef float w, h      #size
    cdef int _user_texcoords
    cdef float _tex_coords[8]
    cdef int _is_init

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
    cdef float x, y
    cdef float w, h
    cdef float _border[4]
    cdef float _tex_coords[8]

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
    cdef float x,y,w,h
    cdef int segments
    cdef tuple _tex_coords

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



cdef class Path
cdef Path _active_path = None


cdef class Path(VertexDataInstruction):
    cdef float pen_x, pen_y
    cdef list points
    cdef Buffer point_buffer
    def __init__(self):
        VertexDataInstruction.__init__(self)
        self.point_buffer = Buffer(sizeof(vertex))
        self.points  = list()

    cdef int add_point(self, float x, float y):
        cdef int idx
        cdef vertex v = vertex2f(x,y)
        for p in self. points:
            if abs(p.x-x) < 0.001 and abs(p.y-y) < 0.001:
                Logger("PATH: ignoring point(x,y)...already in list")
                return 0

        self.point_buffer.add(&v, &idx, 1)
        self.points.append(Point(x,y))
        return idx

    cdef build_stroke(self):
        cdef vertex* p    #pointer into point buffer
        cdef vertex v[4]  #to hold the vertices for each quad were creating
        cdef int  idx[4]  #to hold the vbo indecies for every quad we add
        cdef int num_points, i #number of points in path, loop counter
        cdef float x0,x1, y0,y1, dx,dy, ns, sw
        cdef int  end_point_idx[2]  # to connect end points from previous segment

        sw = 3.0 #self.pen.stroke_width
        p = <vertex*>self.point_buffer.pointer()
        num_points = self.point_buffer.count()

        #generate a quad for every line
        self.v_buffer = Buffer(sizeof(vertex))
        self.i_buffer = Buffer(sizeof(GLint))
        self.element_buffer = Buffer(sizeof(int))
        for i in range(num_points-1):
            #normals for this line: (-dy,dx), (dy,-dx)
            x0 = p[i].x;  x1 = p[i+1].x; dx = (x1-x0);
            y0 = p[i].y;  y1 = p[i+1].y; dy = (y1-y0);

            #normalize normal vector and scale for stroke offset
            ns = sqrt( (dx*dx) + (dy*dy) )
            if ns == 0.0:
                Logger.trace('GPath: skipping line, the two points are 0 '
                             'unit apart.')
                continue

            dx = sw/2.0 * dx/ns
            dy = sw/2.0 * dy/ns

            #create quad, with cornerss pull off the line by the normal
            v[0] = vertex8f(x0, y0, 0,0, -dy, dx, -1.0,-1.0);
            v[1] = vertex8f(x0, y0, 0,0,  dy,-dx,  1.0, 1.0);
            v[2] = vertex8f(x1, y1, 0,0,  dy,-dx,  1.0, 1.0);
            v[3] = vertex8f(x1, y1, 0,0, -dy, dx, -1.0,-1.0);

            #add vertices to vertex buffer, get vbo indices
            self.v_buffer.add(v, idx, 4)
            self.i_buffer.add(idx, NULL, 4)
            self.v_count = self.v_count + 4

            #and extend eleemnt buffer with indices to include this quad in draw
            #print "segment:", idx[0], idx[1], idx[2],  ":",  idx[2], idx[3], idx[0]
            self.element_buffer.add(&idx[0], NULL, 3)
            self.element_buffer.add(&idx[2], NULL, 2)
            self.element_buffer.add(&idx[0], NULL, 1)

            #also connect to the previous line segment with nice joint
            if i > 0: #not the first time...nothing to connect to
                #print "connection:", end_point_idx[0], end_point_idx[1], idx[0],  ":",  idx[0], idx[3], end_point_idx[0]
                self.element_buffer.add(end_point_idx, NULL, 2)
                self.element_buffer.add(&idx[0], NULL, 1)
                self.element_buffer.add(&idx[1], NULL, 1)
                self.element_buffer.add(&idx[1], NULL, 1)
                self.element_buffer.add(end_point_idx, NULL, 1)

            end_point_idx[0] = idx[3]
            end_point_idx[1] = idx[2]

        #update vertex and vbo index pointers
        self.v_data = <vertex*>  self.v_buffer.pointer()
        self.i_data = <int*>     self.i_buffer.pointer()
        self.element_data = <int*> self.element_buffer.pointer()
        self.num_elements = self.element_buffer.count()

        #actually add vertices to VBO
        self.vbo.add_vertices(self.v_data, self.i_data, self.v_count)
        self.canvas.add(self)
        self.canvas.update(self)


    cdef build_fill(self):

        cdef vertex v[4]  #to hold the vertices for each quad were creating
        cdef int  idx[4]  #to hold the vbo indecies for every quad we add
        cdef list triangles
        cdef list indices = []
        Logger.trace('GPath: build fill %s' % str(self.points))
        poly = CDT(self.points)
        triangles = poly.triangulate()


        cdef int i = 0
        self.v_buffer = Buffer(sizeof(vertex))
        self.i_buffer = Buffer(sizeof(GLint))
        for t in triangles:

            v[0] = vertex2f(t.a.x, t.a.y)
            v[1] = vertex2f(t.b.x, t.b.y)
            v[2] = vertex2f(t.c.x, t.c.y)
            self.v_count += 3

            self.v_buffer.add(v, idx, 3)
            self.i_buffer.add(idx, NULL, 3)
            indices.extend([i, i+1, i+2])
            i +=3


        #update vertex and vbo index pointers
        self.v_data = <vertex*>  self.v_buffer.pointer()
        self.i_data = <int*>     self.i_buffer.pointer()
        self.indices = indices

        #actually add vertices to VBO
        self.vbo.add_vertices(self.v_data, self.i_data, self.v_count)
        self.canvas.add(self)
        self.canvas.update(self)

cdef class PathInstruction(GraphicInstruction):
    cdef Path path
    def __init__(self):
        global _active_path
        GraphicInstruction.__init__(self, GI_IGNORE)
        self.path = _active_path



cdef class PathStart(PathInstruction):
    '''Starts a new path at position x,y.  Will raise an Excpetion, if called
    while another path is already started.

    :Parameters:
        `x`: float
            x position
        `y`: float
            y position
    '''
    cdef int index
    def __init__(self):
        global _active_path
        PathInstruction.__init__(self)
        if _active_path != None:
            raise Exception("Can't start a new path while another one is being constructed")
        _active_path = self.path = Path()
        #self.index = self.path.add_point(x, y)


cdef class PathLineTo(PathInstruction):
    '''Adds a line from the current location to the x, y coordinates passed as
    parameters.
    '''
    cdef int index
    def __init__(self, x, y):
        PathInstruction.__init__(self)
        self.index = self.path.add_point(x, y)


cdef class PathClose(PathInstruction):
    '''Closes the path, by adding a line from the current location to the first
    vertex taht started the path.
    '''
    def __init__(self):
        PathInstruction.__init__(self)
        cdef vertex* v = <vertex*> self.path.point_buffer.pointer()
        self.path.add_point(v[0].x, v[0].y)

cdef class PathFill(PathInstruction):
    '''Ends path construction on the current path, the path will be build
    and added to the canvas
    '''
    def __init__(self):
        global _active_path
        PathInstruction.__init__(self)
        self.path.build_fill()
        _active_path = None


cdef class PathStroke(PathInstruction):
    '''Ends path construction on the current path, the path will be build
    and added to the canvas
    '''
    def __init__(self):
        global _active_path
        PathInstruction.__init__(self)
        self.path.build_stroke()
        _active_path = None


cdef class PathEnd(PathStroke):
    pass

