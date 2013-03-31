'''
Context management
==================

.. versionadded:: 1.2.0

This class handle a register of all graphics instructions created, and the
ability to flush and delete them.

You can read more about it at :doc:`api-kivy.graphics`
'''

include "config.pxi"

import gc
from os import environ
from weakref import ref
from kivy.graphics.instructions cimport Canvas
from kivy.graphics.texture cimport Texture, TextureRegion
from kivy.graphics.vbo cimport VBO, VertexBatch
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.graphics.c_opengl cimport *
from kivy.weakmethod import WeakMethod
from time import time
IF USE_OPENGL_DEBUG == 1:
    from kivy.graphics.c_opengl_debug cimport *
from kivy.cache import Cache

cdef Context context = None

cdef class Context:

    def __init__(self):
        self.observers = []
        self.observers_before = []
        self.l_texture = []
        self.l_canvas = []
        self.l_vbo = []
        self.l_vertexbatch = []
        self.l_shader = []
        self.l_fbo = []
        self.flush()
        self.trigger_gl_dealloc = Clock.create_trigger(self.gl_dealloc, 0)

    cdef void flush(self):
        self.lr_texture = []
        self.lr_canvas = []
        self.lr_vbo = []
        self.lr_fbo = []

    cdef void register_texture(self, Texture texture):
        self.l_texture.append(ref(texture))

    cdef void register_canvas(self, Canvas canvas):
        self.l_canvas.append(ref(canvas))

    cdef void register_vbo(self, VBO vbo):
        self.l_vbo.append(ref(vbo))

    cdef void register_vertexbatch(self, VertexBatch vb):
        self.l_vertexbatch.append(ref(vb))

    cdef void register_shader(self, Shader shader):
        self.l_shader.append(ref(shader))

    cdef void register_fbo(self, Fbo fbo):
        self.l_fbo.append(ref(fbo))

    cdef void dealloc_texture(self, Texture texture):
        if texture._nofree or texture.__class__ is TextureRegion:
            return
        if texture.id > 0:
            self.lr_texture.append(texture.id)
            self.trigger_gl_dealloc()

    cdef void dealloc_vbo(self, VBO vbo):
        if vbo.have_id():
            self.lr_vbo.append(vbo.id)
            self.trigger_gl_dealloc()

    cdef void dealloc_vertexbatch(self, VertexBatch batch):
        if batch.have_id():
            self.lr_vbo.append(batch.id)
            self.trigger_gl_dealloc()

    cdef void dealloc_shader(self, Shader shader):
        if shader.program == -1:
            return
        if shader.vertex_shader is not None:
            glDetachShader(shader.program, shader.vertex_shader.shader)
        if shader.fragment_shader is not None:
            glDetachShader(shader.program, shader.fragment_shader.shader)
        glDeleteProgram(shader.program)

    cdef void dealloc_fbo(self, Fbo fbo):
        if fbo.buffer_id != -1:
            self.lr_fbo.append((fbo.buffer_id, fbo.depthbuffer_id))
            self.trigger_gl_dealloc()

    def add_reload_observer(self, callback, before=False):
        '''Add a callback to be called after the whole graphics context have
        been reloaded. This is where you can reupload your custom data in GPU.

        :Parameters:
            `callback`: func(context) -> return None
                The first parameter will be the context itself
            `before`: boolean, default to False
                If True, the callback will be executed before the whole
                reloading processus. Use it if you want to clear your cache for
                example.

        .. versionchanged:: 1.4.0
            `before` parameter added.
        '''
        if before:
            self.observers_before.append(WeakMethod(callback))
        else:
            self.observers.append(WeakMethod(callback))

    def remove_reload_observer(self, callback, before=False):
        '''Remove a callback from the observer list, previously added by
        :func:`add_reload_observer`. 
        '''
        lst = self.observers_before if before else self.observers
        for cb in lst[:]:
            if cb.is_dead() or cb() is callback:
                lst.remove(cb)
                continue

    def reload(self):
        cdef VBO vbo
        cdef VertexBatch batch
        cdef Texture texture
        cdef Shader shader
        cdef Canvas canvas

        # call reload observers that want to do something after a whole gpu
        # reloading.
        for callback in self.observers_before[:]:
            if callback.is_dead():
                self.observers_before.remove(callback)
                continue
            callback()(self)

        # mark all the texture to not delete from the previous reload as to
        # delete now.
        for item in self.l_texture[:]:
            texture = item()
            if texture is None:
                continue
            if texture._nofree == 1:
                texture._nofree = 0
                self.l_texture.remove(item)

        image_objects = Cache._objects['kv.image']
        Cache.remove('kv.loader')
        Cache.remove('kv.image')
        Cache.remove('kv.shader')

        # For texture cache, save the objects. We need to clean the cache as the
        # others to prevent of using it during the reloading part.
        # We'll restore the object later.
        texture_objects = Cache._objects['kv.texture']
        Cache.remove('kv.texture')

        start = time()
        Logger.info('Context: Reloading graphics data...')
        Logger.debug('Context: Collect and flush all garbage')
        self.gc()
        gc.collect()
        self.flush()

        # First step, prevent double loading by setting everything to -1
        # We do this because texture might be loaded in seperate texture at first,
        # then merged from the cache cause of the same source
        Logger.debug('Context: Reload textures')
        cdef list l = self.l_texture[:]
        for item in l:
            texture = item()
            if texture is None:
                continue
            Logger.trace('Context: unset texture id %r' % texture)
            texture._id = -1

        # First time, only reload base texture
        for item in l:
            texture = item()
            if texture is None or isinstance(texture, TextureRegion):
                continue
            Logger.trace('Context: >> reload base texture %r' % texture)
            texture.reload()
            Logger.trace('Context: << reload base texture %r' % texture)

        # Second time, update texture region id
        for item in l:
            texture = item()
            if texture is None or not isinstance(texture, TextureRegion):
                continue
            Logger.trace('Context: >> reload region texture %r' % texture)
            texture.reload()
            Logger.trace('Context: << reload region texture %r' % texture)

        # Restore texture cache
        texture_objects.update(Cache._objects['kv.texture'])
        Cache._objects['kv.texture'] = texture_objects
        image_objects.update(Cache._objects['kv.image'])
        Cache._objects['kv.image'] = image_objects

        Logger.debug('Context: Reload vbos')
        for item in self.l_vbo[:]:
            vbo = item()
            if vbo is not None:
                Logger.trace('Context: reloaded %r' % item())
                vbo.reload()
        Logger.debug('Context: Reload vertex batchs')
        for item in self.l_vertexbatch[:]:
            batch = item()
            if batch is not None:
                Logger.trace('Context: reloaded %r' % item())
                batch.reload()
        Logger.debug('Context: Reload shaders')
        for item in self.l_shader[:]:
            shader = item()
            if shader is not None:
                Logger.trace('Context: reloaded %r' % item())
                shader.reload()
        Logger.debug('Context: Reload canvas')
        for item in self.l_canvas[:]:
            canvas = item()
            if canvas is not None:
                Logger.trace('Context: reloaded %r' % item())
                canvas.reload()

        # call reload observers that want to do something after a whole gpu
        # reloading.
        for callback in self.observers[:]:
            if callback.is_dead():
                self.observers.remove(callback)
                continue
            callback()(self)

        glFinish()
        dt = time() - start
        Logger.info('Context: Reloading done in %2.4fs' % dt)

    def flag_update_canvas(self):
        cdef Canvas canvas
        for item in self.l_canvas:
            canvas = item()
            if canvas:
                canvas.flag_update()

    def gc(self, *largs):
        self.l_texture = [x for x in self.l_texture if x() is not None]
        self.l_canvas = [x for x in self.l_canvas if x() is not None]
        self.l_vbo = [x for x in self.l_vbo if x() is not None]
        self.l_vertexbatch = [x for x in self.l_vertexbatch if x() is not None]

    def gl_dealloc(self, *largs):
        # dealloc all gl resources asynchronously
        cdef GLuint i, j

        # FIXME we are doing gc for each time we dealloc things. But if you have
        # "big" apps, this might just slow it down.
        self.gc()

        if len(self.lr_vbo):
            Logger.trace('Context: releasing %d vbos' % len(self.lr_vbo))
            while len(self.lr_vbo):
                i = self.lr_vbo.pop()
                glDeleteBuffers(1, &i)
        if len(self.lr_texture):
            Logger.trace('Context: releasing %d textures: %r' % (
                len(self.lr_texture), self.lr_texture))
            while len(self.lr_texture):
                i = self.lr_texture.pop()
                glDeleteTextures(1, &i)
        if len(self.lr_fbo):
            Logger.trace('Context: releasing %d fbos' % len(self.lr_fbo))
            while len(self.lr_fbo):
                i, j = self.lr_fbo.pop()
                if i != -1:
                    glDeleteFramebuffers(1, &i)
                if j != -1:
                    glDeleteRenderbuffers(1, &j)


cpdef Context get_context():
    global context
    if context is None:
        context = Context()
    return context

