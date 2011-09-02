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
            dds = DDSFile(filename=filename)
        except:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise

        self.filename = filename
        width, height = dds.size
        im = ImageData(width, height, dds.dxt, dds.images[0])
        if len(dds.images) > 1:
            images = dds.images
            images_size = dds.images_size
            for index in xrange(1, len(dds.images)):
                w, h = images_size[index]
                data = images[index]
                im.add_mipmap(index, w, h, data)
        return [im]

# register
ImageLoader.register(ImageLoaderDDS)
