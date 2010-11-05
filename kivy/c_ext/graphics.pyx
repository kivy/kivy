import os
from kivy import kivy_shader_dir
from kivy.logger import Logger
from kivy.resources import resource_find

from buffer cimport Buffer
from c_opengl cimport *

#TODO, see which ones we have to write in cython directlym e.g. transformations, texture etc.
from kivy.core.image import Image
from kivy.texture import Texture

import numpy
from kivy.lib.transformations import matrix_multiply, identity_matrix, \
             rotation_matrix, translation_matrix, scale_matrix


'''
standard math definitions
'''
cdef double pi = 3.1415926535897931
cdef extern from "math.h":
    double cos(double)
    double sin(double)
    double sqrt(double)


cdef struct vertex:
    GLfloat x, y
    GLfloat s0, t0 
    GLfloat s1, t1
    GLfloat s2, t2

cdef vertex vertex8f(GLfloat x, GLfloat y, GLfloat s0, GLfloat t0, GLfloat s1, GLfloat t1, GLfloat s2, GLfloat t2):
    cdef vertex v
    v.x  = x;   v.y  = y
    v.s0 = s0;  v.t0 = t0
    v.s1 = s1;  v.t1 = t1
    v.s2 = s2;  v.t2 = t2
    return v

cdef vertex vertex6f(GLfloat x, GLfloat y, GLfloat s0, GLfloat t0, GLfloat s1, GLfloat t1):
    return vertex8f(x,y,s0,t0,s1,t1,0.0,0.0)

cdef vertex vertex4f(GLfloat x, GLfloat y, GLfloat s0, GLfloat t0):
    return vertex8f(x,y,s0,t0,0.0,0.0,0.0,0.0)
    
cdef vertex vertex2f(GLfloat x, GLfloat y):
    return vertex8f(x,y,0.0,0.0,0.0,0.0,0.0,0.0)

'''
Description of vertex attributes, standard format for shaders and vbo
'''
cdef list VERTEX_ATTRIBUTES = [ 
    {'name': 'vPosition',  'index':0, 'size': 2, 'type': GL_FLOAT, 'bytesize': sizeof(GLfloat)*2, 'per_vertex': True},
    {'name': 'vTexCoord0', 'index':1, 'size': 2, 'type': GL_FLOAT, 'bytesize': sizeof(GLfloat)*2, 'per_vertex': True},
    {'name': 'vTexCoord1', 'index':2, 'size': 2, 'type': GL_FLOAT, 'bytesize': sizeof(GLfloat)*2, 'per_vertex': True}, 
    {'name': 'vOffset',    'index':3, 'size': 2, 'type': GL_FLOAT, 'bytesize': sizeof(GLfloat)*2, 'per_vertex': True}, 
    {'name': 'vColor',     'index':4, 'size': 4, 'type': GL_FLOAT, 'bytesize': sizeof(GLfloat)*4, 'per_vertex': False} 
] 




cdef class GraphicContext
cdef GraphicContext _default_context = None

cdef int ACTIVE_SHADER = 0



