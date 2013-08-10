from kivy.graphics.instructions cimport Instruction, Canvas
from kivy.graphics.texture cimport Texture
from kivy.graphics.vbo cimport VBO, VertexBatch
from kivy.graphics.shader cimport Shader
from kivy.graphics.fbo cimport Fbo

cdef class Context:
    cdef list observers
    cdef list observers_before
    cdef list l_texture
    cdef list l_canvas
    cdef list l_vbo
    cdef list l_vertexbatch
    cdef list l_shader
    cdef list l_fbo

    cdef object lr_texture
    cdef list lr_canvas
    cdef object lr_vbo
    cdef object lr_fbo_rb
    cdef object lr_fbo_fb

    cdef void register_texture(self, Texture texture)
    cdef void register_canvas(self, Canvas canvas)
    cdef void register_vbo(self, VBO vbo)
    cdef void register_vertexbatch(self, VertexBatch vb)
    cdef void register_shader(self, Shader shader)
    cdef void register_fbo(self, Fbo fbo)

    cdef void dealloc_texture(self, Texture texture)
    cdef void dealloc_vbo(self, VBO vbo)
    cdef void dealloc_vertexbatch(self, VertexBatch vbo)
    cdef void dealloc_shader(self, Shader shader)
    cdef void dealloc_fbo(self, Fbo fbo)

    cdef object trigger_gl_dealloc
    cdef void flush(self)

cpdef Context get_context()
