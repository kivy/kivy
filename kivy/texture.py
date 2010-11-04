'''
Texture: abstraction to handle GL texture, and region
'''

__all__ = ('Texture', 'TextureRegion')

import os
import re
from array import array
from kivy import Logger
import OpenGL
from OpenGL.GL import GL_RGBA, GL_UNSIGNED_BYTE, GL_TEXTURE_MIN_FILTER, \
        GL_TEXTURE_MAG_FILTER, GL_TEXTURE_WRAP_T, GL_TEXTURE_WRAP_S, \
        GL_TEXTURE_2D, GL_TEXTURE_RECTANGLE_NV, GL_TEXTURE_RECTANGLE_ARB, \
        GL_CLAMP_TO_EDGE, GL_LINEAR_MIPMAP_LINEAR, GL_GENERATE_MIPMAP, \
        GL_TRUE, GL_LINEAR, GL_UNPACK_ALIGNMENT, GL_BGR, GL_BGRA, GL_RGB, \
        glEnable, glDisable, glBindTexture, glTexParameteri, glTexImage2D, \
        glTexSubImage2D, glFlush, glGenTextures, glDeleteTextures, \
        GLubyte, glPixelStorei, GL_LUMINANCE
from OpenGL.GL.NV.texture_rectangle import glInitTextureRectangleNV
from OpenGL.GL.ARB.texture_rectangle import glInitTextureRectangleARB
from OpenGL.extensions import hasGLExtension

# for a specific bug in 3.0.0, about deletion of framebuffer.
# same hack as FBO :(
OpenGLversion = tuple(int(re.match('^(\d+)', i).groups()[0]) \
                      for i in OpenGL.__version__.split('.'))
if OpenGLversion < (3, 0, 1):
    try:
        import numpy
        have_numpy = True
    except Exception:
        have_numpy = False


def _nearest_pow2(v):
    # From http://graphics.stanford.edu/~seander/bithacks.html#RoundUpPowerOf2
    # Credit: Sean Anderson
    v -= 1
    v |= v >> 1
    v |= v >> 2
    v |= v >> 4
    v |= v >> 8
    v |= v >> 16
    return v + 1

def _is_pow2(v):
    # http://graphics.stanford.edu/~seander/bithacks.html#DetermineIfPowerOf2
    return (v & (v - 1)) == 0

#
# Releasing texture through GC is problematic
# GC can happen in a middle of glBegin/glEnd
# So, to prevent that, call the _texture_release
# at flip time.
_texture_release_list = []
def _texture_release(*largs):
    global _texture_release_list
    for texture_id in _texture_release_list:
        # try/except are here to prevent an error like this :
        # Exception TypeError: "'NoneType' object is not callable"
        # in <bound method Texture.__del__ of <kivy.texture.Texture
        # object at 0x3a1acb0>> ignored
        #
        # It occured only when leaving the application.
        # So, maybe numpy or pyopengl is unloaded, and have weird things happen.
        #
        try:
            if OpenGLversion < (3, 0, 1) and have_numpy:
                glDeleteTextures(numpy.array(texture_id))
            else:
                glDeleteTextures(texture_id)
        except:
            pass

    # let the list to 0
    _texture_release_list = []

