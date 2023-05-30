'''
Texture
=======

.. versionchanged:: 1.6.0
    Added support for paletted texture on OES: 'palette4_rgb8',
    'palette4_rgba8', 'palette4_r5_g6_b5', 'palette4_rgba4', 'palette4_rgb5_a1',
    'palette8_rgb8', 'palette8_rgba8', 'palette8_r5_g6_b5', 'palette8_rgba4'
    and 'palette8_rgb5_a1'.

:class:`Texture` is a class that handles OpenGL textures. Depending on the
hardware,
some OpenGL capabilities might not be available (BGRA support, NPOT support,
etc.)

You cannot instantiate this class yourself. You must use the function
:meth:`Texture.create` to create a new texture::

    texture = Texture.create(size=(640, 480))

When you create a texture, you should be aware of the default color
and buffer format:

    - the color/pixel format (:attr:`Texture.colorfmt`) that can be one of
      'rgb', 'rgba', 'luminance', 'luminance_alpha', 'bgr' or 'bgra'.
      The default value is 'rgb'
    - the buffer format determines how a color component is stored into memory.
      This can be one of 'ubyte', 'ushort', 'uint', 'byte', 'short', 'int' or
      'float'. The default value and the most commonly used is 'ubyte'.

So, if you want to create an RGBA texture::

    texture = Texture.create(size=(640, 480), colorfmt='rgba')

You can use your texture in almost all vertex instructions with the
:attr:`kivy.graphics.VertexIntruction.texture` parameter. If you want to use
your texture in kv lang, you can save it in an
:class:`~kivy.properties.ObjectProperty` inside your widget.

.. warning::
    Using Texture before OpenGL has been initialized will lead to a crash. If
    you need to create textures before the application has started, import
    Window first: `from kivy.core.window import Window`

Blitting custom data
--------------------

You can create your own data and blit it to the texture using
:meth:`Texture.blit_buffer`.

For example, to blit immutable bytes data::

    # create a 64x64 texture, defaults to rgba / ubyte
    texture = Texture.create(size=(64, 64))

    # create 64x64 rgb tab, and fill with values from 0 to 255
    # we'll have a gradient from black to white
    size = 64 * 64 * 3
    buf = [int(x * 255 / size) for x in range(size)]

    # then, convert the array to a ubyte string
    buf = bytes(buf)

    # then blit the buffer
    texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')

    # that's all ! you can use it in your graphics now :)
    # if self is a widget, you can do this
    with self.canvas:
        Rectangle(texture=texture, pos=self.pos, size=(64, 64))

Since 1.9.0, you can blit data stored in a instance that implements the python
buffer interface, or a memoryview thereof, such as numpy arrays, python
`array.array`, a `bytearray`, or a cython array. This is beneficial if you
expect to blit similar data, with perhaps a few changes in the data.

When using a bytes representation of the data, for every change you have to
regenerate the bytes instance, from perhaps a list, which is very inefficient.
When using a buffer object, you can simply edit parts of the original data.
Similarly, unless starting with a bytes object, converting to bytes requires a
full copy, however, when using a buffer instance, no memory is copied, except
to upload it to the GPU.

Continuing with the example above::

    from array import array

    size = 64 * 64 * 3
    buf = [int(x * 255 / size) for x in range(size)]
    # initialize the array with the buffer values
    arr = array('B', buf)
    # now blit the array
    texture.blit_buffer(arr, colorfmt='rgb', bufferfmt='ubyte')

    # now change some elements in the original array
    arr[24] = arr[50] = 99
    # blit again the buffer
    texture.blit_buffer(arr, colorfmt='rgb', bufferfmt='ubyte')


BGR/BGRA support
----------------

The first time you try to create a BGR or BGRA texture, we check whether
your hardware supports BGR / BGRA textures by checking the extension
'GL_EXT_bgra'.

If the extension is not found, the conversion to RGB / RGBA will be done in
software.


NPOT texture
------------

.. versionchanged:: 1.0.7

    If your hardware supports NPOT, no POT is created.

As the OpenGL documentation says, a texture must be power-of-two sized. That
means
your width and height can be one of 64, 32, 256... but not 3, 68, 42. NPOT means
non-power-of-two. OpenGL ES 2 supports NPOT textures natively but with some
drawbacks. Another type of NPOT texture is called a rectangle texture.
POT, NPOT and textures all have their own pro/cons.

================= ============= ============= =================================
    Features           POT           NPOT                Rectangle
----------------- ------------- ------------- ---------------------------------
OpenGL Target     GL_TEXTURE_2D GL_TEXTURE_2D GL_TEXTURE_RECTANGLE_(NV|ARB|EXT)
Texture coords    0-1 range     0-1 range     width-height range
Mipmapping        Supported     Partially     No
Wrap mode         Supported     Supported     No
================= ============= ============= =================================

If you create a NPOT texture, we first check whether your hardware
supports it by checking the extensions GL_ARB_texture_non_power_of_two or
OES_texture_npot. If none of these are available, we create the nearest
POT texture that can contain your NPOT texture. The :meth:`Texture.create` will
return a :class:`TextureRegion` instead.


Texture atlas
-------------

A texture atlas is a single texture that contains many images.
If you want to separate the original texture into many single ones, you don't
need to. You can get a region of the original texture. That will return the
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

Mipmapping is an OpenGL technique for enhancing the rendering of large textures
to small surfaces. Without mipmapping, you might see pixelation when you
render to small surfaces.
The idea is to precalculate the subtexture and apply some image filter as a
linear filter. Then, when you render a small surface, instead of using the
biggest texture, it will use a lower filtered texture. The result can look
better this way.

To make that happen, you need to specify mipmap=True when you create a
texture. Some widgets already give you the ability to create mipmapped
textures, such as the :class:`~kivy.uix.label.Label` and
:class:`~kivy.uix.image.Image`.

From the OpenGL Wiki : "So a 64x16 2D texture can have 5 mip-maps: 32x8, 16x4,
8x2, 4x1, 2x1, and 1x1". Check http://www.opengl.org/wiki/Texture for more
information.

.. note::

    As the table in previous section said, if your texture is NPOT, we
    create the nearest POT texture and generate a mipmap from it. This
    might change in the future.

Reloading the Texture
---------------------

.. versionadded:: 1.2.0

If the OpenGL context is lost, the Texture must be reloaded. Textures that have
a source are automatically reloaded but generated textures must
be reloaded by the user.

Use the :meth:`Texture.add_reload_observer` to add a reloading function that
will be automatically called when needed::

    def __init__(self, **kwargs):
        super(...).__init__(**kwargs)
        self.texture = Texture.create(size=(512, 512), colorfmt='RGB',
            bufferfmt='ubyte')
        self.texture.add_reload_observer(self.populate_texture)

        # and load the data now.
        self.cbuffer = '\\x00\\xf0\\xff' * 512 * 512
        self.populate_texture(self.texture)

    def populate_texture(self, texture):
        texture.blit_buffer(self.cbuffer)

This way, you can use the same method for initialization and reloading.

.. note::

    For all text rendering with our core text renderer, the texture is generated
    but we already bind a method to redo the text rendering and reupload
    the text to the texture. You don't have to do anything.
'''

