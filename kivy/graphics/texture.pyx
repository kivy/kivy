'''
Texture
=======

:class:`Texture` is a class to handle OpenGL texture. Depending of the hardware,
some OpenGL capabilities might not be available (BGRA support, NPOT support,
etc.)

You cannot instanciate the class yourself. You must use the function
:func:`Texture.create` to create a new texture::

    texture = Texture.create(size=(640, 480))

When you are creating a texture, you must be aware of the default color format
and buffer format:

    - the color/pixel format (:data:`Texture.colorfmt`), that can be one of
      'rgb', 'rgba', 'luminance', 'luminance_alpha', 'bgr', 'bgra'. The default
      value is 'rgb'
    - the buffer format is how a color component is stored into memory. This can
      be one of 'ubyte', 'ushort', 'uint', 'byte', 'short', 'int', 'float'. The
      default value and the most commonly used is 'ubyte'.

So, if you want to create an RGBA texture::

    texture = Texture.create(size=(640, 480), colorfmt='rgba')

You can use your texture in almost all vertex instructions with the
:data:`kivy.graphics.VertexIntruction.texture` parameter. If you want to use
your texture in kv lang, you can save it in an
:class:`~kivy.properties.ObjectProperty` inside your widget.


Blitting custom data
--------------------

You can create your own data and blit it on the texture using
:func:`Texture.blit_data`::

    # create a 64x64 texture, default to rgb / ubyte
    texture = Texture.create(size=(64, 64))

    # create 64x64 rgb tab, and fill with value from 0 to 255
    # we'll have a gradient from black to white
    size = 64 * 64 * 3
    buf = [int(x * 255 / size) for x in xrange(size)]

    # then, convert the array to a ubyte string
    buf = ''.join(map(chr, buf))

    # then blit the buffer
    texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')

    # that's all ! you can use it in your graphics now :)
    # if self is a widget, you can do that
    with self.canvas:
        Rectangle(texture=texture, pos=self.pos, size=(64, 64))


BGR/BGRA support
----------------

The first time you'll try to create a BGR or BGRA texture, we are checking if
your hardware support BGR / BGRA texture by checking the extension
'GL_EXT_bgra'.

If the extension is not found, a conversion to RGB / RGBA will be done in
software.


NPOT texture
------------

.. versionadded:: 1.0.7

    If hardware can support NPOT, no POT are created.

As OpenGL documentation said, a texture must be power-of-two sized. That's mean
your width and height can be one of 64, 32, 256... but not 3, 68, 42. NPOT mean
non-power-of-two. OpenGL ES 2 support NPOT texture natively, but with some
drawbacks. Another type of NPOT texture are also called rectangle texture.
POT, NPOT and texture have their own pro/cons.

================= ============= ============= =================================
    Features           POT           NPOT                Rectangle
----------------- ------------- ------------- ---------------------------------
OpenGL Target     GL_TEXTURE_2D GL_TEXTURE_2D GL_TEXTURE_RECTANGLE_(NV|ARB|EXT)
Texture coords    0-1 range     0-1 range     width-height range
Mipmapping        Supported     Partially     No
Wrap mode         Supported     Supported     No
================= ============= ============= =================================

If you are creating a NPOT texture, we first are checking if your hardware is
capable of it by checking the extensions GL_ARB_texture_non_power_of_two or
OES_texture_npot. If none of theses are availables, we are creating the nearest
POT texture that can contain your NPOT texture. The :func:`Texture.create` will
return a :class:`TextureRegion` instead.


Texture atlas
-------------

We are calling texture atlas a texture that contain many images in it.
If you want to seperate the original texture into many single one, you don't
need to. You can get a region of the original texture. That will return you the
original texture with custom texture coordinates::

    # for example, load a 128x128 image that contain 4 64x64 images
    from kivy.core.image import Image
    texture = Image('mycombinedimage.png').texture

    bottomleft = texture.get_region(0, 0, 64, 64)
    bottomright = texture.get_region(0, 64, 64, 64)
    topleft = texture.get_region(0, 64, 64, 64)
    topright = texture.get_region(64, 64, 64, 64)


.. _mipmap:

Mipmapping
----------

.. versionadded:: 1.0.7

Mipmapping is an OpenGL technique for enhancing the rendering of large texture
to small surface. Without mipmapping, you might seen pixels when you are
rendering to small surface.
The idea is to precalculate subtexture and apply some image filter, as linear
filter. Then, when you rendering a small surface, instead of using the biggest
texture, it will use a lower filtered texture. The result can look better with
that way.

To make that happen, you need to specify mipmap=True when you're creating a
texture. Some widget already give you the possibility to create mipmapped
texture like :class:`~kivy.uix.label.Label` or :class:`~kivy.uix.image.Image`.

From the OpenGL Wiki : "So a 64x16 2D texture can have 5 mip-maps: 32x8, 16x4,
8x2, 4x1, 2x1, and 1x1". Check http://www.opengl.org/wiki/Texture for more
information.

.. note::

    As the table in previous section said, if your texture is NPOT, we are
    actually creating the nearest POT texture and generate mipmap on it. This
    might change in the future.

'''

