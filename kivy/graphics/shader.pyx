#cython: c_string_type=unicode, c_string_encoding=utf8
'''
Shader
======

The :class:`Shader` class handles the compilation of the vertex and fragment
shader as well as the creation of the program in OpenGL.

.. todo::

    Include more complete documentation about the shader.

Header inclusion
----------------

.. versionadded:: 1.0.7

When you are creating a Shader, Kivy will always include default parameters. If
you don't want to rewrite this each time you want to customize / write a new
shader, you can add the "$HEADER$" token and it will be replaced by the
corresponding shader header.

Here is the header for the fragment Shader:

.. include:: ../../kivy/data/glsl/header.fs
    :literal:

And the header for vertex Shader:

.. include:: ../../kivy/data/glsl/header.vs
    :literal:


Single file glsl shader programs
--------------------------------

.. versionadded:: 1.6.0

To simplify shader management, the vertex and fragment shaders can be loaded
automatically from a single glsl source file (plain text). The file should
contain sections identified by a line starting with '---vertex' and
'---fragment' respectively (case insensitive), e.g. ::

    // anything before a meaningful section such as this comment are ignored

    ---VERTEX SHADER--- // vertex shader starts here
    void main(){
        ...
    }

    ---FRAGMENT SHADER--- // fragment shader starts here
    void main(){
        ...
    }

The source property of the Shader should be set to the filename of a glsl
shader file (of the above format), e.g. `phong.glsl`
'''

__all__ = ('Shader', )

include "../include/config.pxi"
include "common.pxi"
include "gl_debug_logger.pxi"

from os.path import join

from kivy.graphics.cgl cimport *

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
        cgl.glGetError()

        # create and compile
        shader = cgl.glCreateShader(self.shadertype)
        cgl.glShaderSource(shader, 1, <const_char_ptr*> &source, NULL)
        cgl.glCompileShader(shader)

        # show any messages
        ctype = 'vertex' if self.shadertype == GL_VERTEX_SHADER else 'fragment'

        # ensure compilation is ok
        cgl.glGetShaderiv(shader, GL_COMPILE_STATUS, &success)

        if success == GL_FALSE:
            error = cgl.glGetError()
            Logger.error('Shader: <%s> failed to compile (gl:%d)' % (
                ctype, error))
            self.process_message('%s shader' % ctype, self.get_shader_log(shader))
            cgl.glDeleteShader(shader)
            return

        Logger.debug('Shader: %s compiled successfully' % ctype.capitalize())
        self.shader = shader

    def __dealloc__(self):
        if self.shader != -1:
            get_context().dealloc_shader_source(self.shader)

    cdef int is_compiled(self):
        if self.shader != -1:
            return 1
        return 0

    cdef void process_message(self, str ctype, message):
        message = message.strip()
        if message:
            Logger.info('Shader: %s: <%s>' % (ctype, message))

    cdef get_shader_log(self, int shader):
        '''Return the shader log.
        '''
        cdef char *msg
        cdef bytes py_msg
        cdef int info_length
        cgl.glGetShaderiv(shader, GL_INFO_LOG_LENGTH, &info_length)
        if info_length <= 0:
            return ""
        msg = <char *>malloc(info_length * sizeof(char))
        if msg == NULL:
            return ""
        msg[0] = "\0"
        cgl.glGetShaderInfoLog(shader, info_length, NULL, msg)
        py_msg = msg
        free(msg)
        return py_msg


