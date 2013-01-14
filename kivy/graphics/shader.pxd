from c_opengl cimport GLuint
from transformation cimport Matrix
from vbo cimport VertexFormat

cdef class ShaderSource:
    cdef int shader
    cdef int shadertype
    cdef set_source(self, char *source)
    cdef str get_shader_log(self, int shader)
    cdef void process_message(self, str ctype, str message)
    cdef int is_compiled(self)

cdef class Shader:
    cdef object __weakref__

    cdef int _success
    cdef int program
    cdef ShaderSource vertex_shader
    cdef ShaderSource fragment_shader
    cdef object _source
    cdef object vert_src
    cdef object frag_src
    cdef dict uniform_locations
    cdef dict uniform_values

    cdef void use(self)
    cdef void stop(self)
    cdef void set_uniform(self, str name, value)
    cdef void upload_uniform(self, str name, value)
    cdef void upload_uniform_matrix(self, int loc, Matrix value)
    cdef int get_uniform_loc(self, str name)
    cdef int get_attribute_loc(self, str name)
    cdef void build(self)
    cdef void build_vertex(self, int link=*)
    cdef void build_fragment(self, int link=*)
    cdef void link_program(self)
    cdef int is_linked(self)
    cdef ShaderSource compile_shader(self, char* source, int shadertype)
    cdef str get_program_log(self, shader)
    cdef void process_message(self, str ctype, str message)
    cdef void reload(self)
