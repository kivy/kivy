'''
SDL2 image loader
=================
'''

__all__ = ('ImageLoaderSDL2', )

from kivy.compat import PY2
from kivy.logger import Logger
from kivy.core.image import ImageLoaderBase, ImageData, ImageLoader
from kivy.core.image import _img_sdl2


class ImageLoaderSDL2(ImageLoaderBase):
    '''Image loader based on the PIL library'''

    def _ensure_ext(self):
        _img_sdl2.init()

    @staticmethod
    def extensions():
        '''Return accepted extensions for this loader'''
        return ('bmp', 'gif', 'jpg', 'jpeg', 'lbm', 'pcx', 'png', 'pnm', 'tga', 'tiff',
                'webp', 'xcf', 'xpm', 'xv')

    @staticmethod
    def can_save():
        return True

    def load(self, filename):
        info = _img_sdl2.load(filename)
        if not info:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise Exception('SDL2: Unable to load image')

        w, h, fmt, pixels, rowlength = info

        # update internals
        self.filename = filename
        return [ImageData(
            w, h, fmt, pixels, source=filename,
            rowlength=rowlength)]

    @staticmethod
    def save(filename, width, height, fmt, pixels):
        # TODO implement the save for sdl2
        #surface = SDL2.image.fromstring(
        #        pixels, (width, height), fmt.upper(), False)
        #SDL2.image.save(surface, filename)
        return True


# register
ImageLoader.register(ImageLoaderSDL2)
