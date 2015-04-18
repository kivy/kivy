from c_opengl cimport GLuint
from transformation cimport Matrix
from vertex cimport VertexFormat

cdef class ShaderSource:
    cdef int shader
    cdef int shadertype
    cdef set_source(self, char *source)
    cdef get_shader_log(self, int shader)
    cdef void process_message(self, str ctype, message)
    cdef int is_compiled(self)

cdef class Shader:
    cdef object __weakref__

    cdef int _success
    cdef VertexFormat _current_vertex_format
    cdef unsigned int program
    cdef ShaderSource vertex_shader
    cdef ShaderSource fragment_shader
    cdef object _source
    cdef object vert_src
    cdef object frag_src
    cdef dict uniform_locations
    cdef dict uniform_values

    cdef void use(self)
    cdef void stop(self)
    cdef int set_uniform(self, str name, value) except -1
    cdef int upload_uniform(self, str name, value) except -1
    cdef void upload_uniform_matrix(self, int loc, Matrix value)
    cdef int get_uniform_loc(self, str name) except *
    cdef int build(self) except -1
    cdef int build_vertex(self, int link=*) except -1
    cdef int build_fragment(self, int link=*) except -1
    cdef int link_program(self) except -1
    cdef int is_linked(self)
    cdef ShaderSource compile_shader(self, str source, int shadertype)
    cdef get_program_log(self, shader)
    cdef void process_message(self, str ctype, message)
    cdef void reload(self)
    cdef void bind_vertex_format(self, VertexFormat vertex_format)