__all__ = ('Texture', 'TextureRegion')

include "config.pxi"
include "common.pxi"
include "opengl_utils_def.pxi"

from os import environ
from array import array
from kivy.logger import Logger

from c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from c_opengl_debug cimport *
from opengl_utils cimport *

# compatibility layer
cdef GLuint GL_BGR = 0x80E0
cdef GLuint GL_BGRA = 0x80E1
cdef GLuint GL_COMPRESSED_RGBA_S3TC_DXT1_EXT = 0x83F1
cdef GLuint GL_COMPRESSED_RGBA_S3TC_DXT3_EXT = 0x83F2
cdef GLuint GL_COMPRESSED_RGBA_S3TC_DXT5_EXT = 0x83F3

cdef object _texture_release_trigger = None
cdef list _texture_release_list = []

cdef dict _gl_color_fmt = {
    'rgba': GL_RGBA, 'bgra': GL_BGRA, 'rgb': GL_RGB, 'bgr': GL_BGR,
    'luminance': GL_LUMINANCE, 'luminance_alpha': GL_LUMINANCE_ALPHA,
    's3tc_dxt1': GL_COMPRESSED_RGBA_S3TC_DXT1_EXT,
    's3tc_dxt3': GL_COMPRESSED_RGBA_S3TC_DXT3_EXT,
    's3tc_dxt5': GL_COMPRESSED_RGBA_S3TC_DXT5_EXT }

cdef dict _gl_buffer_fmt = {
    'ubyte': GL_UNSIGNED_BYTE, 'ushort': GL_UNSIGNED_SHORT,
    'uint': GL_UNSIGNED_INT, 'byte': GL_BYTE,
    'short': GL_SHORT, 'int': GL_INT, 'float': GL_FLOAT }

cdef dict _gl_buffer_size = {
    'ubyte': sizeof(GLubyte), 'ushort': sizeof(GLushort),
    'uint': sizeof(GLuint), 'byte': sizeof(GLbyte),
    'short': sizeof(GLshort), 'int': sizeof(GLint),
    'float': sizeof(GLfloat) }

cdef dict _gl_texture_min_filter = {
    'nearest': GL_NEAREST, 'linear': GL_LINEAR,
    'nearest_mipmap_nearest': GL_NEAREST_MIPMAP_NEAREST,
    'nearest_mipmap_linear': GL_NEAREST_MIPMAP_LINEAR,
    'linear_mipmap_nearest': GL_LINEAR_MIPMAP_NEAREST,
    'linear_mipmap_linear': GL_LINEAR_MIPMAP_LINEAR }



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


cdef inline int _color_fmt_to_gl(str x):
    '''Return the GL numeric value from a color string format
    '''
    x = x.lower()
    try:
        return _gl_color_fmt[x]
    except KeyError:
        raise Exception('Unknown <%s> color format' % x)


cdef inline int _is_compressed_fmt(str x):
    '''Return 1 if the color string format is a compressed one
    '''
    return x.startswith('s3tc_dxt')


cdef inline int _buffer_fmt_to_gl(str x):
    '''Return the GL numeric value from a buffer string format
    '''
    x = x.lower()
    try:
        return _gl_buffer_fmt[x]
    except KeyError:
        raise Exception('Unknown <%s> buffer format' % x)


cdef inline int _buffer_type_to_gl_size(str x):
    '''Return the size of a buffer string format in bytes
    '''
    x = x.lower()
    try:
        return _gl_buffer_size[x]
    except KeyError:
        raise Exception('Unknown <%s> format' % x)


cdef inline GLuint _str_to_gl_texture_min_filter(str x):
    '''Return the GL numeric value from a texture min filter string
    '''
    x = x.lower()
    try:
        return _gl_texture_min_filter[x]
    except KeyError:
        raise Exception('Unknown <%s> texture min filter' % x)


