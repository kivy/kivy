from os.path import join
from kivy.logger import Logger
from kivy.core.image import Image
from kivy import kivy_shader_dir
from kivy.resources import resource_find
from kivy.lib.transformations import identity_matrix
from kivy.c_ext.c_opengl cimport *
from kivy.c_ext.graphics_matrix cimport MatrixStack

cdef class GraphicContext
cdef GraphicContext _default_context

def Context_instance():
    global _default_context
    if _default_context == None:
        _default_context = GraphicContext()
    return _default_context

cdef class GraphicContext:
    '''Handle the saving/restore of the context

    TODO: explain more how it works
    '''

    instance = staticmethod(Context_instance)

    property default_shader:
        def __get__(self):
            if not self._default_shader:
                _default_vertex_shader   = open(join(kivy_shader_dir, 'default.vs')).read()
                _default_fragment_shader = open(join(kivy_shader_dir, 'default.fs')).read()
                self._default_shader = Shader(_default_vertex_shader, _default_fragment_shader)
            return self._default_shader

    property default_texture:
        def __get__(self):
            if not self._default_texture:
                img = Image(join(kivy_shader_dir, 'default.png'))
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
            Logger.warning('GContext: GL Error while drawing frame: %d' % err)

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
        self.set('blend', 1)
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
        cdef Shader shader

        shader = self.state['shader']

        shader.use()
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
                shader = state['shader']
                if x == 'modelview_mat':
                    shader.set_uniform_matrix(x, value)
                else:
                    shader.set_uniform(x, value)

        journal.clear()
        self.need_flush = 0





