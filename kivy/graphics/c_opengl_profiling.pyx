include "config.pxi"
cimport c_opengl as cgl

cdef int GL_BGR = 0x80E0
cdef int GL_BGRA = 0x80E1

cdef dict _gl_buffer_size = {
    cgl.GL_UNSIGNED_BYTE: sizeof(cgl.GLubyte),
    cgl.GL_UNSIGNED_SHORT: sizeof(cgl.GLushort),
    cgl.GL_UNSIGNED_INT: sizeof(cgl.GLuint),
    cgl.GL_BYTE: sizeof(cgl.GLbyte),
    cgl.GL_SHORT: sizeof(cgl.GLshort),
    cgl.GL_INT: sizeof(cgl.GLint),
    cgl.GL_FLOAT: sizeof(cgl.GLfloat)
}

cdef dict _gl_color_size = {
    cgl.GL_RGBA: 4,
    GL_BGRA: 4,
    cgl.GL_RGB: 3,
    GL_BGR: 3,
    cgl.GL_LUMINANCE: 1,
    cgl.GL_LUMINANCE_ALPHA: 2
}

cdef dict _texture_bind = {}
cdef dict _texture_memory = {}
cdef dict _buffer_bind = {}
cdef dict _buffer_memory = {}

#
# texture memory profiling
#

cdef void glBindTexture(cgl.GLenum target, cgl.GLuint texture) with gil:
    _texture_bind[target] = texture
    cgl.glBindTexture(target, texture)

cdef void glTexImage2D(cgl.GLenum target, cgl.GLint level, cgl.GLint
                       internalformat, cgl.GLsizei width, cgl.GLsizei height,
                       cgl.GLint border, cgl.GLenum format, cgl.GLenum type,
                       cgl.GLvoid* pixels) with gil:
    cdef int texid, size
    texid = _texture_bind[target]
    size = width * height * _gl_buffer_size[type] * _gl_color_size[format]
    _texture_memory[texid] = size
    cgl.glTexImage2D(target, level, internalformat, width, height, border,
                     format, type, pixels)

cdef void glDeleteTextures(cgl.GLsizei n, cgl.GLuint* textures) with gil:
    cdef int i, texid
    for i in xrange(n):
        texid = textures[i]
        _texture_memory.pop(texid, None)
    cgl.glDeleteTextures(n, textures)

#
# vbo memory profiling
#

cdef void glBindBuffer(cgl.GLenum target, cgl.GLuint buffer) with gil:
    _buffer_bind[target] = buffer
    cgl.glBindBuffer(target, buffer)

cdef void glBufferData(cgl.GLenum target, cgl.GLsizeiptr size, cgl.GLvoid* data,
                       cgl.GLenum usage) with gil:
    cdef int bufid
    bufid = _buffer_bind[target]
    _buffer_memory[bufid] = size
    cgl.glBufferData(target, size, data, usage)

cdef void glDeleteBuffers(cgl.GLsizei n, cgl.GLuint* buffers) with gil:
    cdef int i, bufid
    for i in xrange(n):
        bufid = buffers[i]
        _buffer_memory.pop(bufid, None)
    cgl.glDeleteBuffers(n, buffers)

#
# dump memory
#

def is_profiling_activated():
    ret = False
    IF USE_OPENGL_PROFILING == 1:
        ret = True
    return ret

def gpu_texture_usage():
    '''Return details about tracked memory used in GPU.
    Available keys:

        * total: return the sum of all memory eated by textures
        * count: return the number of texture currently in GPU
        * data: dictionnary of texture id <=> memory used
    '''
    return {
        'total': sum(_texture_memory.values()),
        'count': len(_texture_memory),
        'data': _texture_memory}

def gpu_buffer_usage():
    '''Return details about tracked memory used in GPU.
    Available keys:

        * total: return the sum of all memory eated by textures
        * count: return the number of texture currently in GPU
        * data: dictionnary of texture id <=> memory used
    '''
    return {
        'total': sum(_buffer_memory.values()),
        'count': len(_buffer_memory),
        'data': _buffer_memory}
