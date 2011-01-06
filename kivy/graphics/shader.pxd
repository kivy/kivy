
from c_opengl cimport *
from transformation cimport Matrix

cdef class Shader:
    cdef int program
    cdef int vertex_shader
    cdef int fragment_shader
    cdef object vert_src
    cdef object frag_src
    cdef dict uniform_locations
    cdef dict uniform_values

    cdef use(self)
    cdef stop(self)
    cdef set_uniform(self, str name, value)
    cdef upload_uniform(self, str name, value)
    cdef upload_uniform_matrix(self, str name, Matrix value)
    cdef int get_uniform_loc(self, str name)
    cdef bind_attrib_locations(self)
    cdef build(self)
    cdef compile_shader(self, char* source, shadertype)
    cdef get_shader_log(self, shader)
    cdef get_program_log(self, shader)
    cdef process_build_log(self)
    cdef process_message(self, str ctype, str message)


