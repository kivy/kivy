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
        # retrieve from http://www.pygame.org/docs/ref/image.html
        return ('jpg', 'png', 'gif', 'bmp', 'pcx', 'tga', 'tiff', 'tif', 'lbm',
               'pbm', 'ppm', 'xpm')

    def load(self, filename):
        Logger.debug('Image: Load <%s>' % filename)
        try:
            im = pygame.image.load(filename)
        except:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise

        mode = ''
        if im.get_bytesize() == 3:
            mode = 'RGB'
        elif im.get_bytesize() == 4:
            mode = 'RGBA'

        # image loader work only with rgb/rgba image
        if mode not in ('RGB', 'RGBA'):
            try:
                imc = im.convert(32)
                mode = 'RGBA'
            except:
                Logger.warning(
                    'Image: Unable to convert image <%s> to RGBA (was %s)' %
                    filename, im.mode)
                raise
            im = imc

        # update internals
        self.filename = filename
        data = pygame.image.tostring(im, mode, True)
        return ImageData(im.get_width(), im.get_height(),
            mode, data)


# register
ImageLoader.register(ImageLoaderPygame)
