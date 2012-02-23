'''
Shader
======

The :class:`Shader` class handle the compilation of the Vertex and Fragment
shader, and the creation of the program in OpenGL.

.. todo::

    Write a more complete documentation about shader.

Header inclusion
----------------

.. versionadded:: 1.0.7

When you are creating a Shader, Kivy will always include default parameters. If
you don't want to rewrite it each time you want to customize / write a new
shader, you can add the "$HEADER$" token, and it will be replaced by the
corresponding shader header.

Here is the header for Fragment Shader:

.. include:: ../../kivy/data/glsl/header.fs
    :literal:

And the header for Vertex Shader:

.. include:: ../../kivy/data/glsl/header.vs
    :literal:

'''

__all__ = ('Shader', )

include "config.pxi"
include "common.pxi"

from os.path import join
from kivy.graphics.c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from kivy.graphics.c_opengl_debug cimport *
from kivy.graphics.vertex cimport vertex_attr_t
from kivy.graphics.vbo cimport vbo_vertex_attr_list, vbo_vertex_attr_count
from kivy.graphics.transformation cimport Matrix
from kivy.logger import Logger
from kivy.cache import Cache
from kivy import kivy_shader_dir

cdef str header_vs = open(join(kivy_shader_dir, 'header.vs')).read()
cdef str header_fs = open(join(kivy_shader_dir, 'header.fs')).read()
cdef str default_vs = open(join(kivy_shader_dir, 'default.vs')).read()
cdef str default_fs = open(join(kivy_shader_dir, 'default.fs')).read()

cdef class ShaderSource:

    def __cinit__(self, shadertype):
        self.shader = -1
        self.shadertype = shadertype

    cdef set_source(self, char *source):
        cdef GLint success = 0
        cdef GLuint error, shader
        cdef str ctype, cacheid

        # XXX to ensure that shader is ok, read error state right now.
        glGetError()

        # create and compile
        shader = glCreateShader(self.shadertype)
        glShaderSource(shader, 1, <const_char_ptr*> &source, NULL)
        glCompileShader(shader)

        # show any messages
        ctype = 'vertex' if self.shadertype == GL_VERTEX_SHADER else 'fragment'
        self.process_message('%s shader' % ctype, self.get_shader_log(shader))

        # ensure compilation is ok
        glGetShaderiv(shader, GL_COMPILE_STATUS, &success)

        if success == GL_FALSE:
            error = glGetError()
            Logger.error('Shader: <%s> failed to compile (gl:%d)' % (
                ctype, error))
            glDeleteShader(shader)
            return

        Logger.info('Shader: %s compiled successfully' % ctype)
        self.shader = shader

    def __dealloc__(self):
        if self.shader != -1:
            glDeleteShader(self.shader)

    cdef int is_compiled(self):
        if self.shader != -1:
            return 1
        return 0

    cdef void process_message(self, str ctype, str message):
        message = message.strip()
        if message:
            Logger.info('Shader: %s: <%s>' % (ctype, message))

    cdef str get_shader_log(self, int shader):
        '''Return the shader log
        '''
        cdef char msg[2048]
        msg[0] = '\0'
        glGetShaderInfoLog(shader, 2048, NULL, msg)
        return msg


