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
from kivy import Logger
from buffer cimport Buffer
from c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from c_opengl_debug cimport *

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
GL_BGR = 0x80E0
GL_BGRA = 0x80E1

cdef list _texture_release_list = []
cdef int _has_bgr = -1
cdef int _has_texture_nv = -1
cdef int _has_texture_arb = -1

cdef int _nearest_pow2(int v):
    # From http://graphics.stanford.edu/~seander/bithacks.html#RoundUpPowerOf2
    # Credit: Sean Anderson
    v -= 1
    v |= v >> 1
    v |= v >> 2
    v |= v >> 4
    v |= v >> 8
    v |= v >> 16
    return v + 1

cdef int _is_pow2(int v):
    # http://graphics.stanford.edu/~seander/bithacks.html#DetermineIfPowerOf2
    return (v & (v - 1)) == 0

cdef _fmt_to_gl_format(str x):
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

cdef _buffer_type_to_gl_format(str x):
    x = x.lower()
    try:
        return {
            'ubyte': GL_UNSIGNED_BYTE,
            'ushort': GL_UNSIGNED_SHORT,
            'uint': GL_UNSIGNED_INT,
            'byte': GL_BYTE,
            'short': GL_SHORT,
            'int': GL_INT,
            'float': GL_FLOAT
        }[x]
    except KeyError:
        raise Exception('Unknown <%s> format' % x)

cdef _gl_format_size(GLuint x):
    if x in (GL_RGB, GL_BGR):
        return 3
    elif x in (GL_RGBA, GL_BGRA):
        return 4
    elif x in (GL_LUMINANCE, ):
        return 1
    raise Exception('Unsupported format size <%s>' % str(format))

cdef int has_bgr():
    global _has_bgr
    if _has_bgr == -1:
        Logger.warning('Texture: BGR/BGRA format is not supported by'
                       'your graphic card')
        Logger.warning('Texture: Software conversion will be done to'
                       'RGB/RGBA')
        _has_bgr = int(hasGLExtension('GL_EXT_bgra'))
    return _has_bgr

cdef int _is_gl_format_supported(str x):
    if x in ('bgr', 'bgra'):
        return not has_bgr()
    return 1

cdef str _convert_gl_format(str x):
    if x == 'bgr':
        return 'rgb'
    elif x == 'bgra':
        return 'rgba'
    return x

cdef _convert_buffer(Buffer data, str fmt):
    # check if format is supported by user
    ret_format = fmt
    ret_buffer = data

    # BGR / BGRA conversion not supported by hardware ?
    if not _is_gl_format_supported(fmt):
        if fmt == 'bgr':
            ret_format = 'rgb'
            a = array('b', data)
            a[0::3], a[2::3] = a[2::3], a[0::3]
            a = a.tostring()
            ret_buffer = Buffer(len(a))
            ret_buffer.add(a)
        elif fmt == 'bgra':
            ret_format = 'rgba'
            a = array('b', data)
            a[0::4], a[2::4] = a[2::4], a[0::4]
            a = a.tostring()
            ret_buffer = Buffer(len(a))
            ret_buffer.add(a)
        else:
            Logger.critical('Texture: non implemented'
                            '%s texture conversion' % fmt)
            raise Exception('Unimplemented texture conversion for %s' %
                            str(format))
    return ret_buffer, ret_format


