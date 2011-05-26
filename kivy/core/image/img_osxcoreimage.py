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
        # XXX
        return ('bmp', 'bufr', 'cur', 'dcx', 'fits', 'fl', 'fpx', 'gbr',
                'gd', 'gif', 'grib', 'hdf5', 'ico', 'im', 'imt', 'iptc',
                'jpeg', 'jpg', 'mcidas', 'mic', 'mpeg', 'msp', 'pcd',
                'pcx', 'pixar', 'png', 'ppm', 'psd', 'sgi', 'spider',
                'tga', 'tiff', 'wal', 'wmf', 'xbm', 'xpm', 'xv')

    def load(self, filename):
        #ret = osxcoreimage.load_raw_image_data(filename)
        ret = osxcoreimage.load_image_data(filename)
        if ret is None:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise Exception('Unable to load image')
        w, h, imgtype, data = ret
        print 'loading image:', filename, w, h, imgtype, 'size:', len(data)
        if 'testpattern' in filename:
            colors = map(lambda c: ord(c) / 255.0, data)
            print colors, '================================' * 5, repr(data)
        return ImageData(w, h, imgtype, data)


# register
ImageLoader.register(ImageLoaderOSXCoreImage)