cdef class Shader:
    '''Create a vertex or fragment shader

    :Parameters:
        `vs`: string, default to None
            source code for vertex shader
        `fs`: string, default to None
            source code for fragment shader
    '''
    def __cinit__(self):
        self._success = 0
        self.program = -1
        self.vertex_shader = None
        self.fragment_shader = None
        self.uniform_locations = dict()
        self.uniform_values = dict()

    def __init__(self, str vs, str fs):
        self.program = glCreateProgram()
        self.bind_attrib_locations()
        self.fs = fs
        self.vs = vs

    def __dealloc__(self):
        if self.program == -1:
            return
        if self.vertex_shader is not None:
            glDetachShader(self.program, self.vertex_shader.shader)
            self.vertex_shader = None
        if self.fragment_shader is not None:
            glDetachShader(self.program, self.fragment_shader.shader)
            self.fragment_shader = None
        glDeleteProgram(self.program)
        self.program = -1

    cdef void use(self):
        '''Use the shader
        '''
        glUseProgram(self.program)
        for k,v in self.uniform_values.iteritems():
            self.upload_uniform(k, v)
        # XXX Very very weird bug. On virtualbox / win7 / glew, if we don't call
        # glFlush or glFinish or glGetIntegerv(GL_CURRENT_PROGRAM, ...), it seem
        # that the pipeline is broken, and we have glitch issue. In order to
        # prevent that on possible other hardware, i've (mathieu) prefered to
        # include a glFlush here. However, it could be nice to know exactly what
        # is going on. Even the glGetIntegerv() is not working here. Broken
        # driver on virtualbox / win7 ????
        # FIXME maybe include that instruction for glew usage only.
        glFlush()

    cdef void stop(self):
        '''Stop using the shader
        '''
        glUseProgram(0)

    cdef void set_uniform(self, str name, value):
        self.uniform_values[name] = value
        self.upload_uniform(name, value)

    cdef void upload_uniform(self, str name, value):
        '''Pass a uniform variable to the shader
        '''
        cdef int vec_size, loc
        cdef int i1, i2, i3, i4
        cdef float f1, f2, f3, f4
        cdef tuple tuple_value
        cdef list list_value
        val_type = type(value)
        loc = self.uniform_locations.get(name, -1)
        if loc == -1:
            loc = self.get_uniform_loc(name)

        #Logger.debug('Shader: uploading uniform %s (loc=%d)' % (name, loc))
        if loc == -1:
            #Logger.debug('Shader: -> ignored')
            return
        #Logger.debug('Shader: -> (gl:%d) %s' % (glGetError(), str(value)))

        if val_type is Matrix:
            self.upload_uniform_matrix(loc, value)
        elif val_type is int:
            glUniform1i(loc, value)
        elif val_type is float:
            glUniform1f(loc, value)
        elif val_type is list:
            list_value = value
            val_type = type(list_value[0])
            vec_size = len(list_value)
            if val_type is float:
                if vec_size == 2:
                    f1, f2 = list_value
                    glUniform2f(loc, f1, f2)
                elif vec_size == 3:
                    f1, f2, f3 = list_value
                    glUniform3f(loc, f1, f2, f3)
                elif vec_size == 4:
                    f1, f2, f3, f4 = list_value
                    glUniform4f(loc, f1, f2, f3, f4)
            elif val_type is int:
                if vec_size == 2:
                    i1, i2 = list_value
                    glUniform2i(loc, i1, i2)
                elif vec_size == 3:
                    i1, i2, i3 = list_value
                    glUniform3i(loc, i1, i2, i3)
                elif vec_size == 4:
                    i1, i2, i3, i4 = list_value
                    glUniform4i(loc, i1, i2, i3, i4)
        elif val_type is tuple:
            tuple_value = value
            val_type = type(tuple_value[0])
            vec_size = len(tuple_value)
            if val_type is float:
                if vec_size == 2:
                    f1, f2 = tuple_value
                    glUniform2f(loc, f1, f2)
                elif vec_size == 3:
                    f1, f2, f3 = tuple_value
                    glUniform3f(loc, f1, f2, f3)
                elif vec_size == 4:
                    f1, f2, f3, f4 = tuple_value
                    glUniform4f(loc, f1, f2, f3, f4)
            elif val_type is int:
                if vec_size == 2:
                    i1, i2 = tuple_value
                    glUniform2i(loc, i1, i2)
                elif vec_size == 3:
                    i1, i2, i3 = tuple_value
                    glUniform3i(loc, i1, i2, i3)
                elif vec_size == 4:
                    i1, i2, i3, i4 = tuple_value
                    glUniform4i(loc, i1, i2, i3, i4)
        else:
            raise Exception('for <%s>, type not handled <%s>' % (name, val_type))

    cdef void upload_uniform_matrix(self, int loc, Matrix value):
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
        self.build_vertex()
        self.build_fragment()

    cdef void build_vertex(self):
        if self.vertex_shader is not None:
            glDetachShader(self.program, self.vertex_shader.shader)
            self.vertex_shader = None
        self.vertex_shader = self.compile_shader(self.vert_src, GL_VERTEX_SHADER)
        if self.vertex_shader is not None:
            glAttachShader(self.program, self.vertex_shader.shader)
        self.link_program()

    cdef void build_fragment(self):
        if self.fragment_shader is not None:
            glDetachShader(self.program, self.fragment_shader.shader)
            self.fragment_shader = None
        self.fragment_shader = self.compile_shader(self.frag_src, GL_FRAGMENT_SHADER)
        if self.fragment_shader is not None:
            glAttachShader(self.program, self.fragment_shader.shader)
        self.link_program()

    cdef void link_program(self):
        if self.vertex_shader is None or self.fragment_shader is None:
            return

        # XXX to ensure that shader is ok, read error state right now.
        glGetError()

        glLinkProgram(self.program)
        self.process_message('program', self.get_program_log(self.program))
        self.uniform_locations = dict()
        error = glGetError()
        if error:
            Logger.error('Shader: GL error %d' % error)
        if not self.is_linked():
            self._success = 0
            raise Exception('Shader didnt link, check info log.')
        self._success = 1

    cdef int is_linked(self):
        cdef GLint result = 0
        glGetProgramiv(self.program, GL_LINK_STATUS, &result)
        return 1 if result == GL_TRUE else 0

    cdef ShaderSource compile_shader(self, char* source, int shadertype):
        cdef ShaderSource shader
        cdef str ctype, cacheid

        ctype = 'vertex' if shadertype == GL_VERTEX_SHADER else 'fragment'

        # try to check if the shader exist in the Cache first
        cacheid = '%s|%s' % (ctype, source)
        shader = Cache.get('kv.shader', cacheid)
        if shader is not None:
            return shader

        shader = ShaderSource(shadertype)
        shader.set_source(source)
        if shader.is_compiled() == 0:
            self._success = 0
            return None

        Cache.append('kv.shader', cacheid, shader)
        return shader

    cdef str get_program_log(self, shader):
        '''Return the program log'''
        cdef char msg[2048]
        msg[0] = '\0'
        glGetProgramInfoLog(shader, 2048, NULL, msg)
        return msg

    cdef void process_message(self, str ctype, str message):
        message = message.strip()
        if message:
            Logger.info('Shader: %s: <%s>' % (ctype, message))

    #
    # Python access
    #

    property vs:
        '''Vertex shader source code.

        If you set a new vertex shader source code, it will be automatically
        compiled and replace the current one.
        '''
        def __get__(self):
            return self.vert_src
        def __set__(self, object source):
            if source is None:
                source = default_vs
            source = source.replace('$HEADER$', header_vs)
            self.vert_src = source
            self.build_vertex()

    property fs:
        '''Fragment shader source code.

        If you set a new fragment shader source code, it will be automatically
        compiled and replace the current one.
        '''
        def __get__(self):
            return self.frag_src
        def __set__(self, object source):
            if source is None:
                source = default_fs
            source = source.replace('$HEADER$', header_fs)
            self.frag_src = source
            self.build_fragment()

    property success:
        '''Indicate if shader is ok for usage or not.
        '''
        def __get__(self):
            return self._success
