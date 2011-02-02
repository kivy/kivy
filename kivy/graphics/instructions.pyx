#cython: embedsignature=True

'''
Canvas
======

The :class:`Canvas` is the root object used for drawing by a
:class:`~kivy.uix.widget.Widget`. Check module documentation for more
information about the usage of Canvas.

'''

__all__ = ('Instruction', 'InstructionGroup',
           'ContextInstruction', 'VertexInstruction',
           'Canvas', 'CanvasBase', 'RenderContext')

include "config.pxi"
include "opcodes.pxi"

from c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from c_opengl_debug cimport *
from kivy.logger import Logger

cdef class Instruction:
    '''Represent the smallest instruction available. This class is for internal
    usage only, don't use it directly.
    '''
    def __cinit__(self):
        self.flags = 0

    def __init__(self, **kwargs):
        self.group = kwargs.get('group', None)
        self.parent = getActiveCanvas()
        if self.parent:
            self.parent.add(self)

    cdef apply(self):
        pass

    cdef flag_update(self):
        if self.parent:
            self.parent.flag_update()
        self.flags |= GI_NEEDS_UPDATE

    cdef flag_update_done(self):
        self.flags &= ~GI_NEEDS_UPDATE

    property needs_redraw:
        def __get__(self):
            return bool(self.flags | GI_NEEDS_UPDATE)


cdef class InstructionGroup(Instruction):
    '''Group of :class:`Instruction`. Add the possibility of adding and
    removing graphics instruction.
    '''
    def __init__(self, **kwargs):
        Instruction.__init__(self, **kwargs)
        self.children = list()
        self.compiled_children = None
        if 'nocompiler' in kwargs:
            self.compiler = None
        else:
            self.compiler = GraphicsCompiler()

    cdef apply(self):
        cdef Instruction c
        if self.compiler:
            if self.flags & GI_NEEDS_UPDATE:
                self.build()
            if self.compiled_children and not (self.flags & GI_NO_APPLY_ONCE):
                for c in self.compiled_children.children:
                    if c.flags & GI_IGNORE:
                        continue
                    c.apply()
            self.flags &= ~GI_NO_APPLY_ONCE
        else:
            for c in self.children:
                c.apply()

    cdef void build(self):
        self.compiled_children = self.compiler.compile(self)
        self.flag_update_done()

    cpdef add(self, Instruction c):
        '''Add a new :class:`Instruction` in our list.
        '''
        if c.parent is None:
            c.parent = self
        self.children.append(c)
        self.flag_update()

    cpdef insert(self, int index, Instruction c):
        '''Insert a new :class:`Instruction` in our list at index.
        '''
        if c.parent is None:
            c.parent = self
        self.children.insert(index, c)
        self.flag_update()

    cpdef remove(self, Instruction c):
        '''Remove an existing :class:`Instruction` from our list.
        '''
        if c.parent is self:
            c.parent = None
        self.children.remove(c)
        self.flag_update()

    cpdef clear(self):
        '''Remove all the :class:`Instruction`
        '''
        cdef Instruction c
        for c in self.children[:]:
            self.remove(c)

    cpdef remove_group(self, str groupname):
        '''Remove all :class:`Instruction` with a specific group name.
        '''
        cdef Instruction c
        for c in self.children[:]:
            if c.group == groupname:
                self.remove(c)

    cpdef get_group(self, str groupname):
        '''Return a generator with all the :class:`Instruction` from a specific
        group name.
        '''
        cdef Instruction c
        return [c for c in self.children if c.group == groupname]

cdef class ContextInstruction(Instruction):
    '''A context instruction is the base for creating non-display instruction
    for Canvas (texture binding, color parameters, matrix manipulation...)
    '''
    def __init__(self, **kwargs):
        Instruction.__init__(self, **kwargs)
        self.flags |= GI_CONTEXT_MOD
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


cdef class VertexInstruction(Instruction):
    def __init__(self, **kwargs):
        #add a BindTexture instruction to bind teh texture used for 
        #this instruction before the actual vertex instruction
        self.texture_binding = BindTexture(**kwargs)
        self.texture = self.texture_binding.texture #auto compute tex coords
        self.tex_coords = kwargs.get('tex_coords', self._tex_coords)

        Instruction.__init__(self, **kwargs)
        self.flags = GI_VERTEX_DATA & GI_NEEDS_UPDATE
        self.batch = VertexBatch()
        self.vertices = []
        self.indices = []

    property texture:
        '''Property for getting/setting the texture to be bound when drawing the
        vertices.
        '''
        def __get__(self):
            return self.texture_binding.texture
        def __set__(self, _tex):
            cdef Texture tex = _tex
            self.texture_binding.texture = tex
            if tex:
                self.tex_coords = tex.tex_coords
            else:
                self.tex_coords = [0.0,0.0, 1.0,0.0, 1.0,1.0, 0.0,1.0]
            self.flag_update()

    property source:
        '''Property for getting/setting a filename as a source for the texture.
        '''
        def __get__(self):
            return self.texture_binding.source
        def __set__(self, source):
            self.texture_binding.source = source
            self.texture = self.texture_binding._texture

    property tex_coords:
        '''Property for getting/setting texture coordinates.
        '''
        def __get__(self):
            return self._tex_coords
        def __set__(self, tc):
            self._tex_coords = list(tc)
            self.flag_update()

    cdef void build(self):
        pass

    cdef update_batch(self):
        self.batch.set_data(self.vertices, self.indices)
        self.flag_update_done()

    cdef apply(self):
        if self.flags & GI_NEEDS_UPDATE:
            self.build()
            self.update_batch()

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.batch.draw()