cdef inline GLuint _str_to_gl_texture_mag_filter(str x):
    '''Return the GL numeric value from a texture mag filter string
    '''
    x = x.lower()
    if x == 'nearest':
        return GL_NEAREST
    elif x == 'linear':
        return GL_LINEAR
    raise Exception('Unknown <%s> texture mag filter' % x)


cdef inline GLuint _str_to_gl_texture_wrap(str x):
    '''Return the GL numeric value from a texture wrap string
    '''
    if x == 'clamp_to_edge':
        return GL_CLAMP_TO_EDGE
    elif x == 'repeat':
        return GL_REPEAT
    elif x == 'mirrored_repeat':
        return GL_MIRRORED_REPEAT


cdef inline int _gl_format_size(GLuint x):
    '''Return the GL numeric value from a texture wrap string
    '''
    if x in (GL_RGB, GL_BGR):
        return 3
    elif x in (GL_RGBA, GL_BGRA):
        return 4
    elif x == GL_LUMINANCE_ALPHA:
        return 2
    elif x == GL_LUMINANCE:
        return 1
    elif x in (GL_COMPRESSED_RGBA_S3TC_DXT1_EXT,
            GL_COMPRESSED_RGBA_S3TC_DXT3_EXT,
            GL_COMPRESSED_RGBA_S3TC_DXT5_EXT):
        return 4
    raise Exception('Unsupported format size <%s>' % str(format))


cdef inline int _is_gl_format_supported(str x):
    if x in ('bgr', 'bgra'):
        return gl_has_capability(GLCAP_BGRA)
    elif x == 's3tc_dxt1':
        return gl_has_capability(GLCAP_DXT1)
    elif x.startswith('s3tc_dxt'):
        return gl_has_capability(GLCAP_S3TC)
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

    # if native support of this format is available, use it
    if gl_has_texture_native_format(fmt):
        return data, fmt

    # no native support, can we at least convert it ?
    if not gl_has_texture_conversion(fmt):
        raise Exception('Unimplemented texture conversion for %s' % fmt)

    # do appropriate conversion, since we accepted it
    ret_format = fmt
    ret_buffer = data

    # BGR -> RGB
    if fmt == 'bgr':
        ret_format = 'rgb'
        a = array('b', data)
        a[0::3], a[2::3] = a[2::3], a[0::3]
        ret_buffer = a.tostring()

    # BGRA -> RGBA
    elif fmt == 'bgra':
        ret_format = 'rgba'
        a = array('b', data)
        a[0::4], a[2::4] = a[2::4], a[0::4]
        ret_buffer = a.tostring()

    else:
        assert False, 'Non implemented texture conversion !' % fmt

    return ret_buffer, ret_format


cdef inline void _gl_prepare_pixels_upload(int width) nogil:
    '''Set the best pixel alignement for the current width
    '''
    if not (width & 0x7):
        glPixelStorei(GL_UNPACK_ALIGNMENT, 8)
    elif not (width & 0x3):
        glPixelStorei(GL_UNPACK_ALIGNMENT, 4)
    elif not (width & 0x1):
        glPixelStorei(GL_UNPACK_ALIGNMENT, 2)
    else:
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)


cdef _texture_create(int width, int height, str colorfmt, str bufferfmt,
                     int mipmap, int allocate):
    '''Create the OpenGL texture.
    '''
    cdef GLuint target = GL_TEXTURE_2D
    cdef GLuint texid = 0
    cdef Texture texture
    cdef int texture_width, texture_height
    cdef int glbufferfmt = _buffer_fmt_to_gl(bufferfmt)
    cdef int make_npot = 0
    cdef int glfmt, iglbufferfmt, datasize, dataerr = 0
    cdef void *data = NULL

    # check if it's a pot or not
    if not _is_pow2(width) or not _is_pow2(height):
        make_npot = 1

    # in case of mipmap is asked for npot texture, make it pot compatible
    if mipmap:
        make_npot = 0

    # depending if npot is available, use the real size or pot size
    if make_npot and gl_has_capability(GLCAP_NPOT):
        texture_width = width
        texture_height = height
    else:
        texture_width = _nearest_pow2(width)
        texture_height = _nearest_pow2(height)

    # generate the texture
    glGenTextures(1, &texid)

    # if the color format is not supported, create the texture with the future
    # color format.
    if not _is_gl_format_supported(colorfmt):
        colorfmt = _convert_gl_format(colorfmt)

    texture = Texture(texture_width, texture_height, target, texid,
                      colorfmt=colorfmt, mipmap=mipmap)

    # set default parameter for this texture
    texture.bind()
    texture.set_wrap('clamp_to_edge')
    if mipmap:
        texture.set_min_filter('linear_mipmap_nearest')
        texture.set_mag_filter('linear')
    else:
        texture.set_min_filter('linear')
        texture.set_mag_filter('linear')

    # if allocation if wanted, do it now
    if allocate:

        # prepare information needed for nogil
        glfmt = _color_fmt_to_gl(colorfmt)
        iglbufferfmt = glbufferfmt
        datasize = texture_width * texture_height * \
                _gl_format_size(glfmt) * _buffer_type_to_gl_size(bufferfmt)

        # act as we have been able to allocate the texture
        texture._is_allocated = 1

        # do the rest outside the Python GIL
        with nogil:
            data = calloc(1, datasize)
            if data != NULL:
                # ensure pixel upload is correct
                _gl_prepare_pixels_upload(texture_width)

                # do the initial upload with fake data
                glTexImage2D(target, 0, glfmt, texture_width, texture_height, 0,
                             glfmt, iglbufferfmt, data)

                # free the data !
                free(data)

                # create mipmap if needed
                if mipmap:
                    glGenerateMipmap(target)
            else:
                dataerr = 1

        if dataerr:
            texture._is_allocated = 0
            raise Exception('Unable to allocate memory for texture (size is %s)' %
                            datasize)

    # if the texture size is the same as initial size, return the texture
    # unmodified
    if texture_width == width and texture_height == height:
        return texture

    # otherwise, return a region of that texture
    return texture.get_region(0, 0, width, height)


