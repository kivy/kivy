'''
Context management
==================

.. versionadded:: 1.2.0

This class manages a registry of all created graphics instructions. It has
the ability to flush and delete them.

You can read more about Kivy graphics contexts in the :doc:`api-kivy.graphics`
module documentation. These are based on
`OpenGL graphics contexts <http://www.opengl.org/wiki/OpenGL_Context>`_.
'''

__all__ = ('Context',)

include "config.pxi"

from cpython.array cimport array
import gc
from os import environ
from weakref import ref
from kivy.graphics.instructions cimport Canvas
from kivy.graphics.texture cimport Texture, TextureRegion
from kivy.graphics.vbo cimport VBO, VertexBatch
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.graphics.c_opengl cimport *
IF USE_OPENGL_MOCK == 1:
    from kivy.graphics.c_opengl_mock cimport *
IF USE_OPENGL_DEBUG == 1:
    from kivy.graphics.c_opengl_debug cimport *
from kivy.weakmethod import WeakMethod
from time import time
from kivy.cache import Cache

cdef Context context = None

cdef class Context:
    """
    The Context class manages groups of graphics instructions. It can also be used to manage
    observer callbacks. See :meth:`add_reload_observer` and :meth:`remove_reload_observer`
    for more information.
    """
    def __init__(self):
        self.observers = []
        self.observers_before = []
        self.l_texture = []
        self.l_canvas = []
        self.l_fbo = []
        self.flush()
        self.trigger_gl_dealloc = Clock.create_trigger(self.gl_dealloc, 0)

    cdef void flush(self):
        gc.collect()
        self.lr_texture = array('i')
        self.lr_canvas = []
        self.lr_vbo = array('i')
        self.lr_fbo_rb = array('i')
        self.lr_fbo_fb = array('i')
        self.lr_shadersource = array('i')
        self.lr_shader = []

    cdef void register_texture(self, Texture texture):
        self.l_texture.append(ref(texture, self.l_texture.remove))

    cdef void register_canvas(self, Canvas canvas):
        self.l_canvas.append(ref(canvas, self.l_canvas.remove))

    cdef void register_fbo(self, Fbo fbo):
        self.l_fbo.append(ref(fbo, self.l_fbo.remove))

    cdef void dealloc_texture(self, Texture texture):
        cdef array arr
        if texture._nofree or texture.__class__ is TextureRegion:
            return
        if texture.id > 0:
            arr = self.lr_texture
            arr.append(texture.id)
            self.trigger_gl_dealloc()

    cdef void dealloc_vbo(self, VBO vbo):
        cdef array arr
        if vbo.have_id():
            arr = self.lr_vbo
            arr.append(vbo.id)
            self.trigger_gl_dealloc()

    cdef void dealloc_vertexbatch(self, VertexBatch batch):
        cdef array arr
        if batch.have_id():
            arr = self.lr_vbo
            arr.append(batch.id)
            self.trigger_gl_dealloc()

    cdef void dealloc_shader(self, Shader shader):
        if shader.program == 0:
            return
        cdef int vs_id = -1
        cdef int fs_id = -1
        self.lr_shader.append((shader.program, vs_id, fs_id))

    cdef void dealloc_shader_source(self, int shader):
        cdef array arr
        if shader == -1:
            return
        arr = self.lr_shadersource
        arr.append(shader)
        self.trigger_gl_dealloc()

    cdef void dealloc_fbo(self, Fbo fbo):
        cdef array arr_fb
        cdef array arr_rb
        if fbo.buffer_id != 0:
            arr_fb = self.lr_fbo_fb
            arr_fb.append(fbo.buffer_id)
            self.trigger_gl_dealloc()
        if fbo.depthbuffer_id != 0:
            arr_rb = self.lr_fbo_rb
            arr_rb.append(fbo.depthbuffer_id)
            # no need to trigger, depthbuffer required absolutely a buffer.

    def add_reload_observer(self, callback, before=False):
        '''(internal) Add a callback to be called after the whole graphics context has
        been reloaded. This is where you can reupload your custom data into the
        GPU.

        :Parameters:
            `callback`: func(context) -> return None
                The first parameter will be the context itself
            `before`: boolean, defaults to False
                If True, the callback will be executed before all the
                reloading processes. Use it if you want to clear your cache for
                example.

        .. versionchanged:: 1.4.0
            `before` parameter added.
        '''
        if before:
            self.observers_before.append(WeakMethod(callback))
        else:
            self.observers.append(WeakMethod(callback))

    def remove_reload_observer(self, callback, before=False):
        '''(internal) Remove a callback from the observer list previously added by
        :meth:`add_reload_observer`.
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
        self.flush()

        # First step, prevent double loading by setting everything to -1
        # We do this because texture might be loaded in separate texture at first,
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

        gc_objects = gc.get_objects()[:]
        Logger.debug('Context: Reload vbos')
        for item in gc_objects:
            if isinstance(item, VBO):
                vbo = item
                Logger.trace('Context: reloaded %r' % vbo)
                vbo.reload()
        Logger.debug('Context: Reload vertex batchs')
        for item in gc_objects:
            if isinstance(item, VertexBatch):
                batch = item
                Logger.trace('Context: reloaded %r' % batch)
                batch.reload()
        Logger.debug('Context: Reload shaders')
        for item in gc_objects:
            if isinstance(item, Shader):
                shader = item
                Logger.trace('Context: reloaded %r' % shader)
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

    def gl_dealloc(self, *largs):
        # dealloc all gl resources asynchronously
        cdef GLuint i, j
        cdef array arr

        if len(self.lr_vbo):
            Logger.trace('Context: releasing %d vbos' % len(self.lr_vbo))
            arr = self.lr_vbo
            glDeleteBuffers(<GLsizei>len(self.lr_vbo), arr.data.as_uints)
            del self.lr_vbo[:]
        if len(self.lr_texture):
            Logger.trace('Context: releasing %d textures: %r' % (
                len(self.lr_texture), self.lr_texture))
            arr = self.lr_texture
            glDeleteTextures(<GLsizei>len(self.lr_texture), arr.data.as_uints)
            del self.lr_texture[:]
        if len(self.lr_fbo_fb):
            Logger.trace('Context: releasing %d framebuffer fbos' % len(self.lr_fbo_fb))
            arr = self.lr_fbo_fb
            glDeleteFramebuffers(<GLsizei>len(self.lr_fbo_fb), arr.data.as_uints)
            del self.lr_fbo_fb[:]
        if len(self.lr_fbo_rb):
            Logger.trace('Context: releasing %d renderbuffer fbos' % len(self.lr_fbo_fb))
            arr = self.lr_fbo_rb
            glDeleteRenderbuffers(<GLsizei>len(self.lr_fbo_rb), arr.data.as_uints)
            del self.lr_fbo_rb[:]
        if len(self.lr_shadersource):
            Logger.trace('Context: releasing %d shader sources' % len(self.lr_shadersource))
            arr = self.lr_shadersource
            for i in self.lr_shadersource:
                glDeleteShader(i)
            del self.lr_shadersource[:]
        if len(self.lr_shader):
            Logger.trace('Context: releasing %d shaders' % len(self.lr_shader))
            for program, vs_id, fs_id in self.lr_shader:
                if vs_id != -1:
                    glDetachShader(program, vs_id)
                if fs_id != -1:
                    glDetachShader(program, fs_id)
                glDeleteProgram(program)
            del self.lr_shader[:]


cpdef Context get_context():
    global context
    if context is None:
        context = Context()
    return context

