'''
SFML: SFML image loader
'''

__all__ = ('ImageLoaderSFML', )

from kivy.core.image import ImageData, ImageLoader, ImageLoaderBase
try:
    from sfml.graphics import Image
except:
    raise


class ImageLoaderSFML(ImageLoaderBase):
    '''Image loader based on SFML library.
    '''

    @staticmethod
    def extensions():
        return ('bmp', 'dds', 'jpg', 'png', 'tga', 'psd')

    def load(self, filename):
        try:
            im = Image.load_from_file(filename)
        except:
            Logger.warning('Image: Unable to load image {0}'.format(filename))

            raise

        self.filename = filename
        fmt = 'rgba'
        data = im.pixels.data

        return [ImageData(im.width, im.height, fmt, data, source=filename)]

ImageLoader.register(ImageLoaderSFML)