cdef class Shader:
    '''Create a vertex or fragment shader

    :Parameters:
        `vert_src` : string 
            source code for vertex shader
        `frag_src` : string
            source code for fragment shader
    '''
    cdef int program
    cdef int vertex_shader
    cdef int fragment_shader
    cdef object vert_src
    cdef object frag_src 
    cdef dict uniform_locations 
    cdef dict uniform_values

    def __cinit__(self):
        self.uniform_locations = dict()
        self.uniform_values = dict()

    def __init__(self, str vert_src, str frag_src):
        self.frag_src = frag_src
        self.vert_src = vert_src
        self.program = glCreateProgram()
        self.bind_attrib_locations()
        self.build()
        
    cdef int get_uniform_loc(self, str name):
        name_byte_str = name
        cdef char* c_name = name_byte_str
        cdef int loc = glGetUniformLocation(self.program, c_name)
        self.uniform_locations[name] = loc
        return loc

    #def __setitem__(self, str name, value):
    cpdef set_uniform(self, str name, value):
        self.uniform_values[name] = value

    cpdef upload_uniform(self, str name, value):
        """pass a uniform variable to the shader"""
        cdef int vec_size, loc
        val_type = type(value)        
        loc = self.uniform_locations.get(name, self.get_uniform_loc(name))
    

        #TODO: use cython matrix transforms
        if val_type == numpy.ndarray:
            self.set_uniform_matrix(name, value)
        elif val_type == int:
            glUniform1i(loc, value)
        elif val_type == float:
            glUniform1f(loc, value)
        else:  
            #must have been a list, tuple, or other sequnce ot be a vector uniform
            val_type = type(value[0])
            vec_size = len(value)
            if val_type == float:
                if vec_size == 2:
                    glUniform2f(loc, value[0], value[1])
                elif vec_size == 3:
                    glUniform3f(loc, value[0], value[1], value[2])
                elif vec_size == 4:
                    glUniform4f(loc, value[0], value[1], value[2], value[3])
            elif val_type == int:
                if vec_size == 2:
                    glUniform2i(loc, value[0], value[1])
                elif vec_size == 3:
                    glUniform3i(loc, value[0], value[1], value[2])
                elif vec_size == 4:
                    glUniform4i(loc, value[0], value[1], value[2], value[3])       


    cdef set_uniform_matrix(self, str name, value):
        #TODO: use cython matrix transforms
        cdef int loc = self.uniform_locations.get(name, self.get_uniform_loc(name))
        cdef GLfloat mat[16] 
        np_flat = numpy.ascontiguousarray(value.T, dtype='float32').flatten()
        for i in range(16):
            mat[i] = <GLfloat>np_flat[i]
        glUniformMatrix4fv(loc, 1, False, mat) 

    cpdef use(self):
        '''Use the shader'''
        if ACTIVE_SHADER == self.program:
            return
        glUseProgram(self.program)
        for k,v in self.uniform_values.iteritems():
            self.upload_uniform(k, v)
        
    cpdef stop(self):
        '''Stop using the shader'''
        glUseProgram(0)

    cdef bind_attrib_locations(self):
        cdef char* c_name
        for attr in VERTEX_ATTRIBUTES:
            c_name = attr['name']
            glBindAttribLocation(self.program, attr['index'], c_name)
            if attr['per_vertex']:
                glEnableVertexAttribArray(attr['index'])

    cdef build(self):
        self.vertex_shader = self.compile_shader(self.vert_src, GL_VERTEX_SHADER)
        self.fragment_shader = self.compile_shader(self.frag_src, GL_FRAGMENT_SHADER)
        glAttachShader(self.program, self.vertex_shader)
        glAttachShader(self.program, self.fragment_shader)
        glLinkProgram(self.program)
        self.uniform_locations = dict()
        self.process_build_log()

    cdef compile_shader(self, char* source, shadertype):
        shader = glCreateShader(shadertype)
        glShaderSource(shader, 1, <GLchar**> &source, NULL)
        glCompileShader(shader)
        return shader

    cdef get_shader_log(self, shader):
        '''Return the shader log'''
        cdef int msg_len
        cdef char msg[2048]
        glGetShaderInfoLog(shader, 2048, &msg_len, msg)
        return msg

    cdef get_program_log(self, shader):
        '''Return the program log'''
        cdef int msg_len
        cdef char msg[2048]
        glGetProgramInfoLog(shader, 2048, &msg_len, msg)
        return msg

    cdef process_build_log(self):
        message = self.get_program_log(self.program)
        if message:
            Logger.error('Shader: shader program message: %s' % message)
            raise Exception(message)
        else:
            Logger.debug('Shader compiled sucessfully')
   

 
def Context_instance():
    global _default_context
    if _default_context == None:
        _default_context = GraphicContext()
    return _default_context



cdef class MatrixStack:
    cdef list stack
    cdef GraphicContext context

    def __init__(self, context):
        self.context = context
        self.stack = [identity_matrix()]

    def pop(self):
        self.stack.pop()
        self.context.set('modelview_mat', self.stack[-1])

    def push(self):
        mat = matrix_multiply(identity_matrix(), self.stack[-1])
        self.stack.append(mat)

    def apply(self, mat):
        self.stack[-1] = matrix_multiply(mat, self.stack[-1])
        self.context.set('modelview_mat', self.stack[-1])

    def transform(self):
        return self.stack[-1]


cdef class GraphicContext:
    '''Handle the saving/restore of the context

    TODO: explain more how it works
    '''
    cdef dict state
    cdef list stack
    cdef set journal
    cdef readonly int need_flush
    cdef Shader  _default_shader
    cdef object _default_texture
    cdef int need_redraw

    instance = staticmethod(Context_instance)

    property default_shader:
        def __get__(self):
            if not self._default_shader:
                _default_vertex_shader   = open(os.path.join(kivy_shader_dir, 'default.vs')).read()
                _default_fragment_shader = open(os.path.join(kivy_shader_dir, 'default.fs')).read()
                self._default_shader = Shader(_default_vertex_shader, _default_fragment_shader)
            return self._default_shader

    property default_texture:
        def __get__(self):
            if not self._default_texture:
                img = Image(os.path.join(kivy_shader_dir, 'default.png'))
                self._default_texture = img.texture
            return self._default_texture

    def __cinit__(self):
        self.state = {}
        self.stack = []
        self.journal = set()
        self.need_flush = 0
        self._default_shader = None

    def __init__(self):
        # create initial state
        self.reset()
        self.save()
        self.need_redraw = 1

    cpdef post_update(self):
        self.need_redraw = 1

    cpdef finish_frame(self):
        self.need_redraw = 0
        err = glGetError()
        if err:
            print "GL Error while drawing frame:", err

    cpdef set(self, str key, value):
        self.state[key] = value
        self.journal.add(key)
        self.need_flush = 1

    cpdef get(self, str key):
        return self.state[key]

    cpdef reset(self):
        self.set('shader', self.default_shader)
        self.set('projection_mat', identity_matrix())
        self.set('modelview_mat', identity_matrix())
        self.set('color', (1.0, 1.0, 1.0, 1.0) )
        self.set('blend', 0)
        self.set('blend_sfactor', GL_SRC_ALPHA)
        self.set('blend_dfactor', GL_ONE_MINUS_SRC_ALPHA)
        #self.set('linewidth', 1)
        self.set('texture0', self.default_texture)
        self.set('mvm', MatrixStack(self))

    cpdef save(self):
        self.stack.append(self.state.copy())

    cpdef restore(self):
        newstate = self.stack.pop()
        state = self.state
        for k, v in newstate.iteritems():
            if not state[k] is v:
                self.set(k, v)
    
    cpdef flush(self):
        # activate all the last changes done on context
        # apply all the actions in the journal !
        cdef dict state
        cdef set journal
        cdef str x

        self.state['shader'].use()
        
        if not self.journal:
            return

        state = self.state
        journal = self.journal
        for x in journal:
            value = state[x]
            if x in ('mvm',):
                continue
            if x == 'color':
                glVertexAttrib4f(4, value[0], value[1], value[2], value[3]) #vColor

            elif x == 'texture0':
                if not value:
                    value = self._default_texture
                glActiveTexture(GL_TEXTURE0)
                glBindTexture(value.target, value.id)
            
            elif x == 'blend':
                if value:   glEnable(GL_BLEND)
                else:       glDisable(GL_BLEND)
            
            elif x in ('blend_sfactor', 'blend_dfactor'):
                glBlendFunc(state['blend_sfactor'], state['blend_dfactor'])
         
            elif x != 'shader': #set uniform variable
                #print "setting uniform", x, value
                self.state['shader'].set_uniform(x, value)

        journal.clear()
        self.need_flush = 0





