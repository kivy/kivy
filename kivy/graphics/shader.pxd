
from c_opengl cimport GLuint
from transformation cimport Matrix

cdef class Shader:
    cdef int program
    cdef int vertex_shader
    cdef int fragment_shader
    cdef object vert_src
    cdef object frag_src
    cdef dict uniform_locations
    cdef dict uniform_values

    cdef void use(self)
    cdef void stop(self)
    cdef void set_uniform(self, str name, value)
    cdef void upload_uniform(self, str name, value)
    cdef void upload_uniform_matrix(self, str name, Matrix value)
    cdef int get_uniform_loc(self, str name)
    cdef void bind_attrib_locations(self)
    cdef void build(self)
    cdef GLuint compile_shader(self, char* source, shadertype)
    cdef str get_shader_log(self, shader)
    cdef str get_program_log(self, shader)
    cdef void process_build_log(self)
    cdef void process_message(self, str ctype, str message)


