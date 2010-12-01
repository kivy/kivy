include "opcodes.pxi"

__all__ = ('GraphicsInstruction', 'InstructionGroup', 
           'ContextInstruction', 'VertexInstruction',
           'Canvas','RenderContext')

from kivy.logger import Logger

cdef class GraphicsInstruction:
    def __cinit__(self):
        self.flags = 0

    def __init__(self):
        self.parent = getActiveCanvas()
        if self.parent:
            self.parent.add(self)

    cdef apply(self):
        pass

    cdef flag_update(self):
        if self.parent:
            self.parent.flag_update()
        self.flags |= GI_NEED_UPDATE

    cdef flag_update_done(self):
        self.flags &= ~GI_NEED_UPDATE



cdef class InstructionGroup(GraphicsInstruction):
    def __init__(self):
        GraphicsInstruction.__init__(self)
        self.children = list()


    cdef apply(self):
        cdef GraphicsInstruction c
        for c in self.children:
            c.apply()


    cpdef add(self, GraphicsInstruction c):
        c.parent = self
        self.children.append(c)
        self.flag_update()

    cpdef remove(self, GraphicsInstruction c):
        c.parent = None
        self.children.remove(c)
        self.flag_update()


cdef class ContextInstruction(GraphicsInstruction):
    def __init__(self):
        GraphicsInstruction.__init__(self)
        self.flags &= GI_CONTEXT_MOD
        self.context_state = dict()
        self.context_push = list()
        self.context_pop = list()

    cdef RenderContext get_context(self):
        cdef RenderContext context = getActiveContext()
        return context

    cdef apply(self):
        cdef RenderContext context = self.get_context()
        context.push_states(self.context_push)
        context.set_states(self.context_state)
        context.pop_states(self.context_pop)

    cdef set_state(self, str name, value):
        self.context_state[name] = value
        self.flag_update()

    cdef push_state(self, str name):
        self.context_push.append(name)
        self.flag_update()

    cdef pop_state(self, str name):
        self.context_pop.append(name)
        self.flag_update()

cdef class VertexInstruction(GraphicsInstruction):
    def __init__(self, **kwargs):
        #add a BindTexture instruction to bind teh texture used for 
        #this instruction before the actual vertex instruction
        Logger.warn("VERTINSTR %s" % kwargs)
        self.texture_binding = BindTexture(**kwargs)
        self.texture = self.texture_binding.texture #auto compute tex coords
        self.tex_coords = kwargs.get('tex_coords', self._tex_coords)

        GraphicsInstruction.__init__(self)
        self.flags = GI_VERTEX_DATA & GI_NEED_UPDATE
        self.batch = VertexBatch()
        self.vertices = list()
        self.indices = list()

    property texture:
        '''Set/get the texture to be bound when drawing the vertices'''
        def __get__(self):
            return self.texture_binding.texture
        def __set__(self, tex):
            self.texture_binding.texture = tex
            if tex:
                self.tex_coords = tex.tex_coords
            else:
                self.tex_coords = [0.0,0.0, 1.0,0.0, 1.0,1.0, 0.0,1.0]
            self.flag_update()

    property source:
        def __get__(self):
            return self.texture_binding.source
        def __set__(self, source):
            self.texture_binding.source = source
            self.texture = self.texture_binding._texture

    property tex_coords:
        def __get__(self):
            return self._tex_coords
        def __set__(self, tc):
            Logger.debug("setting texture coords %s %s" %(self, tc))
            self._tex_coords = list(tc)
            self.flag_update()

    cdef build(self):
        pass

    cdef update_batch(self):
        self.batch.set_data(self.vertices, self.indices)
        self.flag_update_done()

    cdef apply(self):
        if self.flags & GI_NEED_UPDATE:
            self.build()
            self.update_batch()
        self.batch.draw()