cdef class VBO:
    cdef GLuint id
    cdef int usage
    cdef int target
    cdef list format
    cdef Buffer data
    cdef int need_upload
    cdef int vbo_size
    
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
        self.update_buffer()
        glBindBuffer(GL_ARRAY_BUFFER, self.id)
        cdef int offset = 0
        for attr in self.format:
            if not attr['per_vertex']:
                continue
            glVertexAttribPointer(attr['index'], attr['size'], attr['type'], GL_FALSE, sizeof(vertex), <GLvoid*>offset)
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






'''
Insruction type bitmask. Graphic Instruction Codes
bitmask to hold various graphic intrcution codes so its 
possible to set teh code on any GraphicInstruction
in order to let the compiler know how to handle it best
'''
cdef int GI_NOOP         = 0x0000000
cdef int GI_IGNORE       = 0x0000001
cdef int GI_VERTEX_DATA  = 0x0000002
cdef int GI_CONTEXT_MOD  = 0x0000004




cdef class GraphicInstruction
cdef class VertexDataInstruction
cdef class Canvas
cdef Canvas ACTIVE_CANVAS = None

cdef class Canvas:
    cdef GraphicContext _context
    cdef VBO vertex_buffer
    cdef list texture_map
    cdef list batch

    #move to graphics compiler?:
    cdef int _need_compile
    cdef int num_slices
    cdef list batch_slices

    def __cinit__(self):
        global _default_context
        if _default_context == None:
            _default_context = GraphicContext()
        self._context = _default_context
        self.vertex_buffer = VBO()
        self.texture_map = []
        self.batch = []
        
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

    cpdef __enter__(self):
        global ACTIVE_CANVAS
        ACTIVE_CANVAS = self

    cpdef __exit__(self, extype, value, traceback):
        global ACTIVE_CANVAS 
        ACTIVE_CANVAS = None

    cdef add(self, GraphicInstruction instruction):
        self.need_compile = 1
        self.batch.append(instruction)

    cdef update(self, instruction):
        ''' called by graphic instructions taht are part of teh canvas,
            when they have been changed in some way ''' 
        self.need_compile = 1

    cdef remove(self, element):
        self.need_compile = 1
        pass

    cdef compile(self):
        with self:
            self.compile_run()

    cdef compile_init(self):
        self.texture_map = []
        self.batch_slices = []

    cdef compile_run(self):
        cdef GraphicInstruction item
        cdef int slice_start = -1
        cdef int slice_stop  = -1
        cdef int i, code

        self.compile_init()

        print "starting compile"

        for i in xrange(len(self.batch)):
            item = self.batch[i]
            code = item.CODE

            print "batch element CODE:", code

            #the instruction modifies teh context, so we cant combine the drawing
            #calls before and after it
            if code & GI_CONTEXT_MOD:
                print "context mod"
                #first compile the slices we been loopiing over which we can combine
                #from slice_start to slice_stop. (using compile_slice() )
                #add the context modifying instruction to batch_slices
                #reset slice start/stop index
                self.compile_slice('draw', slice_start, slice_stop)
                self.batch_slices.append(('instruction', item)) 
                slice_start = slice_stop = -1
            
            #the instruction pushes vertices to the pipeline and doesnt modify
            #teh context, so we can happily combine it with any prior or follwing
            #instructions that do teh same, just keep incrementing slice stop index
            #until we cant combine any more, then well call compile_slice()
            elif code & GI_VERTEX_DATA:
                print "Vertex data"
                slice_stop = i
                if slice_start == -1:
                    slice_start = i

        #maybe we ended on an slice of vartex data, whcih we didnt push yet
        self.compile_slice('draw', slice_start, slice_stop)



    cdef compile_slice(self, str command, slice_start, slice_end):
        print "compiling slice:", slice_start, slice_end, command
        cdef VertexDataInstruction item
        cdef Buffer b = Buffer(sizeof(GLint))
        cdef int tex_target = -1
        cdef int tex_id = -1
        cdef int v, i

        #check if we have a valid slice
        if slice_start == -1:
            print "nothign to compile..empty slice"
            return


        #loop pver all teh whole slice, and combine all instructions
        for item in self.batch[slice_start:slice_end+1]:  
            print "adding", item, "to batch_slice"
            # add the vertex indices to be drawn from this item
            for i in range(item.num_elements): 
                v = item.element_data[i]
                b.add(&v, NULL, 1)

            #handle textures (should go somewhere else?, maybe set GI_CONTEXT_MOD FLAG ALSO?)
            if item.texture:
                print "texture attached, must split batch_slice"
                if item.texture.id == tex_id: #the same, sweet, keep going
                    print "texture already bound on context...no split after all"
                    continue
                elif item.texture.id != tex_id:  #nope..muts bind the new texture
                    print "bindign new texture", item.texture 
                    target = item.texture.target
                    tex_id = item.texture.id
                    self.batch_slices.append(('instruction', BindTexture(item.texture)))
                    self.batch_slices.append((command, b))
                    b = Buffer(sizeof(GLint))
            elif tex_id != -1: #no item.texture..must unbind bound_texture and start new slice
                print "unbinding previous bound tetxure"
                self.batch_slices.append(('instruction', BindTexture(None)))
                
                #self.batch_slices.append(('instruction', UnbindTexture(0, tex_target)))
                self.batch_slices.append((command, b))
                b = Buffer(sizeof(GLint))


        print "done compiling slice"
        if b.count() > 0:  # last slice, all done, only have to add if there is actually somethign in it
            print "adding last slice"
            self.batch_slices.append((command, b))


    cpdef draw(self): 
        cdef int i
        cdef Buffer b

        if self.need_compile:
            self.compile()
            print "Done Compiling", self.batch_slices
            self.need_compile = 0

        self.vertex_buffer.bind() 
        attr = VERTEX_ATTRIBUTES[0]
        glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer.id)

        for command, item in self.batch_slices:
            #print command, item
            if command == 'draw':
                self.context.flush()
                b = item
                #print "drawing elements:", b.count()
                glDrawElements(GL_TRIANGLES, b.count(), GL_UNSIGNED_INT, b.pointer())
            elif command == 'instruction':
                item.apply()

        self.context.finish_frame()
                





