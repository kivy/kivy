'''
OpenGL utilities
================

.. versionadded:: 1.0.7
'''

__all__ = ('gl_get_extensions', 'gl_has_extension',
        'gl_has_capability', 'gl_register_get_size',
        'gl_has_texture_format', 'gl_has_texture_conversion',
        'gl_has_texture_native_format', 'gl_get_texture_formats',
        'GLCAP_BGRA', 'GLCAP_NPOT', 'GLCAP_S3TC', 'GLCAP_DXT1')

include "opengl_utils_def.pxi"
cimport c_opengl
from kivy.logger import Logger
from opengl import _GL_GET_SIZE


cdef list _gl_extensions = []
cdef dict _gl_caps = {}
cdef tuple _gl_texture_fmts = (
    'rgb', 'rgba', 'luminance', 'luminance_alpha',
    'bgr', 'bgra', 's3tc_dxt1', 's3tc_dxt3', 's3tc_dxt5')


cpdef list gl_get_extensions():
    '''Return a list of OpenGL extensions available. All the names in the list
    have the `GL_` stripped at the start if exist, and are in lowercase.

    >>> print gl_get_extensions()
    ['arb_blend_func_extended', 'arb_color_buffer_float', 'arb_compatibility',
     'arb_copy_buffer'... ]

    '''
    global _gl_extensions
    cdef bytes extensions
    if not _gl_extensions:
        extensions = <char *>c_opengl.glGetString(c_opengl.GL_EXTENSIONS)
        _gl_extensions[:] = [x[3:].lower() if x[:3] == 'GL_' else x.lower()\
                for x in extensions.split()]
    return _gl_extensions


cpdef int gl_has_extension(str name):
    '''Check if an OpenGL extension is available. If the name start with `GL_`,
    it will be stripped for the test, and converted to lowercase.

        >>> gl_has_extension('NV_get_tex_image')
        False
        >>> gl_has_extension('OES_texture_npot')
        True

    '''
    name = name.lower()
    if name.startswith('GL_'):
        name = name[3:]
    return name in gl_get_extensions()


cpdef gl_register_get_size(int constid, int size):
    '''Register an association between a OpenGL Const used in glGet* to a number
    of elements.

    By example, the GPU_MEMORY_INFO_DEDICATED_VIDMEM_NVX is a special pname that
    will return 1 integer (nvidia only).

        >>> GPU_MEMORY_INFO_DEDICATED_VIDMEM_NVX = 0x9047
        >>> gl_register_get_size(GPU_MEMORY_INFO_DEDICATED_VIDMEM_NVX, 1)
        >>> glGetIntegerv(GPU_MEMORY_INFO_DEDICATED_VIDMEM_NVX)[0]
        524288

    '''
    _GL_GET_SIZE[constid] = size


cpdef int gl_has_capability(int cap):
    '''Return the status of a OpenGL Capability. This is a wrapper that auto
    discover all the capabilities that Kivy might need. The current capabilites
    test are:

        - GLCAP_BGRA: Test the support of BGRA texture format
        - GLCAP_NPOT: Test the support of Non Power of Two texture
        - GLCAP_S3TC: Test the support of S3TC texture (DXT1, DXT3, DXT5)
        - GLCAP_DXT1: Test the support of DXT texture (subset of S3TC)

    '''
    cdef int value = _gl_caps.get(cap, -1)
    cdef str msg

    # if we got a value, it's already initialized, return it!
    if value!= -1:
        return value

    # ok, never been initialized, do it now.
    if cap == c_GLCAP_BGRA:
        msg = 'BGRA texture support'
        value = gl_has_extension('EXT_bgra')

    elif cap == c_GLCAP_NPOT:
        msg = 'NPOT texture support'
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

    else:
        raise Exception('Unknown capability')

    _gl_caps[cap] = value
    if value:
        Logger.info('GL: %s is available' % msg)
    else:
        Logger.warning('GL: %s is not available' % msg)

    return value


cpdef tuple gl_get_texture_formats():
    '''Return a list of texture format recognized by kivy.
    The texture list is informative, but might not been supported by your
    hardware. If you want a list of supported textures, you must filter that
    list like that::

        supported_fmts = [gl_has_texture_format(x) for x in gl_get_texture_formats()]

    '''
    return _gl_texture_fmts


cpdef int gl_has_texture_native_format(str fmt):
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
    if fmt in ('rgb', 'rgba', 'luminance', 'luminance_alpha'):
        return 1
    if fmt in ('bgr', 'bgra'):
        return gl_has_capability(c_GLCAP_BGRA)
    if fmt == 's3tc_dxt1':
        return gl_has_capability(c_GLCAP_DXT1)
    if fmt.startswith('s3tc_dxt'):
        return gl_has_capability(c_GLCAP_S3TC)
    return 0


cpdef int gl_has_texture_conversion(str fmt):
    '''Return 1 if the texture can be converted to a native format
    '''
    return fmt in ('bgr', 'bgra')


cpdef int gl_has_texture_format(str fmt):
    '''Return if a texture format is supported by your system, natively or by
    conversion. For example, if your card doesn't support 'bgra', we are able to
    convert to 'rgba', but in software mode.
    '''
    # check if the support of a format can be done natively
    if gl_has_texture_native_format(fmt):
        return 1
    # otherwise, check if it can be converted
    return gl_has_texture_conversion(fmt)
