'''
Image: handle loading of images
'''

__all__ = ('Image', 'ImageLoader', 'ImageData')

from kivy.event import EventDispatcher
from kivy.core import core_register_libs
from kivy.texture import Texture, TextureRegion

class ImageData(object):
    '''Container for data image : width, height, mode and data.

    .. warning::
        Only RGB and RGBA mode are allowed.
    '''

    __slots__ = ('width', 'height', 'mode', 'data')
    _supported_modes = ('RGB', 'RGBA', 'BGR', 'BGRA')

    def __init__(self, width, height, mode, data):
        assert mode in ImageData._supported_modes
        self.width = int(width)
        self.height = int(height)
        self.mode = mode
        self.data = data

    def release_data(self):
        self.data = None


class ImageLoaderBase(object):
    '''Base to implement an image loader.'''

    __slots__ = ('_texture', '_data', 'filename', 'keep_data',
                '_texture_rectangle', '_texture_mipmap')

    def __init__(self, filename, **kwargs):
        self._texture_rectangle = kwargs.get('texture_rectangle', True)
        self._texture_mipmap = kwargs.get('texture_mipmap', False)
        self.keep_data  = kwargs.get('keep_data', False)
        self.filename   = filename
        self._texture   = None
        self._data      = self.load(filename)

    def load(self, filename):
        '''Load an image'''
        return None

    @property
    def width(self):
        '''Image width
        '''
        return self._data.width

    @property
    def height(self):
        '''Image height
        '''
        return self._data.height

    @property
    def size(self):
        '''Image size (width, height)
        '''
        return (self._data.width, self._data.height)

    @property
    def texture(self):
        '''Get the image texture (created on the first call)
        '''
        if self._texture is None:
            if self._data is None:
                return None
            self._texture = Texture.create_from_data(
                self._data, rectangle=self._texture_rectangle,
                mipmap=self._texture_mipmap)
            if not self.keep_data:
                self._data.release_data()
        return self._texture


class ImageLoader(object):
    __slots__ = ('loaders')
    loaders = []

    @staticmethod
    def register(defcls):
        ImageLoader.loaders.append(defcls)

    @staticmethod
    def load(filename, **kwargs):
        # extract extensions
        ext = filename.split('.')[-1].lower()
        im = None
        for loader in ImageLoader.loaders:
            if ext not in loader.extensions():
                continue
            im = loader(filename, **kwargs)
            break
        if im is None:
            raise Exception('Unsupported extension <%s>, no loader found.' % ext)
        return im


class Image(EventDispatcher):
    '''Load an image, and store the size and texture.

    :Parameters:
        `arg` : can be str or Texture or Image object
            A string is interpreted as a path to the image that should be loaded.
            You can also provide a texture object or an already existing image object.
            In the latter case, a real copy of the given image object will be
            returned.
        `keep_data` : bool, default to False
            Keep the image data when texture is created
        `opacity` : float, default to 1.0
            Opacity of the image
        `scale` : float, default to 1.0
            Scale of the image
        `texture_rectangle` : bool, default to True
            Use rectangle texture is available (if false, will use the nearest
            power of 2 size for texture)
        `texture_mipmap` : bool, default to False
            Create mipmap for the texture
    '''

    copy_attributes = ('_size', '_filename', '_texture', '_image',
                       '_texture_rectangle', '_texture_mipmap')

    def __init__(self, arg, **kwargs):
        kwargs.setdefault('keep_data', False)

        super(Image, self).__init__()

        self._texture_rectangle = kwargs.get('texture_rectangle', True)
        self._texture_mipmap    = kwargs.get('texture_mipmap', False)
        self._keep_data = kwargs.get('keep_data')
        self._size      = [0, 0]
        self._image     = None
        self._filename  = None
        self._texture   = None

        if isinstance(arg, Image):
            for attr in Image.copy_attributes:
                self.__setattr__(attr, arg.__getattribute__(attr))
        elif type(arg) in (Texture, TextureRegion):
            self._texture   = arg
            self._size      = self.texture.size
        elif isinstance(arg, ImageLoaderBase):
            self.image      = arg
        elif isinstance(arg, basestring):
            self.filename   = arg
        else:
            raise Exception('Unable to load image with type %s' % str(type(arg)))

    @staticmethod
    def load(filename, **kwargs):
        '''Load an image

        :Parameters:
            `filename` : str
                Filename of the image
            `keep_data` : bool, default to False
                Keep the image data when texture is created
        '''
        kwargs.setdefault('keep_data', False)
        return Image(filename, **kwargs)

    def _get_image(self):
        return self._image
    def _set_image(self, image):
        self._image = image
        if image:
            self._size[0]      = self.image.width
            self._size[1]     = self.image.height
    image = property(_get_image, _set_image,
            doc='Get/set the data image object')

    def _get_filename(self):
        return self._filename
    def _set_filename(self, value):
        if value is None:
            return
        if value == self._filename:
            return
        self._filename = value
        self.image     = ImageLoader.load(
                self._filename, keep_data=self._keep_data,
                texture_rectangle=self._texture_rectangle,
                texture_mipmap=self._texture_mipmap)
    filename = property(_get_filename, _set_filename,
            doc='Get/set the filename of image')

    @property
    def size(self):
        '''Image size (width, height)
        '''
        return self._size

    @property
    def width(self):
        '''Image width
        '''
        return self._size[0]

    @property
    def height(self):
        '''Image height
        '''
        return self._size[1]

    @property
    def texture(self):
        '''Texture of the image'''
        if self.image:
            return self.image.texture
        return self._texture

    def read_pixel(self, x, y):
        '''For a given local x/y position, return the color at that position.

        .. warning::
            This function can be used only with images loaded with
            keep_data=True keyword. For examples ::

                m = Image.load('image.png', keep_data=True)
                color = m.read_pixel(150, 150)

        :Parameters:
            `x` : int
                Local x coordinate of the pixel in question.
            `y` : int
                Local y coordinate of the pixel in question.
        '''
        data = self.image._data

        # can't use this fonction without ImageData
        if data.data is None:
            raise EOFError('Image data is missing, make sure that image is'
                           'loaded with keep_data=True keyword.')

        # check bounds
        x, y = int(x), int(y)
        if not (0 <= x < data.width and 0 <= y < data.height):
            raise IndexError('Position (%d, %d) is out of range.' % (x, y))

        assert data.mode in ImageData._supported_modes
        size = 3 if data.mode in ('RGB', 'BGR') else 4
        index = y * data.width * size + x * size
        raw = data.data[index:index+size]
        color = map(lambda c: ord(c) / 255.0, raw)

        # conversion for BGR->RGB, BGR->RGBA format
        if data.mode in ('BGR', 'BGRA'):
            color[0], color[2] = color[2], color[0]

        return color


def load(filename):
    '''Load an image'''
    return Image.load(filename)

# load image loaders
core_register_libs('image', (
    ('pygame', 'img_pygame'),
    ('pil', 'img_pil'),
))