cdef class GraphicInstruction:
    cdef int CODE     #Graphic instruction op code
    cdef Canvas canvas  #canvas on which to operate


    def __init__(self, int code):
        '''
            Base class for all Graphi Instructions
            :Parameters:
            `code`, constant: instruction code for hinting teh compiler
                currently a combination of:
                    GI_NOOP
                    GI_IGNORE
                    GI_CONTEXT_MOD
                    GI_VERTEX_DATA
                    
        '''
        global ACTIVE_CANVAS
        self.CODE = code
        self.canvas = ACTIVE_CANVAS


cdef class ContextInstruction(GraphicInstruction):
    cdef GraphicContext context
    def __init__(self, *args, **kwargs):  
        '''
           Abstract Base class for GraphicInstructions that modidifies the
           context.  (so that canvas/compiler can know about how to optimize)
        '''
        GraphicInstruction.__init__(self, GI_CONTEXT_MOD)
        self.context = self.canvas.context
        self.canvas.add(self)
        
    cpdef apply(self):
        pass




cdef class PushMatrix(ContextInstruction):
    '''
    PushMatrix on context's matrix stack
    '''
    def apply(self):
        self.context.get('mvm').push()
     
cdef class PopMatrix(ContextInstruction):
    '''
    Pop Matrix from context's matrix stack onto model view
    '''
    def apply(self):
        self.context.get('mvm').push()


cdef class MatrixInstruction(ContextInstruction):
    '''
    Base class for Matrix Instruction on canvas
    '''

    cdef object mat 

    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self)

    cpdef apply(self):
        '''
        apply matrix to the matix of this instance to the 
        context model view matrix
        '''
        self.context.get('mvm').apply(self.mat)

    property matrix:
        '''
        matrix property.  numpy matrix from trasformation module
        setting the matrix using this porperty when a change is made 
        is important, becasue it will notify teh context about 
        teh update
        '''
        def __get__(self):
            return self.mat
        def __set__(self, mat):
            self.mat = mat
            self.context.post_update()


