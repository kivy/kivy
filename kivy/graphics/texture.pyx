#cython: embedsignature=True

'''
Texture management
==================

OpenGL texture can be a pain to manage ourself, except if you know perfectly all
the OpenGL API :).
'''

__all__ = ('Texture', 'TextureRegion')

include "config.pxi"

import os
import re
from array import array
from kivy.clock import Clock
from kivy.logger import Logger

from c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from c_opengl_debug cimport *

cdef extern from "stdlib.h":
    ctypedef unsigned long size_t
    void free(void *ptr) nogil
    void *calloc(size_t nmemb, size_t size) nogil
    void *malloc(size_t size) nogil

# XXX move missing symbol in c_opengl
# utilities
AVAILABLE_GL_EXTENSIONS = ''
def hasGLExtension( specifier ):
    '''Given a string specifier, check for extension being available
    '''
    global AVAILABLE_GL_EXTENSIONS
    cdef bytes extensions
    if not AVAILABLE_GL_EXTENSIONS:
        extensions = <char *>glGetString( GL_EXTENSIONS )
        AVAILABLE_GL_EXTENSIONS[:] = extensions.split()
    return specifier in AVAILABLE_GL_EXTENSIONS

# compatibility layer
cdef GLuint GL_BGR = 0x80E0
cdef GLuint GL_BGRA = 0x80E1

cdef list _texture_release_list = []
cdef int _has_bgr = -1
cdef int _has_texture_nv = -1
cdef int _has_texture_arb = -1

cdef inline int _nearest_pow2(int v):
    # From http://graphics.stanford.edu/~seander/bithacks.html#RoundUpPowerOf2
    # Credit: Sean Anderson
    v -= 1
    v |= v >> 1
    v |= v >> 2
    v |= v >> 4
    v |= v >> 8
    v |= v >> 16
    return v + 1

cdef inline int _is_pow2(int v):
    # http://graphics.stanford.edu/~seander/bithacks.html#DetermineIfPowerOf2
    return (v & (v - 1)) == 0

cdef inline int _fmt_to_gl_format(str x):
    x = x.lower()
    if x == 'rgba':
        return GL_RGBA
    elif x == 'bgra':
        return GL_BGRA
    elif x == 'bgr':
        return GL_BGR
    elif x == 'rgb':
        return GL_RGB
    raise Exception('Unknown <%s> texture format' % x)

cdef dict _gl_format_type = {
    'ubyte': GL_UNSIGNED_BYTE,
    'ushort': GL_UNSIGNED_SHORT,
    'uint': GL_UNSIGNED_INT,
    'byte': GL_BYTE,
    'short': GL_SHORT,
    'int': GL_INT,
    'float': GL_FLOAT
}

cdef inline int _buffer_type_to_gl_format(str x):
    x = x.lower()
    try:
        return _gl_format_type[x]
    except KeyError:
        raise Exception('Unknown <%s> format' % x)

cdef dict _gl_buffer_size = {
    'ubyte': sizeof(GLubyte),
    'ushort': sizeof(GLushort),
    'uint': sizeof(GLuint),
    'byte': sizeof(GLbyte),
    'short': sizeof(GLshort),
    'int': sizeof(GLint),
    'float': sizeof(GLfloat)
}

cdef inline int _buffer_type_to_gl_size(str x):
    x = x.lower()
    try:
        return _gl_buffer_size[x]
    except KeyError:
        raise Exception('Unknown <%s> format' % x)

cdef inline int _gl_format_size(GLuint x):
    if x in (GL_RGB, GL_BGR):
        return 3
    elif x in (GL_RGBA, GL_BGRA):
        return 4
    elif x == GL_LUMINANCE:
        return 1
    raise Exception('Unsupported format size <%s>' % str(format))

cdef inline int has_bgr():
    global _has_bgr
    if _has_bgr == -1:
        Logger.warning('Texture: BGR/BGRA format is not supported by'
                       'your graphic card')
        Logger.warning('Texture: Software conversion will be done to'
                       'RGB/RGBA')
        _has_bgr = int(hasGLExtension('GL_EXT_bgra'))
    return _has_bgr

cdef inline int _is_gl_format_supported(str x):
    if x in ('bgr', 'bgra'):
        return not has_bgr()
    return 1

cdef inline str _convert_gl_format(str x):
    if x == 'bgr':
        return 'rgb'
    elif x == 'bgra':
        return 'rgba'
    return x

