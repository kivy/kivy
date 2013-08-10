'''
Framebuffer
===========

Fbo is like an offscreen window. You can activate the fbo for rendering into a
texture, and use your fbo as a texture for another drawing.

Fbo act as a :class:`kivy.graphics.instructions.Canvas`.

Example of using an fbo for some color rectangles::

    from kivy.graphics import Fbo, Color, Rectangle

    class FboTest(Widget):
        def __init__(self, **kwargs):
            super(FboTest, self).__init__(**kwargs)

            # first step is to create the fbo and use the fbo texture on other
            # rectangle

            with self.canvas:
                # create the fbo
                self.fbo = Fbo(size=(256, 256))

                # show our fbo on the widget in different size
                Color(1, 1, 1)
                Rectangle(size=(32, 32), texture=self.fbo.texture)
                Rectangle(pos=(32, 0), size=(64, 64), texture=self.fbo.texture)
                Rectangle(pos=(96, 0), size=(128, 128), texture=self.fbo.texture)

            # in the second step, you can draw whatever you want on the fbo
            with self.fbo:
                Color(1, 0, 0, .8)
                Rectangle(size=(256, 64))
                Color(0, 1, 0, .8)
                Rectangle(size=(64, 256))

If you change anything in the `self.fbo` object, it will be automaticly updated,
and canvas where the fbo is putted will be automaticly updated too.

Reloading the FBO content
-------------------------

.. versionadded:: 1.2.0

If the OpenGL context is lost, then the FBO is lost too. You need to reupload
data on it yourself. Use the :func:`Fbo.add_reload_observer` to add a reloading
function that will be automatically called when needed::

    def __init__(self, **kwargs):
        super(...).__init__(**kwargs)
        self.fbo = Fbo(size=(512, 512))
        self.fbo.add_reload_observer(self.populate_fbo)

        # and load the data now.
        self.populate_fbo(self.fbo)


    def populate_fbo(self, fbo):
        with fbo:
            # .. put your Color / Rectangle / ... here

This way, you could use the same method for initialization and for reloading.
But it's up to you.

'''

__all__ = ('Fbo', )

include "config.pxi"
include "opcodes.pxi"

from os import environ
from kivy.logger import Logger
from kivy.weakmethod import WeakMethod
from kivy.graphics.texture cimport Texture
from kivy.graphics.transformation cimport Matrix
from kivy.graphics.context cimport get_context

from kivy.graphics.c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from kivy.graphics.c_opengl_debug cimport *
from kivy.graphics.instructions cimport RenderContext, Canvas
from kivy.graphics.opengl import glReadPixels as py_glReadPixels

cdef list fbo_stack = []
cdef list fbo_release_list = []