cdef class Transform(MatrixInstruction):
    '''
    Transform class.  A matrix instruction class which 
    has function to modify the transformation matrix
    
    '''
    cpdef transform(self, object trans): 
        '''
        multiply the instructions matrix by trans
        '''
        self.mat = matrix_multiply(self.mat, trans)

    cpdef translate(self, float tx, float ty, float tz):
        '''
        translate the instrcutions transformation by tx, ty, tz
        '''
        self.transform( translation_matrix(tx, ty, tz) )

    cpdef rotate(self, float angle, float ax, float ay, float az):
        '''
        rotate the transformation by matrix by angle degress around the 
        axis defined by the vector ax, ay, az
        '''
        self.transform( rotation_matrix(angle, [ax, ay, az]) )

    cpdef scale(self, float s):
        '''
        Applies a uniform scaling of s to teh matrix transformation
        '''
        self.transform( scale_matrix(s, s, s) )

    cpdef identity(self):
        '''
        resets teh transformation to teh identity matrix 
        '''
        self.matrix = identity_matrix()


       
cdef class Rotate(Transform):
    '''
    Rotate the coordinate space by applying a rotation trnasformation
    on teh modelview matrix.  you can set the properties of teh 
    instructions afterwards with e.g.: 
    rot.angle = 90
    rot.axis = (0,0,1)  
    '''
    cdef float _angle
    cdef tuple _axis

    def __init__(self, *args):
        Transform.__init__(self)
        if len(args) == 4:
            self.set(args[0], args[1], args[2], args[3])

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


cdef class  Scale(Transform):
    '''
    Instruction to perform a uniform scale transformation
    '''
    cdef float s
    def __init__(self, *args):
        Transform.__init__(self)
        if len(args) == 1:
            self.s = args[0]
            self.matrix = scale_matrix(self.s)
 
    property scale:  
        ''' 
        sets the scale factor for the transformation
        '''
        def __get__(self):
            return self.s
        def __set__(self, s): 
            self.s = s
            self.matrix = scale_matrix(s)


cdef class  Translate(Transform):
    '''
    Instruction to create a translation of teh model view coordinate space
    '''
    cdef float _x, _y, _z
    def __init__(self, *args):
        Transform.__init__(self)
        if len(args) == 3:
            self.matrix = translation_matrix(args)

    def set_translate(self, x, y, z): 
        self.matrix = translation_matrix([x,y,z]) 

    property x:
        ''' sets teh translation on the x axis'''
        def __get__(self):
            return self._x
        def __set__(self, float x):
            self.set_translate(x, self._y, self._z)
    
    property y:
        ''' sets the translation on teh y axis '''
        def __get__(self):
            return self._y
        def __set__(self, float y):
            self.set_translate(self._x, y, self._z)
 
    property z:
        ''' sets teh translation on teh z axis ''' 
        def __get__(self):
            return self._z
        def __set__(self, float z):
            self.set_translate(self._x, self._y, z)

    property xy:
        ''' 2 tuple with translation vector in 2D for x and y axis '''
        def __get__(self):
            return self._x, self._y
        def __set__(self, c):
            self.set_translate(c[0], c[1], self._z)
 
    property xyz:  
        ''' 3 tuple translation vector in 3D in x, y, and z axis'''
        def __get__(self):
            return self._x, self._y, self._z
        def __set__(self, c): 
            self.set_translate(c[0], c[1], c[2])





cdef class LineWidth(ContextInstruction):
    '''
    Instruction to set the line width of teh drawing context
    '''
    cdef float lw
    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self, **kwargs)
        if len(args) == 1:
            self.lw = args[0]

    def set(self, float lw):
        self.lw = lw

    cpdef apply(self):
        self.canvas.context.set('linewidth', self.lw)


cdef class Color(ContextInstruction):
    #TODO:
    '''
     add blending "mode", so user can pass str or enum
     e.g.: 'normal', 'subtract', 'multiply', 'burn', 'dodge', etc
    '''    
    cdef list color    
 
    def __init__(self, *args, **kwargs):
        '''
        SetColor will change the color being used to draw in the context
        :Parameters:
        
        '''
        ContextInstruction.__init__(self)
        self.rgba = args
        self.canvas.add(self)
        
    cpdef apply(self):
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
            self.rbga = rgba

    property r:
        def __get__(self):
            return self.color[0]
        def __set__(self, r):
            self.rbga = [r, self.g, self.b, self.a]
    property g:
        def __get__(self):
            return self.color[1]
        def __set__(self, g):
            self.rbga = [self.r, g, self.b, self.a]
    property b:
        def __get__(self):
            return self.color[2]
        def __set__(self, b):
            self.rbga = [self.r, self.g, b, self.a]
    property a:
        def __get__(self):
            return self.color[3]
        def __set__(self, a):
            self.rbga = [self.r, self.g, self.b, a]



cdef class BindTexture(ContextInstruction):
    cdef object texture
    """
    def __init__(self, *args, **kwargs):
        '''
        BindTexture Graphic instruction:
            The BindTexture Instruction will bind a texture and enable
            GL_TEXTURE_2D for subsequent drawing.

        :Parameters:
            `texture`, Texture:  specifies teh texture to bind to teh given index 
        '''
        ContextInstruction.__init__(self)
        self.texture = tex
    """
    cpdef apply(self): 
        self.canvas.context.set('texture0', self.texture)

    def set(self, object texture):
        self.texture = texture



