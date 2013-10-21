'''
Texture
=======

.. versionchanged:: 1.6.0
    Added support for paletted texture on OES: 'palette4_rgb8',
    'palette4_rgba8', 'palette4_r5_g6_b5', 'palette4_rgba4', 'palette4_rgb5_a1',
    'palette8_rgb8', 'palette8_rgba8', 'palette8_r5_g6_b5', 'palette8_rgba4',
    'palette8_rgb5_a1'

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

Reloading the Texture
---------------------

.. versionadded:: 1.2.0

If the OpenGL context is lost, the Texture must be reloaded. Texture having a
source are automatically reloaded without any help. But generated textures must
be reloaded by the user.

Use the :func:`Texture.add_reload_observer` to add a reloading function that will be
automatically called when needed::

    def __init__(self, **kwargs):
        super(...).__init__(**kwargs)
        self.texture = Texture.create(size=(512, 512), colorfmt='RGB',
            bufferfmt='ubyte')
        self.texture.add_reload_observer(self.populate_texture)

        # and load the data now.
        self.cbuffer = '\x00\xf0\xff' * 512 * 512
        self.populate_texture(self.texture)

    def populate_texture(self, texture):
        texture.blit_buffer(self.cbuffer)

This way, you could use the same method for initialization and for reloading.

.. note::

    For all text rendering with our core text renderer, texture is generated,
    but we are binding already a method to redo the text rendering and reupload
    the text to the texture. You have nothing to do on that case.
'''

__all__ = ('Texture', 'TextureRegion')

include "config.pxi"
include "common.pxi"
include "opengl_utils_def.pxi"

from array import array
from kivy.weakmethod import WeakMethod
from kivy.graphics.context cimport get_context

from kivy.graphics.c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from kivy.graphics.c_opengl_debug cimport *
from kivy.graphics.opengl_utils cimport *

# update flags
cdef int TI_MIN_FILTER      = 1 << 0
cdef int TI_MAG_FILTER      = 1 << 1
cdef int TI_WRAP            = 1 << 2
cdef int TI_NEED_GEN        = 1 << 3
cdef int TI_NEED_ALLOCATE   = 1 << 4
cdef int TI_NEED_PIXELS     = 1 << 5


# compatibility layer
cdef GLuint GL_BGR = 0x80E0
cdef GLuint GL_BGRA = 0x80E1
cdef GLuint GL_COMPRESSED_RGBA_S3TC_DXT1_EXT = 0x83F1
cdef GLuint GL_COMPRESSED_RGBA_S3TC_DXT3_EXT = 0x83F2
cdef GLuint GL_COMPRESSED_RGBA_S3TC_DXT5_EXT = 0x83F3
cdef GLuint GL_ETC1_RGB8_OES = 0x8D64
cdef GLuint GL_PALETTE4_RGB8_OES = 0x8B90
cdef GLuint GL_PALETTE4_RGBA8_OES = 0x8B91
cdef GLuint GL_PALETTE4_R5_G6_B5_OES = 0x8B92
cdef GLuint GL_PALETTE4_RGBA4_OES = 0x8B93
cdef GLuint GL_PALETTE4_RGB5_A1_OES = 0x8B94
cdef GLuint GL_PALETTE8_RGB8_OES = 0x8B95
cdef GLuint GL_PALETTE8_RGBA8_OES = 0x8B96
cdef GLuint GL_PALETTE8_R5_G6_B5_OES = 0x8B97
cdef GLuint GL_PALETTE8_RGBA4_OES = 0x8B98
cdef GLuint GL_PALETTE8_RGB5_A1_OES = 0x8B99
cdef GLuint GL_COMPRESSED_RGB_PVRTC_4BPPV1_IMG = 0x8C00
cdef GLuint GL_COMPRESSED_RGB_PVRTC_2BPPV1_IMG = 0x8C01
cdef GLuint GL_COMPRESSED_RGBA_PVRTC_4BPPV1_IMG = 0x8C02
cdef GLuint GL_COMPRESSED_RGBA_PVRTC_2BPPV1_IMG = 0x8C03


