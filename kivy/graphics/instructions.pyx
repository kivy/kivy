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
           'Canvas', 'CanvasBase', 'RenderContext',
           'Callback')

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
        self.parent = None

    def __init__(self, **kwargs):
        self.group = kwargs.get('group', None)
        if kwargs.get('noadd'):
            self.flags |= GI_NO_REMOVE
            return
        self.parent = getActiveCanvas()
        if self.parent:
            self.parent.add(self)

    cdef void apply(self):
        pass

    cdef void flag_update(self, int do_parent=1):
        if do_parent and self.parent:
            self.parent.flag_update()
        self.flags |= GI_NEEDS_UPDATE

    cdef void flag_update_done(self):
        self.flags &= ~GI_NEEDS_UPDATE

    cdef void radd(self, InstructionGroup ig):
        ig.children.append(self)
        self.set_parent(ig)

    cdef void rremove(self, InstructionGroup ig):
        ig.children.remove(self)
        self.set_parent(None)

    cdef void rinsert(self, InstructionGroup ig, int index):
        ig.children.insert(index, self)
        self.set_parent(ig)

    cdef void set_parent(self, Instruction parent):
        self.parent = parent

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

    cdef void apply(self):
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
        c.radd(self)
        self.flag_update()
        return

    cpdef insert(self, int index, Instruction c):
        '''Insert a new :class:`Instruction` in our list at index.
        '''
        c.rinsert(self, index)
        self.flag_update()

    cpdef remove(self, Instruction c):
        '''Remove an existing :class:`Instruction` from our list.
        '''
        c.rremove(self)
        self.flag_update()

    cpdef clear(self):
        '''Remove all the :class:`Instruction`
        '''
        cdef Instruction c
        for c in self.children[:]:
            if c.flags & GI_NO_REMOVE:
                continue
            self.remove(c)

    cpdef remove_group(self, str groupname):
        '''Remove all :class:`Instruction` with a specific group name.
        '''
        cdef Instruction c
        for c in self.children[:]:
            if c.flags & GI_NO_REMOVE:
                continue
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

    cdef void apply(self):
        cdef RenderContext context = self.get_context()
        if len(self.context_push):
            context.push_states(self.context_push)
        if len(self.context_state):
            context.set_states(self.context_state)
        if len(self.context_pop):
            context.pop_states(self.context_pop)

    cdef void set_state(self, str name, value):
        self.context_state[name] = value
        self.flag_update()

    cdef void push_state(self, str name):
        self.context_push.append(name)
        self.flag_update()

    cdef void pop_state(self, str name):
        self.context_pop.append(name)
        self.flag_update()