cdef class VertexDataInstruction(GraphicInstruction): 
    #canvas, vbo and texture to use with this element
    cdef VBO vbo           
    cdef object _texture    
   
    #local vertex buffers and vbo index storage 
    cdef int     v_count   #vertex count
    cdef Buffer  v_buffer  #local buffer of vertex data
    cdef vertex* v_data  

    #local buffer of vertex indices on vbp
    cdef Buffer  i_buffer 
    cdef int*    i_data

    #indices to draw.  e.g. [1,2,3], will draw triangle:
    #  self.v_data[0], self.v_data[1], self.v_data[2]
    cdef int*    element_data
    cdef Buffer  element_buffer
    cdef int     num_elements  


    def __init__(self, **kwargs):
        '''
        VertexDataInstruction
        A VertexDataInstruction pushes vertices into teh graphics pipeline
        this class manages a vbo, allocating a set of vertices on teh vbo
        and can update the vbo data, when local changes have been made

        :Parameters:
            `texture`: The tetxure to be bound while drawing teh vertices

        '''
        GraphicInstruction.__init__(self, GI_VERTEX_DATA)
        self.vbo     = self.canvas.vertex_buffer
        self.v_count = 0 #no vertices to draw until initialized
        self._texture = kwargs.get('texture', None)

        print "VERTEX INIT", 

    cdef allocate_vertex_buffers(self, int num_verts):
        ''' For allocating and initializing vertes data buffers
            of this GraphicElement both locally and on VBO

            Allocates local vertex and index buffers to be able to 
            hold num_verts vertices.  adds teh vertices to the vbo
            associated with the elements canvas and sets vbo indices
            in i_data.  

            After calling the follwoing buffers will have enough room
            for num_verts: 

            self.vbo:  num_verts are added to teh canvas' VBO

            self.v_data : `vertex*`, vertex array with enough room for num_verts.
                           pointing to start of v_buffer, so you can set data
                           using indexing.  liek:  self.v_data[i] = <vertex> v

            self.i_data : 'int*', int array of size num_verts.  has vbo index of
                          vertex in v_data.  so self.i_data[i] is vbo index of 
                          self.v_buffer[i]  
        '''

        print "allocating vertex data:", num_verts
        #create vertex and index buffers
        self.v_buffer = Buffer(sizeof(vertex))
        self.i_buffer = Buffer(sizeof(GLint))

        #allocate enough room for vertex and index data
        self.v_count = num_verts
        self.v_buffer.grow(num_verts)
        self.i_buffer.grow(num_verts)

        #set data pointers to be able to index vertices and indices
        self.v_data = <vertex*>  self.v_buffer.pointer()
        self.i_data = <int*> self.i_buffer.pointer()

        #allocte on vbo and update indices with 
        self.vbo.add_vertices(self.v_data, self.i_data, self.v_count)
        print "done allocating"


    property indices:
        '''
        `indecies` : this property is write only.  it determines, which of teh vertices 
                     from this object will be drawn by teh canvas.  if e.g. teh object 
                     has 4 vertices.  tehn setting vdi.indices = (0,1,2 2,4,0), will
                     draw two triangles corrosponding to the vertices stored in v_data
                     this function automatically converts teh indices from local to vbo indices 
        '''
        def __set__(self, object batch): #list or tuple..iterable?
            #create element buffer for list of vbo indices to be drawn
            self.element_buffer = Buffer(sizeof(int))
            cdef int i, e
            print "setting indices!!"
            for i in xrange(len(batch)):
                e = batch[i]
                self.element_buffer.add(&self.i_data[e], NULL, 1)
            self.element_data = <int*> self.element_buffer.pointer()
            self.num_elements = self.element_buffer.count()
            #since we changed the list of vertices to draw, canvas must recompile 
            self.canvas.update(self)


    cdef update_vbo_data(self):
        '''
            updates teh vertex data stored on vbo to be same as local 
            needs to be called if you change v_data inside this element
        '''
        cdef vertex* vtx = self.v_data
        cdef int* idx    = self.i_data
        cdef int i
        print "updating vbo data:"
        for i in range(self.v_count): 
            #print idx[i], vtx[i].x, vtx[i].y, vtx[i].s0, vtx[i].t0
            self.vbo.update_vertices(idx[i], &vtx[i], 1)     

    property texture:
        ''' set/get the texture to be bound while the vertices are being drawn'''
        def __get__(self):
            return self._texture
        def __set__(self, tex):
            self._texture = tex

 

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
    cdef float _tex_coords[8] 

    def __init__(self, **kwargs):       
        VertexDataInstruction.__init__(self, **kwargs)
        self.allocate_vertex_buffers(4)

        #get keyword args for configuring rectangle
        self.x, self.y  = kwargs.get('pos',  (0,0))
        self.w, self.h  = kwargs.get('size', (100,100))
        cdef tuple t_coords =  (0.0,0.0, 1.0,0.0, 1.0,1.0, 0.0,1.0)
        if self.texture:
            t_coords = self.texture.tex_coords
        self.tex_coords  = kwargs.get('tex_coords', t_coords)
        
        #tell VBO which triangles to draw using our vertices 
        self.indices = (0,1,2, 2,3,0) 
        self.canvas.add(self)

    cdef build(self):
        cdef float* tc = self._tex_coords
        cdef float x,y,w,h
        x = self.x; y=self.y; w = self.w; h = self.h
        self.v_data[0] = vertex4f(x,    y, tc[0], tc[1])
        self.v_data[1] = vertex4f(x+w,  y, tc[2], tc[3])
        self.v_data[2] = vertex4f(x+w, y+h, tc[4], tc[5])
        self.v_data[3] = vertex4f(x,   y+h, tc[6], tc[7])
        self.update_vbo_data()

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
            cdef int i
            print "setting textire coordinates:", coords
            for i in range(8):
                self._tex_coords[i] = coords[i]
            self.build()



