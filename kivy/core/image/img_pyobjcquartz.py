
'''
PIL: PIL image loader
'''

__all__ = ('ImageLoaderPyObjCQuartz', )

try:
    from Quartz import *
    from Cocoa import *
    from kivy.utils import create_quartz_context, get_context_bitmap_data
except:
    raise

from kivy.logger import Logger
from array import array
from . import ImageLoaderBase, ImageData, ImageLoader


class ImageLoaderPyObjCQuartz(ImageLoaderBase):

    @staticmethod
    def extensions():
        '''Return accepted extension for this loader'''
        # See "Supported Image File Formats" in the Cocoa drawing guide
        sup = ['eps', 'epi', 'epsf', 'epsi', 'ps', 'tiff', 'tif', 'jpg',
               'jpeg', 'jpe', 'gif', 'png', 'pict', 'pct', 'pic', 'bmp',
               'BMPf', 'ico', 'icns']
        sup_up = [format.upper() for format in sup]
        return sup + sup_up

    def load(self, fn):
        try:
            url = CFURLCreateFromFileSystemRepresentation(None, fn, len(fn), 0)
            imgsrc = CGImageSourceCreateWithURL(url, None)
            img = CGImageSourceCreateImageAtIndex(imgsrc, 0, None)
            width = CGImageGetWidth(img)
            height = CGImageGetHeight(img)
            rect = CGRectMake(0, 0, width, height)
            space = CGColorSpaceCreateDeviceRGB()
            ctx = create_quartz_context(width, height)
            # This is necessary as the image would be vertically flipped otherwise
            CGContextTranslateCTM(ctx, 0, height)
            CGContextScaleCTM(ctx, 1, -1)
            CGContextDrawImage(ctx, rect, img)
            w, h, imgtype, data = get_context_bitmap_data(ctx)
            return ImageData(w, h, imgtype, data)
        except:
            raise
            Logger.warning('Image: Unable to load image <%s>' % fn)
            raise Exception('Unable to load image')


# register
ImageLoader.register(ImageLoaderPyObjCQuartz)