cdef class VertexInstruction(Instruction):
    '''A vertex instruction is the base for creating displayed instruction
    for Canvas (Rectangles, Triangles, Lines, Ellipse...)
    '''
    def __init__(self, **kwargs):
        #add a BindTexture instruction to bind teh texture used for 
        #this instruction before the actual vertex instruction
        self.texture_binding = BindTexture(noadd=True, **kwargs)
        self.texture = self.texture_binding.texture #auto compute tex coords
        self.tex_coords = kwargs.get('tex_coords', self._tex_coords)

        Instruction.__init__(self, **kwargs)
        self.flags = GI_VERTEX_DATA & GI_NEEDS_UPDATE
        self.batch = VertexBatch()

    cdef void radd(self, InstructionGroup ig):
        cdef Instruction instr = self.texture_binding
        ig.children.append(self.texture_binding)
        ig.children.append(self)
        instr.set_parent(ig)
        self.set_parent(ig)

    cdef void rinsert(self, InstructionGroup ig, int index):
        cdef Instruction instr = self.texture_binding
        ig.children.insert(index, self.texture_binding)
        ig.children.insert(index, self)
        instr.set_parent(ig)
        self.set_parent(ig)

    cdef void rremove(self, InstructionGroup ig):
        cdef Instruction instr = self.texture_binding
        ig.children.remove(self.texture_binding)
        ig.children.remove(self)
        instr.set_parent(None)
        self.set_parent(None)

    property texture:
        '''Property that represent the texture used for drawing this
        Instruction. You can set a new texture like this::

            from kivy.core.image import Image

            texture = Image('logo.png').texture
            with self.canvas:
                Rectangle(texture=texture, pos=self.pos, size=self.size)

        Usually, you will use :data:`source` attribute instead of texture.
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
        '''This property represent the filename to used for the texture.
        If you want to use another image as a source, you can do::

            with self.canvas:
                Rectangle(source='mylogo.png', pos=self.pos, size=self.size)

        Or in a kivy language::

            <MyWidget>:
                canvas:
                    Rectangle:
                        source: 'myfilename.png'
                        pos: self.pos
                        size: self.size

        .. note::
            
            The filename will be search with
            :func:`kivy.resources.resource_find` function.

        '''
        def __get__(self):
            return self.texture_binding.source
        def __set__(self, source):
            self.texture_binding.source = source
            self.texture = self.texture_binding._texture

    property tex_coords:
        '''This property represent the texture coordinate used for drawing the
        vertex instruction. The value must be a list of 8 values.

        A texture coordinate have a position (u, v), and a size (w, h). The size
        can be negative, and will represent the 'inversed' texture. By default,
        the tex_coords will be::

            [u, v, u + w, v, u + w, y + h, u, y + h]

        You can pass your own texture coordinate, if you want to do fancy
        effects.

        .. warning::

            The default value as exposed just before can be negative. Depending
            of the provider of image nor label, the coordinate are flip in
            vertical, because of the order of internal image. Instead of
            flipping the image data, we are just flipping the texture coordinate 
            to be faster.

        '''
        def __get__(self):
            return self._tex_coords
        def __set__(self, tc):
            self._tex_coords = list(tc)
            self.flag_update()

    cdef void build(self):
        pass

    cdef void apply(self):
        if self.flags & GI_NEEDS_UPDATE:
            self.build()
            self.flag_update_done()

        # TODO: REMOVE THIS UGLY THING §!!!!!!!!!!!!!
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.batch.draw()


cdef class Callback(Instruction):
    '''A Callback is a instruction that will be called when the drawing happen.
    If you are building a canvas, you can do::

        with self.canvas:
            Color(1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)
            Callback(self.my_callback)

    The definition of the callback must be::

        def my_callback(self, instr):
            print 'I am called !'

    The drawing of your canvas can not happen until something new changes. From
    your callback, you can ask for an update::

        with self.canvas:
            self.cb = Canvas(self.my_callback)
        # then later in the code
        self.cb.ask_update()

    If you are using the Callback class to call rendering method of another
    toolkit, you will have issues with opengl context. The opengl state can be
    changed inside the another tookit, and so, as soon as you'll back to Kivy,
    it will just broke. You can have glitch, crash, etc.
    To prevent that, you can activate the :data:`reset_context` option. It will
    reset the opengl context state to make Kivy rendering correct, after the
    call of your callback.

    .. warning::

        The :data:`reset_context` is not a full OpenGL reset. If you have issues
        around that, please contact us.

    '''
    cdef object func
    cdef int _reset_context

    def __init__(self, arg, **kwargs):
        Instruction.__init__(self, **kwargs)
        self.func = arg
        self._reset_context = int(kwargs.get('reset_context', False))

    def ask_update(self):
        '''Ask the parent canvas to update itself the next frame.
        Can be useful when a texture content is changing, but anything else in
        the canvas.
        '''
        self.flag_update()

    cdef void apply(self):
        cdef RenderContext context
        cdef Shader shader

        if self.func(self):
            self.flag_update_done()

        if self._reset_context:
            # FIXME do that in a proper way
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_CULL_FACE)
            glDisable(GL_SCISSOR_TEST)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glUseProgram(0)

            # FIXME don't use 10. use max texture available from gl conf
            for i in xrange(10):
                glActiveTexture(GL_TEXTURE0 + i)
                glBindTexture(GL_TEXTURE_2D, 0)
                glDisableVertexAttribArray(i)
                glBindBuffer(GL_ARRAY_BUFFER, 0)
                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

            # force binding again all our textures.
            context = getActiveContext()
            shader = context.shader
            context.enter()
            shader.bind_attrib_locations()
            for index, texture in context.bind_texture.iteritems():
                context.set_texture(index, texture)

    cdef void enter(self):
        self._shader.use()

    property reset_context:
        '''Set to True if you want to reset OpenGL context for kivy after the
        callback have been called.
        '''
        def __get__(self):
            return self._reset_context
        def __set__(self, value):
            value = int(value)
            if self._reset_context == value:
                return
            self._reset_context = value
            self.flag_update()


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

    cpdef clear(self):
        cdef Instruction c
        for c in self.children[:]:
            if c is self._before or c is self._after:
                continue
            if c.flags & GI_NO_REMOVE:
                continue
            self.remove(c)

    cpdef draw(self):
        '''Apply the instruction on our window.
        '''
        self.apply()

    cpdef add(self, Instruction c):
        # the after group must remain the last one.
        if self._after is None:
            c.radd(self)
        else:
            c.rinsert(self, -1)
        self.flag_update()

    cpdef remove(self, Instruction c):
        c.rremove(self)
        self.flag_update()

    def ask_update(self):
        '''Ask the canvas to update itself the next frame.
        Can be useful when a texture content is changing, but anything else in
        the canvas.
        '''
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
        self._shader = Shader(vs_src, fs_src)

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

        self._shader.use()
        for key, stack in self.state_stacks.iteritems():
            self.set_state(key, stack[0])

    cdef void set_state(self, str name, value):
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
        self._shader.set_uniform(name, value)

    cdef get_state(self, str name):
        return self.state_stacks[name][-1]

    cdef void set_states(self, dict states):
        cdef str name
        for name, value in states.iteritems():
            self.set_state(name, value)

    cdef void push_state(self, str name):
        stack = self.state_stacks[name]
        stack.append(stack[-1])
        self.flag_update()

    cdef void push_states(self, list names):
        cdef str name
        for name in names:
            self.push_state(name)

    cdef void pop_state(self, str name):
        stack = self.state_stacks[name]
        stack.pop()
        self.set_state(name, stack[-1])
        self.flag_update()

    cdef void pop_states(self, list names):
        cdef str name
        for name in names:
            self.pop_state(name)

    cdef void set_texture(self, int index, Texture texture):
        # TODO this code is actually broken,
        # the binded texture can be already set, but we may changed if we came
        # from another render context.
        #if index in self.bind_texture and \
        #   self.bind_texture[index] is texture:
        #    return
        self.bind_texture[index] = texture
        glActiveTexture(GL_TEXTURE0 + index)
        glBindTexture(texture.target, texture.id)
        self.flag_update()

    cdef void enter(self):
        self._shader.use()

    cdef void apply(self):
        cdef list keys = self.state_stacks.keys()
        pushActiveContext(self)
        self.push_states(keys)
        Canvas.apply(self)
        self.pop_states(keys)
        popActiveContext()
        self.flag_update_done()

    def __setitem__(self, key, val):
        self.set_state(key, val)

    def __getitem__(self, key):
        return self._shader.uniform_values[key]

    property shader:
        def __get__(self):
            return self._shader



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