cdef class BorderRectangle(VertexDataInstruction):
    cdef float x, y
    cdef float w, h
    cdef float _border[4]
    cdef float _tex_coords[8]

    def __init__(self, **kwargs):       
        #we have 16 vertices in BorderRectangle
        
        VertexDataInstruction.__init__(self, **kwargs)
        self.allocate_vertex_buffers(16)


        #get keyword args for configuring rectangle
        cdef tuple s = kwargs.get('size', (100, 100))
        cdef tuple p = kwargs.get('pos', (0,0))
        cdef tuple bv = kwargs.get('border', (5,5,5,5))
        cdef float* b = self._border
        b[0] = bv[0];  b[1]=bv[1];  b[2]=bv[2];  b[3]=bv[3];
        self.x = p[0]; self.y = p[1]
        self.w = s[0]; self.h = s[1]
       
        self.build()      


        #tell VBO which triangles to draw using our vertices 
        #two triangles per quad       
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
             0,  1, 12,    12, 11,  0,  #bottom left 
             1,  2, 13,    13, 12,  1,  #bottom middle 
             2,  3,  4,     4, 13,  2,  #bottom right 
            13,  4,  5,     5, 14, 13,   #center right 
            14,  5,  6,     6,  7, 14,   #top right 
            15, 14,  7,     7,  8, 15,   #top middle 
            10, 15,  8,     8,  9, 10,   #top left 
            11, 12, 15,    15, 10, 11,   #center left 
            12, 13, 14,    14, 15, 12)   #center middel 
        self.canvas.add(self)

    cdef build(self):
        if not self.texture:
            print "need texture for BorderImage"
            return

        #pos and size of border rectangle
        cdef float x,y,w,h
        x=self.x;  y=self.y; w=self.w;  h=self.h
        
        #width and heigth of texture in pixels, and tex coord space 
        cdef float tw, th, tcw, tch
        cdef float* tc = self._tex_coords
        tsize  = self.texture.size
        tw  = tsize[0]
        th  = tsize[1]
        tcw = tc[2] - tc[0]  #right - left
        tch = tc[7] - tc[1]  #top - bottom
        
        #calculate border offset in texture coord space 
        # border width(px)/texture width(px) *  tcoord width
        cdef float *b = self._border
        cdef float tb[4] #border offset in texture coordinate space
        tb[0] = b[0] / th*tch  
        tb[1] = b[1] / tw*tcw 
        tb[2] = b[2] / th*tch
        tb[3] = b[3] / tw*tcw

        #print "x,y,w,h:", x, y, w, h
        #print "texture|coord size:", tw, th, tcw, tch
        #print "border:", b[0], b[1], b[2], b[3]
        #print "texture border:", tb[0], tb[1], tb[2], tb[3]
       
         #horizontal and vertical sections
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

        #set the vertex data
        cdef vertex* v = self.v_data
        #bottom row
        v[0] = vertex4f(hs[0], vs[0], ths[0], tvs[0])
        v[1] = vertex4f(hs[1], vs[0], ths[1], tvs[0])
        v[2] = vertex4f(hs[2], vs[0], ths[2], tvs[0])
        v[3] = vertex4f(hs[3], vs[0], ths[3], tvs[0])

        #bottom inner border row
        v[11] = vertex4f(hs[0], vs[1], ths[0], tvs[1])
        v[12] = vertex4f(hs[1], vs[1], ths[1], tvs[1])
        v[13] = vertex4f(hs[2], vs[1], ths[2], tvs[1])
        v[4]  = vertex4f(hs[3], vs[1], ths[3], tvs[1])

        #top inner border row
        v[10] = vertex4f(hs[0], vs[2], ths[0], tvs[2])
        v[15] = vertex4f(hs[1], vs[2], ths[1], tvs[2])
        v[14] = vertex4f(hs[2], vs[2], ths[2], tvs[2])
        v[5]  = vertex4f(hs[3], vs[2], ths[3], tvs[2])

        #top row
        v[9] = vertex4f(hs[0], vs[3], ths[0], tvs[3])
        v[8] = vertex4f(hs[1], vs[3], ths[1], tvs[3])
        v[7] = vertex4f(hs[2], vs[3], ths[2], tvs[3])
        v[6] = vertex4f(hs[3], vs[3], ths[3], tvs[3])
        
        #phew....all done
        self.update_vbo_data()



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
            print "setting size: ", size
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

    property texture:
        def __get__(self):
            return self._texture
        def __set__(self, tex):
            if tex == None:
                return
            cdef int i
            self._texture = tex
            tcords = self.texture.tex_coords
            print "SETTINF texture coords:", tcords
            for i in range(8):
                self._tex_coords[i] = tcords[i] 
            self.build()



