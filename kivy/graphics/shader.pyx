#cython: embedsignature=True

'''
Shader
======

The :class:`Shader` class handle the compilation of the Vertex and Fragment
shader, and the creation of the program in OpenGL.

.. todo::

    Write a more complete documentation about shader.

'''

__all__ = ('Shader', )

include "config.pxi"
include "common.pxi"

from kivy.graphics.c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from kivy.graphics.c_opengl_debug cimport *
from kivy.graphics.vertex cimport vertex_attr_t
from kivy.graphics.vbo cimport vbo_vertex_attr_list, vbo_vertex_attr_count
from kivy.graphics.transformation cimport Matrix
from kivy.logger import Logger


cdef class Shader:
    '''Create a vertex or fragment shader

    :Parameters:
        `vert_src` : string
            source code for vertex shader
        `frag_src` : string
            source code for fragment shader
    '''
    def __cinit__(self):
        self.program = -1
        self.vertex_shader = -1
        self.fragment_shader = -1
        self.uniform_locations = dict()
        self.uniform_values = dict()

    def __init__(self, str vert_src, str frag_src):
        self.frag_src = frag_src
        self.vert_src = vert_src
        self.program = glCreateProgram()
        self.bind_attrib_locations()
        self.build()

    def __dealloc__(self):
        if self.program != -1:
            if self.vertex_shader != -1:
                glDetachShader(self.program, self.vertex_shader)
                glDeleteShader(self.vertex_shader)
                self.vertex_shader = -1
            if self.fragment_shader != -1:
                glDetachShader(self.program, self.fragment_shader)
                glDeleteShader(self.fragment_shader)
                self.fragment_shader = -1
            glDeleteProgram(self.program)
            self.program = -1

    cdef void use(self):
        '''Use the shader
        '''
        glUseProgram(self.program)
        for k,v in self.uniform_values.iteritems():
            self.upload_uniform(k, v)


    cdef void stop(self):
        '''Stop using the shader
        '''
        glUseProgram(0)

    cdef void set_uniform(self, str name, value):
        self.uniform_values[name] = value
        for k,v in self.uniform_values.iteritems():
            self.upload_uniform(k, v)

    cdef void upload_uniform(self, str name, value):
        '''Pass a uniform variable to the shader
        '''
        cdef int vec_size, loc
        val_type = type(value)
        loc = self.uniform_locations.get(name, self.get_uniform_loc(name))
        #Logger.trace("Shader: uploading uniform " + name +"," +str(loc) + 
        #" \n\t" +str(value) + "\n\t" + "Error " + str(glGetError()))

        if val_type == Matrix:
            self.upload_uniform_matrix(name, value)
        elif val_type == int:
            glUniform1i(loc, value)
        elif val_type == float:
            glUniform1f(loc, value)
        elif val_type in (list, tuple):
            #must have been a list, tuple, or other sequnce and be a vector uniform
            val_type = type(value[0])
            vec_size = len(value)
            if val_type == float:
                if vec_size == 2:
                    glUniform2f(loc, value[0], value[1])
                elif vec_size == 3:
                    glUniform3f(loc, value[0], value[1], value[2])
                elif vec_size == 4:
                    glUniform4f(loc, value[0], value[1], value[2], value[3])
            elif val_type == int:
                if vec_size == 2:
                    glUniform2i(loc, value[0], value[1])
                elif vec_size == 3:
                    glUniform3i(loc, value[0], value[1], value[2])
                elif vec_size == 4:
                    glUniform4i(loc, value[0], value[1], value[2], value[3])
        else:
            raise Exception('for <%s>, type not handled <%s>' % (name, val_type))

    cdef void upload_uniform_matrix(self, str name, Matrix value):
        cdef int loc = self.uniform_locations.get(name, self.get_uniform_loc(name))
        cdef GLfloat mat[16]
        for x in xrange(16):
            mat[x] = <GLfloat>value.mat[x]
        glUniformMatrix4fv(loc, 1, False, mat)


    cdef int get_uniform_loc(self, str name):
        name_byte_str = name
        cdef char* c_name = name_byte_str
        cdef int loc = glGetUniformLocation(self.program, c_name)
        self.uniform_locations[name] = loc
        return loc

    cdef void bind_attrib_locations(self):
        cdef int i
        cdef vertex_attr_t *attr
        cdef vertex_attr_t *vattr = vbo_vertex_attr_list()
        for i in xrange(vbo_vertex_attr_count()):
            attr = &vattr[i]
            glBindAttribLocation(self.program, attr.index, attr.name)
            if attr.per_vertex == 1:
                glEnableVertexAttribArray(attr.index)

    cdef void build(self):
        if self.vertex_shader != -1:
            glDetachShader(self.program, self.vertex_shader)
            glDeleteShader(self.vertex_shader)
            self.vertex_shader = -1
        if self.fragment_shader != -1:
            glDetachShader(self.program, self.fragment_shader)
            glDeleteShader(self.fragment_shader)
            self.fragment_shader = -1
        self.vertex_shader = self.compile_shader(self.vert_src, GL_VERTEX_SHADER)
        self.fragment_shader = self.compile_shader(self.frag_src, GL_FRAGMENT_SHADER)
        glAttachShader(self.program, self.vertex_shader)
        glAttachShader(self.program, self.fragment_shader)
        glLinkProgram(self.program)
        self.uniform_locations = dict()
        self.process_build_log()
        if not self.is_linked():
            raise Exception('Shader didnt link, check info log.')

    cdef int is_linked(self):
        cdef GLint result
        glGetProgramiv(self.program, GL_LINK_STATUS, &result)
        return 1 if result == GL_TRUE else 0

    cdef GLuint compile_shader(self, char* source, shadertype):
        shader = glCreateShader(shadertype)
        glShaderSource(shader, 1, <char**> &source, NULL)
        glCompileShader(shader)

        cdef GLint success
        glGetShaderiv(shader, GL_COMPILE_STATUS, &success)
        if success == GL_FALSE:
            Logger.error('Shader <%s> failed to compile' % (
                'vertex' if shadertype == GL_VERTEX_SHADER else 'fragment'))
            return -1
        return shader

    cdef str get_shader_log(self, shader):
        '''Return the shader log'''
        cdef char msg[2048]
        msg[0] = '\0'
        glGetShaderInfoLog(shader, 2048, NULL, msg)
        return msg


    cdef str get_program_log(self, shader):
        '''Return the program log'''
        cdef char msg[2048]
        msg[0] = '\0'
        glGetProgramInfoLog(shader, 2048, NULL, msg)
        return msg

    cdef void process_build_log(self):
        self.process_message('vertex shader', self.get_shader_log(self.vertex_shader))
        self.process_message('fragment shader', self.get_shader_log(self.fragment_shader))
        self.process_message('program', self.get_program_log(self.program))
        error = glGetError()
        if error:
            Logger.error('Shader: GL error %d' % error)

    cdef void process_message(self, str ctype, str message):
        message = message.strip()
        if message and message != 'Success.':
            Logger.info('Shader: %s: <%s>' % (ctype, message))
        else:
            Logger.info('Shader: %s compiled successfully' % ctype)

