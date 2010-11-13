from shader cimport *
from instructions cimport *

cdef class RenderContext(GraphicsGroup):
    cdef Shader shader

    def __init__(self):
        _default_vertex_shader   = open(join(kivy_shader_dir, 'default.vs')).read()
        _default_fragment_shader = open(join(kivy_shader_dir, 'default.fs')).read()
        self.shader = Shader(_default_vertex_shader, _default_fragment_shader)


    cdef apply(self):
        cdef Shader old_shader = self.shader.active_shader()
        self.shader.use()

        GraphicsGroup.apply(self)

        if old_shader:
            old_shader.use()
