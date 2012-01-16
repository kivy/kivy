'''
Canvas
======

The :class:`Canvas` is the root object used for drawing by a
:class:`~kivy.uix.widget.Widget`. Check the class documentation for more
information about the usage of Canvas.
'''

__all__ = ('Instruction', 'InstructionGroup',
           'ContextInstruction', 'VertexInstruction',
           'Canvas', 'CanvasBase',
           'RenderContext', 'Callback')

include "config.pxi"
include "opcodes.pxi"

from c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from c_opengl_debug cimport *
from kivy.logger import Logger


cdef int _need_reset_gl = 1
cdef int _active_texture = -1

cdef void reset_gl_context():
    global _need_reset_gl, _active_texture
    _need_reset_gl = 0
    _active_texture = 0
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glActiveTexture(GL_TEXTURE0)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)


cdef class Instruction:
    '''Represents the smallest instruction available. This class is for internal
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
        if do_parent == 1 and self.parent is not None:
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
            if (self.flags & GI_NEEDS_UPDATE) > 0:
                return True
            return False


cdef class InstructionGroup(Instruction):
    '''Group of :class:`Instruction`. Adds the possibility of adding and
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
        cdef list children
        if self.compiler is not None:
            if self.flags & GI_NEEDS_UPDATE:
                self.build()
            if self.compiled_children is not None and not (self.flags & GI_NO_APPLY_ONCE):
                children = self.compiled_children.children
                for c in children:
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
        '''Add a new :class:`Instruction` to our list.
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

    def indexof(self, Instruction c):
        cdef int i
        for i in xrange(len(self.children)):
            if self.children[i] is c:
                return i
        return -1

    def length(self):
        return len(self.children)

    cpdef clear(self):
        '''Remove all the :class:`Instruction`.
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
        '''Return an iterable with all the :class:`Instruction` with a specific
        group name.
        '''
        cdef Instruction c
        return [c for c in self.children if c.group == groupname]


