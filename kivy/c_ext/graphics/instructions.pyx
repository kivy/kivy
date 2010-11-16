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
        Logger.trace("GraphicsInstruction: init \n\t adding self to " + str(self.parent))
        if self.parent:
            self.parent.add(self)

    cdef apply(self):
        pass

    cdef flag_update(self):
        if self.parent:
            self.parent.flag_update()
        self.flags &= GI_NEED_UPDATE

    cdef flag_update_done(self):
        self.flags &= ~GI_NEED_UPDATE



cdef class InstructionGroup(GraphicsInstruction):
    def __init__(self):
        GraphicsInstruction.__init__(self)
        self.children = list()


    cdef apply(self):
        Logger.trace("InstructionGroup: " + str(self))
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

    cdef apply(self):
        Logger.trace("Context Instruction:  active_context" +str(getActiveContext()))
        getActiveContext().set_states(self.context_state)

    cdef set_state(self, str name, value):
        self.context_state[name] = value
        self.flag_update()


cdef class VertexInstruction(GraphicsInstruction):
    def __init__(self):
        GraphicsInstruction.__init__(self)
        self.flags = GI_VERTEX_DATA
        self.batch = VertexBatch()
        self.vertices = list()
        self.indices = list()
        
    cdef build(self):
        pass

    cdef update_batch(self):
        self.batch.set_data(self.vertices, self.indices)
        self.flag_update_done()

    cdef apply(self):
        Logger.trace("VertexInstr: " + str(self.flags & GI_NEED_UPDATE))
        if 1 or self.flags & GI_NEED_UPDATE:
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
from os.path import join
from kivy import kivy_shader_dir
from kivy.lib.transformations import identity_matrix

cdef class RenderContext(InstructionGroup):

    def __init__(self, *args, **kwargs):
        InstructionGroup.__init__(self)

        vertex_file   = join(kivy_shader_dir, 'default.vs')
        fragment_file = join(kivy_shader_dir, 'default.fs')
        vertex_file   = kwargs.get('vertex_shader',   vertex_file)
        fragment_file = kwargs.get('fragment_shader', fragment_file)
        vertex_src   = open(vertex_file,   'r').read()
        fragment_src = open(fragment_file, 'r').read()
        self.shader = Shader(vertex_src, fragment_src)
        self.shader.use()
        self.set_states({
            'modelview_mat':identity_matrix(),
            'linewidth' : 1.0,
            'color' : [1.0,1.0,1.0,1.0]
        })

    cdef set_state(self, str name, value):
        self.shader.set_uniform(name, value)

    cdef set_states(self, dict states):
        cdef str name
        for name, value in states.iteritems():
            Logger.trace("RenderContext:set_states: " + name + str(value))
            self.shader.set_uniform(name, value)
            Logger.trace("RenderContext:\t Error %d" % glGetError())


    cdef enter(self):
        global ACTIVE_CONTEXT
        Logger.trace("RenderContext: enabling shader, "+str(self.shader))
        self.shader.use()

    cdef apply(self):
        pushActiveContext(self)
        Logger.trace("RenderContext:  entered, active_context:" +str(getActiveContext()))
        InstructionGroup.apply(self)
        popActiveContext()
        Logger.trace("RenderContext: end\n\n\n")

    cpdef draw(self):
        self.apply()




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

        