cdef dict _gl_color_fmt = {
    'rgba': GL_RGBA, 'bgra': GL_BGRA, 'rgb': GL_RGB, 'bgr': GL_BGR,
    'luminance': GL_LUMINANCE, 'luminance_alpha': GL_LUMINANCE_ALPHA,
    's3tc_dxt1': GL_COMPRESSED_RGBA_S3TC_DXT1_EXT,
    's3tc_dxt3': GL_COMPRESSED_RGBA_S3TC_DXT3_EXT,
    's3tc_dxt5': GL_COMPRESSED_RGBA_S3TC_DXT5_EXT,
    'etc1_rgb8': GL_ETC1_RGB8_OES,
    'palette4_rgb8': GL_PALETTE4_RGB8_OES,
    'palette4_rgba8': GL_PALETTE4_RGBA8_OES,
    'palette4_r5_g6_b5': GL_PALETTE4_R5_G6_B5_OES,
    'palette4_rgba4': GL_PALETTE4_RGBA4_OES,
    'palette4_rgb5_a1': GL_PALETTE4_RGB5_A1_OES,
    'palette8_rgb8': GL_PALETTE8_RGB8_OES,
    'palette8_rgba8': GL_PALETTE8_RGBA8_OES,
    'palette8_r5_g6_b5': GL_PALETTE8_R5_G6_B5_OES,
    'palette8_rgba4': GL_PALETTE8_RGBA4_OES,
    'palette8_rgb5_a1': GL_PALETTE8_RGB5_A1_OES,
    'pvrtc_rgba2': GL_COMPRESSED_RGBA_PVRTC_2BPPV1_IMG,
    'pvrtc_rgba4': GL_COMPRESSED_RGBA_PVRTC_4BPPV1_IMG,
    'pvrtc_rgb2': GL_COMPRESSED_RGB_PVRTC_2BPPV1_IMG,
    'pvrtc_rgb4': GL_COMPRESSED_RGB_PVRTC_4BPPV1_IMG }


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


cdef inline int _color_fmt_to_gl(x):
    '''Return the GL numeric value from a color string format
    '''
    x = x.lower()
    try:
        return _gl_color_fmt[x]
    except KeyError:
        raise Exception('Unknown <%s> color format' % x)


cdef inline int _is_compressed_fmt(x):
    '''Return 1 if the color string format is a compressed one
    '''
    if x.startswith('palette'):
        return 1
    if x.startswith('pvrtc_'):
        return 1
    if x.startswith('etc1_'):
        return 1
    return x.startswith('s3tc_dxt')


cdef inline int _buffer_fmt_to_gl(x):
    '''Return the GL numeric value from a buffer string format
    '''
    x = x.lower()
    try:
        return _gl_buffer_fmt[x]
    except KeyError:
        raise Exception('Unknown <%s> buffer format' % x)


cdef inline int _buffer_type_to_gl_size(x):
    '''Return the size of a buffer string format in str
    '''
    x = x.lower()
    try:
        return _gl_buffer_size[x]
    except KeyError:
        raise Exception('Unknown <%s> format' % x)


cdef inline GLuint _str_to_gl_texture_min_filter(x):
    '''Return the GL numeric value from a texture min filter string
    '''
    x = x.lower()
    try:
        return _gl_texture_min_filter[x]
    except KeyError:
        raise Exception('Unknown <%s> texture min filter' % x)


cdef inline GLuint _str_to_gl_texture_mag_filter(x):
    '''Return the GL numeric value from a texture mag filter string
    '''
    x = x.lower()
    if x == 'nearest':
        return GL_NEAREST
    elif x == 'linear':
        return GL_LINEAR
    raise Exception('Unknown <%s> texture mag filter' % x)


cdef inline GLuint _str_to_gl_texture_wrap(x):
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