cdef class Ellipse(VertexDataInstruction):
    cdef float x,y,w,h
    cdef int segments

    def __init__(self, *args, **kwargs):
        VertexDataInstruction.__init__(self, **kwargs)

        #get keyword args for configuring rectangle
        cdef tuple s = kwargs.get('size', (100, 100))
        cdef tuple p = kwargs.get('pos', (0,0))
        self.segments = kwargs.get('segments', 180)
        self.x = p[0]; self.y = p[1]
        self.w = s[0]; self.h = s[1]

        self.allocate_vertex_buffers(self.segments + 1)
        self.build()     
        
        indices = []
        for i in range(self.segments):
            indices.extend(  (i, 360, i+1) )
        print indices
        self.indices = indices
        self.canvas.add(self)

    cdef build(self):
        cdef float x, y, angle, rx, ry
        cdef vertex* v = self.v_data
        cdef int i = 0
        angle = 0.0
        rx = 0.5*(self.w-self.x)
        ry = 0.5*(self.h-self.y)
        for i in xrange(self.segments):
            # rad = deg * (pi / 180), where pi/180 = 0.0174...
            angle = i * 360.0/self.segments *0.017453292519943295
            # Polar coordinates to cartesian space
            x = self.x + (rx * 2.0 * cos(angle))
            y = self.y + (ry * 2.0 * sin(angle))
            v[i] = vertex2f(x, y)
        v[self.segments] = vertex2f(self.x+rx, self.y+ry)
        self.update_vbo_data()
        
             



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
            print "setting size: ", size
            self.w = size[0]
            self.h = size[1]
            self.build()



cdef class Path(VertexDataInstruction):
    cdef float pen_x, pen_y
    cdef Buffer point_buffer
    def __init__(self):
        VertexDataInstruction.__init__(self)
        self.point_buffer = Buffer(sizeof(vertex))

    cdef int add_point(self, float x, float y):
        cdef int idx
        cdef vertex v = vertex2f(x,y)
        self.point_buffer.add(&v, &idx, 1)
        return idx

    cdef build(self):
        cdef vertex* p    #pointer into point buffer
        cdef vertex v[4]  #to hold the vertices for each quad were creating
        cdef int  idx[4]  #to hold teh vbo indecies for every quad we add 
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
                print "skipping line, the two points are 0 unit apart."
                continue

            dx = sw/2.0 * dx/ns
            dy = sw/2.0 * dy/ns

            #create quad, with cornerss pull off the line by the normal
            v[0] = vertex2f(x0-dy, y0+dx); 
            v[1] = vertex2f(x0+dy, y0-dx); 
            v[2] = vertex2f(x1+dy, y1-dx); 
            v[3] = vertex2f(x1-dy, y1+dx); 

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



cdef Path ACTIVE_PATH = None
cdef class PathInstruction(GraphicInstruction):
    cdef Path path 
    def __init__(self):
        global ACTIVE_PATH
        GraphicInstruction.__init__(self, GI_IGNORE) 
        self.path = ACTIVE_PATH



cdef class PathStart(PathInstruction): 
    cdef int index
    def __init__(self, float x, float y):
        '''
        Starts a new path at position x,y.  Will raise an Excpetion, if called while another path is already started
        :Parameters:
            `x`, float:  x position
            `y`, float:  y position
        '''
        global ACTIVE_PATH
        PathInstruction.__init__(self)
        if ACTIVE_PATH != None: 
            raise Exception("Can't start a new path while another one is being constructed")
        ACTIVE_PATH = self.path = Path() 
        self.index = self.path.add_point(x, y)
        

cdef class PathLineTo(PathInstruction):
    cdef int index
    def __init__(self, x, y): 
        '''
        Adds a line from the current location to the x, y coordinates passed as parameters 
        '''
        PathInstruction.__init__(self)
        self.index = self.path.add_point(x, y)


cdef class PathClose(PathInstruction):
    def __init__(self): 
        '''
        Closes the path, by adding a line from teh current location to the first vertex taht started teh path
        '''
        PathInstruction.__init__(self)
        cdef vertex* v = <vertex*> self.path.point_buffer.pointer()
        self.path.add_point(v[0].x, v[0].y)


cdef class PathEnd(PathInstruction):
    def __init__(self):
        '''
        ends path construction on teh current path, teh path will be build
        and added to the canvas
        '''    
        global ACTIVE_PATH
        PathInstruction.__init__(self) 
        self.path.build()
        ACTIVE_PATH = None
        print "END PATH", ACTIVE_PATH
'''
    cdef class PathMoveTo(PathInstruction):
    cdef float x,y
    def __init__(self, x, y): 
        PathInstruction.__init__(self) 
        self.path.pen_state = PEN_UP
        self.path.pen_x = x
        self.path.pen_y = y
'''