cdef class Fbo(RenderContext):
    '''Fbo class for wrapping the OpenGL Framebuffer extension. The Fbo support
    "with" statement.

    :Parameters:
        `clear_color`: tuple, default to (0, 0, 0, 0)
            Define the default color for clearing the framebuffer
        `size`: tuple, default to (1024, 1024)
            Default size of the framebuffer
        `push_viewport`: bool, default to True
            If True, the OpenGL viewport will be set to the framebuffer size,
            and will be automatically restored when the framebuffer released.
        `with_depthbuffer`: bool, default to False
            If True, the framebuffer will be allocated with a Z buffer.
        `texture`: :class:`~kivy.graphics.texture.Texture`, default to None
            If None, a default texture will be created.
    '''
    cdef str resolve_status(self, int status):
        if status == GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT:
            return 'Incomplete attachment'
        elif status == GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS:
            return 'Incomplete dimensions'
        elif status == GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT:
            return 'Incomplete missing attachment'
        elif status == GL_FRAMEBUFFER_UNSUPPORTED:
            return 'Unsupported'
        IF USE_OPENGL_ES2 == 0:
            if status == 0x8219: #GL_FRAMEBUFFER_UNDEFINED
                return 'Undefined framebuffer'
            elif status == 0x8cdb: #GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER
                return 'Incomplete draw buffer'
            elif status == 0x8cdc: #GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER
                return 'Incomplete read buffer'
            elif status == 0x8d56: #GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE
                return 'Incomplete multisample'
            elif status == 0x8da8: #GL_FRAMEBUFFER_INCOMPLETE_LAYER_TARGETS
                return 'Incomplete layer targets'
            elif status == 0x8da9: #GL_FRAMEBUFFER_INCOMPLETE_LAYER_COUNT
                return 'Incomplete layer count'
        return 'Unknown (status=%x)' % status

    cdef void raise_exception(self, str message, int status=0):
        if status:
            message += ': %s (%d)' % (self.resolve_status(status), status)
        raise Exception(message)

    def __init__(self, *args, **kwargs):
        get_context().register_fbo(self)

        RenderContext.__init__(self, *args, **kwargs)

        if 'clear_color' not in kwargs:
            kwargs['clear_color'] = (0, 0, 0, 0)
        if 'size' not in kwargs:
            kwargs['size'] = (1024, 1024)
        if 'push_viewport' not in kwargs:
            kwargs['push_viewport'] = True
        if 'with_depthbuffer' not in kwargs:
            kwargs['with_depthbuffer'] = False
        if 'texture' not in kwargs:
            kwargs['texture'] = None

        self.buffer_id = 0
        self.depthbuffer_id = 0
        self._width, self._height  = kwargs['size']
        self.clear_color = kwargs['clear_color']
        self._depthbuffer_attached = int(kwargs['with_depthbuffer'])
        self._push_viewport = int(kwargs['push_viewport'])
        self._is_bound = 0
        self._texture = kwargs['texture']
        self.observers = []

        self.create_fbo()

    def __dealloc__(self):
        get_context().dealloc_fbo(self)

    cdef void delete_fbo(self):
        self._texture = None
        get_context().dealloc_fbo(self)
        self.buffer_id = 0
        self.depthbuffer_id = 0

    cdef void create_fbo(self):
        cdef GLuint f_id = 0
        cdef GLint old_fid = 0
        cdef int status
        cdef int do_clear = 0

        # create texture
        if self._texture is None:
            self._texture = Texture.create(size=(self._width, self._height))
            do_clear = 1

        # apply any changes if needed
        self._texture.bind()

        # create framebuffer
        glGenFramebuffers(1, &f_id)
        self.buffer_id = f_id
        glGetIntegerv(GL_FRAMEBUFFER_BINDING, &old_fid)
        glBindFramebuffer(GL_FRAMEBUFFER, self.buffer_id)

        # if we need depth, create a renderbuffer
        if self._depthbuffer_attached:
             
            glGenRenderbuffers(1, &f_id)
            self.depthbuffer_id = f_id
            glBindRenderbuffer(GL_RENDERBUFFER, self.depthbuffer_id)
            glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT16,
                                  self._width, self._height)
            glBindRenderbuffer(GL_RENDERBUFFER, 0)
            glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT,
                                      GL_RENDERBUFFER, self.depthbuffer_id)

        # attach the framebuffer to our texture
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                self._texture._target, self._texture._id, 0)

        # check the status of the framebuffer
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status != GL_FRAMEBUFFER_COMPLETE:
            self.raise_exception('FBO Initialization failed', status)

        # clear the fbo
        if do_clear:
            self.clear_buffer()

        # unbind the framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, old_fid)

        cdef Matrix projection_mat = Matrix()
        projection_mat.view_clip(0.0, self._width, 0.0, self._height, -1.0, 1.0, 0)
        self.set_state('projection_mat', projection_mat)

    cpdef bind(self):
        '''Bind the FBO to the current opengl context.
        `Bind` mean that you enable the Framebuffer, and all the drawing
        operations will act inside the Framebuffer, until :func:`release` is
        called.

        The bind/release operation are automatically done when you add graphics
        object in it. But if you want to manipulate a Framebuffer yourself, you
        can use it like this::

            self.fbo = FBO()
            self.fbo.bind()
            # do any drawing command
            self.fbo.release()

            # then, your fbo texture is available at
            print(self.fbo.texture)
        '''
        if self._is_bound:
            self.raise_exception('FBO already binded.')
        else:
            self._is_bound = 1

        # stack our fbo to the last binded fbo
        cdef GLint old_fid = 0
        if len(fbo_stack) == 0:
            # the very first time we're going to create it, fill with the
            # initial framebuffer
            glGetIntegerv(GL_FRAMEBUFFER_BINDING, &old_fid)
            fbo_stack.append(old_fid)
        fbo_stack.append(self.buffer_id)
        glBindFramebuffer(GL_FRAMEBUFFER, self.buffer_id)

        # if asked, push the viewport
        if self._push_viewport:
            glGetIntegerv(GL_VIEWPORT, <GLint *>self._viewport)
            glViewport(0, 0, self._width, self._height)

    cpdef release(self):
        '''Release the Framebuffer (unbind).
        '''
        if self._is_bound == 0:
            self.raise_exception('FBO cannot be released (not binded).')
        else:
            self._is_bound = 0

        # bind the latest fbo, or unbind it.
        fbo_stack.pop()
        glBindFramebuffer(GL_FRAMEBUFFER, fbo_stack[-1])

        # if asked, restore the viewport
        if self._push_viewport:
            glViewport(self._viewport[0], self._viewport[1],
                       self._viewport[2], self._viewport[3])

    cpdef clear_buffer(self):
        '''Clear the framebuffer with the :data:`clear_color`.

        You need to bound the framebuffer yourself before calling this
        method::

            fbo.bind()
            fbo.clear_buffer()
            fbo.release()

        '''
        glClearColor(self._clear_color[0], self._clear_color[1],
                     self._clear_color[2], self._clear_color[3])
        if self._depthbuffer_attached:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        else:
            glClear(GL_COLOR_BUFFER_BIT)

    cdef void apply(self):
        if self.flags & GI_NEEDS_UPDATE:
            self.bind()
            RenderContext.apply(self)
            self.release()
            self.flag_update_done()

    cdef void reload(self):
        # recreate the framebuffer, without deleting it. the deletion is not
        # handled by us.
        self.create_fbo()
        self.flag_update()
        # notify observers
        for callback in self.observers:
            if callback.is_dead():
                self.observers.remove(callback)
                continue
            callback()(self)

    def add_reload_observer(self, callback):
        '''Add a callback to be called after the whole graphics context have
        been reloaded. This is where you can reupload your custom data in GPU.

        .. versionadded:: 1.2.0

        :Parameters:
            `callback`: func(context) -> return None
                The first parameter will be the context itself
        '''
        self.observers.append(WeakMethod(callback))

    def remove_reload_observer(self, callback):
        '''Remove a callback from the observer list, previously added by
        :func:`add_reload_observer`.

        .. versionadded:: 1.2.0

        '''
        for cb in self.observers[:]:
            if cb.is_dead() or cb() is callback:
                self.observers.remove(cb)
                continue


    property size:
        '''Size of the framebuffer, in (width, height) format.

        If you change the size, the framebuffer content will be lost.
        '''
        def __get__(self):
            return (self._width, self._height)
        def __set__(self, x):
            cdef int w, h
            w, h = x
            if w == self._width and h == self._height:
                return
            self._width, self._height = x
            self.delete_fbo()
            self.create_fbo()
            self.flag_update()

    property clear_color:
        '''Clear color in (red, green, blue, alpha) format.
        '''
        def __get__(self):
            return (self._clear_color[0],
                    self._clear_color[1],
                    self._clear_color[2],
                    self._clear_color[3])
        def __set__(self, x):
            x = list(x)
            if len(x) != 4:
                raise Exception('clear_color must be a list/tuple of 4 entry.')
            self._clear_color[0] = x[0]
            self._clear_color[1] = x[1]
            self._clear_color[2] = x[2]
            self._clear_color[3] = x[3]

    property texture:
        '''Return the framebuffer texture
        '''
        def __get__(self):
            return self._texture

    property pixels:
        '''Get the pixels texture, in RGBA format only, unsigned byte.

        .. versionadded:: 1.7.0
        '''
        def __get__(self):
            w,h = self._width, self._height
            self.bind()
            data = py_glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE)
            self.release()
            return data

    cpdef get_pixel_color(self, int wx, int wy):
        """Get the color of the pixel with specified window
        coordinates wx, wy. It returns result in RGBA format.
 
        .. versionadded:: 1.8.0
        """
        if wx > self._width or wy > self._height:
            # window coordinates should not exceed the
            # frame buffer size
            return (0, 0, 0, 0)
        self.bind()
        data = py_glReadPixels(wx, wy, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE)
        self.release()
        raw_data = str(memoryview(data))
        
        return [ord(i) for i in raw_data]