cdef inline int _is_gl_format_supported(x):
    if x in ('bgr', 'bgra'):
        return gl_has_capability(GLCAP_BGRA)
    elif x == 's3tc_dxt1':
        return gl_has_capability(GLCAP_DXT1)
    elif x.startswith('s3tc_dxt'):
        return gl_has_capability(GLCAP_S3TC)
    elif x.startswith('etc1_'):
        return gl_has_capability(GLCAP_ETC1)
    return 1


cdef inline str _convert_gl_format(x):
    if x == 'bgr':
        return 'rgb'
    elif x == 'bgra':
        return 'rgba'
    return x


cdef inline _convert_buffer(bytes data, fmt):
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


cdef Texture _texture_create(int width, int height, colorfmt, bufferfmt,
                     int mipmap, int allocate, object callback):
    '''Create the OpenGL texture.
    '''
    cdef GLuint target = GL_TEXTURE_2D
    cdef GLuint texid = 0
    cdef Texture texture
    cdef int texture_width, texture_height
    cdef int glbufferfmt = _buffer_fmt_to_gl(bufferfmt)
    cdef int make_npot = 0

    # check if it's a pot or not
    if not _is_pow2(width) or not _is_pow2(height):
        make_npot = 1

    IF not USE_OPENGL_ES2:
        if gl_get_version_major() < 3:
            mipmap = 0

    # in case of mipmap is asked for npot texture, make it pot compatible
    if mipmap:
        make_npot = 0
        allocate = 1

    # depending if npot is available, use the real size or pot size
    if make_npot and gl_has_capability(c_GLCAP_NPOT):
        texture_width = width
        texture_height = height
    else:
        texture_width = _nearest_pow2(width)
        texture_height = _nearest_pow2(height)

    # create the texture with the future color format.
    colorfmt = _convert_gl_format(colorfmt)
    texture = Texture(texture_width, texture_height, target,
                      colorfmt=colorfmt, bufferfmt=bufferfmt, mipmap=mipmap,
                      callback=callback)
    if allocate or make_npot:
        texture.flags |= TI_NEED_ALLOCATE

    # set default parameter for this texture
    texture.set_wrap('clamp_to_edge')
    if mipmap:
        texture.set_min_filter('linear_mipmap_nearest')
        texture.set_mag_filter('linear')
    else:
        texture.set_min_filter('linear')
        texture.set_mag_filter('linear')

    # if the texture size is the same as initial size, return the texture
    # unmodified
    if texture_width == width and texture_height == height:
        return texture

    # otherwise, return a region of that texture
    return texture.get_region(0, 0, width, height)


