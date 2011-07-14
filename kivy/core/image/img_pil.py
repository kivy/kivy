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
import zipfile
#####  focus on trying to remove these
import numpy as np
import cStringIO as SIO

class ImageSequence:
    """ Class ImageSequence: handle images with sequences
    """

    def __init__(self, im):
        self.im = im
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
    def img_correct(self, _img_tmp):
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
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
    def _img_array_from_zip(self, _filename):
        """
        Read images from an zip file.
        Returns a list/array of typ ImageData
        """
        # Read all images inside
        z = zipfile.ZipFile(_filename, 'r')
        image_data = []
        for item in z.namelist():
            try:
                tmpfile = z.read(item)
                img_tmp = Image.open((SIO.StringIO(tmpfile)))
                image_data.append(ImageData(img_tmp.size[0], img_tmp.size[1],
                                img_tmp.mode.lower(), img_tmp.tostring()))
            except:
                Logger.warning('Image: Unable to load image <%s>' % _filename)
                #raise# return the data read till now
                #this should Ideally handle truncated zips
        z.close()
        # Done
        return image_data
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
    def _img_array(self):
        """
        Read images from an animated file.
        Returns a list/array of typ ImageData
        """
        # Check Numpy
        if np is None:
            raise RuntimeError("Need Numpy to read animated gif files.")

        pilIm = self.im
        pilIm.seek(0)

        # Read all images inside
        images = []
        try:
            while True:
                # Get image as numpy array
                tmp = pilIm.convert() # Make without palette
                a = np.asarray(tmp)
                if len(a.shape)==0:
                    raise MemoryError("Too little memory to convert \
                        PIL image to array")
                # Store, and next
                images.append(a)
                pilIm.seek(pilIm.tell()+1)
        except EOFError:
            pass
        # Convert to normal PIL images if needed
        image_data = []
        for im in images:
            img_tmp = Image.fromarray(im)
            img_tmp = self.img_correct(img_tmp)
            image_data.append(ImageData(img_tmp.size[0], img_tmp.size[1],
                                img_tmp.mode.lower(), img_tmp.tostring()))
        # Done
        return image_data
#-----------------------------------------------------------------------------


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
                'tga', 'tiff', 'wal', 'wmf', 'xbm', 'xpm', 'xv', 'zip')
                #  addition of .zip image sequences
    def load(self, filename):
        Logger.debug('Image: Load <%s>' % filename)
        # handle zip's differently
        ext = filename.split('.')[-1].lower()
        if ext == 'zip':
            # update internals
            self.filename = filename
            img_sq = ImageSequence(None)
            # returns a array of type ImageData
            # of len 1 if not a sequence image
            return  img_sq._img_array_from_zip(filename)
        else:
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
