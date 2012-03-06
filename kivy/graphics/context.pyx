'''
Context management
==================

.. versionadded:: 1.1.2

This class handle a register of all graphics instructions created, and the
ability to flush and delete them.
'''

include "config.pxi"

from os import environ
from weakref import ref
from kivy.graphics.instructions cimport Canvas
from kivy.graphics.texture cimport Texture, TextureRegion
from kivy.graphics.vbo cimport VBO, VertexBatch
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.graphics.c_opengl cimport *
from time import time
IF USE_OPENGL_DEBUG == 1:
    from kivy.graphics.c_opengl_debug cimport *
from kivy.cache import Cache

cdef Context context = None

cdef class Context:

    def __init__(self):
        self.l_texture = []
        self.l_canvas = []
        self.l_vbo = []
        self.l_vertexbatch = []
        self.l_shader = []
        self.lr_texture = []
        self.lr_canvas = []
        self.lr_vbo = []
        self.trigger_gl_dealloc = Clock.create_trigger(self.gl_dealloc, 0)

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

    cdef void dealloc_texture(self, Texture texture):
        if texture._nofree or texture.__class__ is TextureRegion:
            return
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

    cdef void flush(self):
        self.lr_texture = []
        self.lr_canvas = []
        self.lr_vbo = []

    def reload(self):
        cdef VBO vbo
        cdef VertexBatch batch
        cdef Texture texture
        cdef Shader shader
        cdef Canvas canvas

        start = time()
        Logger.info('Context: Reloading graphics data...')
        Logger.info('Context: Collect and flush all garbage')
        self.gc()
        self.flush()

        Cache.remove('kv.image')
        Cache.remove('kv.texture')
        Cache.remove('kv.shader')


        # First step, prevent double loading by setting everything to -1
        # We do this because texture might be loaded in seperate texture at first,
        # then merged from the cache cause of the same source
        Logger.info('Context: Reload textures')
        cdef list l = self.l_texture[:]
        for item in l:
            texture = item()
            if texture is None:
                continue
            texture._id = -1

        # First time, only reload base texture
        for item in l:
            texture = item()
            if texture is None or isinstance(texture, TextureRegion):
                continue
            texture.reload()

        # Second time, update texture region id
        for item in l:
            texture = item()
            if texture is None or not isinstance(texture, TextureRegion):
                continue
            texture.reload()

        Logger.info('Context: Reload vbos')
        for item in self.l_vbo[:]:
            vbo = item()
            if vbo is not None:
                Logger.info('Context: reloaded %r' % item())
                vbo.reload()
        Logger.info('Context: Reload vertex batchs')
        for item in self.l_vertexbatch[:]:
            batch = item()
            if batch is not None:
                Logger.info('Context: reloaded %r' % item())
                batch.reload()
        Logger.info('Context: Reload shaders')
        for item in self.l_shader[:]:
            shader = item()
            if shader is not None:
                Logger.info('Context: reloaded %r' % item())
                shader.reload()
        Logger.info('Context: Reload canvas')
        for item in self.l_canvas[:]:
            canvas = item()
            if canvas is not None:
                Logger.info('Context: reloaded %r' % item())
                canvas.reload()

        glFinish()
        dt = time() - start
        Logger.info('Context: Reloading done in %2.4fs' % dt)


    def gc(self, *largs):
        self.l_texture = [x for x in self.l_texture if x() is not None]
        self.l_canvas = [x for x in self.l_canvas if x() is not None]
        self.l_vbo = [x for x in self.l_vbo if x() is not None]
        self.l_vertexbatch = [x for x in self.l_vertexbatch if x() is not None]

    def gl_dealloc(self, *largs):
        # dealloc all gl resources asynchronously
        cdef GLuint i
        if len(self.lr_vbo):
            Logger.info('Context: releasing %d vbos' % len(self.lr_vbo))
            while len(self.lr_vbo):
                i = self.lr_vbo.pop()
                glDeleteBuffers(1, &i)
        if len(self.lr_texture):
            Logger.info('Context: releasing %d textures' % len(self.lr_texture))
            while len(self.lr_texture):
                i = self.lr_texture.pop()
                glDeleteTextures(1, &i)


cpdef Context get_context():
    global context
    if context is None:
        context = Context()
    return context