def texture_create(size=None, colorfmt=None, bufferfmt=None, mipmap=False):
    '''Create a texture based on size.

    :Parameters:
        `size`: tuple, default to (128, 128)
            Size of the texture
        `colorfmt`: str, default to 'rgba'
            Internal color format of the texture. Can be 'rgba' or 'rgb',
            'luminance', 'luminance_alpha'
        `bufferfmt`: str, default to 'ubyte'
            Internal buffer format of the texture. Can be 'ubyte', 'ushort',
            'uint', 'bute', 'short', 'int', 'float'
        `mipmap`: bool, default to False
            If True, it will automatically generate mipmap texture.

    '''
    cdef int width = 128, height = 128
    if size is not None:
        width, height = size
    if colorfmt is None:
        colorfmt = 'rgba'
    if bufferfmt is None:
        bufferfmt = 'ubyte'
    return _texture_create(width, height, colorfmt, bufferfmt, mipmap, 1)


def texture_create_from_data(im, mipmap=False):
    '''Create a texture from an ImageData class
    '''

    cdef int width = im.width
    cdef int height = im.height
    cdef int allocate = 1

    # optimization, if the texture is power of 2, don't allocate in
    # _texture_create, but allocate in blit_data => only 1 upload
    if _is_pow2(width) and _is_pow2(height):
        allocate = 0

    # if imagedata have more than one image, activate mipmap
    if im.have_mipmap:
        mipmap = True

    texture = _texture_create(width, height, im.fmt, 'ubyte', mipmap, allocate)
    if texture is None:
        return None

    texture.blit_data(im)

    return texture


