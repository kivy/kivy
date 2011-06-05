#cython: embedsignature=True

'''
Texture management
==================

OpenGL texture can be a pain to manage ourself, except if you know perfectly all
the OpenGL API :).
'''

__all__ = ('Texture', 'TextureRegion')

include "config.pxi"

from os import environ
from array import array
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
AVAILABLE_GL_EXTENSIONS = []
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

cdef object _texture_release_trigger = None
cdef list _texture_release_list = []
cdef int _has_bgr = -1
cdef int _has_npot_support = -1
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

cdef dict _gl_color_fmt = {
    'rgba': GL_RGBA,
    'bgra': GL_BGRA,
    'rgb': GL_RGB,
    'bgr': GL_BGR,
    'luminance': GL_LUMINANCE,
    'luminance_alpha': GL_LUMINANCE_ALPHA,
}

cdef inline int _color_fmt_to_gl(str x):
    x = x.lower()
    try:
        return _gl_color_fmt[x]
    except KeyError:
        raise Exception('Unknown <%s> color format' % x)

cdef dict _gl_buffer_fmt = {
    'ubyte': GL_UNSIGNED_BYTE,
    'ushort': GL_UNSIGNED_SHORT,
    'uint': GL_UNSIGNED_INT,
    'byte': GL_BYTE,
    'short': GL_SHORT,
    'int': GL_INT,
    'float': GL_FLOAT
}

cdef inline int _buffer_fmt_to_gl(str x):
    x = x.lower()
    try:
        return _gl_buffer_fmt[x]
    except KeyError:
        raise Exception('Unknown <%s> buffer format' % x)

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

cdef dict _gl_texture_min_filter = {
    'nearest': GL_NEAREST,
    'linear': GL_LINEAR,
    'nearest_mipmap_nearest': GL_NEAREST_MIPMAP_NEAREST,
    'nearest_mipmap_linear': GL_NEAREST_MIPMAP_LINEAR,
    'linear_mipmap_nearest': GL_LINEAR_MIPMAP_NEAREST,
    'linear_mipmap_linear': GL_LINEAR_MIPMAP_LINEAR,
}

cdef inline GLuint _str_to_gl_texture_min_filter(str x):
    x = x.lower()
    try:
        return _gl_texture_min_filter[x]
    except KeyError:
        raise Exception('Unknown <%s> texture min filter' % x)

cdef inline GLuint _str_to_gl_texture_mag_filter(str x):
    x = x.lower()
    if x == 'nearest':
        return GL_NEAREST
    elif x == 'linear':
        return GL_LINEAR
    raise Exception('Unknown <%s> texture mag filter' % x)

cdef inline GLuint _str_to_gl_texture_wrap(str x):
    if x == 'clamp_to_edge':
        return GL_CLAMP_TO_EDGE
    elif x == 'repeat':
        return GL_REPEAT
    elif x == 'mirrored_repeat':
        return GL_MIRRORED_REPEAT

cdef inline int _gl_format_size(GLuint x):
    if x in (GL_RGB, GL_BGR):
        return 3
    elif x in (GL_RGBA, GL_BGRA):
        return 4
    elif x == GL_LUMINANCE_ALPHA:
        return 2
    elif x == GL_LUMINANCE:
        return 1
    raise Exception('Unsupported format size <%s>' % str(format))

cdef inline int has_bgr():
    global _has_bgr
    if _has_bgr == -1:
        _has_bgr = int(hasGLExtension('GL_EXT_bgra'))
        if not _has_bgr:
            Logger.warning('Texture: BGR/BGRA format is not supported by'
                           'your graphic card')
            Logger.warning('Texture: Software conversion will be done to'
                           'RGB/RGBA')
    return _has_bgr

cdef inline int has_npot_support():
    global _has_npot_support
    if _has_npot_support == -1:
        _has_npot_support = int(hasGLExtension('GL_ARB_texture_non_power_of_two'))
        if not _has_npot_support:
            _has_npot_support = int(hasGLExtension('OES_texture_npot'))
        if _has_npot_support:
            Logger.info('Texture: NPOT texture are supported natively')
        else:
            Logger.warning('Texture: NPOT texture are not supported natively')
    return _has_npot_support


cdef inline int _is_gl_format_supported(str x):
    if x in ('bgr', 'bgra'):
        return has_bgr()
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

cdef inline void _gl_prepare_pixels_upload(int width) nogil:
    if not (width & 0x7):
        glPixelStorei(GL_UNPACK_ALIGNMENT, 8)
    elif not (width & 0x3):
        glPixelStorei(GL_UNPACK_ALIGNMENT, 4)
    elif not (width & 0x1):
        glPixelStorei(GL_UNPACK_ALIGNMENT, 2)
    else:
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)


