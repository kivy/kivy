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


class ImageSequence:
    '''ImageSequence: Image sequences in array

    NOTE:
        gif animation has a lot of Issues(transparency/color depths... etc).
        In order to keep simple what is implimented here is what is natively
        supported by pil

        As a general rule try to use gifs that have no transparency
        gif's with transparency will work but be ready for some
        artifacts for now.
    '''

    def __init__(self, im):
        self.im = im

    def img_correct(self, _img_tmp):
        '''Convert image to the correct format and orientation.
        '''
        # image loader work only with rgb/rgba image
        if _img_tmp.mode.lower() not in ('rgb', 'rgba'):
            try:
                imc = _img_tmp.convert('RGBA')
            except:
                Logger.warning(
                    'Image: Unable to convert image to rgba (was %s)' %
                    (_img_tmp.mode.lower()))
                raise
            _img_tmp = imc
            # image are not in the good direction, flip !
        _img_tmp = _img_tmp.transpose(Image.FLIP_TOP_BOTTOM)
        return _img_tmp

    def _img_array(self):
        '''Read images from an animated file.
        Returns a list/array of typ ImageData
        '''
        pilIm = self.im
        pilIm.seek(0)

        # Read all images inside
        image_data = []
        try:
            while True:
                img_tmp = pilIm
                img_tmp = self.img_correct(img_tmp)
                image_data.append(ImageData(img_tmp.size[0], img_tmp.size[1],
                                img_tmp.mode.lower(), img_tmp.tostring()))
                pilIm.seek(pilIm.tell()+1)
        except EOFError:
            pass
        # Done
        return image_data


class ImageLoaderPIL(ImageLoaderBase):
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
        Logger.debug('Image: Load <%s>' % filename)
        try:
            im = Image.open(filename)
        except:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise
        # sequence image class
        img_sq = ImageSequence(im)
        # update internals
        self.filename = filename
        # returns a arrayof type ImageData len 1 if not a sequence image
        return  img_sq._img_array()

# register
ImageLoader.register(ImageLoaderPIL)