cdef inline _convert_buffer(bytes data, str fmt):
    cdef bytes ret_buffer
    cdef str ret_format

    # check if format is supported by user
    ret_format = fmt
    ret_buffer = data

    # BGR / BGRA conversion not supported by hardware ?
    if not _is_gl_format_supported(fmt):
        if fmt == 'bgr':
            ret_format = 'rgb'
            a = array('b', data)
            a[0::3], a[2::3] = a[2::3], a[0::3]
            ret_buffer = a.tostring()
        elif fmt == 'bgra':
            ret_format = 'rgba'
            a = array('b', data)
            a[0::4], a[2::4] = a[2::4], a[0::4]
            ret_buffer = a.tostring()
        else:
            Logger.critical('Texture: non implemented'
                            '%s texture conversion' % fmt)
            raise Exception('Unimplemented texture conversion for %s' %
                            str(format))
    return ret_buffer, ret_format


cdef _texture_create(int width, int height, str fmt, str buffertype, int
                     rectangle, int mipmap):
    cdef GLuint target = GL_TEXTURE_2D
    cdef int texture_width, texture_height
    cdef int glbuffertype = _buffer_type_to_gl_format(buffertype)

    if mipmap:
        raise Exception('Mipmapping is not yet implemented on Kivy')

    if rectangle:
        rectangle = 0
        if not _is_pow2(width) or not _is_pow2(height):
            # Adapt this part to make it work.
            # It cannot work for OpenGL ES 2.0,
            # but for standard computer, we can gain lot of memory
            '''
            try:
                if Texture._has_texture_nv is None:
                    Texture._has_texture_nv = glInitTextureRectangleNV()
                if Texture._has_texture_nv:
                    target = GL_TEXTURE_RECTANGLE_NV
                    rectangle = 1
            except Exception:
                pass

            try:
                if Texture._has_texture_arb is None:
                    Texture._has_texture_arb = glInitTextureRectangleARB()
                if not rectangle and Texture._has_texture_arb:
                    target = GL_TEXTURE_RECTANGLE_ARB
                    rectangle = 1
            except Exception:
                pass
            '''

            # Can't do mipmap with rectangle texture
            if rectangle:
                mipmap = 0

    if rectangle:
        texture_width = width
        texture_height = height
    else:
        texture_width = _nearest_pow2(width)
        texture_height = _nearest_pow2(height)

    cdef GLuint texid
    glGenTextures(1, &texid)

    if not _is_gl_format_supported(fmt):
        fmt = _convert_gl_format(fmt)

    cdef Texture texture = Texture(texture_width, texture_height, target, texid,
                      fmt=fmt, mipmap=mipmap)

    texture.bind()
    texture.wrap = GL_CLAMP_TO_EDGE
    if mipmap:
        texture.min_filter  = GL_LINEAR_MIPMAP_LINEAR
        #texture.mag_filter  = GL_LINEAR_MIPMAP_LINEAR
        #glTexParameteri(GL_TEXTURE_2D, GL_GENERATE_MIPMAP, GL_TRUE)
    else:
        texture.min_filter  = GL_LINEAR
        texture.mag_filter  = GL_LINEAR

    # ok, allocate memory for initial texture
    cdef int glfmt = _fmt_to_gl_format(fmt)
    cdef int datasize = texture_width * texture_height * \
            _gl_format_size(glfmt) * _buffer_type_to_gl_size(buffertype)
    cdef void *data = NULL
    cdef int dataerr = 0

    with nogil:
        data = calloc(1, datasize)
        if data != NULL:
            glTexImage2D(target, 0, glfmt, texture_width, texture_height, 0,
                         glfmt, glbuffertype, data)
            glFlush()
            free(data)
            data = NULL
        else:
            dataerr = 1

    if dataerr:
        raise Exception('Unable to allocate memory for texture (size is %s)' %
                        datasize)

    if rectangle:
        texture.uvsize = (width, height)


    if texture_width == width and texture_height == height:
        return texture

    return texture.get_region(0, 0, width, height)

def texture_create(size=None, fmt=None, buffertype=None, rectangle=False, mipmap=False):
    '''Create a texture based on size.

    :Parameters:
        `size`: tuple, default to (128, 128)
            Size of the texture
        `fmt`: str, default to 'rgba'
            Internal format of the texture. Can be 'rgba' or 'rgb'
        `rectangle`: bool, default to False
            If True, it will use special opengl command for creating a rectangle
            texture. It's not available on OpenGL ES, but can be used for
            desktop. If we are on OpenGL ES platform, this parameter will be
            ignored.
        `mipmap`: bool, default to False
            If True, it will automatically generate mipmap texture.
    '''
    cdef int width, height
    if size is None:
        width = height = 128
    else:
        width, height = size
    if fmt is None:
        fmt = 'rgba'
    if buffertype is None:
        buffertype = 'ubyte'
    return _texture_create(width, height, fmt, buffertype, rectangle, mipmap)


