'''
Pygame: Pygame image loader

.. warning::

    Pygame has been deprecated and will be removed in the release after Kivy
    1.11.0.
'''

__all__ = ('ImageLoaderPygame', )

from kivy.logger import Logger
from kivy.core.image import ImageLoaderBase, ImageData, ImageLoader
from os.path import isfile
from kivy.utils import deprecated

try:
    import pygame
except:
    raise


class ImageLoaderPygame(ImageLoaderBase):
    '''Image loader based on the PIL library'''

    @deprecated(
        msg='Pygame has been deprecated and will be removed after 1.11.0')
    def __init__(self, *largs, **kwargs):
        super(ImageLoaderPygame, self).__init__(*largs, **kwargs)

    @staticmethod
    def extensions():
        '''Return accepted extensions for this loader'''
        # under OS X, i got with "pygame.error: File is not a Windows BMP
        # file". documentation said: The image module is a required dependency
        # of Pygame, but it only optionally supports any extended file formats.
        # By default it can only load uncompressed BMP image
        if pygame.image.get_extended() == 0:
            return ('bmp', )
        return ('jpg', 'jpeg', 'jpe', 'png', 'bmp', 'pcx', 'tga', 'tiff',
                'tif', 'lbm', 'pbm', 'ppm', 'xpm')

    @staticmethod
    def can_save(fmt, is_bytesio):
        if is_bytesio:
            return False
        return fmt in ('png', 'jpg')

    @staticmethod
    def can_load_memory():
        return True

    def load(self, filename):
        if not filename:
            import traceback
            traceback.print_stack()
            return
        try:
            im = None
            if self._inline:
                im = pygame.image.load(filename, 'x.{}'.format(self._ext))
            elif isfile(filename):
                with open(filename, 'rb') as fd:
                    im = pygame.image.load(fd)
            elif isinstance(filename, bytes):
                try:
                    fname = filename.decode()
                    if isfile(fname):
                        with open(fname, 'rb') as fd:
                            im = pygame.image.load(fd)
                except UnicodeDecodeError:
                    pass
            if im is None:
                im = pygame.image.load(filename)
        except:
            # Logger.warning(type(filename)('Image: Unable to load image <%s>')
            #               % filename)
            raise

        fmt = ''
        if im.get_bytesize() == 3 and not im.get_colorkey():
            fmt = 'rgb'
        elif im.get_bytesize() == 4:
            fmt = 'rgba'

        # image loader work only with rgb/rgba image
        if fmt not in ('rgb', 'rgba'):
            try:
                imc = im.convert(32)
                fmt = 'rgba'
            except:
                try:
                    imc = im.convert_alpha()
                    fmt = 'rgba'
                except:
                    Logger.warning(
                        'Image: Unable to convert image %r to rgba (was %r)' %
                        (filename, im.fmt))
                    raise
            im = imc

        # update internals
        if not self._inline:
            self.filename = filename
        data = pygame.image.tostring(im, fmt.upper())
        return [ImageData(im.get_width(), im.get_height(),
                fmt, data, source=filename)]

    @staticmethod
    def save(filename, width, height, pixelfmt, pixels, flipped,
             imagefmt=None):
        surface = pygame.image.fromstring(
            pixels, (width, height), pixelfmt.upper(), flipped)
        pygame.image.save(surface, filename)
        return True


# register
ImageLoader.register(ImageLoaderPygame)