cdef class CanvasBase(InstructionGroup):
    def __enter__(self):
        pushActiveCanvas(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        popActiveCanvas()

cdef class Canvas(CanvasBase):
    '''Our famous Canvas class. Use this class for add graphics or context
    instructions to use when drawing

    .. note::

        The Canvas support "with" statement.

    Usage of Canvas without "with" statement::

        self.canvas.add(Color(1., 1., 0))
        self.canvas.add(Rectangle(size=(50, 50)))

    Usage of Canvas with the "with" statement::

        with self.canvas:
            Color(1., 1., 0)
            Rectangle(size=(50, 50))
    '''

    def __init__(self, **kwargs):
        CanvasBase.__init__(self, **kwargs)
        self._before = None
        self._after = None

    cpdef draw(self):
        '''Apply the instruction on our window.
        '''
        self.apply()

    cpdef add(self, Instruction c):
        if c.parent is None:
            c.parent = self
        # the after group must remain the last one.
        if self._after is None:
            self.children.append(c)
        else:
            self.children.insert(-1, c)
        self.flag_update()

    cpdef remove(self, Instruction c):
        if c.parent is self:
            c.parent = None
        self.children.remove(c)
        self.flag_update()

    property before:
        '''Property for getting the before group.
        '''
        def __get__(self):
            if self._before is None:
                self._before = CanvasBase()
                self.insert(0, self._before)
            return self._before

    property after:
        '''Property for getting the after group.
        '''
        def __get__(self):
            cdef CanvasBase c
            if self._after is None:
                c = CanvasBase()
                self.add(c)
                self._after = c
            return self._after

# Active Canvas and getActiveCanvas function is used
# by instructions, so they know which canvas to add
# tehmselves to
cdef CanvasBase ACTIVE_CANVAS = None

cdef CanvasBase getActiveCanvas():
    global ACTIVE_CANVAS
    return ACTIVE_CANVAS

# Canvas Stack, for internal use so canvas can be bound 
# inside other canvas, and restroed when other canvas is done
cdef list CANVAS_STACK = list()

cdef pushActiveCanvas(CanvasBase c):
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
#from texture cimport *

from os.path import join
from kivy import kivy_shader_dir
from kivy.cache import Cache
from kivy.core.image import Image
from kivy.graphics.transformation cimport Matrix

cdef class RenderContext(Canvas):
    '''The render context store all the necessary information for drawing, aka:

    - the fragment shader
    - the vertex shader
    - the default texture
    - the state stack (color, texture, matrix...)
    '''
    def __init__(self, *args, **kwargs):
        self.bind_texture = dict()
        Canvas.__init__(self, **kwargs)
        vs_src = kwargs.get('vs', None)
        fs_src = kwargs.get('fs', None)
        if vs_src is None:
            vs_file = join(kivy_shader_dir, 'default.vs')
            vs_src  = open(vs_file, 'r').read()
        if fs_src is None:
            fs_file = join(kivy_shader_dir, 'default.fs')
            fs_src  = open(fs_file, 'r').read()
        self.shader = Shader(vs_src, fs_src)

        # load default texture image
        filename = join(kivy_shader_dir, 'default.png')
        tex = Cache.get('kv.texture', filename)
        if not tex:
            tex = Image(filename).texture
            Cache.append('kv.texture', filename, tex)
        self.default_texture = tex

        self.state_stacks = {
            'texture0' : [0],
            'linewidth': [1.0],
            'color'    : [[1.0,1.0,1.0,1.0]],
            'projection_mat': [Matrix()],
            'modelview_mat' : [Matrix()],
        }

        self.shader.use()
        for key, stack in self.state_stacks.iteritems():
            self.set_state(key, stack[0])

    cdef set_state(self, str name, value):
        #upload the uniform value for the shdeer
        cdef list d
        if not name in self.state_stacks:
            self.state_stacks[name] = [value]
            self.flag_update()
        else:
            d = self.state_stacks[name]
            if value != d[-1]:
                d[-1] = value
                self.flag_update()
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
        self.flag_update()

    cdef push_states(self, list names):
        cdef str name
        for name in names:
            self.push_state(name)

    cdef pop_state(self, str name):
        stack = self.state_stacks[name]
        stack.pop()
        self.set_state(name, stack[-1])
        self.flag_update()

    cdef pop_states(self, list names):
        cdef str name
        for name in names:
            self.pop_state(name)

    cdef set_texture(self, int index, Texture texture):
        if index in self.bind_texture and \
           self.bind_texture[index] is texture:
            return
        self.bind_texture[index] = texture
        glActiveTexture(GL_TEXTURE0 + index)
        glBindTexture(texture.target, texture.id)
        self.flag_update()

    cdef enter(self):
        self.shader.use()

    cdef apply(self):
        keys = self.state_stacks.keys()
        self.push_states(keys)
        pushActiveContext(self)
        Canvas.apply(self)
        popActiveContext()
        self.pop_states(keys)
        self.flag_update_done()

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