__all__ = ('Texture', 'TextureRegion')

include "../include/config.pxi"
include "common.pxi"
include "opengl_utils_def.pxi"
include "img_tools.pxi"
include "gl_debug_logger.pxi"

cimport cython
from os import environ
from kivy.utils import platform
from kivy.weakmethod import WeakMethod
from kivy.graphics.context cimport get_context

cimport kivy.graphics.cgl as cgldef
from kivy.graphics.cgl cimport *
from kivy.graphics.opengl_utils cimport gl_has_capability, gl_get_version_major

cdef int gles_limts = int(environ.get(
    'KIVY_GLES_LIMITS', int(platform not in ('win', 'macosx', 'linux'))))

# update flags
cdef int TI_MIN_FILTER      = 1 << 0
cdef int TI_MAG_FILTER      = 1 << 1
cdef int TI_WRAP            = 1 << 2
cdef int TI_NEED_GEN        = 1 << 3
cdef int TI_NEED_ALLOCATE   = 1 << 4
cdef int TI_NEED_PIXELS     = 1 << 5

# compatibility layer
DEF GL_BGR = 0x80E0
DEF GL_BGRA = 0x80E1
DEF GL_COMPRESSED_RGBA_S3TC_DXT1_EXT = 0x83F1
DEF GL_COMPRESSED_RGBA_S3TC_DXT3_EXT = 0x83F2
DEF GL_COMPRESSED_RGBA_S3TC_DXT5_EXT = 0x83F3
DEF GL_ETC1_RGB8_OES = 0x8D64
DEF GL_PALETTE4_RGB8_OES = 0x8B90
DEF GL_PALETTE4_RGBA8_OES = 0x8B91
DEF GL_PALETTE4_R5_G6_B5_OES = 0x8B92
DEF GL_PALETTE4_RGBA4_OES = 0x8B93
DEF GL_PALETTE4_RGB5_A1_OES = 0x8B94
DEF GL_PALETTE8_RGB8_OES = 0x8B95
DEF GL_PALETTE8_RGBA8_OES = 0x8B96
DEF GL_PALETTE8_R5_G6_B5_OES = 0x8B97
DEF GL_PALETTE8_RGBA4_OES = 0x8B98
DEF GL_PALETTE8_RGB5_A1_OES = 0x8B99
DEF GL_COMPRESSED_RGB_PVRTC_4BPPV1_IMG = 0x8C00
DEF GL_COMPRESSED_RGB_PVRTC_2BPPV1_IMG = 0x8C01
DEF GL_COMPRESSED_RGBA_PVRTC_4BPPV1_IMG = 0x8C02
DEF GL_COMPRESSED_RGBA_PVRTC_2BPPV1_IMG = 0x8C03
DEF GL_RED = 0x1903
DEF GL_RG = 0x8227
DEF GL_R8 = 0x8229
DEF GL_RG8 = 0x822B
DEF GL_RGBA8 =  0x8058
DEF GL_UNPACK_ROW_LENGTH = 0x0CF2
DEF GL_UNPACK_SKIP_ROWS = 0x0CF3
DEF GL_UNPACK_SKIP_PIXELS = 0x0CF4

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
    'pvrtc_rgb4': GL_COMPRESSED_RGB_PVRTC_4BPPV1_IMG,
    'red': GL_RED, 'rg': GL_RG,
    'r8': GL_R8, 'rg8': GL_RG8, 'rgba8': GL_RGBA8}

