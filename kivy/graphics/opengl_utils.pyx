#cython: c_string_type=unicode, c_string_encoding=utf8
'''
OpenGL utilities
================

.. versionadded:: 1.0.7
'''

__all__ = ('gl_get_extensions', 'gl_has_extension',
        'gl_has_capability', 'gl_register_get_size',
        'gl_has_texture_format', 'gl_has_texture_conversion',
        'gl_has_texture_native_format', 'gl_get_texture_formats',
        'gl_get_version', 'gl_get_version_minor', 'gl_get_version_major',
        'GLCAP_BGRA', 'GLCAP_NPOT', 'GLCAP_S3TC', 'GLCAP_DXT1', 'GLCAP_ETC1')

include "config.pxi"
include "opengl_utils_def.pxi"
cimport c_opengl
if USE_OPENGL_DEBUG:
    cimport kivy.graphics.c_opengl_debug as cgl
elif USE_OPENGL_MOCK:
    cimport kivy.graphics.c_opengl_mock as cgl
else:
    cimport kivy.graphics.c_opengl as cgl
from kivy.logger import Logger
from kivy.utils import platform
from kivy.graphics.opengl import _GL_GET_SIZE


cdef list _gl_extensions = []
cdef dict _gl_caps = {}
cdef tuple _gl_texture_fmts = (
    'rgb', 'rgba', 'luminance', 'luminance_alpha',
    'bgr', 'bgra', 's3tc_dxt1', 's3tc_dxt3', 's3tc_dxt5',
    'pvrtc_rgb4', 'pvrtc_rgb2', 'pvrtc_rgba4', 'pvrtc_rgba2')
cdef int _gl_version_major = -1
cdef int _gl_version_minor = -1
cdef str _platform = str(platform)


cpdef list gl_get_extensions():
    '''Return a list of OpenGL extensions available. All the names in the list
    have the `GL_` stripped at the start (if it exists) and are in lowercase.

    >>> print(gl_get_extensions())
    ['arb_blend_func_extended', 'arb_color_buffer_float', 'arb_compatibility',
     'arb_copy_buffer'... ]

    '''
    global _gl_extensions
    cdef str extensions
    if not _gl_extensions:
        extensions = <char *>cgl.glGetString(c_opengl.GL_EXTENSIONS)
        _gl_extensions[:] = [x[3:].lower() if x[:3] == 'GL_' else x.lower()\
                for x in extensions.split()]
    return _gl_extensions


cpdef int gl_has_extension(name):
    '''Check if an OpenGL extension is available. If the name starts with `GL_`,
    it will be stripped for the test and converted to lowercase.

        >>> gl_has_extension('NV_get_tex_image')
        False
        >>> gl_has_extension('OES_texture_npot')
        True

    '''
    IF USE_OPENGL_MOCK:
        return True
    name = name.lower()
    if name.startswith('GL_'):
        name = name[3:]
    return name in gl_get_extensions()


cpdef gl_register_get_size(int constid, int size):
    '''Register an association between an OpenGL Const used in glGet* to a number
    of elements.

    By example, the GPU_MEMORY_INFO_DEDICATED_VIDMEM_NVX is a special pname that
    will return the integer 1 (nvidia only).

        >>> GPU_MEMORY_INFO_DEDICATED_VIDMEM_NVX = 0x9047
        >>> gl_register_get_size(GPU_MEMORY_INFO_DEDICATED_VIDMEM_NVX, 1)
        >>> glGetIntegerv(GPU_MEMORY_INFO_DEDICATED_VIDMEM_NVX)[0]
        524288

    '''
    _GL_GET_SIZE[constid] = size


cpdef int gl_has_capability(int cap):
    '''Return the status of a OpenGL Capability. This is a wrapper that
    auto-discovers all the capabilities that Kivy might need. The current
    capabilities tested are:

        - GLCAP_BGRA: Test the support of BGRA texture format
        - GLCAP_NPOT: Test the support of Non Power of Two texture
        - GLCAP_S3TC: Test the support of S3TC texture (DXT1, DXT3, DXT5)
        - GLCAP_DXT1: Test the support of DXT texture (subset of S3TC)
        - GLCAP_ETC1: Test the support of ETC1 texture

    '''
    cdef int value = _gl_caps.get(cap, -1)
    cdef str msg, sval

    # if we got a value, it's already initialized, return it!
    if value != -1:
        return value

    # ok, never been initialized, do it now.
    if cap == c_GLCAP_BGRA:
        msg = 'BGRA texture support'
        if _platform == 'ios':
            value = gl_has_extension('APPLE_texture_format_BGRA8888')
        else:
            value = gl_has_extension('EXT_bgra')
        if not value:
            value = gl_has_extension('EXT_texture_format_BGRA888')

    elif cap == c_GLCAP_NPOT:
        msg = 'NPOT texture support'
        if _platform == 'ios' or _platform == 'android':
            # Adreno 200 renderer doesn't support NPOT
            sval = <char *>cgl.glGetString(c_opengl.GL_RENDERER)
            if sval == 'Adreno 200':
                value = 0
            else:
                value = 1
        else:
            value = gl_has_extension('ARB_texture_non_power_of_two')
            if not value:
                value = gl_has_extension('OES_texture_npot')
            if not value:
                # motorola droid don't have OES_ but IMG_
                value = gl_has_extension('IMG_texture_npot')

    elif cap == c_GLCAP_S3TC:
        # S3TC support DXT1, DXT3 and DXT5
        msg = 'S3TC texture support'
        value = gl_has_extension('S3_s3tc')
        if not value:
            value = gl_has_extension('EXT_texture_compression_s3tc')
        if not value:
            value = gl_has_extension('OES_texture_compression_s3tc')

    elif cap == c_GLCAP_DXT1:
        # DXT1 is included inside S3TC, but not the inverse.
        msg = 'DXT1 texture support'
        value = gl_has_capability(c_GLCAP_S3TC)
        if not value:
            value = gl_has_extension('EXT_texture_compression_dxt1')

    elif cap == c_GLCAP_PVRTC:
        # PVRTC = PowerVR, mostly available in iOS device
        msg = 'PVRTC texture support'
        value = gl_has_extension('IMG_texture_compression_pvrtc')

    elif cap == c_GLCAP_ETC1:
        # PVRTC = PowerVR, mostly available in iOS device
        msg = 'ETC1 texture support'
        value = gl_has_extension('OES_compressed_ETC1_RGB8_texture')

    elif cap == c_GLCAP_UNPACK_SUBIMAGE:
        # Is GL_UNPACK_ROW_LENGTH is supported
        msg = 'Unpack subimage support'
        if _platform == 'ios' or _platform == 'android':
            value = gl_has_extension('EXT_unpack_subimage')
        else:
            value = 1

    else:
        raise Exception('Unknown capability')

    _gl_caps[cap] = value
    if value:
        Logger.info('GL: %s is available' % msg)
    else:
        Logger.warning('GL: %s is not available' % msg)

    return value