class Texture(object):
    '''Handle a OpenGL texture. This class can be used to create simple texture
    or complex texture based on ImageData.'''

    __slots__ = ('tex_coords', '_width', '_height', '_target', '_id', '_mipmap',
                '_gl_wrap', '_gl_min_filter', '_gl_mag_filter', '_rectangle')

    _has_bgr = None
    _has_bgr_tested = False
    _has_texture_nv = None
    _has_texture_arb = None

    def __init__(self, width, height, target, texid, mipmap=False, rectangle=False):
        self.tex_coords     = (0., 0., 1., 0., 1., 1., 0., 1.)
        self._width         = width
        self._height        = height
        self._target        = target
        self._id            = texid
        self._mipmap        = mipmap
        self._gl_wrap       = None
        self._gl_min_filter = None
        self._gl_mag_filter = None
        self._rectangle     = rectangle

    def __del__(self):
        # Add texture deletion outside GC call.
        # This case happen if some texture have been not deleted
        # before application exit...
        if _texture_release_list is not None:
            _texture_release_list.append(self.id)

    @property
    def mipmap(self):
        '''Return True if the texture have mipmap enabled (readonly)'''
        return self._mipmap

    @property
    def rectangle(self):
        '''Return True if the texture is a rectangle texture (readonly)'''
        return self._rectangle

    @property
    def id(self):
        '''Return the OpenGL ID of the texture (readonly)'''
        return self._id

    @property
    def target(self):
        '''Return the OpenGL target of the texture (readonly)'''
        return self._target

    @property
    def width(self):
        '''Return the width of the texture (readonly)'''
        return self._width

    @property
    def height(self):
        '''Return the height of the texture (readonly)'''
        return self._height

    def flip_vertical(self):
        '''Flip tex_coords for vertical displaying'''
        a, b, c, d, e, f, g, h = self.tex_coords
        self.tex_coords = (g, h, e, f, c, d, a, b)

    def get_region(self, x, y, width, height):
        '''Return a part of the texture, from (x,y) with (width,height)
        dimensions'''
        return TextureRegion(x, y, width, height, self)

    def bind(self):
        '''Bind the texture to current opengl state'''
        glBindTexture(self.target, self.id)

    def enable(self):
        '''Do the appropriate glEnable()'''
        glEnable(self.target)

    def disable(self):
        '''Do the appropriate glDisable()'''
        glDisable(self.target)

    def _get_min_filter(self):
        return self._gl_min_filter
    def _set_min_filter(self, x):
        if x == self._gl_min_filter:
            return
        self.bind()
        glTexParameteri(self.target, GL_TEXTURE_MIN_FILTER, x)
        self._gl_min_filter = x
    min_filter = property(_get_min_filter, _set_min_filter,
                          doc='''Get/set the GL_TEXTURE_MIN_FILTER property''')

    def _get_mag_filter(self):
        return self._gl_mag_filter
    def _set_mag_filter(self, x):
        if x == self._gl_mag_filter:
            return
        self.bind()
        glTexParameteri(self.target, GL_TEXTURE_MAG_FILTER, x)
        self._gl_mag_filter = x
    mag_filter = property(_get_mag_filter, _set_mag_filter,
                          doc='''Get/set the GL_TEXTURE_MAG_FILTER property''')

    def _get_wrap(self):
        return self._gl_wrap
    def _set_wrap(self, wrap):
        if wrap == self._gl_wrap:
            return
        self.bind()
        glTexParameteri(self.target, GL_TEXTURE_WRAP_S, wrap)
        glTexParameteri(self.target, GL_TEXTURE_WRAP_T, wrap)
    wrap = property(_get_wrap, _set_wrap,
                    doc='''Get/set the GL_TEXTURE_WRAP_S,T property''')

    @staticmethod
    def create(width, height, format=GL_RGBA, rectangle=False, mipmap=False):
        '''Create a texture based on size.'''
        target = GL_TEXTURE_2D
        rectangle = False
        if rectangle:
            if _is_pow2(width) and _is_pow2(height):
                rectangle = False
            else:
                rectangle = False

                try:
                    if Texture._has_texture_nv is None:
                        Texture._has_texture_nv = glInitTextureRectangleNV()
                    if Texture._has_texture_nv:
                        target = GL_TEXTURE_RECTANGLE_NV
                        rectangle = True
                except Exception:
                    pass

                try:
                    if Texture._has_texture_arb is None:
                        Texture._has_texture_arb = glInitTextureRectangleARB()
                    if not rectangle and Texture._has_texture_arb:
                        target = GL_TEXTURE_RECTANGLE_ARB
                        rectangle = True
                except Exception:
                    pass

                if not rectangle:
                    Logger.debug(
                        'Texture: Missing support for rectangular texture')
                else:
                    # Can't do mipmap with rectangle texture
                    mipmap = False

        if rectangle:
            texture_width = width
            texture_height = height
        else:
            texture_width = _nearest_pow2(width)
            texture_height = _nearest_pow2(height)

        texid = glGenTextures(1)
        texture = Texture(texture_width, texture_height, target, texid,
                          mipmap=mipmap)

        texture.bind()
        texture.wrap        = GL_CLAMP_TO_EDGE
        if mipmap:
            texture.min_filter  = GL_LINEAR_MIPMAP_LINEAR
            #texture.mag_filter  = GL_LINEAR_MIPMAP_LINEAR
            glTexParameteri(GL_TEXTURE_2D, GL_GENERATE_MIPMAP, GL_TRUE)
        else:
            texture.min_filter  = GL_LINEAR
            texture.mag_filter  = GL_LINEAR

        if not Texture.is_gl_format_supported(format):
            format = Texture.convert_gl_format(format)

        data = (GLubyte * texture_width * texture_height *
                Texture.gl_format_size(format))()
        glTexImage2D(target, 0, format, texture_width, texture_height, 0,
                     format, GL_UNSIGNED_BYTE, data)

        if rectangle:
            texture.tex_coords = \
                (0., 0., width, 0., width, height, 0., height)

        glFlush()

        if texture_width == width and texture_height == height:
            return texture

        return texture.get_region(0, 0, width, height)

    @staticmethod
    def create_from_data(im, rectangle=True, mipmap=False):
        '''Create a texture from an ImageData class'''

        format = Texture.mode_to_gl_format(im.mode)

        texture = Texture.create(im.width, im.height,
                                 format, rectangle=rectangle,
                                 mipmap=mipmap)
        if texture is None:
            return None

        texture.blit_data(im)

        return texture

    def blit_data(self, im, pos=(0, 0)):
        '''Replace a whole texture with a image data'''
        self.blit_buffer(im.data, size=(im.width, im.height),
                         mode=im.mode, pos=pos)

    def blit_buffer(self, buffer, size=None, mode='RGB', format=None,
                    pos=(0, 0), buffertype=GL_UNSIGNED_BYTE):
        '''Blit a buffer into a texture.

        :Parameters:
            `buffer` : str
                Image data
            `size` : tuple, default to texture size
                Size of the image (width, height)
            `mode` : str, default to 'RGB'
                Image mode, can be one of RGB, RGBA, BGR, BGRA
            `format` : glconst, default to None
                if format is passed, it will be used instead of mode
            `pos` : tuple, default to (0, 0)
                Position to blit in the texture
            `buffertype` : glglconst, default to GL_UNSIGNED_BYTE
                Type of the data buffer
        '''
        if size is None:
            size = self.size
        if format is None:
            format = self.mode_to_gl_format(mode)
        target = self.target
        glBindTexture(target, self.id)
        glEnable(target)

        # activate 1 alignement, of window failed on updating weird size
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

        # need conversion ?
        pdata, format = self._convert_buffer(buffer, format)

        # transfer the new part of texture
        glTexSubImage2D(target, 0, pos[0], pos[1],
                        size[0], size[1], format,
                        buffertype, pdata)

        glFlush()
        glDisable(target)

    @staticmethod
    def has_bgr():
        if not Texture._has_bgr_tested:
            Logger.warning('Texture: BGR/BGRA format is not supported by'
                           'your graphic card')
            Logger.warning('Texture: Software conversion will be done to'
                           'RGB/RGBA')
            Texture._has_bgr = hasGLExtension('GL_EXT_bgra')
            Texture._has_bgr_tested = True
        return Texture._has_bgr

    @staticmethod
    def is_gl_format_supported(format):
        if format in (GL_BGR, GL_BGRA):
            return not Texture.has_bgr()
        return True

    @staticmethod
    def convert_gl_format(format):
        if format == GL_BGR:
            return GL_RGB
        elif format == GL_BGRA:
            return GL_RGBA
        return format

    def _convert_buffer(self, data, format):
        # check if format is supported by user
        ret_format = format
        ret_buffer = data

        # BGR / BGRA conversion not supported by hardware ?
        if not Texture.is_gl_format_supported(format):
            if format == GL_BGR:
                ret_format = GL_RGB
                a = array('b', data)
                a[0::3], a[2::3] = a[2::3], a[0::3]
                ret_buffer = a.tostring()
            elif format == GL_BGRA:
                ret_format = GL_RGBA
                a = array('b', data)
                a[0::4], a[2::4] = a[2::4], a[0::4]
                ret_buffer = a.tostring()
            else:
                Logger.critical('Texture: non implemented'
                                '%s texture conversion' % str(format))
                raise Exception('Unimplemented texture conversion for %s' %
                                str(format))
        return ret_buffer, ret_format

    @property
    def size(self):
        return (self.width, self.height)

    @staticmethod
    def mode_to_gl_format(format):
        if format == 'RGBA':
            return GL_RGBA
        elif format == 'BGRA':
            return GL_BGRA
        elif format == 'BGR':
            return GL_BGR
        else:
            return GL_RGB

    @staticmethod
    def gl_format_size(format):
        if format in (GL_RGB, GL_BGR):
            return 3
        elif format in (GL_RGBA, GL_BGRA):
            return 4
        elif format in (GL_LUMINANCE, ):
            return 1
        raise Exception('Unsupported format size <%s>' % str(format))

    def __str__(self):
        return '<Texture size=(%d, %d)>' % self.size


class TextureRegion(Texture):
    '''Handle a region of a Texture class. Useful for non power-of-2
    texture handling.'''

    __slots__ = ('x', 'y', 'owner')

    def __init__(self, x, y, width, height, origin):
        super(TextureRegion, self).__init__(
            width, height, origin.target, origin.id)
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

if 'KIVY_DOC' not in os.environ:
    from kivy.clock import Clock

    # install tick to release texture every 200ms
    Clock.schedule_interval(_texture_release, 0.2)