cdef class Shader:
    '''Create a vertex or fragment shader.

    :Parameters:
        `vs`: string, defaults to None
            Source code for vertex shader
        `fs`: string, defaults to None
            Source code for fragment shader
    '''
    def __cinit__(self):
        self._success = 0
        self.program = 0
        self.vertex_shader = None
        self.fragment_shader = None
        self.uniform_locations = dict()
        self.uniform_values = dict()

    def __init__(self, str vs=None, str fs=None, str source=None):
        self.program = cgl.glCreateProgram()
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
        cgl.glUseProgram(0)

        # avoid shaders to be collected
        if self.vertex_shader:
            self.vertex_shader.shader = -1
            self.vertex_shader = None
        if self.fragment_shader:
            self.fragment_shader.shader = -1
            self.fragment_shader = None

        #self.uniform_values = dict()
        self.uniform_locations = dict()
        self._success = 0
        self._current_vertex_format = None
        self.program = cgl.glCreateProgram()
        self.fs = self.fs
        self.vs = self.vs

    cdef void use(self):
        '''Use the shader.
        '''
        cgl.glUseProgram(self.program)
        log_gl_error('Shader.use-glUseProgram')
        for k, v in self.uniform_values.iteritems():
            self.upload_uniform(k, v)
        if cgl_get_initialized_backend_name() == 'glew':
            # XXX Very very weird bug. On virtualbox / win7 / glew, if we don't call
            # glFlush or glFinish or glGetIntegerv(GL_CURRENT_PROGRAM, ...), it seem
            # that the pipeline is broken, and we have glitch issue. In order to
            # prevent that on possible other hardware, i've (mathieu) preferred to
            # include a glFlush here. However, it could be nice to know exactly what
            # is going on. Even the glGetIntegerv() is not working here. Broken
            # driver on virtualbox / win7 ????
            # FIXME maybe include that instruction for glew usage only.
            cgl.glFlush()

    cdef void stop(self):
        '''Stop using the shader.
        '''
        cgl.glUseProgram(0)
        log_gl_error('Shader.stop-glUseProgram')

    cdef int set_uniform(self, str name, value) except -1:
        if name in self.uniform_values and self.uniform_values[name] == value:
            return 0
        cdef GLint data
        cgl.glGetIntegerv(GL_CURRENT_PROGRAM, &data)
        log_gl_error('Shader.set_uniform-glGetIntegerv')
        if data != self.program:
            cgl.glUseProgram(self.program)
            log_gl_error('Shader.set_uniform-glUseProgram')
        self.uniform_values[name] = value
        self.upload_uniform(name, value)
        return 0

    cdef int upload_uniform(self, str name, value) except -1:
        '''Pass a uniform variable to the shader.
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
            return 0
        #Logger.debug('Shader: -> (gl:%d) %s' % (glGetError(), str(value)))

        if val_type is Matrix:
            self.upload_uniform_matrix(loc, value)
            log_gl_error('Shader.upload_uniform-glUniformMatrix4fv'
                ' {name}'.format(name=name))
        elif val_type is int:
            cgl.glUniform1i(loc, value)
            log_gl_error('Shader.upload_uniform-glUniform1i'
                ' {name}'.format(name=name))
        elif val_type is float:
            cgl.glUniform1f(loc, value)
            log_gl_error('Shader.upload_uniform-glUniform1f'
                ' {name}'.format(name=name))
        elif val_type is list:
            list_value = value
            val_type = type(list_value[0])
            vec_size = len(list_value)
            if val_type is float:
                if vec_size == 2:
                    f1, f2 = list_value
                    cgl.glUniform2f(loc, f1, f2)
                    log_gl_error('Shader.upload_uniform-glUniform2f'
                        ' {name}'.format(name=name))
                elif vec_size == 3:
                    f1, f2, f3 = list_value
                    cgl.glUniform3f(loc, f1, f2, f3)
                    log_gl_error('Shader.upload_uniform-glUniform3f'
                        ' {name}'.format(name=name))
                elif vec_size == 4:
                    f1, f2, f3, f4 = list_value
                    cgl.glUniform4f(loc, f1, f2, f3, f4)
                    log_gl_error('Shader.upload_uniform-glUniform4f'
                        ' {name}'.format(name=name))
                else:
                    float_list = <GLfloat *>malloc(vec_size * sizeof(GLfloat))
                    if float_list is NULL:
                        raise MemoryError()
                    for index in xrange(vec_size):
                        float_list[index] = <GLfloat>list_value[index]
                    cgl.glUniform1fv(loc, <GLint>vec_size, float_list)
                    log_gl_error('Shader.upload_uniform-glUniform1fv'
                        ' {name}'.format(name=name))
                    free(float_list)
            elif val_type is int:
                if vec_size == 2:
                    i1, i2 = list_value
                    cgl.glUniform2i(loc, i1, i2)
                    log_gl_error('Shader.upload_uniform-glUniform2i'
                        ' {name}'.format(name=name))
                elif vec_size == 3:
                    i1, i2, i3 = list_value
                    cgl.glUniform3i(loc, i1, i2, i3)
                    log_gl_error('Shader.upload_uniform-glUniform3i'
                        ' {name}'.format(name=name))
                elif vec_size == 4:
                    i1, i2, i3, i4 = list_value
                    cgl.glUniform4i(loc, i1, i2, i3, i4)
                    log_gl_error('Shader.upload_uniform-glUniform4i'
                        ' {name}'.format(name=name))
                else:
                    int_list = <int *>malloc(vec_size * sizeof(GLint))
                    if int_list is NULL:
                        raise MemoryError()
                    for index in xrange(vec_size):
                        int_list[index] = <GLint>list_value[index]
                    cgl.glUniform1iv(loc, <GLint>vec_size, int_list)
                    log_gl_error('Shader.upload_uniform-glUniform1iv'
                        ' {name}'.format(name=name))
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
                        cgl.glUniform2fv(loc, list_size, float_list)
                        log_gl_error('Shader.upload_uniform-glUniform2fv'
                            ' {name}'.format(name=name))
                    elif vec_size == 3:
                        cgl.glUniform3fv(loc, list_size, float_list)
                        log_gl_error('Shader.upload_uniform-glUniform3fv'
                            ' {name}'.format(name=name))
                    elif vec_size == 4:
                        cgl.glUniform4fv(loc, list_size, float_list)
                        log_gl_error('Shader.upload_uniform-glUniform4fv'
                            ' {name}'.format(name=name))
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
                        cgl.glUniform2iv(loc, list_size, int_list)
                        log_gl_error('Shader.upload_uniform-glUniform2iv'
                            ' {name}'.format(name=name))
                    elif vec_size == 3:
                        cgl.glUniform3iv(loc, list_size, int_list)
                        log_gl_error('Shader.upload_uniform-glUniform3iv'
                            ' {name}'.format(name=name))
                    elif vec_size == 4:
                        cgl.glUniform4iv(loc, list_size, int_list)
                        log_gl_error('Shader.upload_uniform-glUniform4iv'
                            ' {name}'.format(name=name))
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
                    cgl.glUniform2f(loc, f1, f2)
                    log_gl_error('Shader.upload_uniform-glUniform2f'
                        ' {name}'.format(name=name))
                elif vec_size == 3:
                    f1, f2, f3 = tuple_value
                    cgl.glUniform3f(loc, f1, f2, f3)
                    log_gl_error('Shader.upload_uniform-glUniform3f'
                        ' {name}'.format(name=name))
                elif vec_size == 4:
                    f1, f2, f3, f4 = tuple_value
                    cgl.glUniform4f(loc, f1, f2, f3, f4)
                    log_gl_error('Shader.upload_uniform-glUniform4f'
                        ' {name}'.format(name=name))
            elif val_type is int:
                if vec_size == 2:
                    i1, i2 = tuple_value
                    cgl.glUniform2i(loc, i1, i2)
                    log_gl_error('Shader.upload_uniform-glUniform2i'
                        ' {name}'.format(name=name))
                elif vec_size == 3:
                    i1, i2, i3 = tuple_value
                    cgl.glUniform3i(loc, i1, i2, i3)
                    log_gl_error('Shader.upload_uniform-glUniform3i'
                        ' {name}'.format(name=name))
                elif vec_size == 4:
                    i1, i2, i3, i4 = tuple_value
                    cgl.glUniform4i(loc, i1, i2, i3, i4)
                    log_gl_error('Shader.upload_uniform-glUniform4i'
                        ' {name}'.format(name=name))
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
                        cgl.glUniform2fv(loc, list_size, float_list)
                        log_gl_error('Shader.upload_uniform-glUniform2fv'
                            ' {name}'.format(name=name))
                    elif vec_size == 3:
                        cgl.glUniform3fv(loc, list_size, float_list)
                        log_gl_error('Shader.upload_uniform-glUniform3fv'
                            ' {name}'.format(name=name))
                    elif vec_size == 4:
                        cgl.glUniform4fv(loc, list_size, float_list)
                        log_gl_error('Shader.upload_uniform-glUniform4fv'
                            ' {name}'.format(name=name))
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
                        cgl.glUniform2iv(loc, list_size, int_list)
                        log_gl_error('Shader.upload_uniform-glUniform2iv'
                            ' {name}'.format(name=name))
                    elif vec_size == 3:
                        cgl.glUniform3iv(loc, list_size, int_list)
                        log_gl_error('Shader.upload_uniform-glUniform3iv'
                            ' {name}'.format(name=name))
                    elif vec_size == 4:
                        cgl.glUniform4iv(loc, list_size, int_list)
                        log_gl_error('Shader.upload_uniform-glUniform4iv'
                            ' {name}'.format(name=name))
                    else:
                        Logger.debug(
                            'Shader: unsupported {}x{} int array'.format(
                            list_size, vec_size))
                    free(int_list)
        else:
            raise Exception('for <%s>, type not handled <%s>' % (name, val_type))
        return 0

    cdef void upload_uniform_matrix(self, int loc, Matrix value):
        cdef GLfloat mat[16]
        for x in xrange(16):
            mat[x] = <GLfloat>value.mat[x]
        cgl.glUniformMatrix4fv(loc, 1, False, mat)

    cdef int get_uniform_loc(self, str name) except *:
        cdef bytes c_name = name.encode('utf-8')
        cdef int loc = cgl.glGetUniformLocation(self.program, c_name)
        log_gl_error(
            'Shader.get_uniform_loc-glGetUniformLocation ({name})'.format(
            name=name))
        self.uniform_locations[name] = loc
        return loc

    cdef void bind_vertex_format(self, VertexFormat vertex_format):
        cdef unsigned int i
        cdef vertex_attr_t *attr
        cdef bytes name

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
                if attr.index != <unsigned int>-1:
                  cgl.glDisableVertexAttribArray(attr.index)
                log_gl_error(
                    'Shader.bind_vertex_format-glDisableVertexAttribArray')

        # bind the new vertex format
        if vertex_format:
            vertex_format.last_shader = self
            for i in xrange(vertex_format.vattr_count):
                attr = &vertex_format.vattr[i]
                if attr.per_vertex == 0:
                    continue
                name = <bytes>attr.name
                attr.index = cgl.glGetAttribLocation(self.program, <char *>name)
                if attr.index != <unsigned int>-1:
                    cgl.glEnableVertexAttribArray(attr.index)
                log_gl_error(
                    'Shader.bind_vertex_format-glEnableVertexAttribArray')

        # save for the next run.
        self._current_vertex_format = vertex_format

    cdef int build(self) except -1:
        self.build_vertex()
        self.build_fragment()
        return 0

    cdef int build_vertex(self, int link=1) except -1:
        if self.vertex_shader is not None:
            cgl.glDetachShader(self.program, self.vertex_shader.shader)
            log_gl_error('Shader.build_vertex-glDetachShader')
            self.vertex_shader = None
        self.vertex_shader = self.compile_shader(self.vert_src, GL_VERTEX_SHADER)
        if self.vertex_shader is not None:
            cgl.glAttachShader(self.program, self.vertex_shader.shader)
            log_gl_error('Shader.build_vertex-glAttachShader')
        if link:
            self.link_program()
        return 0

    cdef int build_fragment(self, int link=1) except -1:
        if self.fragment_shader is not None:
            cgl.glDetachShader(self.program, self.fragment_shader.shader)
            log_gl_error('Shader.build_fragment-glDetachShader')
            self.fragment_shader = None
        self.fragment_shader = self.compile_shader(self.frag_src, GL_FRAGMENT_SHADER)
        if self.fragment_shader is not None:
            cgl.glAttachShader(self.program, self.fragment_shader.shader)
            log_gl_error('Shader.build_fragment-glAttachShader')
        if link:
            self.link_program()

    cdef int link_program(self) except -1:
        if self.vertex_shader is None or self.fragment_shader is None:
            return 0

        # XXX to ensure that shader is ok, read error state right now.
        cgl.glGetError()

        cgl.glLinkProgram(self.program)
        self.uniform_locations = dict()
        error = cgl.glGetError()
        if error:
            Logger.error('Shader: GL error %d' % error)
        if not self.is_linked():
            self._success = 0
            self.process_message('program', self.get_program_log(self.program))
            raise Exception('Shader didnt link, check info log.')
        self._success = 1
        return 0

    cdef int is_linked(self):
        cdef GLint result = 0
        cgl.glGetProgramiv(self.program, GL_LINK_STATUS, &result)
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
        '''Return the program log.'''
        cdef char msg[2048]
        cdef GLsizei length
        msg[0] = '\0'
        cgl.glGetProgramInfoLog(shader, 2048, &length, msg)
        # XXX don't use the msg[:length] as a string directly, or the unicode
        # will fail on shitty driver. Ie, some Intel drivers return a static
        # unitialized string of length 40, with just a content of "Success.\n\0"
        # Trying to decode data after \0 will just fail. So use bytes, and
        # convert only the part before \0.
        # XXX Also, we cannot use directly msg as a python string, as some
        # others drivers doesn't include a \0 (which is great.)
        if length == 0:
            return ""
        cdef bytes ret = msg[:length]
        return ret.split(b'\0')[0].decode('utf-8')

    cdef void process_message(self, str ctype, message):
        message = message.strip()
        if message:
            Logger.info('Shader: %s: <%s>' % (ctype, message))

    #
    # Python access
    #

    @property
    def source(self):
        '''glsl  source code.

        source should be the filename of a glsl shader that contains both the
        vertex and fragment shader sourcecode, each designated by a section
        header consisting of one line starting with either "--VERTEX" or
        "--FRAGMENT" (case insensitive).

        .. versionadded:: 1.6.0
        '''
        return self._source

    @source.setter
    def source(self, object source):
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

    @property
    def vs(self):
        '''Vertex shader source code.

        If you set a new vertex shader code source, it will be automatically
        compiled and will replace the current vertex shader.
        '''
        return self.vert_src

    @vs.setter
    def vs(self, object source):
        if source is None:
            source = default_vs
        source = source.replace('$HEADER$', header_vs)
        self.vert_src = source
        self.build_vertex()

    @property
    def fs(self):
        '''Fragment shader source code.

        If you set a new fragment shader code source, it will be automatically
        compiled and will replace the current fragment shader.
        '''
        return self.frag_src

    @fs.setter
    def fs(self, object source):
        if source is None:
            source = default_fs
        source = source.replace('$HEADER$', header_fs)
        self.frag_src = source
        self.build_fragment()

    @property
    def success(self):
        '''Indicate whether the shader loaded successfully and is ready for
        usage or not.
        '''
        return self._success
