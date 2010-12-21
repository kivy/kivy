'''
Framebuffer
===========

Fbo is like an offscreen window. You can activate the fbo for rendering into a
texture, and use your fbo as a texture for another drawing.
'''

__all__ = ('Fbo',)

import kivy
from kivy import Logger

from c_opengl cimport *
from instructions cimport RenderContext, Canvas

cdef class Fbo(RenderContext):
    def __init__(self, *args, **kwargs):
        RenderContext.__init__(self, *args, **kwargs)

        kwargs.setdefault('clear_color', (0, 0, 0, 0))
        kwargs.setdefault('size', (1024, 1024))
        kwargs.setdefault('push_viewport', False)
        kwargs.setdefault('with_depthbuffer', True)

        self.size                 = kwargs.get('size')
        self.clear_color          = kwargs.get('clear_color')
        self.depthbuffer_attached = kwargs.get('with_depthbuffer')
        self.push_viewport        = kwargs.get('push_viewport')
        self._is_bound             = False

        # create buffers and textures
        self.texture = kivy.Texture.create(self.width, self.height)

        cdef GLuint id
        glGenFramebuffers(1, &id)
        self.buffer_id = id
        glBindFramebuffer(GL_FRAMEBUFFER, self.buffer_id)

        if self.depthbuffer_attached:
            glGenRenderbuffers(1, &id)
            self.depthbuffer_id = id
            glBindRenderbuffer(GL_RENDERBUFFER, self.depthbuffer_id)
            glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT,
                                  self.width, self.height)
            glBindRenderbuffer(GL_RENDERBUFFER, 0)
            glFramebufferRenderbuffer(GL_FRAMEBUFFER, 
                                         GL_DEPTH_ATTACHMENT,
                                         GL_RENDERBUFFER, 
                                         self.depthbuffer_id)

        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                GL_TEXTURE_2D, self.texture.id, 0)

        cdef int status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status:
            Logger.error("Error initializing FBO.  %d" % status)


        glBindFramebuffer(GL_FRAMEBUFFER, 0)


    cpdef bind(self):
        self._is_bound = True
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
        glViewport(0, 0, self.width, self.height)

    cpdef release(self):
        self._is_bound = False
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    cpdef clear(self):
        cdef float c[4] 
        c[0] = self.clear_color[0]
        c[1] = self.clear_color[2]
        c[2] = self.clear_color[2]
        c[3] = self.clear_color[3]
        glClearColor(c[0],c[1],c[2],c[3])
        if self.depthbuffer_attached:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        else:
            glClear(GL_COLOR_BUFFER_BIT)


    def __enter__(self):
        Canvas.__enter__(self)
        self.bind()

    def __exit__(self, type, value, traceback):
        Canvas.__exit__(self, type, value, traceback)
        self.release()