def texture_create_from_data(im, rectangle=True, mipmap=False):
    '''Create a texture from an ImageData class'''

    texture = _texture_create(im.width, im.height, im.fmt, 'ubyte',
                             rectangle, mipmap)
    if texture is None:
        return None

    texture.blit_data(im)

    return texture

cdef class Texture:
    '''Handle a OpenGL texture. This class can be used to create simple texture
    or complex texture based on ImageData.'''

    create = staticmethod(texture_create)
    create_from_data = staticmethod(texture_create_from_data)


    def __init__(self, width, height, target, texid, fmt='rgb', mipmap=False, rectangle=False):
        self._width         = width
        self._height        = height
        self._target        = target
        self._id            = texid
        self._mipmap        = mipmap
        self._gl_wrap       = 0
        self._gl_min_filter = 0
        self._gl_mag_filter = 0
        self._uvx           = 0.
        self._uvy           = 0.
        self._uvw           = 1.
        self._uvh           = 1.
        self._rectangle     = rectangle
        self._fmt           = fmt
        self.update_tex_coords()

    def __del__(self):
        self.release()

    cdef release(self):
        # Add texture deletion outside GC call.
        # This case happen if some texture have been not deleted
        # before application exit...
        if _texture_release_list is not None:
            _texture_release_list.append(self._id)

    property mipmap:
        '''Return True if the texture have mipmap enabled (readonly)'''
        def __get__(self):
            return self._mipmap

    property rectangle:
        '''Return True if the texture is a rectangle texture (readonly)'''
        def __get__(self):
            return self._rectangle

    property id:
        '''Return the OpenGL ID of the texture (readonly)'''
        def __get__(self):
            return self._id

    property target:
        '''Return the OpenGL target of the texture (readonly)'''
        def __get__(self):
            return self._target

    property width:
        '''Return the width of the texture (readonly)'''
        def __get__(self):
            return self._width

    property height:
        '''Return the height of the texture (readonly)'''
        def __get__(self):
            return self._height

    property tex_coords:
        '''Return the list of tex_coords (opengl)'''
        def __get__(self):
            return (
                self._tex_coords[0],
                self._tex_coords[1],
                self._tex_coords[2],
                self._tex_coords[3],
                self._tex_coords[4],
                self._tex_coords[5],
                self._tex_coords[6],
                self._tex_coords[7],
            )

    property uvpos:
        '''Get/set the UV position inside texture
        '''
        def __get__(self):
            return (self._uvx, self._uvy)
        def __set__(self, x):
            self._uvx, self._uvy = x
            self.update_tex_coords()

    property uvsize:
        '''Get/set the UV size inside texture.

        .. warning::
            The size can be negative is the texture is flipped.
        '''
        def __get__(self):
            return (self._uvw, self._uvh)
        def __set__(self, x):
            self._uvw, self._uvh = x
            self.update_tex_coords()

    cdef update_tex_coords(self):
        self._tex_coords[0] = self._uvx
        self._tex_coords[1] = self._uvy
        self._tex_coords[2] = self._uvx + self._uvw
        self._tex_coords[3] = self._uvy
        self._tex_coords[4] = self._uvx + self._uvw
        self._tex_coords[5] = self._uvy + self._uvh
        self._tex_coords[6] = self._uvx
        self._tex_coords[7] = self._uvy + self._uvh

    cpdef flip_vertical(self):
        '''Flip tex_coords for vertical displaying'''
        self._uvy += self._uvh
        self._uvh = -self._uvh
        self.update_tex_coords()

    cpdef get_region(self, x, y, width, height):
        '''Return a part of the texture, from (x,y) with (width,height)
        dimensions'''
        return TextureRegion(x, y, width, height, self)

    cpdef bind(self):
        '''Bind the texture to current opengl state'''
        glBindTexture(self._target, self._id)

    cpdef enable(self):
        '''Do the appropriate glEnable()'''
        glEnable(self._target)

    cpdef disable(self):
        '''Do the appropriate glDisable()'''
        glDisable(self._target)

    property min_filter:
        '''Get/set the GL_TEXTURE_MIN_FILTER property
        '''
        def __get__(self):
            return self._gl_min_filter
        def __set__(self, x):
            if x == self._gl_min_filter:
                return
            self.bind()
            glTexParameteri(self.target, GL_TEXTURE_MIN_FILTER, x)
            self._gl_min_filter = x

    property mag_filter:
        '''Get/set the GL_TEXTURE_MAG_FILTER property
        '''
        def __get__(self):
            return self._gl_mag_filter
        def __set__(self, x):
            if x == self._gl_mag_filter:
                return
            self.bind()
            glTexParameteri(self.target, GL_TEXTURE_MAG_FILTER, x)
            self._gl_mag_filter = x

    property wrap:
        '''Get/set the GL_TEXTURE_WRAP_S,T property
        '''
        def __get__(self):
            return self._gl_wrap
        def __set__(self, wrap):
            if wrap == self._gl_wrap:
                return
            self.bind()
            glTexParameteri(self.target, GL_TEXTURE_WRAP_S, wrap)
            glTexParameteri(self.target, GL_TEXTURE_WRAP_T, wrap)

    def blit_data(self, im, pos=None):
        '''Replace a whole texture with a image data'''
        self.blit_buffer(im.data, size=(im.width, im.height),
                         fmt=im.fmt, pos=pos)

    def blit_buffer(self, pbuffer, size=None, fmt=None,
                    pos=None, buffertype=None):
        '''Blit a buffer into a texture.

        :Parameters:
            `pbuffer` : str
                Image data
            `size` : tuple, default to texture size
                Size of the image (width, height)
            `fmt` : str, default to 'rgb'
                Image format, can be one of 'rgb', 'rgba', 'bgr', 'bgra'
            `pos` : tuple, default to (0, 0)
                Position to blit in the texture
            `buffertype` : str, default to 'ubyte'
                Type of the data buffer, can be one of 'ubyte', 'ushort',
                'uint', 'byte', 'short', 'int', 'float'
        '''
        cdef GLuint target = self.target
        cdef int tid = self._id
        if fmt is None:
            fmt = 'rgb'
        if buffertype is None:
            buffertype = 'ubyte'
        if pos is None:
            pos = (0, 0)
        if size is None:
            size = self.size
        buffertype = _buffer_type_to_gl_format(buffertype)

        # need conversion ?
        cdef bytes data, pdata
        data = pbuffer
        pdata, fmt = _convert_buffer(data, fmt)

        # prepare nogil
        cdef int glfmt = _fmt_to_gl_format(fmt)
        cdef int x = pos[0]
        cdef int y = pos[1]
        cdef int w = size[0]
        cdef int h = size[1]
        cdef char *cdata = <char *>data
        cdef int glbuffertype = buffertype

        with nogil:
            glBindTexture(target, self._id)
            glEnable(target)
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glTexSubImage2D(target, 0, x, y, w, h, glfmt, glbuffertype, cdata)
            glFlush()
            glDisable(target)

    property size:
        def __get__(self):
            return (self.width, self.height)

    def __str__(self):
        return '<Texture size=(%d, %d)>' % self.size

