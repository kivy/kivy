'''
PIL: PIL image loader
'''

__all__ = ('ImageLoaderPIL', )

try:
    from PIL import Image as PILImage
except:
    import Image as PILImage

from kivy.logger import Logger
from kivy.core.image import ImageLoaderBase, ImageData, ImageLoader


class ImageLoaderPIL(ImageLoaderBase):
    '''Image loader based on the PIL library.

    .. versionadded::

        In 1.0.8, support for GIF animation was added.

        Gif animation has a lot of issues(transparency/color depths... etc).
        In order to keep it simple, what is implimented here is what is
        natively supported by the PIL library.

        As a general rule, try to use gifs that have no transparency.
        Gif's with transparency will work but be prepared for some
        artifacts until transparency support is improved.

    '''

    @staticmethod
    def can_save():
        return True

    @staticmethod
    def extensions():
        '''Return accepted extensions for this loader'''
        # See http://www.pythonware.com/library/pil/handbook/index.htm
        return ('bmp', 'bufr', 'cur', 'dcx', 'fits', 'fl', 'fpx', 'gbr',
                'gd', 'gif', 'grib', 'hdf5', 'ico', 'im', 'imt', 'iptc',
                'jpeg', 'jpg', 'mcidas', 'mic', 'mpeg', 'msp', 'pcd',
                'pcx', 'pixar', 'png', 'ppm', 'psd', 'sgi', 'spider',
                'tga', 'tiff', 'wal', 'wmf', 'xbm', 'xpm', 'xv')

    def _img_correct(self, _img_tmp):
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

        return _img_tmp

    def _img_read(self, im):
        '''Read images from an animated file.
        '''
        im.seek(0)

        # Read all images inside
        try:
            img_ol = None
            while True:
                img_tmp = im
                img_tmp = self._img_correct(img_tmp)
                if img_ol:
                    # paste new frame over old so as to handle
                    # transparency properly
                    img_ol.paste(img_tmp, (0, 0), img_tmp)
                    img_tmp = img_ol
                img_ol = img_tmp
                yield ImageData(img_tmp.size[0], img_tmp.size[1],
                                img_tmp.mode.lower(), img_tmp.tostring())
                im.seek(im.tell() + 1)
        except EOFError:
            pass

    def load(self, filename):
        try:
            im = PILImage.open(filename)
        except:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise
        # update internals
        self.filename = filename
        # returns an array of type ImageData len 1 if not a sequence image
        return list(self._img_read(im))

    @staticmethod
    def save(filename, width, height, fmt, pixels):
        image = PILImage.fromstring(fmt.upper(), (width, height), pixels)
        image.save(filename)
        return True


# register
ImageLoader.register(ImageLoaderPIL)
