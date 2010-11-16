from os.path import join
from kivy import kivy_shader_dir




cdef class RenderContext(InstructionGroup):

    def __init__(self, *args, **kwargs):
        cdef str vertex_src   = join(kivy_shader_dir, 'default.vs')
        cdef str fragment_src = join(kivy_shader_dir, 'default.fs')
        vertex_src   = kwargs.get('vertex_shader',   vertex_src)
        fragment_src = kwargs.get('fragment_shader', fragment_src)
        self.shader = Shader(vertex_src, fragment_src)

    cdef set_state(self, str name, value):
        self.shader.set_uniform(name, value)

    cdef set_states(self, dict states):
        cdef str name
        for name, value in states.iteritems():
            self.shader.set_uniform(name, value)

    cdef enter(self):
        global ACTIVE_CONTEXT
        if ACTIVE_CONTEXT == self:
            return
        self.shader.use()

    cdef apply(self):
        pushActiveContext(self)
        InstructionGroup.apply(self)
        popActiveContext()




cdef RenderContext ACTIVE_CONTEXT = None
cdef list CONTEXT_STACK  = list()

cdef RenderContext getActiveContext():
    global ACTIVE_CONTEXT
    return ACTIVE_CONTEXT

cdef pushActiveContext(RenderContext c):
    global CONTEXT_STACK, ACTIVE_CONTEXT
    CONTEXT_STACK.append(ACTIVE_CONTEXT)
    c.enter()

cdef popActiveContext():
    global CONTEXT_STACK, ACTIVE_CONTEXT
    ACTIVE_CONTEXT = CONTEXT_STACK.pop()
    if ACTIVE_CONTEXT:
        ACTIVE_CONTEXT.enter()
