'''
PIL: PIL image loader
'''

__all__ = ('ImageLoaderPIL', )

try:
    from PIL import Image
except:
    raise

from kivy.logger import Logger
from . import ImageLoaderBase, ImageData, ImageLoader


class ImageLoaderPIL(ImageLoaderBase):
    '''Image loader based on PIL library'''

    @staticmethod
    def extensions():
        '''Return accepted extension for this loader'''
        # See http://www.pythonware.com/library/pil/handbook/index.htm
        return ('bmp', 'bufr', 'cur', 'dcx', 'eps', 'fits', 'fl', 'fpx', 'gbr',
                'gd', 'gif', 'grib', 'hdf5', 'ico', 'im', 'imt', 'iptc',
                'jpeg', 'jpg', 'mcidas', 'mic', 'mpeg', 'msp', 'palm', 'pcd',
                'pcx', 'pdf', 'pixar', 'png', 'ppm', 'psd', 'sgi', 'spider',
                'tga', 'tiff', 'wal', 'wmf', 'xbm', 'xpm', 'xv')

    def load(self, filename):
        Logger.debug('Image: Load <%s>' % filename)
        try:
            im = Image.open(filename)
        except:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise

        # image loader work only with rgb/rgba image
        if im.mode.lower() not in ('rgb', 'rgba'):
            try:
                imc = im.convert('RGBA')
            except:
                Logger.warning(
                    'Image: Unable to convert image <%s> to rgba (was %s)' %
                    (filename, im.mode.lower()))
                raise
            im = imc

        # image are not in the good direction, flip !
        im = im.transpose(Image.FLIP_TOP_BOTTOM)

        # update internals
        self.filename = filename

        return ImageData(im.size[0], im.size[1],
            im.mode.lower(), im.tostring())

# register
ImageLoader.register(ImageLoaderPIL)