cdef dict _gl_buffer_fmt = {
    'ubyte': GL_UNSIGNED_BYTE, 'ushort': GL_UNSIGNED_SHORT,
    'uint': GL_UNSIGNED_INT, 'byte': GL_BYTE,
    'short': GL_SHORT, 'int': GL_INT, 'float': GL_FLOAT}


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
    '''Return the GL numeric value from a color string format.
    '''
    x = x.lower()
    try:
        return _gl_color_fmt[x]
    except KeyError:
        raise Exception('Unknown <%s> color format' % x)


cdef inline int _is_compressed_fmt(x):
    '''Return 1 if the color string format is a compressed one.
    '''
    if x.startswith('palette'):
        return 1
    if x.startswith('pvrtc_'):
        return 1
    if x.startswith('etc1_'):
        return 1
    return x.startswith('s3tc_dxt')


cdef inline int _buffer_fmt_to_gl(x):
    '''Return the GL numeric value from a buffer string format.
    '''
    x = x.lower()
    try:
        return _gl_buffer_fmt[x]
    except KeyError:
        raise Exception('Unknown <%s> buffer format' % x)


cdef inline int _buffer_type_to_gl_size(x):
    '''Return the size of a buffer string format in str.
    '''
    x = x.lower()
    try:
        return _gl_buffer_size[x]
    except KeyError:
        raise Exception('Unknown <%s> format' % x)


cdef inline GLuint _str_to_gl_texture_min_filter(x):
    '''Return the GL numeric value from a texture min filter string.
    '''
    x = x.lower()
    try:
        return _gl_texture_min_filter[x]
    except KeyError:
        raise Exception('Unknown <%s> texture min filter' % x)


cdef inline GLuint _str_to_gl_texture_mag_filter(x):
    '''Return the GL numeric value from a texture mag filter string.
    '''
    x = x.lower()
    if x == 'nearest':
        return GL_NEAREST
    elif x == 'linear':
        return GL_LINEAR
    raise Exception('Unknown <%s> texture mag filter' % x)


cdef inline GLuint _str_to_gl_texture_wrap(x):
    '''Return the GL numeric value from a texture wrap string.
    '''
    if x == 'clamp_to_edge':
        return GL_CLAMP_TO_EDGE
    elif x == 'repeat':
        return GL_REPEAT
    elif x == 'mirrored_repeat':
        return GL_MIRRORED_REPEAT


cdef inline int _gl_format_size(GLuint x):
    '''Return the GL numeric value from a texture wrap string.
    '''
    if x in (GL_RGB, GL_BGR):
        return 3
    elif x in (GL_RGBA, GL_BGRA):
        return 4
    elif x in (GL_LUMINANCE_ALPHA, GL_RG):
        return 2
    elif x in (GL_LUMINANCE, GL_RED):
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


cdef inline void _gl_prepare_pixels_upload(int width) nogil:
    '''Set the best pixel alignment for the current width.
    '''
    if not (width & 0x7):
        cgl.glPixelStorei(GL_UNPACK_ALIGNMENT, 8)
    elif not (width & 0x3):
        cgl.glPixelStorei(GL_UNPACK_ALIGNMENT, 4)
    elif not (width & 0x1):
        cgl.glPixelStorei(GL_UNPACK_ALIGNMENT, 2)
    else:
        cgl.glPixelStorei(GL_UNPACK_ALIGNMENT, 1)