cdef _texture_create(int width, int height, str colorfmt, str bufferfmt, int
                     rectangle, int mipmap, int allocate):
    cdef GLuint target = GL_TEXTURE_2D
    cdef int texture_width, texture_height
    cdef int glbufferfmt = _buffer_fmt_to_gl(bufferfmt)
    cdef int npot_support = has_npot_support()

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

    if rectangle or npot_support:
        texture_width = width
        texture_height = height
    else:
        texture_width = _nearest_pow2(width)
        texture_height = _nearest_pow2(height)

    cdef GLuint texid
    glGenTextures(1, &texid)

    if not _is_gl_format_supported(colorfmt):
        colorfmt = _convert_gl_format(colorfmt)

    cdef Texture texture = Texture(texture_width, texture_height, target, texid,
                      colorfmt=colorfmt, mipmap=mipmap)

    texture.bind()
    texture.set_wrap('clamp_to_edge')
    if mipmap:
        texture.set_min_filter('linear_mipmap_nearest')
        texture.set_mag_filter('linear')
    else:
        texture.set_min_filter('linear')
        texture.set_mag_filter('linear')

    # ok, allocate memory for initial texture
    cdef int glfmt = _color_fmt_to_gl(colorfmt)
    cdef int iglbufferfmt = glbufferfmt
    cdef int datasize = texture_width * texture_height * \
            _gl_format_size(glfmt) * _buffer_type_to_gl_size(bufferfmt)
    cdef void *data = NULL
    cdef int dataerr = 0

    '''
    if glfmt == GL_RGB:
        iglbufferfmt = GL_UNSIGNED_SHORT_5_6_5
    elif glfmt == GL_RGBA:
        iglbufferfmt = GL_UNSIGNED_SHORT_4_4_4_4
    '''

    if allocate:
        texture._is_allocated = 1
        with nogil:
            data = calloc(1, datasize)
            if data != NULL:
                _gl_prepare_pixels_upload(texture_width)
                glTexImage2D(target, 0, glfmt, texture_width, texture_height, 0,
                             glfmt, iglbufferfmt, data)
                # disable the flush call. it was used for a bug in ati, but i'm
                # not sure at 100%. :) (mathieu)
                #glFlush()
                free(data)
                data = NULL
                if mipmap:
                    glGenerateMipmap(target)
            else:
                dataerr = 1

        if dataerr:
            texture._is_allocated = 0
            raise Exception('Unable to allocate memory for texture (size is %s)' %
                            datasize)

    if rectangle:
        texture.uvsize = (width, height)


    if texture_width == width and texture_height == height:
        return texture

    return texture.get_region(0, 0, width, height)

