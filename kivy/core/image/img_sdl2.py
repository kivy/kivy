'''
SDL2 image loader
=================
'''

__all__ = ('ImageLoaderSDL2', )

from kivy.logger import Logger
from kivy.core.image import ImageLoaderBase, ImageData, ImageLoader
from kivy.core.image import _img_sdl2


class ImageLoaderSDL2(ImageLoaderBase):
    '''Image loader based on SDL2_image'''

    def _ensure_ext(self):
        _img_sdl2.init()

    @staticmethod
    def extensions():
        '''Return accepted extensions for this loader'''
        return ('bmp', 'jpg', 'jpeg', 'jpe', 'lbm', 'pcx', 'png', 'pnm',
                'tga', 'tiff', 'webp', 'xcf', 'xpm', 'xv')

    @staticmethod
    def can_save():
        return True

    @staticmethod
    def can_load_memory():
        return True

    def load(self, filename):
        if self._inline:
            data = filename.read()
            info = _img_sdl2.load_from_memory(data)
        else:
            info = _img_sdl2.load_from_filename(filename)
        if not info:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise Exception('SDL2: Unable to load image')

        w, h, fmt, pixels, rowlength = info

        # update internals
        if not self._inline:
            self.filename = filename
        return [ImageData(
            w, h, fmt, pixels, source=filename,
            rowlength=rowlength)]

    @staticmethod
    def save(filename, width, height, fmt, pixels, flipped):
        _img_sdl2.save(filename, width, height, fmt, pixels, flipped)
        return True


# register
ImageLoader.register(ImageLoaderSDL2)