#TODO: move back into canvas.pyx, but need to resolve circular reference to instructions
cdef class Canvas(InstructionGroup):
    cpdef draw(self):
        self.apply()

    def __enter__(self):
        pushActiveCanvas(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        popActiveCanvas()

# Active Canvas and getActiveCanvas function is used
# by instructions, so they know which canvas to add
# tehmselves to
cdef Canvas ACTIVE_CANVAS = None

cdef Canvas getActiveCanvas():
    global ACTIVE_CANVAS
    return ACTIVE_CANVAS


# Canvas Stack, for internal use so canvas can be bound 
# inside other canvas, and restroed when other canvas is done
cdef list CANVAS_STACK = list()

cdef pushActiveCanvas(Canvas c):
    global ACTIVE_CANVAS, CANVAS_STACK
    CANVAS_STACK.append(ACTIVE_CANVAS)
    ACTIVE_CANVAS = c

cdef popActiveCanvas():
    global ACTIVE_CANVAS, CANVAS_STACK
    ACTIVE_CANVAS = CANVAS_STACK.pop()










#TODO: same as canvas, move back to context.pyx..fix circular import 
#on actual import from python problem
include "common.pxi"
from vertex cimport *
from texture cimport *

from os.path import join
from kivy import kivy_shader_dir
from kivy.core.image import Image
from kivy.lib.transformations import identity_matrix




cdef class RenderContext(Canvas):

    def __init__(self, *args, **kwargs):
        Canvas.__init__(self)
        vs_file = join(kivy_shader_dir, 'default.vs')
        fs_file = join(kivy_shader_dir, 'default.fs')
        vs_src  = open(vs_file, 'r').read()
        fs_src  = open(fs_file, 'r').read()
        self.shader = Shader(vs_src, fs_src)
        self.texture_manager = TextureManager()

        self.default_texture = Image(join(kivy_shader_dir, 'default.png')).texture

        self.state_stacks = {
            'texture0' : [0],
            'linewidth': [1.0],
            'color'    : [[1.0,1.0,1.0,1.0]],
            'projection_mat': [identity_matrix()],
            'modelview_mat' : [identity_matrix()],
        }

        self.shader.use()
        for key, stack in self.state_stacks.iteritems():
            self.set_state(key, stack[0])

    cdef set_state(self, str name, value):
        #upload the uniform value for the shdeer
        self.state_stacks[name][-1] = value
        self.shader.set_uniform(name, value)

    cdef get_state(self, str name):
        return self.state_stacks[name][-1]

    cdef set_states(self, dict states):
        cdef str name
        for name, value in states.iteritems():
            self.set_state(name, value)

    cdef push_state(self, str name):
        stack = self.state_stacks[name] 
        stack.append(stack[-1])

    cdef push_states(self, list names):
        cdef str name
        for name in names:
            self.push_state(name)

    cdef pop_state(self, str name):
        stack = self.state_stacks[name] 
        stack.pop()
        self.set_state(name, stack[-1])

    cdef pop_states(self, list names):
        cdef str name
        for name in names:
            self.pop_state(name)

    cdef enter(self):
        self.shader.use()

    cdef apply(self):
        pushActiveContext(self)
        Canvas.apply(self)
        popActiveContext()
        
    def __setitem__(self, key, val):
        self.set_state(key, val)

    def __getitem__(self, key):
        return self.shader.uniform_values[key]





cdef RenderContext ACTIVE_CONTEXT = None
cdef list CONTEXT_STACK  = list()

cdef RenderContext getActiveContext():
    global ACTIVE_CONTEXT
    return ACTIVE_CONTEXT

cdef pushActiveContext(RenderContext c):
    global CONTEXT_STACK, ACTIVE_CONTEXT
    CONTEXT_STACK.append(ACTIVE_CONTEXT)
    ACTIVE_CONTEXT = c
    c.enter()

cdef popActiveContext():
    global CONTEXT_STACK, ACTIVE_CONTEXT
    ACTIVE_CONTEXT = CONTEXT_STACK.pop()
    if ACTIVE_CONTEXT:
        ACTIVE_CONTEXT.enter()

        
