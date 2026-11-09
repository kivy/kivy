'''
PIL: PIL image loader
'''

__all__ = ('ImageLoaderPIL', )

try:
    import Image as PILImage
except ImportError:
    # for python3
    from PIL import Image as PILImage

from kivy.logger import Logger
from kivy.core.image import ImageLoaderBase, ImageData, ImageLoader

try:
    # Pillow
    PILImage.frombytes
    PILImage.Image.tobytes
except AttributeError:
    # PIL
    # monkey patch frombytes and tobytes methods, refs:
    # https://github.com/kivy/kivy/issues/5460
    PILImage.frombytes = PILImage.frombuffer
    PILImage.Image.tobytes = PILImage.Image.tostring


class ImageLoaderPIL(ImageLoaderBase):
    '''Image loader based on the PIL library.

    .. versionadded:: 1.0.8

    Support for GIF animation added.

    Gif animation has a lot of issues(transparency/color depths... etc).
    In order to keep it simple, what is implemented here is what is
    natively supported by the PIL library.

    .. versionchanged:: 3.0.0
        Pillow composites the frames of a GIF animation itself, applying
        the disposal method, so the loader no longer pastes frames over
        each other.

    '''
    _provider_name = 'pil'

    @staticmethod
    def can_save(fmt, is_bytesio_like):
        if is_bytesio_like:
            return False
        return fmt in ImageLoaderPIL.extensions()

    @staticmethod
    def can_load_memory():
        return True

    @staticmethod
    def extensions():
        '''Return accepted extensions for this loader'''
        PILImage.init()
        return tuple((ext_with_dot[1:] for ext_with_dot in PILImage.EXTENSION))

    def _img_correct(self, _img_tmp):
        '''Convert image to the correct format and orientation.
        '''
        # image loader work only with rgb/rgba image
        if _img_tmp.mode.lower() not in ('rgb', 'rgba'):
            try:
                imc = _img_tmp.convert('RGBA')
            except Exception:
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

        # Read all images inside. Pillow composites each animation frame
        # onto the previous one, applying the disposal method.
        try:
            while True:
                img_tmp = self._img_correct(im)
                yield ImageData(img_tmp.size[0], img_tmp.size[1],
                                img_tmp.mode.lower(), img_tmp.tobytes())
                im.seek(im.tell() + 1)
        except EOFError:
            pass

    def load(self, filename):
        try:
            im = PILImage.open(filename)
        except Exception:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise
        # update internals
        if not self._inline:
            self.filename = filename
        # returns an array of type ImageData len 1 if not a sequence image
        return list(self._img_read(im))

    @staticmethod
    def save(filename, width, height, pixelfmt, pixels, flipped=False,
             imagefmt=None):
        image = PILImage.frombytes(pixelfmt.upper(), (width, height), pixels)
        if flipped:
            image = image.transpose(PILImage.FLIP_TOP_BOTTOM)
        image.save(filename)
        return True


# register
ImageLoader.register(ImageLoaderPIL)
