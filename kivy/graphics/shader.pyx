#cython: c_string_type=unicode, c_string_encoding=utf8
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


Single file glsl shader programs
--------------------------------

.. versionadded:: 1.6.0

To simplify shader management, the vertex and fragment shaders can be loaded 
automatically from a single glsl source file (plain text).  The file should 
contain sections identified by a line starting with '---vertex' and 
`---fragment` respectively (case insensitive) like e.g.::

    // anything before a meaningful section such as this comment are ignored

    ---VERTEX SHADER--- // vertex shader starts here
    void main(){
        ...
    }

    ---FRAGMENT SHADER--- // fragment shader starts here
    void main(){
        ...
    }

The source property of the Shader should be set tpo the filename of a glsl
shader file (of the above format), like e.g. `phong.glsl`
'''

__all__ = ('Shader', )

include "config.pxi"
include "common.pxi"

from os.path import join
from kivy.graphics.c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from kivy.graphics.c_opengl_debug cimport *
from kivy.graphics.vertex cimport vertex_attr_t
from kivy.graphics.transformation cimport Matrix
from kivy.graphics.context cimport get_context
from kivy.logger import Logger
from kivy.cache import Cache
from kivy import kivy_shader_dir


cdef str header_vs = ''
cdef str header_fs = ''
cdef str default_vs = ''
cdef str default_fs = ''
with open(join(kivy_shader_dir, 'header.vs')) as fin:
    header_vs = fin.read()
with open(join(kivy_shader_dir, 'header.fs')) as fin:
    header_fs = fin.read()
with open(join(kivy_shader_dir, 'default.vs')) as fin:
    default_vs = fin.read()
with open(join(kivy_shader_dir, 'default.fs')) as fin:
    default_fs = fin.read()


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

        Logger.debug('Shader: %s compiled successfully' % ctype.capitalize())
        self.shader = shader

    def __dealloc__(self):
        if self.shader != -1:
            glDeleteShader(self.shader)

    cdef int is_compiled(self):
        if self.shader != -1:
            return 1
        return 0

    cdef void process_message(self, str ctype, message):
        message = message.strip()
        if message:
            Logger.info('Shader: %s: <%s>' % (ctype, message))

    cdef get_shader_log(self, int shader):
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

    def __init__(self, str vs=None, str fs=None, str source=None):
        get_context().register_shader(self)
        self.program = glCreateProgram()
        if source:
            self.source = source
        else:
            self._source = None
            self.fs = fs
            self.vs = vs

    def __dealloc__(self):
        get_context().dealloc_shader(self)

    cdef void reload(self):
        # Note that we don't free previous created shaders. The current reload
        # is called only when the gl context is reseted. If we do it, we might
        # free newly created shaders (id collision)
        glUseProgram(0)
        self.vertex_shader = None
        self.fragment_shader = None
        #self.uniform_values = dict()
        self.uniform_locations = dict()
        self._success = 0
        self._current_vertex_format = None
        self.program = glCreateProgram()
        self.fs = self.fs
        self.vs = self.vs

    cdef void use(self):
        '''Use the shader
        '''
        glUseProgram(self.program)
        for k, v in self.uniform_values.iteritems():
            self.upload_uniform(k, v)
        IF USE_GLEW == 1:
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
        if name in self.uniform_values and self.uniform_values[name] == value:
            return
        self.uniform_values[name] = value
        self.upload_uniform(name, value)

    cdef void upload_uniform(self, str name, value):
        '''Pass a uniform variable to the shader
        '''
        cdef long vec_size, index, x, y
        cdef int list_size
        cdef int loc, i1, i2, i3, i4
        cdef float f1, f2, f3, f4
        cdef tuple tuple_value
        cdef list list_value
        cdef GLfloat *float_list
        cdef GLint *int_list
        val_type = type(value)
        loc = self.uniform_locations.get(name, -1)
        if loc == -1:
            loc = self.get_uniform_loc(name)

        #Logger.debug('Shader: uploading uniform %s (loc=%d, value=%r)' % (name, loc, value))
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
                else:
                    float_list = <GLfloat *>malloc(vec_size * sizeof(GLfloat))
                    if float_list is NULL:
                        raise MemoryError()
                    for index in xrange(vec_size):
                        float_list[index] = <GLfloat>list_value[index]
                    glUniform1fv(loc, <GLint>vec_size, float_list)
                    free(float_list)
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
                else:
                    int_list = <int *>malloc(vec_size * sizeof(GLint))
                    if int_list is NULL:
                        raise MemoryError()
                    for index in xrange(vec_size):
                        int_list[index] = <GLint>list_value[index]
                    glUniform1iv(loc, <GLint>vec_size, int_list)
                    free(int_list)
            elif val_type is list:
                list_size = <int>len(value)
                vec_size = len(value[0])
                val_type = type(value[0][0])
                if val_type is float:
                    float_list = <GLfloat *>malloc(
                            list_size * vec_size * sizeof(GLfloat))
                    if float_list is NULL:
                        raise MemoryError()
                    for x in xrange(list_size):
                        for y in xrange(vec_size):
                            float_list[vec_size * x + y] = <GLfloat>value[x][y]
                    if vec_size == 2:
                        glUniform2fv(loc, list_size, float_list)
                    elif vec_size == 3:
                        glUniform3fv(loc, list_size, float_list)
                    elif vec_size == 4:
                        glUniform4fv(loc, list_size, float_list)
                    else:
                        Logger.debug(
                            'Shader: unsupported {}x{} float array'.format(
                            list_size, vec_size))
                    free(float_list)
                elif val_type is int:
                    int_list = <GLint *>malloc(
                            list_size * vec_size * sizeof(GLint))
                    if int_list is NULL:
                        raise MemoryError()
                    for x in xrange(list_size):
                        for y in xrange(vec_size):
                            int_list[vec_size * x + y] = <GLint>value[x][y]
                    if vec_size == 2:
                        glUniform2iv(loc, list_size, int_list)
                    elif vec_size == 3:
                        glUniform3iv(loc, list_size, int_list)
                    elif vec_size == 4:
                        glUniform4iv(loc, list_size, int_list)
                    else:
                        Logger.debug(
                            'Shader: unsupported {}x{} int array'.format(
                            list_size, vec_size))
                    free(int_list)
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
            elif val_type is list:
                list_size = <int>len(value)
                vec_size = len(value[0])
                val_type = type(value[0][0])
                if val_type is float:
                    float_list = <GLfloat *>malloc(
                            list_size * vec_size * sizeof(GLfloat))
                    if float_list is NULL:
                        raise MemoryError()
                    for x in xrange(list_size):
                        for y in xrange(vec_size):
                            float_list[vec_size * x + y] = <GLfloat>value[x][y]
                    if vec_size == 2:
                        glUniform2fv(loc, list_size, float_list)
                    elif vec_size == 3:
                        glUniform3fv(loc, list_size, float_list)
                    elif vec_size == 4:
                        glUniform4fv(loc, list_size, float_list)
                    else:
                        Logger.debug(
                            'Shader: unsupported {}x{} float array'.format(
                            list_size, vec_size))
                    free(float_list)
                elif val_type is int:
                    int_list = <GLint *>malloc(
                            list_size * vec_size * sizeof(GLint))
                    if int_list is NULL:
                        raise MemoryError()
                    for x in xrange(list_size):
                        for y in xrange(vec_size):
                            int_list[vec_size * x + y] = <GLint>value[x][y]
                    if vec_size == 2:
                        glUniform2iv(loc, list_size, int_list)
                    elif vec_size == 3:
                        glUniform3iv(loc, list_size, int_list)
                    elif vec_size == 4:
                        glUniform4iv(loc, list_size, int_list)
                    else:
                        Logger.debug(
                            'Shader: unsupported {}x{} int array'.format(
                            list_size, vec_size))
                    free(int_list)
        else:
            raise Exception('for <%s>, type not handled <%s>' % (name, val_type))

    cdef void upload_uniform_matrix(self, int loc, Matrix value):
        cdef GLfloat mat[16]
        for x in xrange(16):
            mat[x] = <GLfloat>value.mat[x]
        glUniformMatrix4fv(loc, 1, False, mat)

    cdef int get_uniform_loc(self, str name):
        cdef bytes c_name = name.encode('utf-8')
        cdef int loc = glGetUniformLocation(self.program, c_name)
        self.uniform_locations[name] = loc
        return loc

    cdef void bind_vertex_format(self, VertexFormat vertex_format):
        cdef unsigned int i
        cdef vertex_attr_t *attr

        # if the current vertex format used in the shader is the current one, do
        # nothing.
        # the same vertex format might be used by others shaders, so the
        # attr.index would not be accurate. we need to update it as well.
        if vertex_format and self._current_vertex_format is vertex_format and \
                vertex_format.last_shader is self:
            return

        # unbind the previous vertex format
        if self._current_vertex_format:
            for i in xrange(self._current_vertex_format.vattr_count):
                attr = &self._current_vertex_format.vattr[i]
                if attr.per_vertex == 0:
                    continue
                glDisableVertexAttribArray(attr.index)

        # bind the new vertex format
        if vertex_format:
            vertex_format.last_shader = self
            for i in xrange(vertex_format.vattr_count):
                attr = &vertex_format.vattr[i]
                if attr.per_vertex == 0:
                    continue
                attr.index = glGetAttribLocation(self.program, <char *><bytes>attr.name)
                glEnableVertexAttribArray(attr.index)

        # save for the next run.
        self._current_vertex_format = vertex_format

    cdef void build(self):
        self.build_vertex()
        self.build_fragment()

    cdef void build_vertex(self, int link=1):
        if self.vertex_shader is not None:
            glDetachShader(self.program, self.vertex_shader.shader)
            self.vertex_shader = None
        self.vertex_shader = self.compile_shader(self.vert_src, GL_VERTEX_SHADER)
        if self.vertex_shader is not None:
            glAttachShader(self.program, self.vertex_shader.shader)
        if link:
            self.link_program()

    cdef void build_fragment(self, int link=1):
        if self.fragment_shader is not None:
            glDetachShader(self.program, self.fragment_shader.shader)
            self.fragment_shader = None
        self.fragment_shader = self.compile_shader(self.frag_src, GL_FRAGMENT_SHADER)
        if self.fragment_shader is not None:
            glAttachShader(self.program, self.fragment_shader.shader)
        if link:
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
        if result == GL_TRUE:
            return 1
        return 0

    cdef ShaderSource compile_shader(self, str source, int shadertype):
        cdef ShaderSource shader
        cdef str ctype, cacheid
        cdef bytes b_source = source.encode('utf-8')

        ctype = 'vertex' if shadertype == GL_VERTEX_SHADER else 'fragment'

        # try to check if the shader exist in the Cache first
        cacheid = '%s|%s' % (ctype, source)
        shader = Cache.get('kv.shader', cacheid)
        if shader is not None:
            return shader

        shader = ShaderSource(shadertype)
        shader.set_source(b_source)
        if shader.is_compiled() == 0:
            self._success = 0
            return None

        Cache.append('kv.shader', cacheid, shader)
        return shader

    cdef get_program_log(self, shader):
        '''Return the program log'''
        cdef char msg[2048]
        cdef GLsizei length
        msg[0] = '\0'
        glGetProgramInfoLog(shader, 2048, &length, msg)
        return msg[:length]

    cdef void process_message(self, str ctype, message):
        message = message.strip()
        if message:
            Logger.info('Shader: %s: <%s>' % (ctype, message))

    #
    # Python access
    #

    property source:
        '''glsl  source code.

        source shoudl be a filename of a glsl shader, that contains both
        vertex and fragment shader sourcecode;  each designated by a section
        header consisting of one line starting with either "--VERTEX" or
        "--FRAGMENT" (case insensitive).

        .. versionadded:: 1.6.0
        '''
        def __get__(self):
            return self._source
        def __set__(self, object source):
            self._source = source
            if source is None:
                self.vs = None
                self.fs = None
                return
            self.vert_src = ""
            self.frag_src = ""
            glsl_source = "\n"
            Logger.info('Shader: Read <{}>'.format(self._source))
            with open(self._source) as fin:
                glsl_source += fin.read()
            sections = glsl_source.split('\n---')
            for section in sections:
                lines = section.split('\n')
                if lines[0].lower().startswith("vertex"):
                    _vs = '\n'.join(lines[1:])
                    self.vert_src = _vs.replace('$HEADER$', header_vs)
                if lines[0].lower().startswith("fragment"):
                    _fs = '\n'.join(lines[1:])
                    self.frag_src = _fs.replace('$HEADER$', header_fs)
            self.build_vertex(0)
            self.build_fragment(0)
            self.link_program()

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