def texture_create(size=None, colorfmt=None, bufferfmt=None, mipmap=False,
    callback=None):
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
        `callback`: callable(), default to False
            If a function is provided, it will be called when data will be
            needed in the texture.

    .. versionchanged:: 1.7.0
        :data:`callback` has been added
    '''
    cdef int width = 128, height = 128, allocate = 1
    if size is not None:
        width, height = size
    if colorfmt is None:
        colorfmt = 'rgba'
    if bufferfmt is None:
        bufferfmt = 'ubyte'
    if callback is not None:
        allocate = 0
    return _texture_create(width, height, colorfmt, bufferfmt, mipmap,
            allocate, callback)


def texture_create_from_data(im, mipmap=False):
    '''Create a texture from an ImageData class
    '''
    cdef int width = im.width
    cdef int height = im.height
    cdef int allocate = 1
    cdef int no_blit = 0
    cdef Texture texture

    # optimization, if the texture is power of 2, don't allocate in
    # _texture_create, but allocate in blit_data => only 1 upload
    if _is_pow2(width) and _is_pow2(height):
        allocate = 0
    elif gl_has_capability(c_GLCAP_NPOT):
        allocate = 0

    # if imagedata have more than one image, activate mipmap
    if im.have_mipmap:
        mipmap = True

    IF not USE_OPENGL_ES2:
        if gl_get_version_major() < 3:
            mipmap = False

    if width == 0 or height == 0:
        height = width = 1
        allocate = 1
        no_blit = 1
    texture = _texture_create(width, height, im.fmt, 'ubyte', mipmap, allocate,
                             None)
    if texture is None:
        return None

    texture._source = im.source
    if no_blit == 0:
        texture.blit_data(im)

    return texture


cdef class Texture:
    '''Handle a OpenGL texture. This class can be used to create simple texture
    or complex texture based on ImageData.'''

    create = staticmethod(texture_create)
    create_from_data = staticmethod(texture_create_from_data)

    def __init__(self, width, height, target, texid=0, colorfmt='rgb',
            bufferfmt='ubyte', mipmap=False, source=None, callback=None):
        self.observers = []
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
        self._bufferfmt     = bufferfmt
        self._source        = source
        self._nofree        = 0
        self._callback      = callback

        if texid == 0:
            self.flags |= TI_NEED_GEN
        if callback is not None:
            self.flags |= TI_NEED_PIXELS

        self.update_tex_coords()
        get_context().register_texture(self)

    def __dealloc__(self):
        get_context().dealloc_texture(self)

    cdef void update_tex_coords(self):
        self._tex_coords[0] = self._uvx
        self._tex_coords[1] = self._uvy
        self._tex_coords[2] = self._uvx + self._uvw
        self._tex_coords[3] = self._uvy
        self._tex_coords[4] = self._uvx + self._uvw
        self._tex_coords[5] = self._uvy + self._uvh
        self._tex_coords[6] = self._uvx
        self._tex_coords[7] = self._uvy + self._uvh

    def add_reload_observer(self, callback):
        '''Add a callback to be called after the whole graphics context have
        been reloaded. This is where you can reupload your custom data in GPU.

        .. versionadded:: 1.2.0

        :Parameters:
            `callback`: func(context) -> return None
                The first parameter will be the context itself
        '''
        self.observers.append(WeakMethod(callback))

    def remove_reload_observer(self, callback):
        '''Remove a callback from the observer list, previously added by
        :func:`add_reload_observer`.

        .. versionadded:: 1.2.0

        '''
        for cb in self.observers[:]:
            if cb.is_dead() or cb() is callback:
                self.observers.remove(cb)
                continue

    cdef void allocate(self):
        cdef int glfmt, iglbufferfmt, datasize, dataerr = 0
        cdef void *data = NULL
        cdef int is_npot = 0

        # check if it's a pot or not
        if not _is_pow2(self._width) or not _is_pow2(self._height):
            make_npot = is_npot = 1

        # prepare information needed for nogil
        glfmt = _color_fmt_to_gl(self._colorfmt)
        iglbufferfmt = _buffer_fmt_to_gl(self._bufferfmt)
        datasize = self._width * self._height * \
                _gl_format_size(glfmt) * _buffer_type_to_gl_size(self._bufferfmt)

        # act as we have been able to allocate the texture
        self._is_allocated = 1

        # do the rest outside the Python GIL
        with nogil:
            data = calloc(1, datasize)
            if data != NULL:
                # ensure pixel upload is correct
                _gl_prepare_pixels_upload(self._width)

                # do the initial upload with fake data
                glTexImage2D(self._target, 0, glfmt, self._width, self._height,
                        0, glfmt, iglbufferfmt, data)

                # free the data !
                free(data)

                # create mipmap if needed
                if self._mipmap and is_npot == 0:
                    glGenerateMipmap(self._target)
            else:
                dataerr = 1

        if dataerr:
            self._is_allocated = 0
            raise Exception('Unable to allocate memory for texture (size is %s)' %
                            datasize)

    cpdef flip_vertical(self):
        '''Flip tex_coords for vertical displaying'''
        self._uvy += self._uvh
        self._uvh = -self._uvh
        self.update_tex_coords()

    cpdef get_region(self, x, y, width, height):
        '''Return a part of the texture defined by the rectangle arguments
        (x, y, width, height). Returns a :class:`TextureRegion` instance.'''
        return TextureRegion(x, y, width, height, self)

    def ask_update(self, callback):
        '''Indicate that the content of the texture should be updated, and the
        callback function need to be called when the texture will be really
        used.
        '''
        self.flags |= TI_NEED_PIXELS
        self._callback = callback

    cpdef bind(self):
        '''Bind the texture to current opengl state'''
        cdef GLuint value

        # if we have no change to apply, just bind and exit
        if not self.flags:
            glBindTexture(self._target, self._id)
            return

        if self.flags & TI_NEED_GEN:
            self.flags &= ~TI_NEED_GEN
            glGenTextures(1, &self._id)

        glBindTexture(self._target, self._id)

        if self.flags & TI_NEED_ALLOCATE:
            self.flags &= ~TI_NEED_ALLOCATE
            self.allocate()

        if self.flags & TI_NEED_PIXELS:
            self.flags &= ~TI_NEED_PIXELS
            if self._callback:
                self._callback(self)
                self._callback = None

        if self.flags & TI_MIN_FILTER:
            self.flags &= ~TI_MIN_FILTER
            value = _str_to_gl_texture_min_filter(self._min_filter)
            glTexParameteri(self._target, GL_TEXTURE_MIN_FILTER, value)

        if self.flags & TI_MAG_FILTER:
            self.flags &= ~TI_MAG_FILTER
            value = _str_to_gl_texture_mag_filter(self._mag_filter)
            glTexParameteri(self._target, GL_TEXTURE_MAG_FILTER, value)

        if self.flags & TI_WRAP:
            self.flags &= ~TI_WRAP
            value = _str_to_gl_texture_wrap(self._wrap)
            glTexParameteri(self._target, GL_TEXTURE_WRAP_S, value)
            glTexParameteri(self._target, GL_TEXTURE_WRAP_T, value)

    cdef void set_min_filter(self, x):
        if self._min_filter != x:
            self._min_filter = x
            self.flags |= TI_MIN_FILTER

    cdef void set_mag_filter(self, x):
        if self._mag_filter != x:
            self._mag_filter = x
            self.flags |= TI_MAG_FILTER

    cdef void set_wrap(self, x):
        if self._wrap != x:
            self._wrap = x
            self.flags |= TI_WRAP

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

        # bind the texture, and create anything that should be created at this
        # time.
        self.bind()

        # need conversion ?
        cdef bytes data
        data = pbuffer
        data, colorfmt = _convert_buffer(data, colorfmt)

        # prepare nogil
        cdef int iglfmt = _color_fmt_to_gl(self._colorfmt)
        cdef int glfmt = _color_fmt_to_gl(colorfmt)
        cdef long datasize = len(pbuffer)
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
            if is_compressed:
                glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
                glCompressedTexImage2D(target, _mipmap_level, glfmt, w, h, 0,
                        <GLsizei>datasize, cdata)
            elif is_allocated:
                _gl_prepare_pixels_upload(w)
                glTexSubImage2D(target, _mipmap_level, x, y, w, h, glfmt, glbufferfmt, cdata)
            else:
                _gl_prepare_pixels_upload(w)
                glTexImage2D(target, _mipmap_level, iglfmt, w, h, 0, glfmt, glbufferfmt, cdata)
            if _mipmap_generation:
                glGenerateMipmap(target)

    def _on_proxyimage_loaded(self, image):
        if image is not self._proxyimage:
            return
        self._reload_propagate(image.image.texture)
        self._proxyimage = None

        # the texture might impact something on the drawing, so ask to refresh
        # the window.
        # FIXME: the texture used in BindTexture should ask for a retrigger
        get_context().flag_update_canvas()

    cdef void reload(self):
        cdef Texture texture
        if self._id != -1:
            return
        if self._source is None:
            # manual texture recreation
            texture = texture_create(self.size, self.colorfmt, self.bufferfmt,
                    self.mipmap)
        else:
            source = self._source
            proto = source.split(':', 1)[0]
            if proto in ('http', 'https', 'ftp', 'smb'):
                from kivy.loader import Loader
                self._proxyimage = Loader.image(source)
                self._id = 0 # FIXME this will point to an invalid texture ...
                self._proxyimage.bind(on_load=self._on_proxyimage_loaded)
                if self._proxyimage.loaded:
                    self._on_proxyimage_loaded(self._proxyimage)
                return
            else:
                from kivy.core.image import Image
                image = Image(self._source, nocache=True)
                texture = image.texture

        self._reload_propagate(texture)

    cdef void _reload_propagate(self, Texture texture):
        # set the same parameters as our current texture
        texture.set_wrap(self.wrap)
        texture.set_min_filter(self.min_filter)
        texture.set_mag_filter(self.mag_filter)
        texture.flags |= TI_MIN_FILTER | TI_MAG_FILTER | TI_WRAP
        texture.uvpos = self.uvpos
        texture.uvsize = self.uvsize

        # ensure the new opengl ID will not get through GC
        texture.bind()
        self._id = texture.id
        texture._nofree = 1

        # then update content again
        for callback in self.observers[:]:
            if callback.is_dead():
                self.observers.remove(callback)
                continue
            callback()(self)

    def save(self, filename):
        '''Save the texture content into a file. Check
        :meth:`kivy.core.image.Image.save` for more information about the usage.

        .. versionadded:: 1.7.0
        '''
        from kivy.core.image import Image
        return Image(self).save(filename)

    def __repr__(self):
        return '<Texture hash=%r id=%d size=%r colorfmt=%r bufferfmt=%r source=%r observers=%d>' % (
            id(self), self._id, self.size, self.colorfmt, self.bufferfmt,
            self._source, len(self.observers))

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
                self._tex_coords[7])

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

    property bufferfmt:
        '''Return the buffer format used in this texture. (readonly)

        .. versionadded:: 1.2.0
        '''
        def __get__(self):
            return self._bufferfmt

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
            self.set_wrap(wrap)

    property pixels:
        '''Get the pixels texture, in RGBA format only, unsigned byte.

        .. versionadded:: 1.7.0
        '''
        def __get__(self):
            from kivy.graphics.fbo import Fbo
            return Fbo(size=self.size, texture=self).pixels


cdef class TextureRegion(Texture):
    '''Handle a region of a Texture class. Useful for non power-of-2
    texture handling.'''

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

    def __repr__(self):
        return '<TextureRegion of %r hash=%r id=%d size=%r colorfmt=%r bufferfmt=%r source=%r observers=%d>' % (
            self.owner, id(self), self._id, self.size, self.colorfmt,
            self.bufferfmt, self._source, len(self.observers))

    cdef void reload(self):
        # texture region are reloaded _after_ normal texture
        # so that could work, except if it's a region of region
        # it's safe to retrigger a reload, since the owner texture will be not
        # really reloaded if its id is not -1.
        self.owner.reload()
        self._id = self.owner.id

        # then update content again
        self.bind()
        for callback in self.observers[:]:
            if callback.is_dead():
                self.observers.remove(callback)
                continue
            callback()(self)

    def ask_update(self, callback):
        # redirect to owner
        self.owner.ask_update(callback)

    cpdef bind(self):
        self.owner.bind()

    property pixels:
        def __get__(self):
            from kivy.graphics.fbo import Fbo
            from kivy.graphics import Color, Rectangle
            fbo = Fbo(size=self.size)
            fbo.clear()
            self.flip_vertical()
            with fbo:
                Color(1, 1, 1)
                Rectangle(size=self.size, texture=self,
                        tex_coords=self.tex_coords)
            fbo.draw()
            self.flip_vertical()
            return fbo.pixels