cpdef tuple gl_get_texture_formats():
    '''Return a list of texture formats recognized by kivy.
    The texture list is informative but might not been supported by your
    hardware. If you want a list of supported textures, you must filter that
    list as follows::

        supported_fmts = [gl_has_texture_format(x) for x in gl_get_texture_formats()]

    '''
    return _gl_texture_fmts


cpdef int gl_has_texture_native_format(fmt):
    '''Return 1 if the texture format is handled natively.

    >>> gl_has_texture_format('azdmok')
    0
    >>> gl_has_texture_format('rgba')
    1
    >>> gl_has_texture_format('s3tc_dxt1')
    [INFO   ] [GL          ] S3TC texture support is available
    [INFO   ] [GL          ] DXT1 texture support is available
    1

    '''
    if fmt in ('rgb', 'rgba', 'luminance', 'luminance_alpha', 'red', 'rg'):
        return 1
    if fmt in ('palette4_rgb8', 'palette4_rgba8', 'palette4_r5_g6_b5', 'palette4_rgba4', 'palette4_rgb5_a1', 'palette8_rgb8', 'palette8_rgba8', 'palette8_r5_g6_b5', 'palette8_rgba4', 'palette8_rgb5_a1'):
        return gl_has_extension('OES_compressed_paletted_texture')
    if fmt in ('bgr', 'bgra'):
        return gl_has_capability(c_GLCAP_BGRA)
    if fmt == 's3tc_dxt1':
        return gl_has_capability(c_GLCAP_DXT1)
    if fmt.startswith('s3tc_dxt'):
        return gl_has_capability(c_GLCAP_S3TC)
    if fmt.startswith('pvrtc_'):
        return gl_has_capability(c_GLCAP_PVRTC)
    if fmt.startswith('etc1_'):
        return gl_has_capability(c_GLCAP_ETC1)
    return 0


cpdef int gl_has_texture_conversion(fmt):
    '''Return 1 if the texture can be converted to a native format.
    '''
    return fmt in ('bgr', 'bgra')


cpdef int gl_has_texture_format(fmt):
    '''Return whether a texture format is supported by your system, natively or
    by conversion. For example, if your card doesn't support 'bgra', we are able
    to convert to 'rgba' but only in software mode.
    '''
    # check if the support of a format can be done natively
    if gl_has_texture_native_format(fmt):
        return 1
    # otherwise, check if it can be converted
    return gl_has_texture_conversion(fmt)


cpdef tuple gl_get_version():
    '''Return the (major, minor) OpenGL version, parsed from the GL_VERSION.

    .. versionadded:: 1.2.0
    '''

    global _gl_version_minor, _gl_version_major
    cdef str version

    if _gl_version_major == -1:

        _gl_version_minor = _gl_version_major = 0
        version = str(<char *>cgl.glGetString(c_opengl.GL_VERSION))

        try:
            # same parsing algo as Panda3D
            sver = ''
            found = 0
            for c in version:
                if found and c == ' ':
                    break
                if 49 <= ord(c) <= 57:
                    found = 1
                if found:
                    sver += c

            component = sver.split('.')
            if len(component) >= 1:
                _gl_version_major = int(component[0])
            if len(component) >= 2:
                _gl_version_minor = int(component[1])

        except:
            Logger.warning('OpenGL: Error while parsing GL_VERSION')

    return _gl_version_major, _gl_version_minor


cpdef int gl_get_version_major():
    '''Return the major component of the OpenGL version.

    .. versionadded:: 1.2.0
    '''
    if _gl_version_major == -1:
        gl_get_version()
    return _gl_version_major


cpdef int gl_get_version_minor():
    '''Return the minor component of the OpenGL version.

    .. versionadded:: 1.2.0
    '''
    if _gl_version_major == -1:
        gl_get_version()
    return _gl_version_minor