cdef class TextureRegion(Texture):
    '''Handle a region of a Texture class. Useful for non power-of-2
    texture handling.'''

    cdef int x
    cdef int y
    cdef Texture owner

    def __init__(self, int x, int y, int width, int height, Texture origin):
        Texture.__init__(self, width, height, origin.target, origin.id)
        self.x = x
        self.y = y
        self.owner = origin

        # recalculate texture coordinate
        cdef float origin_u1, origin_v1, origin_u2, origin_v2
        origin_u1 = origin._uvx
        origin_v1 = origin._uvy
        origin_u2 = origin._uvx + origin._uvw
        origin_v2 = origin._uvy + origin._uvh
        self._uvx = (x / <float>origin._width) * origin._uvw + origin_u1
        self._uvy = (y / <float>origin._height) * origin._uvh + origin_v1
        self._uvw = (width / <float>origin._width) * origin._uvw
        self._uvh = (height / <float>origin._height) * origin._uvh
        self.update_tex_coords()

# Releasing texture through GC is problematic
# GC can happen in a middle of glBegin/glEnd
# So, to prevent that, call the _texture_release
# at flip time.
def _texture_release(*largs):
    cdef GLuint texture_id
    if not _texture_release_list:
        return
    Logger.trace('Texture: releasing %d textures' % len(_texture_release_list))
    for texture_id in _texture_release_list:
        glDeleteTextures(1, &texture_id)
    del _texture_release_list[:]

# install tick to release texture every 200ms
Clock.schedule_interval(_texture_release, 0.2)