def texture_create(size=None, colorfmt=None, bufferfmt=None, rectangle=False, mipmap=False):
    '''Create a texture based on size.

    :Parameters:
        `size`: tuple, default to (128, 128)
            Size of the texture
        `colorfmt`: str, default to 'rgba'
            Internal color format of the texture. Can be 'rgba' or 'rgb',
            'luminance', 'luminance_alpha'
        `bufferfmt': str, default to 'ubyte'
            Internal buffer format of the texture. Can be 'ubyte', 'ushort',
            'uint', 'bute', 'short', 'int', 'float'
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
    if colorfmt is None:
        colorfmt = 'rgba'
    if bufferfmt is None:
        bufferfmt = 'ubyte'
    return _texture_create(width, height, colorfmt, bufferfmt, rectangle,
                           mipmap, 1)


def texture_create_from_data(im, rectangle=True, mipmap=False):
    '''Create a texture from an ImageData class'''

    cdef int width = im.width
    cdef int height = im.height
    cdef int allocate = 1

    # optimization, if the texture is power of 2, don't allocate in
    # _texture_create, but allocate in blit_data => only 1 upload
    if _is_pow2(width) and _is_pow2(height):
        allocate = 0

    texture = _texture_create(width, height, im.fmt, 'ubyte',
                             rectangle, mipmap, allocate)
    if texture is None:
        return None

    texture.blit_data(im)

    return texture

cdef class Texture:
    '''Handle a OpenGL texture. This class can be used to create simple texture
    or complex texture based on ImageData.'''

    create = staticmethod(texture_create)
    create_from_data = staticmethod(texture_create_from_data)


    def __init__(self, width, height, target, texid, colorfmt='rgb', mipmap=False, rectangle=False):
        self._width         = width
        self._height        = height
        self._target        = target
        self._id            = texid
        self._mipmap        = mipmap
        self._wrap          = None
        self._min_filter    = None
        self._mag_filter    = None
        self._is_allocated  = 0
        self._uvx           = 0.
        self._uvy           = 0.
        self._uvw           = 1.
        self._uvh           = 1.
        self._rectangle     = rectangle
        self._colorfmt      = colorfmt
        self.update_tex_coords()

    def __dealloc__(self):
        # Add texture deletion outside GC call.
        # This case happen if some texture have been not deleted
        # before application exit...
        if _texture_release_list is not None:
            _texture_release_list.append(self._id)
            if _texture_release_trigger is not None:
                _texture_release_trigger()

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

    cdef set_min_filter(self, str x):
        cdef GLuint _value = _str_to_gl_texture_min_filter(x)
        glTexParameteri(self.target, GL_TEXTURE_MIN_FILTER, _value)
        self._min_filter = x

    cdef set_mag_filter(self, str x):
        cdef GLuint _value = _str_to_gl_texture_mag_filter(x)
        glTexParameteri(self.target, GL_TEXTURE_MAG_FILTER, _value)
        self._mag_filter = x

    cdef set_wrap(self, str x):
        cdef GLuint _value = _str_to_gl_texture_wrap(x)
        glTexParameteri(self.target, GL_TEXTURE_WRAP_S, _value)
        glTexParameteri(self.target, GL_TEXTURE_WRAP_T, _value)
        self._wrap = x

    property min_filter:
        '''Get/set the min filter texture. Available values:

        - linear
        - nearest
        - linear_mipmap_linear
        - linear_mipmap_nearest
        - nearest_mipmap_nearest
        - nearest_mipmap_linear

        Check opengl documentation for more information about the behavior of
        theses values : http://www.khronos.org/opengles/sdk/docs/man/xhtml/glTexParameter.xml.
        '''
        def __get__(self):
            return self._min_filter
        def __set__(self, x):
            cdef GLuint value
            if x == self._min_filter:
                return
            self.bind()
            self.set_min_filter(x)

    property mag_filter:
        '''Get/set the mag filter texture. Available values:

        - linear
        - nearest

        Check opengl documentation for more information about the behavior of
        theses values : http://www.khronos.org/opengles/sdk/docs/man/xhtml/glTexParameter.xml.
        '''
        def __get__(self):
            return self._mag_filter
        def __set__(self, x):
            if x == self._mag_filter:
                return
            self.bind()
            self.set_mag_filter(x)

    property wrap:
        '''Get/set the wrap texture. Available values:

        - repeat
        - mirrored_repeat
        - clamp_to_edge

        Check opengl documentation for more information about the behavior of
        theses values : http://www.khronos.org/opengles/sdk/docs/man/xhtml/glTexParameter.xml.
        '''
        def __get__(self):
            return self._wrap
        def __set__(self, wrap):
            if wrap == self._wrap:
                return
            self.bind()
            self.set_wrap(wrap)

    def blit_data(self, im, pos=None):
        '''Replace a whole texture with a image data'''
        self.blit_buffer(im.data, size=(im.width, im.height),
                         colorfmt=im.fmt, pos=pos)

    def blit_buffer(self, pbuffer, size=None, colorfmt=None,
                    pos=None, bufferfmt=None):
        '''Blit a buffer into a texture.

        :Parameters:
            `pbuffer` : str
                Image data
            `size` : tuple, default to texture size
                Size of the image (width, height)
            `colorfmt` : str, default to 'rgb'
                Image format, can be one of 'rgb', 'rgba', 'bgr', 'bgra',
                'luminance', 'luminance_alpha'
            `pos` : tuple, default to (0, 0)
                Position to blit in the texture
            `bufferfmt` : str, default to 'ubyte'
                Type of the data buffer, can be one of 'ubyte', 'ushort',
                'uint', 'byte', 'short', 'int', 'float'
        '''
        cdef GLuint target = self.target
        cdef int tid = self._id
        if colorfmt is None:
            colorfmt = 'rgb'
        if bufferfmt is None:
            bufferfmt = 'ubyte'
        if pos is None:
            pos = (0, 0)
        if size is None:
            size = self.size
        bufferfmt = _buffer_fmt_to_gl(bufferfmt)

        # need conversion ?
        cdef bytes data
        data = pbuffer
        data, colorfmt = _convert_buffer(data, colorfmt)

        # prepare nogil
        cdef int glfmt = _color_fmt_to_gl(colorfmt)
        cdef int x = pos[0]
        cdef int y = pos[1]
        cdef int w = size[0]
        cdef int h = size[1]
        cdef char *cdata = <char *>data
        cdef int glbufferfmt = bufferfmt
        cdef int is_allocated = self._is_allocated

        with nogil:
            glBindTexture(target, self._id)
            _gl_prepare_pixels_upload(w)
            if is_allocated:
                glTexSubImage2D(target, 0, x, y, w, h, glfmt, glbufferfmt, cdata)
            else:
                glTexImage2D(target, 0, glfmt, w, h, 0, glfmt, glbufferfmt, cdata)
                # disable the flush call. it was used for a bug in ati, but i'm
                # not sure at 100%. :) (mathieu)
                #glFlush()

    property size:
        def __get__(self):
            return (self.width, self.height)

    def __str__(self):
        return '<Texture id=%d size=(%d, %d)>' % (
            self._id, self.width, self.height)

cdef class TextureRegion(Texture):
    '''Handle a region of a Texture class. Useful for non power-of-2
    texture handling.'''

    cdef int x
    cdef int y
    cdef Texture owner

    def __init__(self, int x, int y, int width, int height, Texture origin):
        Texture.__init__(self, width, height, origin.target, origin.id)
        self._is_allocated = 1
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

if 'KIVY_DOC_INCLUDE' not in environ:
    # install tick to release texture every 200ms
    from kivy.clock import Clock
    _texture_release_trigger = Clock.create_trigger(_texture_release)