cdef Texture _texture_create(int width, int height, colorfmt, bufferfmt,
                     int mipmap, int allocate, object callback, object icolorfmt):
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

    if not cgldef.kivy_opengl_es2:
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
    icolorfmt = _convert_gl_format(icolorfmt)
    texture = Texture(texture_width, texture_height, target,
                      colorfmt=colorfmt, bufferfmt=bufferfmt, mipmap=mipmap,
                      callback=callback, icolorfmt=icolorfmt)
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
    callback=None, icolorfmt=None):
    '''Create a texture based on size.

    :Parameters:
        `size`: tuple, defaults to (128, 128)
            Size of the texture.
        `colorfmt`: str, defaults to 'rgba'
            Color format of the texture. Can be 'rgba' or 'rgb',
            'luminance' or 'luminance_alpha'. On desktop, additional values are
            available: 'red', 'rg'.
        `icolorfmt`: str, defaults to the value of `colorfmt`
            Internal format storage of the texture. Can be 'rgba' or 'rgb',
            'luminance' or 'luminance_alpha'. On desktop, additional values are
            available: 'r8', 'rg8', 'rgba8'.
        `bufferfmt`: str, defaults to 'ubyte'
            Internal buffer format of the texture. Can be 'ubyte', 'ushort',
            'uint', 'bute', 'short', 'int' or 'float'.
        `mipmap`: bool, defaults to False
            If True, it will automatically generate the mipmap texture.
        `callback`: callable(), defaults to False
            If a function is provided, it will be called when data is
            needed in the texture.

    .. versionchanged:: 1.7.0
        :attr:`callback` has been added
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
    if icolorfmt is None:
        icolorfmt = colorfmt
    return _texture_create(width, height, colorfmt, bufferfmt, mipmap,
            allocate, callback, icolorfmt)


def texture_create_from_data(im, mipmap=False):
    '''Create a texture from an ImageData class.
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

    if not cgldef.kivy_opengl_es2:
        if gl_get_version_major() < 3:
            mipmap = False

    if width == 0 or height == 0:
        height = width = 1
        allocate = 1
        no_blit = 1
    texture = _texture_create(width, height, im.fmt, 'ubyte', mipmap, allocate,
                             None, im.fmt)
    if texture is None:
        return None

    texture._source = im.source
    if no_blit == 0:
        texture.blit_data(im)

    return texture


