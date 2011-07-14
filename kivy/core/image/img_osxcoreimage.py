'''
PIL: PIL image loader
'''

__all__ = ('ImageLoaderOSXCoreImage', )

try:
    from kivy.core.image import osxcoreimage
except:
    raise

from kivy.logger import Logger
from . import ImageLoaderBase, ImageData, ImageLoader


class ImageLoaderOSXCoreImage(ImageLoaderBase):
    '''Image loader based on PIL library'''

    @staticmethod
    def extensions():
        '''Return accepted extension for this loader'''
        # See "Supported Image File Formats" in the Cocoa drawing guide
        sup = ['eps', 'epi', 'epsf', 'epsi', 'ps', 'tiff', 'tif', 'jpg',
               'jpeg', 'jpe', 'gif', 'png', 'pict', 'pct', 'pic', 'bmp',
               'BMPf', 'ico', 'icns']
        sup_up = [format.upper() for format in sup]
        return sup + sup_up

    def load(self, filename):
        ret = osxcoreimage.load_image_data(filename)
        if ret is None:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise Exception('Unable to load image')
        w, h, imgtype, data = ret
        return ImageData(w, h, imgtype, data)


# register
ImageLoader.register(ImageLoaderOSXCoreImage)
