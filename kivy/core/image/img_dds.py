'''
DDS: DDS image loader
'''

__all__ = ('ImageLoaderDDS', )

from kivy.lib.ddsfile import DDSFile
from kivy.logger import Logger
from . import ImageLoaderBase, ImageData, ImageLoader

class ImageLoaderDDS(ImageLoaderBase):

    @staticmethod
    def extensions():
        return ('dds', )

    def load(self, filename):
        Logger.debug('Image: Load <%s>' % filename)
        try:
            im = DDSFile(filename=filename)
        except:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise

        self.filename = filename
        width, height = im.size
        return ImageData(width, height, im.dxt, im.images[0])

# register
ImageLoader.register(ImageLoaderDDS)
