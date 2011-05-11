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
        # See http://www.pythonware.com/library/pil/handbook/index.htm
        return ('bmp', 'bufr', 'cur', 'dcx', 'fits', 'fl', 'fpx', 'gbr',
                'gd', 'gif', 'grib', 'hdf5', 'ico', 'im', 'imt', 'iptc',
                'jpeg', 'jpg', 'mcidas', 'mic', 'mpeg', 'msp', 'pcd',
                'pcx', 'pixar', 'png', 'ppm', 'psd', 'sgi', 'spider',
                'tga', 'tiff', 'wal', 'wmf', 'xbm', 'xpm', 'xv')

    def load(self, filename):
        print 'before'
        print osxcoreimage.load_raw_image_data('/Users/dennda/blobs1.png')
        print 'after'
        return ImageData(64, 64, 'rgb', '\xff'*64*64*3)

# register
ImageLoader.register(ImageLoaderOSXCoreImage)