cdef class Texture:
    '''Handle an OpenGL texture. This class can be used to create simple
    textures or complex textures based on ImageData.'''

    _sequenced_textures = {}
    '''Internal use only for textures of sequenced images
    '''
    create = staticmethod(texture_create)
    create_from_data = staticmethod(texture_create_from_data)

    def __init__(self, width, height, target, texid=0, colorfmt='rgb',
            bufferfmt='ubyte', mipmap=False, source=None, callback=None,
            icolorfmt='rgb'):
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
        self._icolorfmt     = icolorfmt
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
        '''Add a callback to be called after the whole graphics context has
        been reloaded. This is where you can reupload your custom data into
        the GPU.

        .. versionadded:: 1.2.0

        :Parameters:
            `callback`: func(context) -> return None
                The first parameter will be the context itself.
        '''
        self.observers.append(WeakMethod(callback))

    def remove_reload_observer(self, callback):
        '''Remove a callback from the observer list, previously added by
        :meth:`add_reload_observer`.

        .. versionadded:: 1.2.0

        '''
        for cb in self.observers[:]:
            method = cb()
            if method is None or method is callback:
                self.observers.remove(cb)
                continue

    cdef void allocate(self):
        cdef int iglfmt, glfmt, iglbufferfmt, datasize, dataerr = 0
        cdef void *data = NULL
        cdef int is_npot = 0

        # check if it's a pot or not
        if not _is_pow2(self._width) or not _is_pow2(self._height):
            make_npot = is_npot = 1

        # prepare information needed for nogil
        glfmt = _color_fmt_to_gl(self._colorfmt)
        iglfmt = _color_fmt_to_gl(self._icolorfmt)
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
                cgl.glTexImage2D(self._target, 0, iglfmt, self._width, self._height,
                        0, glfmt, iglbufferfmt, data)

                # free the data !
                free(data)

                # create mipmap if needed
                if self._mipmap and is_npot == 0:
                    cgl.glGenerateMipmap(self._target)
            else:
                dataerr = 1

        if dataerr:
            self._is_allocated = 0
            raise Exception('Unable to allocate memory for texture (size is %s)' %
                            datasize)

    cpdef flip_vertical(self):
        '''Flip tex_coords for vertical display.'''
        self._uvy += self._uvh
        self._uvh = -self._uvh
        self.update_tex_coords()

    cpdef flip_horizontal(self):
        '''Flip tex_coords for horizontal display.

        .. versionadded:: 1.9.0

        '''
        self._uvx += self._uvw
        self._uvw = -self._uvw
        self.update_tex_coords()

    cpdef get_region(self, x, y, width, height):
        '''Return a part of the texture defined by the rectangular arguments
        (x, y, width, height). Returns a :class:`TextureRegion` instance.'''
        return TextureRegion(x, y, width, height, self)

    def ask_update(self, callback):
        '''Indicate that the content of the texture should be updated and the
        callback function needs to be called when the texture will be
        used.
        '''
        self.flags |= TI_NEED_PIXELS
        self._callback = callback

    cpdef bind(self):
        '''Bind the texture to the current opengl state.'''
        cdef GLuint value

        # if we have no change to apply, just bind and exit
        if not self.flags:
            cgl.glBindTexture(self._target, self._id)
            log_gl_error('Texture.bind-glBindTexture')
            return

        if self.flags & TI_NEED_GEN:
            self.flags &= ~TI_NEED_GEN
            cgl.glGenTextures(1, &self._id)
            log_gl_error('Texture.bind-glGenTextures')

        cgl.glBindTexture(self._target, self._id)
        log_gl_error('Texture.bind-glBindTexture')

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
            cgl.glTexParameteri(self._target, GL_TEXTURE_MIN_FILTER, value)
            log_gl_error('Texture.bind-glTexParameteri (GL_TEXTURE_MIN_FILTER)')

        if self.flags & TI_MAG_FILTER:
            self.flags &= ~TI_MAG_FILTER
            value = _str_to_gl_texture_mag_filter(self._mag_filter)
            cgl.glTexParameteri(self._target, GL_TEXTURE_MAG_FILTER, value)
            log_gl_error('Texture.bind-glTexParameteri (GL_TEXTURE_MAG_FILTER')

        if self.flags & TI_WRAP:
            self.flags &= ~TI_WRAP
            value = _str_to_gl_texture_wrap(self._wrap)
            cgl.glTexParameteri(self._target, GL_TEXTURE_WRAP_S, value)
            log_gl_error('Texture.bind-glTexParameteri (GL_TEXTURE_WRAP_S)')
            cgl.glTexParameteri(self._target, GL_TEXTURE_WRAP_T, value)
            log_gl_error('Texture.bind-glTexParameteri (GL_TEXTURE_WRAP_T')

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
        '''Replace a whole texture with image data.
        '''
        blit = self.blit_buffer

        # depending if imagedata have mipmap, think different.
        if not im.have_mipmap:
            blit(im.data, size=im.size, colorfmt=im.fmt, pos=pos,
                    rowlength=im.rowlength)
        else:
            # upload each level
            for level, width, height, data, rowlength in im.iterate_mipmaps():
                blit(data, size=(width, height),
                     colorfmt=im.fmt, pos=pos,
                     mipmap_level=level, mipmap_generation=False,
                     rowlength=rowlength)

    @cython.cdivision(True)
    def blit_buffer(self, pbuffer, size=None, colorfmt=None,
                    pos=None, bufferfmt=None, mipmap_level=0,
                    mipmap_generation=True, int rowlength=0):
        '''Blit a buffer into the texture.

        .. note::

            Unless the canvas will be updated due to other changes,
            :meth:`~kivy.graphics.instructions.Canvas.ask_update` should be
            called in order to update the texture.

        :Parameters:
            `pbuffer`: bytes, or a class that implements the buffer interface\
 (including memoryview).
                A buffer containing the image data. It can be either a bytes
                object or a instance of a class that implements the python
                buffer interface, e.g. `array.array`, `bytearray`, numpy arrays
                etc. If it's not a bytes object, the underlying buffer must
                be contiguous, have only one dimension and must not be
                readonly, even though the data is not modified, due to a cython
                limitation. See module description for usage details.
            `size`: tuple, defaults to texture size
                Size of the image (width, height)
            `colorfmt`: str, defaults to 'rgb'
                Image format, can be one of 'rgb', 'rgba', 'bgr', 'bgra',
                'luminance' or 'luminance_alpha'.
            `pos`: tuple, defaults to (0, 0)
                Position to blit in the texture.
            `bufferfmt`: str, defaults to 'ubyte'
                Type of the data buffer, can be one of 'ubyte', 'ushort',
                'uint', 'byte', 'short', 'int' or 'float'.
            `mipmap_level`: int, defaults to 0
                Indicate which mipmap level we are going to update.
            `mipmap_generation`: bool, defaults to True
                Indicate if we need to regenerate the mipmap from level 0.

        .. versionchanged:: 1.0.7

            added `mipmap_level` and `mipmap_generation`

        .. versionchanged:: 1.9.0
            `pbuffer` can now be any class instance that implements the python
            buffer interface and / or memoryviews thereof.

        '''
        cdef GLuint target = self._target
        cdef int glbufferfmt
        if colorfmt is None:
            colorfmt = 'rgb'
        if bufferfmt is None:
            bufferfmt = 'ubyte'
        if pos is None:
            pos = (0, 0)
        if size is None:
            size = self.size
        glbufferfmt = _buffer_fmt_to_gl(bufferfmt)

        # gles limitation/issue: cannot blit buffer on a different
        # buffer/colorfmt
        # Reference: https://github.com/kivy/kivy/issues/1600
        if gles_limts:
            if colorfmt.lower() != self.colorfmt.lower():
                raise Exception((
                    "GLES LIMIT: Cannot blit with a different colorfmt than "
                    "the created texture. (texture has {}, you passed {}). "
                    "Consider setting KIVY_GLES_LIMITS"
                    ).format(self.colorfmt, colorfmt))
            if bufferfmt.lower() != self.bufferfmt.lower():
                raise Exception((
                    "GLES LIMIT: Cannot blit with a different bufferfmt than "
                    "the created texture. (texture has {}, you passed {}). "
                    "Consider setting KIVY_GLES_LIMITS"
                    ).format(self.bufferfmt, bufferfmt))

        # bind the texture, and create anything that should be created at this
        # time.
        self.bind()

        # need conversion, do check here because it seems to be faster ?
        if not gl_has_texture_native_format(colorfmt):
            pbuffer, colorfmt = convert_to_gl_format(pbuffer, colorfmt,
                                                     size[0], size[1])
        cdef char [:] char_view
        cdef short [:] short_view
        cdef unsigned short [:] ushort_view
        cdef int [:] int_view
        cdef unsigned int [:] uint_view
        cdef float [:] float_view
        cdef char *cdata = NULL
        cdef long datasize = 0
        if isinstance(pbuffer, bytes):  # if it's bytes, just use memory
            cdata = <bytes>pbuffer  # explicit bytes
            datasize = <long>len(pbuffer)
        else:   # if it's a memoryview or buffer type, use start of memory
            if glbufferfmt == GL_UNSIGNED_BYTE or glbufferfmt == GL_BYTE:
                char_view = pbuffer
                cdata = &char_view[0]
                datasize = char_view.nbytes
            elif glbufferfmt == GL_SHORT:
                short_view = pbuffer
                cdata = <char *>&short_view[0]
                datasize = short_view.nbytes
            elif glbufferfmt == GL_UNSIGNED_SHORT:
                ushort_view = pbuffer
                cdata = <char *>&ushort_view[0]
                datasize = ushort_view.nbytes
            elif glbufferfmt == GL_INT:
                int_view = pbuffer
                cdata = <char *>&int_view[0]
                datasize = int_view.nbytes
            elif glbufferfmt == GL_UNSIGNED_INT:
                uint_view = pbuffer
                cdata = <char *>&uint_view[0]
                datasize = uint_view.nbytes
            elif glbufferfmt == GL_FLOAT:
                float_view = pbuffer
                cdata = <char *>&float_view[0]
                datasize = float_view.nbytes

        # prepare nogil
        cdef int iglfmt = _color_fmt_to_gl(self._icolorfmt)
        cdef int glfmt = _color_fmt_to_gl(colorfmt)
        cdef int x = pos[0]
        cdef int y = pos[1]
        cdef int w = size[0]
        cdef int h = size[1]
        cdef int is_allocated = self._is_allocated
        cdef int is_compressed = _is_compressed_fmt(colorfmt)
        cdef int _mipmap_generation = mipmap_generation and self._mipmap
        cdef int _mipmap_level = mipmap_level

        # if there is a pitch/rowlength passed for the texture,
        # determine the alignment needed, and see if GL can handle it on the
        # current platform.
        cdef int bytes_per_pixels = _gl_format_size(glfmt)
        cdef int target_rowlength = w * bytes_per_pixels * _buffer_type_to_gl_size(bufferfmt)
        cdef int need_unpack = rowlength > 0 and rowlength != target_rowlength
        cdef char *cpdata = NULL
        cdef char *cpsrc
        cdef char *cpdst
        cdef int i
        cdef int require_subimage = 0

        # if the hardware doesn't support native unpack, use alternative method.
        if need_unpack and not gl_has_capability(GLCAP_UNPACK_SUBIMAGE):
            require_subimage = 1
            need_unpack = 0

        with nogil:

            if need_unpack:
                # native unpack supported, use it.
                cgl.glPixelStorei(GL_UNPACK_ROW_LENGTH, rowlength / bytes_per_pixels)
                if y != 0:
                    cgl.glPixelStorei(GL_UNPACK_SKIP_ROWS, y)
                if x != 0:
                    cgl.glPixelStorei(GL_UNPACK_SKIP_PIXELS, x)
                _gl_prepare_pixels_upload(rowlength)

            elif require_subimage:
                # make a temporary copy to a format without alignment for upload
                cpsrc = cdata
                cpdst = cpdata = <char *>malloc(target_rowlength * h)
                for i in range(h):
                    memcpy(cpdst, cpsrc, target_rowlength)
                    cpsrc += rowlength
                    cpdst += target_rowlength
                cdata = cpdata
                datasize = target_rowlength * h

            else:
                _gl_prepare_pixels_upload(w)

            if is_compressed:
                cgl.glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
                cgl.glCompressedTexImage2D(target, _mipmap_level, glfmt, w, h, 0,
                        <GLsizei>datasize, cdata)
            elif is_allocated:
                cgl.glTexSubImage2D(target, _mipmap_level, x, y, w, h, glfmt,
                    glbufferfmt, cdata)
            else:
                cgl.glTexImage2D(target, _mipmap_level, iglfmt, w, h, 0, glfmt,
                    glbufferfmt, cdata)

            if _mipmap_generation:
                cgl.glGenerateMipmap(target)

            if need_unpack:
                cgl.glPixelStorei(GL_UNPACK_ROW_LENGTH, 0)
                if y != 0:
                    cgl.glPixelStorei(GL_UNPACK_SKIP_ROWS, 0)
                if x != 0:
                    cgl.glPixelStorei(GL_UNPACK_SKIP_PIXELS, 0)
            elif require_subimage:
                if cpdata != NULL:
                    free(cpdata)

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
        if self._id != <GLuint>-1:
            return
        if self._source is None:
            # manual texture recreation
            texture = texture_create(self.size, self.colorfmt, self.bufferfmt,
                    self.mipmap)
        else:
            source = osource = self._source
            proto = None
            if source.startswith('zip|'):
                proto = 'zip'
                source = source[4:]
            chr = type(source)
            no_cache, filename, mipmap, count = source.split(chr('|'))
            source = chr(u'{}|{}|{}').format(filename, mipmap, count)

            if not proto:
                proto = filename.split(chr(':'), 1)[0]

            if proto in ('http', 'https', 'ftp', 'smb'):
                from kivy.loader import Loader
                self._proxyimage = Loader.image(filename)
                self._id = 0 # FIXME this will point to an invalid texture ...
                self._proxyimage.bind(on_load=self._on_proxyimage_loaded)
                if self._proxyimage.loaded:
                    self._on_proxyimage_loaded(self._proxyimage)
                return

            mipmap = 0 if mipmap == '0' else 1
            if count == '0':
                if proto =='zip' or filename.endswith('.gif'):
                    from kivy.core.image import ImageLoader
                    image = ImageLoader.load(filename, nocache=True, mipmap=mipmap)

                    texture_list = []
                    create_tex = self.create_from_data
                    for data in image._data[1:]:
                        tex = create_tex(data, mipmap=mipmap)
                        texture_list.append(tex)
                    self._sequenced_textures[filename] = texture_list
                else:
                    from kivy.core.image import Image
                    image = Image(filename, nocache=True, mipmap=mipmap)
                texture = image.texture
            else:
                item_no = int(count) - 1
                texture = self._sequenced_textures[filename][item_no]


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
            method = callback()
            if method is None:
                self.observers.remove(callback)
                continue
            method(self)

    def save(self, filename, flipped=True, fmt=None):
        '''Save the texture content to a file. Check
        :meth:`kivy.core.image.Image.save` for more information.

        The flipped parameter flips the saved image vertically, and
        defaults to True.

        .. versionadded:: 1.7.0

        .. versionchanged:: 1.8.0

            Parameter `flipped` added, defaults to True. All the OpenGL Texture
            are read from bottom / left, it need to be flipped before saving.
            If you don't want to flip the image, set flipped to False.

        .. versionchanged:: 1.11.0

            Parameter `fmt` added, to pass the final format to the image provider.
            Used if filename is a BytesIO
        '''
        from kivy.core.image import Image
        return Image(self).save(filename, flipped=flipped, fmt=fmt)

    def __repr__(self):
        return '<Texture hash=%r id=%d size=%r colorfmt=%r bufferfmt=%r source=%r observers=%d>' % (
            id(self), self._id, self.size, self.colorfmt, self.bufferfmt,
            self._source, len(self.observers))

    @property
    def size(self):
        '''Return the (width, height) of the texture (readonly).
        '''
        return (self.width, self.height)

    @property
    def mipmap(self):
        '''Return True if the texture has mipmap enabled (readonly).
        '''
        return self._mipmap

    @property
    def id(self):
        '''Return the OpenGL ID of the texture (readonly).
        '''
        return self._id

    @property
    def target(self):
        '''Return the OpenGL target of the texture (readonly).
        '''
        return self._target

    @property
    def width(self):
        '''Return the width of the texture (readonly).
        '''
        return self._width

    @property
    def height(self):
        '''Return the height of the texture (readonly).
        '''
        return self._height

    @property
    def tex_coords(self):
        '''Return the list of tex_coords (opengl).
        '''
        return (
            self._tex_coords[0],
            self._tex_coords[1],
            self._tex_coords[2],
            self._tex_coords[3],
            self._tex_coords[4],
            self._tex_coords[5],
            self._tex_coords[6],
            self._tex_coords[7])

    @property
    def uvpos(self):
        '''Get/set the UV position inside the texture.
        '''
        return (self._uvx, self._uvy)

    @uvpos.setter
    def uvpos(self, x):
        self._uvx, self._uvy = x
        self.update_tex_coords()

    @property
    def uvsize(self):
        '''Get/set the UV size inside the texture.

        .. warning::
            The size can be negative if the texture is flipped.
        '''
        return (self._uvw, self._uvh)

    @uvsize.setter
    def uvsize(self, x):
        self._uvw, self._uvh = x
        self.update_tex_coords()

    @property
    def colorfmt(self):
        '''Return the color format used in this texture (readonly).

        .. versionadded:: 1.0.7
        '''
        return self._colorfmt

    @property
    def bufferfmt(self):
        '''Return the buffer format used in this texture (readonly).

        .. versionadded:: 1.2.0
        '''
        return self._bufferfmt

    @property
    def min_filter(self):
        '''Get/set the min filter texture. Available values:

        - linear
        - nearest
        - linear_mipmap_linear
        - linear_mipmap_nearest
        - nearest_mipmap_nearest
        - nearest_mipmap_linear

        Check the opengl documentation for more information about the behavior
        of these values :
        http://www.khronos.org/opengles/sdk/docs/man/xhtml/glTexParameter.xml.
        '''
        return self._min_filter

    @min_filter.setter
    def min_filter(self, x):
        self.set_min_filter(x)

    @property
    def mag_filter(self):
        '''Get/set the mag filter texture. Available values:

        - linear
        - nearest

        Check the opengl documentation for more information about the behavior
        of these values :
        http://www.khronos.org/opengles/sdk/docs/man/xhtml/glTexParameter.xml.
        '''
        return self._mag_filter

    @mag_filter.setter
    def mag_filter(self, x):
        self.set_mag_filter(x)

    @property
    def wrap(self):
        '''Get/set the wrap texture. Available values:

        - repeat
        - mirrored_repeat
        - clamp_to_edge

        Check the opengl documentation for more information about the behavior
        of these values :
        http://www.khronos.org/opengles/sdk/docs/man/xhtml/glTexParameter.xml.
        '''
        return self._wrap

    @wrap.setter
    def wrap(self, wrap):
        self.set_wrap(wrap)

    @property
    def pixels(self):
        '''Get the pixels texture, in RGBA format only, unsigned byte. The
        origin of the image is at bottom left.

        .. versionadded:: 1.7.0
        '''
        from kivy.graphics.fbo import Fbo
        return Fbo(size=self.size, texture=self).pixels


cdef class TextureRegion(Texture):
    '''Handle a region of a Texture class. Useful for non power-of-2
    texture handling.'''

    def __init__(self, int x, int y, int width, int height, Texture origin):
        Texture.__init__(self, width, height, origin.target, origin.id)
        self._is_allocated = 1
        self._mipmap = origin._mipmap
        self._colorfmt = origin._colorfmt
        self._bufferfmt = origin._bufferfmt
        self._icolorfmt = origin._icolorfmt
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
            method = callback()
            if method is None:
                self.observers.remove(callback)
                continue
            method(self)

    def ask_update(self, callback):
        # redirect to owner
        self.owner.ask_update(callback)

    cpdef bind(self):
        self.owner.bind()

    @property
    def pixels(self):
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