cdef class Texture:
    '''Handle a OpenGL texture. This class can be used to create simple texture
    or complex texture based on ImageData.'''

    create = staticmethod(texture_create)
    create_from_data = staticmethod(texture_create_from_data)

    def __init__(self, width, height, target, texid, colorfmt='rgb',
                 mipmap=False):
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
        glTexParameteri(self._target, GL_TEXTURE_MIN_FILTER, _value)
        self._min_filter = x

    cdef set_mag_filter(self, str x):
        cdef GLuint _value = _str_to_gl_texture_mag_filter(x)
        glTexParameteri(self._target, GL_TEXTURE_MAG_FILTER, _value)
        self._mag_filter = x

    cdef set_wrap(self, str x):
        cdef GLuint _value = _str_to_gl_texture_wrap(x)
        glTexParameteri(self._target, GL_TEXTURE_WRAP_S, _value)
        glTexParameteri(self._target, GL_TEXTURE_WRAP_T, _value)
        self._wrap = x


    def blit_data(self, im, pos=None):
        '''Replace a whole texture with a image data
        '''
        blit = self.blit_buffer

        # depending if imagedata have mipmap, think different.
        if not im.have_mipmap:
            blit(im.data, size=im.size, colorfmt=im.fmt, pos=pos)
        else:
            # upload each level
            for level, width, height, data in im.iterate_mipmaps():
                blit(data, size=(width, height),
                     colorfmt=im.fmt, pos=pos,
                     mipmap_level=level, mipmap_generation=False)

    def blit_buffer(self, pbuffer, size=None, colorfmt=None,
                    pos=None, bufferfmt=None, mipmap_level=0,
                    mipmap_generation=True):
        '''Blit a buffer into a texture.

        .. versionadded:: 1.0.7 added mipmap_level + mipmap_generation

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
            `mipmap_level`: int, default to 0
                Indicate which mipmap level we are going to update
            `mipmap_generation`: bool, default to False
                Indicate if we need to regenerate mipmap from level 0
        '''
        cdef GLuint target = self._target
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
        cdef int datasize = len(pbuffer)
        cdef int x = pos[0]
        cdef int y = pos[1]
        cdef int w = size[0]
        cdef int h = size[1]
        cdef char *cdata = <char *>data
        cdef int glbufferfmt = bufferfmt
        cdef int is_allocated = self._is_allocated
        cdef int is_compressed = _is_compressed_fmt(colorfmt)
        cdef int _mipmap_generation = mipmap_generation and self._mipmap
        cdef int _mipmap_level = mipmap_level

        with nogil:
            glBindTexture(target, self._id)
            if is_compressed:
                glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
                glCompressedTexImage2D(target, _mipmap_level, glfmt, w, h, 0, datasize, cdata)
            elif is_allocated:
                _gl_prepare_pixels_upload(w)
                glTexSubImage2D(target, _mipmap_level, x, y, w, h, glfmt, glbufferfmt, cdata)
            else:
                _gl_prepare_pixels_upload(w)
                glTexImage2D(target, _mipmap_level, glfmt, w, h, 0, glfmt, glbufferfmt, cdata)
            if _mipmap_generation:
                glGenerateMipmap(target)

    def __str__(self):
        return '<Texture id=%d size=(%d, %d)>' % (
            self._id, self.width, self.height)

    property size:
        '''Return the (width, height) of the texture (readonly)
        '''
        def __get__(self):
            return (self.width, self.height)

    property mipmap:
        '''Return True if the texture have mipmap enabled (readonly)
        '''
        def __get__(self):
            return self._mipmap

    property id:
        '''Return the OpenGL ID of the texture (readonly)
        '''
        def __get__(self):
            return self._id

    property target:
        '''Return the OpenGL target of the texture (readonly)
        '''
        def __get__(self):
            return self._target

    property width:
        '''Return the width of the texture (readonly)
        '''
        def __get__(self):
            return self._width

    property height:
        '''Return the height of the texture (readonly)
        '''
        def __get__(self):
            return self._height

    property tex_coords:
        '''Return the list of tex_coords (opengl)
        '''
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

    property colorfmt:
        '''Return the color format used in this texture. (readonly)

        .. versionadded:: 1.0.7
        '''
        def __get__(self):
            return self._colorfmt

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
        def __set__(self, str x):
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
        def __set__(self, str x):
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
        def __set__(self, str wrap):
            if wrap == self._wrap:
                return
            self.bind()
            self.set_wrap(wrap)

cdef class TextureRegion(Texture):
    '''Handle a region of a Texture class. Useful for non power-of-2
    texture handling.'''

    cdef int x
    cdef int y
    cdef Texture owner

    def __init__(self, int x, int y, int width, int height, Texture origin):
        Texture.__init__(self, width, height, origin.target, origin.id)
        self._is_allocated = 1
        self._mipmap = origin._mipmap
        self.x = x
        self.y = y
        self.owner = origin

        # recalculate texture coordinate
        cdef float origin_u1, origin_v1
        origin_u1 = origin._uvx
        origin_v1 = origin._uvy
        self._uvx = (x / <float>origin._width) * origin._uvw + origin_u1
        self._uvy = (y / <float>origin._height) * origin._uvh + origin_v1
        self._uvw = (width / <float>origin._width) * origin._uvw
        self._uvh = (height / <float>origin._height) * origin._uvh
        self.update_tex_coords()

    def __str__(self):
        return '<TextureRegion id=%d size=(%d, %d)>' % (
            self._id, self.width, self.height)

# Releasing texture through GC is problematic
def _texture_release(*largs):
    cdef GLuint texture_id
    if not _texture_release_list:
        return
    Logger.trace('Texture: releasing %d textures' % len(_texture_release_list))
    for texture_id in _texture_release_list:
        glDeleteTextures(1, &texture_id)
    del _texture_release_list[:]

if 'KIVY_DOC_INCLUDE' not in environ:
    from kivy.clock import Clock
    _texture_release_trigger = Clock.create_trigger(_texture_release)