cdef class ContextInstruction(Instruction):
    '''The ContextInstruction class is the base for the creation of instructions
    that don't have a direct visual representation, but instead modify the
    current Canvas' state, e.g. texture binding, setting color parameters,
    matrix manipulation and so on.
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
        if self.context_push:
            context.push_states(self.context_push)
        if self.context_state:
            context.set_states(self.context_state)
        if self.context_pop:
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
    '''The VertexInstruction class is the base for all graphics instructions
    that have a direct visual representation on the canvas, such as Rectangles,
    Triangles, Lines, Ellipse and so on.
    '''
    def __init__(self, **kwargs):
        # Set a BindTexture instruction to bind the texture used for
        # this instruction before the actual vertex instruction
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
        '''Property that represents the texture used for drawing this
        Instruction. You can set a new texture like this::

            from kivy.core.image import Image

            texture = Image('logo.png').texture
            with self.canvas:
                Rectangle(texture=texture, pos=self.pos, size=self.size)

        Usually, you will use the :data:`source` attribute instead of the
        texture.
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
        '''This property represents the filename to load the texture from.
        If you want to use an image as source, do it like this::

            with self.canvas:
                Rectangle(source='mylogo.png', pos=self.pos, size=self.size)

        Here's the equivalent in Kivy language::

            <MyWidget>:
                canvas:
                    Rectangle:
                        source: 'myfilename.png'
                        pos: self.pos
                        size: self.size

        .. note::
            
            The filename will be searched with the
            :func:`kivy.resources.resource_find` function.

        '''
        def __get__(self):
            return self.texture_binding.source
        def __set__(self, source):
            self.texture_binding.source = source
            self.texture = self.texture_binding._texture

    property tex_coords:
        '''This property represents the texture coordinates used for drawing the
        vertex instruction. The value must be a list of 8 values.

        A texture coordinate has a position (u, v), and a size (w, h). The size
        can be negative, and would represent the 'flipped' texture. By default,
        the tex_coords are::

            [u, v, u + w, v, u + w, y + h, u, y + h]

        You can pass your own texture coordinates, if you want to achieve fancy
        effects.

        .. warning::

            The default value as mentioned before can be negative. Depending
            on the image and label providers, the coordinates are flipped
            vertically, because of the order in which the image is internally
            stored. Instead of flipping the image data, we are just flipping
            the texture coordinates to be faster.

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
        self.batch.draw()


cdef class Callback(Instruction):
    '''.. versionadded:: 1.0.4
    
    A Callback is an instruction that will be called when the drawing
    operation is performed. When adding instructions to a canvas, you can do
    this::

        with self.canvas:
            Color(1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)
            Callback(self.my_callback)

    The definition of the callback must be::

        def my_callback(self, instr):
            print 'I have been called!'

    .. warning::

        Note that if you perform many and/or costly calls to callbacks, you
        might potentially slow down the rendering performance significantly.

    The drawing of your canvas can not happen until something new happens. From
    your callback, you can ask for an update::

        with self.canvas:
            self.cb = Callback(self.my_callback)
        # then later in the code
        self.cb.ask_update()

    If you use the Callback class to call rendering methods of another
    toolkit, you will have issues with the OpenGL context. The OpenGL state may
    have been manipulated by the other toolkit, and as soon as program flow
    returns to Kivy, it will just break. You can have glitches, crashes, black
    holes might occur, etc.
    To avoid that, you can activate the :data:`reset_context` option. It will
    reset the OpenGL context state to make Kivy's rendering correct, after the
    call to your callback.

    .. warning::

        The :data:`reset_context` is not a full OpenGL reset. If you have issues
        regarding that, please contact us.

    '''
    def __init__(self, arg, **kwargs):
        Instruction.__init__(self, **kwargs)
        self.func = arg
        self._reset_context = int(kwargs.get('reset_context', False))

    def ask_update(self):
        '''Inform the parent canvas that we'd like it to update on the next
        frame. This is useful when you need to trigger a redraw due to some
        value having changed for example.

        .. versionadded:: 1.0.4
        '''
        self.flag_update()

    cdef void apply(self):
        cdef RenderContext context
        cdef Shader shader
        cdef int i

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
            shader = context._shader
            context.enter()
            shader.bind_attrib_locations()
            for index, texture in context.bind_texture.iteritems():
                context.set_texture(index, texture)

            reset_gl_context()

    cdef void enter(self):
        self._shader.use()

    property reset_context:
        '''Set this to True if you want to reset the OpenGL context for Kivy
        after the callback has been called.
        '''
        def __get__(self):
            return self._reset_context
        def __set__(self, value):
            cdef int ivalue = int(value)
            if self._reset_context == ivalue:
                return
            self._reset_context = ivalue
            self.flag_update()


cdef class CanvasBase(InstructionGroup):
    def __enter__(self):
        pushActiveCanvas(self)

    def __exit__(self, *largs):
        popActiveCanvas()


cdef class Canvas(CanvasBase):
    '''The important Canvas class. Use this class to add graphics or context
    instructions that you want to be used for drawing.

    .. note::

        The Canvas supports Python's ``with`` statement and its enter & exit
        semantics.

    Usage of a canvas without the ``with`` statement::

        self.canvas.add(Color(1., 1., 0))
        self.canvas.add(Rectangle(size=(50, 50)))

    Usage of a canvas with Python's ``with`` statement::

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
        '''Inform the canvas that we'd like it to update on the next frame.
        This is useful when you need to trigger a redraw due to some value
        having changed for example.
        '''
        self.flag_update()

    property before:
        '''Property for getting the 'before' group.
        '''
        def __get__(self):
            if self._before is None:
                self._before = CanvasBase()
                self.insert(0, self._before)
            return self._before

    property after:
        '''Property for getting the 'after' group.
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
    '''The render context stores all the necessary information for drawing, i.e.:

    - The vertex shader
    - The fragment shader
    - The default texture
    - The state stack (color, texture, matrix...)
    '''
    def __init__(self, *args, **kwargs):
        cdef str key
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
        # Upload the uniform value to the shader
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
        oldvalue = stack.pop()
        if oldvalue != stack[-1]:
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
        global _active_texture
        self.bind_texture[index] = texture
        if _active_texture != index:
            _active_texture = index
            glActiveTexture(GL_TEXTURE0 + index)
        glBindTexture(texture._target, texture._id)
        self.flag_update()

    cdef void enter(self):
        self._shader.use()

    cdef void leave(self):
        self._shader.stop()

    cdef void apply(self):
        cdef list keys = self.state_stacks.keys()
        pushActiveContext(self)
        if _need_reset_gl:
            reset_gl_context()
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
    if ACTIVE_CONTEXT:
        ACTIVE_CONTEXT.leave()
    ACTIVE_CONTEXT = CONTEXT_STACK.pop()
    if ACTIVE_CONTEXT:
        ACTIVE_CONTEXT.enter()

