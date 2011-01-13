#cython: embedsignature=True

'''
Framebuffer
===========

Fbo is like an offscreen window. You can activate the fbo for rendering into a
texture, and use your fbo as a texture for another drawing.

Fbo act as a :class:`kivy.graphics.instructions.Canvas`.

Exemple of using an fbo for some color rectangles ::

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
'''

__all__ = ('Fbo', 'FboException')

include "config.pxi"
include "opcodes.pxi"

from kivy import Logger
from kivy.graphics.texture cimport Texture
from kivy.graphics.transformation cimport Matrix

from c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from c_opengl_debug cimport *
from instructions cimport RenderContext, Canvas

cdef list fbo_stack = [0]

class FboException(Exception):
    '''FboException is fired when an FBO error happen during creation or usage.
    '''
    def __init__(self, message, status=0):
        if status:
            message += ': %s (%d)' % (self.resolve_status(status), status)
        super(FboException, self).__init__(message)

    def resolve_status(self, status):
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
        `with_depthbuffer`: bool, default to True
            If True, the framebuffer will be allocated with a Z buffer.
        `texture`: :class:`~kivy.graphics.texture.Texture`, default to None
            If None, a default texture will be created.
    '''
    def __init__(self, *args, **kwargs):
        RenderContext.__init__(self, *args, **kwargs)

        kwargs.setdefault('clear_color', (0, 0, 0, 0))
        kwargs.setdefault('size', (1024, 1024))
        kwargs.setdefault('push_viewport', True)
        kwargs.setdefault('with_depthbuffer', True)

        self._buffer_id             = -1
        self._depthbuffer_id        = -1
        self._width, self._height   = kwargs.get('size')
        self.clear_color            = kwargs.get('clear_color')
        self._depthbuffer_attached  = int(kwargs.get('with_depthbuffer'))
        self._push_viewport         = int(kwargs.get('push_viewport'))
        self._is_bound              = 0
        self._texture               = kwargs.get('texture', None)

        self.create_fbo()

    cdef delete_fbo(self):
        # care on this case, if the deletion happen in another thread than main
        # thread, we are lost :)
        self._texture = None
        self._depthbuffer_attached = 0
        if self._buffer_id != -1:
            glDeleteFramebuffers(1, &self._buffer_id)
            self._buffer_id = -1
        if self._depthbuffer_id != -1:
            glDeleteRenderbuffers(1, &self._depthbuffer_id)
            self._depthbuffer_id = -1

    cdef create_fbo(self):
        cdef GLuint f_id
        cdef int status

        # create texture
        if self._texture is None:
            self._texture = Texture.create(size=(self._width, self._height))

        # create framebuffer
        glGenFramebuffers(1, &f_id)
        self._buffer_id = f_id
        glBindFramebuffer(GL_FRAMEBUFFER, self._buffer_id)

        # if we need depth, create a renderbuffer
        if self._depthbuffer_attached:
            glGenRenderbuffers(1, &f_id)
            self._depthbuffer_id = f_id
            glBindRenderbuffer(GL_RENDERBUFFER, self._depthbuffer_id)
            glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT,
                                  self._width, self._height)
            glBindRenderbuffer(GL_RENDERBUFFER, 0)
            glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT,
                                      GL_RENDERBUFFER, self._depthbuffer_id)

        # attach the framebuffer to our texture
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                self._texture._target, self._texture._id, 0)

        # check the status of the framebuffer
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status != GL_FRAMEBUFFER_COMPLETE:
            raise FboException('FBO Initialization failed', status)

        # clear the fbo
        self.clear_buffer()

        # unbind the framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        cdef Matrix projection_mat = Matrix()
        projection_mat.view_clip(0.0, self._width, 0.0, self._height, -1.0, 1.0, 0)
        self.set_state('projection_mat', projection_mat)

    cpdef bind(self):
        if self._is_bound:
            raise FboException('FBO is already binded.')
        else:
            self._is_bound = 1

        # stack our fbo to the last binded fbo
        fbo_stack.append(self._buffer_id)
        glBindFramebuffer(GL_FRAMEBUFFER, self._buffer_id)

        # if asked, push the viewport
        if self._push_viewport:
            glGetIntegerv(GL_VIEWPORT, <GLint *>&self._viewport)
            glViewport(0, 0, self._width, self._height)

    cpdef release(self):
        if self._is_bound == 0:
            raise FboException('Cannot release a FBO not binded.')
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
        '''Clear the framebuffer with the :data:`clear_color`
        '''
        glClearColor(self._clear_color[0], self._clear_color[1],
                     self._clear_color[2], self._clear_color[3])
        if self._depthbuffer_attached:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        else:
            glClear(GL_COLOR_BUFFER_BIT)

    cdef apply(self):
        if self.flags & GI_NEED_UPDATE:
            self.bind()
            RenderContext.apply(self)
            self.release()
            self.flag_update_done()

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
