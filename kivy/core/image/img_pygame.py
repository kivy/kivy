'''
Pygame: Pygame image loader
'''

__all__ = ('ImageLoaderPygame', )

from kivy.logger import Logger
from . import ImageLoaderBase, ImageData, ImageLoader

try:
    import pygame
except:
    raise


class ImageLoaderPygame(ImageLoaderBase):
    '''Image loader based on PIL library'''

    @staticmethod
    def extensions():
        '''Return accepted extension for this loader'''
        # under macosx, i got with "pygame.error: File is not a Windows BMP
        # file". documentation said: The image module is a required dependency
        # of Pygame, but it only optionally supports any extended file formats.
        # By default it can only load uncompressed BMP image
        if pygame.image.get_extended() == 0:
            return ('bmp', )
        # Note to self:try to learn to use loader preferences instead-
        # of this- remove gif support from pygame
        return ('jpg', 'jpeg', 'png', 'bmp', 'pcx', 'tga', 'tiff', 'tif', 'lbm',
               'pbm', 'ppm', 'xpm')

    def load(self, filename):
        try:
            try:
                im = pygame.image.load(filename)
            except UnicodeEncodeError:
                im = pygame.image.load(filename.encode('utf8'))
        except:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise

        fmt = ''
        if im.get_bytesize() == 3:
            fmt = 'rgb'
        elif im.get_bytesize() == 4:
            fmt = 'rgba'

        # image loader work only with rgb/rgba image
        if fmt not in ('rgb', 'rgba'):
            try:
                imc = im.convert(32)
                fmt = 'rgba'
            except:
                Logger.warning(
                    'Image: Unable to convert image <%s> to rgba (was %s)' %
                    filename, im.fmt)
                raise
            im = imc

        # update internals
        self.filename = filename
        data = pygame.image.tostring(im, fmt.upper(), True)
        return [ImageData(im.get_width(), im.get_height(), fmt, data)]

# register
ImageLoader.register(ImageLoaderPygame)
