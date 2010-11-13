
from c_opengl cimport *

cdef class Shader:
    cdef int program
    cdef int vertex_shader
    cdef int fragment_shader
    cdef object vert_src
    cdef object frag_src
    cdef dict uniform_locations
    cdef dict uniform_values

    cdef Shader active_shader(self)

    cdef int get_uniform_loc(self, str name)
    cpdef set_uniform(self, str name, value)
    cpdef upload_uniform(self, str name, value)
    cdef set_uniform_matrix(self, str name, value)
    cpdef use(self)
    cpdef stop(self)
    cdef bind_attrib_locations(self)
    cdef build(self)
    cdef compile_shader(self, char* source, shadertype)
    cdef get_shader_log(self, shader)
    cdef get_program_log(self, shader)
    cdef process_build_log(self)
    cdef process_message(self, str ctype, str message)