cdef _texture_create(int width, int height, str fmt, int rectangle, int mipmap):
    cdef GLuint target = GL_TEXTURE_2D
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

    texture = Texture(texture_width, texture_height, target, texid,
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

    cdef int glfmt = _fmt_to_gl_format(fmt)
    cdef Buffer data
    data = Buffer(sizeof(GLubyte) * texture_width * texture_height *
            _gl_format_size(glfmt))
    glTexImage2D(target, 0, glfmt, texture_width, texture_height, 0,
                 glfmt, GL_UNSIGNED_BYTE, data.pointer())

    if rectangle:
        texture.tex_coords = \
            (0., 0., width, 0., width, height, 0., height)

    glFlush()

    if texture_width == width and texture_height == height:
        return texture

    return texture.get_region(0, 0, width, height)

def texture_create(size=(128, 128), fmt='rgba', rectangle=False, mipmap=False):
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
    width, height = size
    return _texture_create(width, height, fmt, rectangle, mipmap)


def texture_create_from_data(im, rectangle=True, mipmap=False):
    '''Create a texture from an ImageData class'''

    texture = _texture_create(im.width, im.height, im.fmt,
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
        self.tex_coords     = (0., 0., 1., 0., 1., 1., 0., 1.)
        self._width         = width
        self._height        = height
        self._target        = target
        self._id            = texid
        self._mipmap        = mipmap
        self._gl_wrap       = 0
        self._gl_min_filter = 0
        self._gl_mag_filter = 0
        self._rectangle     = rectangle
        self._fmt           = fmt

    def __del__(self):
        # Add texture deletion outside GC call.
        # This case happen if some texture have been not deleted
        # before application exit...
        if _texture_release_list is not None:
            _texture_release_list.append(self.id)

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

    cpdef flip_vertical(self):
        '''Flip tex_coords for vertical displaying'''
        a, b, c, d, e, f, g, h = self.tex_coords
        self.tex_coords = (g, h, e, f, c, d, a, b)

    cpdef get_region(self, x, y, width, height):
        '''Return a part of the texture, from (x,y) with (width,height)
        dimensions'''
        return TextureRegion(x, y, width, height, self)

    cpdef bind(self):
        '''Bind the texture to current opengl state'''
        glBindTexture(self.target, self.id)

    cpdef enable(self):
        '''Do the appropriate glEnable()'''
        glEnable(self.target)

    cpdef disable(self):
        '''Do the appropriate glDisable()'''
        glDisable(self.target)

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

    def blit_data(self, im, pos=(0, 0)):
        '''Replace a whole texture with a image data'''
        self.blit_buffer(im.data, size=(im.width, im.height),
                         fmt=im.fmt, pos=pos)

    def blit_buffer(self, pbuffer, size=None, fmt='rgb',
                    pos=(0, 0), buffertype='ubyte'):
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
        if size is None:
            size = self.size
        buffertype = _buffer_type_to_gl_format(buffertype)
        target = self.target
        glBindTexture(target, self.id)
        glEnable(target)

        # activate 1 alignement, of window failed on updating weird size
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

        # need conversion ?
        cdef Buffer data, pdata
        data = Buffer(len(pbuffer))
        cdef bytes bbuffer
        bbuffer = pbuffer
        data.add(<char *>bbuffer, NULL, 1)
        pdata, fmt = _convert_buffer(data, fmt)
        glfmt = _fmt_to_gl_format(fmt)

        # transfer the new part of texture
        glTexSubImage2D(target, 0, pos[0], pos[1],
                        size[0], size[1], glfmt,
                        buffertype, pdata.pointer())

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
        origin_u1 = origin.tex_coords[0]
        origin_v1 = origin.tex_coords[1]
        origin_u2 = origin.tex_coords[2]
        origin_v2 = origin.tex_coords[5]
        scale_u = origin_u2 - origin_u1
        scale_v = origin_v2 - origin_v1
        u1 = x / float(origin.width) * scale_u + origin_u1
        v1 = y / float(origin.height) * scale_v + origin_v1
        u2 = (x + width) / float(origin.width) * scale_u + origin_u1
        v2 = (y + height) / float(origin.height) * scale_v + origin_v1
        self.tex_coords = (u1, v1, u2, v1, u2, v2, u1, v2)

    def __del__(self):
        # don't use self of owner !
        pass

'''
if 'KIVY_DOC' not in os.environ:
    from kivy.clock import Clock

    # Releasing texture through GC is problematic
    # GC can happen in a middle of glBegin/glEnd
    # So, to prevent that, call the _texture_release
    # at flip time.
    def _texture_release(*largs):
        cdef GLuint texture_id
        for texture_id in _texture_release_list:
            glDeleteTextures(1, &texture_id)
        del _texture_release_list[:]

    # install tick to release texture every 200ms
    Clock.schedule_interval(_texture_release, 0.2)
'''
