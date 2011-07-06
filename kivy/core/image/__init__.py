'''
Image
=====

Core classes for loading image and convert them to
:class:`~kivy.graphics.texture.Texture`. The raw image data can be keep in
memory for further access.

.. note::

    Saving image is not yet supported.
'''

__all__ = ('Image', 'ImageLoader', 'ImageData')

from kivy.event import EventDispatcher
from kivy.core  import core_register_libs
from kivy.cache import Cache
from kivy.clock import Clock

# late binding
Texture = TextureRegion = None


class ImageData(object):
    '''Container for data image : width, height, fmt and data.

    .. warning::
        Only RGB and RGBA format are allowed.
    '''

    __slots__ = ('width', 'height', 'fmt', 'data')
    _supported_fmts = ('rgb', 'rgba', 'bgr', 'bgra')

    def __init__(self, width, height, fmt, data):
        assert fmt in ImageData._supported_fmts

        #: Image width in pixels
        self.width = int(width)

        #: Image height in pixels
        self.height = int(height)

        #: Decoded image format
        self.fmt = fmt

        #: Data bytes. Can be None if the data have been released
        self.data = data

    def release_data(self):
        self.data = None


class ImageLoaderBase(object):
    '''Base to implement an image loader.'''

    __slots__ = ('_texture', '_data', 'filename', 'keep_data',
                '_mipmap')

    def __init__(self, filename, **kwargs):
        self._mipmap   = kwargs.get('mipmap', False)
        self.keep_data = kwargs.get('keep_data', False)
        self.filename  = filename
        self._texture  = None
        self._data     = self.load(filename) # returns a array of type ImageData (sequenc of images)

    def load(self, filename):
        '''Load an image'''
        return None

    @property
    def width(self):
        '''Image width
        '''
        return self._data[0].width

    @property
    def height(self):
        '''Image height
        '''
        return self._data[0].height

    @property
    def size(self):
        '''Image size (width, height)
        '''
        return (self._data[0].width, self._data[0].height)

    @property
    def texture(self):
        '''Get the image texture (created on the first call)
        '''
        if self._texture is None:
            if self._data is None:
                return None
            self._texture = Texture.create_from_data(
                self._data[0], mipmap=self._mipmap)
            if not self.keep_data:
                self._data[0].release_data()
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
            raise Exception('Unknown extension <%s>, no loader found.' % ext)
        return im


class Image(EventDispatcher):
    '''Load an image, and store the size and texture.

    .. versionadded::
        In 1.0.7, mipmap attribute have been added, texture_mipmap and
        texture_rectangle have been deleted.

    :Parameters:
        `arg` : can be str or Texture or Image object
            A string is interpreted as a path to the image to be loaded.
            You can also provide a texture object or an already existing
            image object. In the latter case, a real copy of the given
            image object will be returned.
        `keep_data` : bool, default to False
            Keep the image data when texture is created
        `opacity` : float, default to 1.0
            Opacity of the image
        `scale` : float, default to 1.0
            Scale of the image
        `mipmap` : bool, default to False
            Create mipmap for the texture
    '''

    copy_attributes = ('_size', '_filename', '_texture', '_image',
                       '_mipmap')

    def __init__(self, arg, **kwargs):
        kwargs.setdefault('keep_data', False)

        super(Image, self).__init__()

        self._mipmap = kwargs.get('mipmap', False)
        self._keep_data = kwargs.get('keep_data')
        self._size = [0, 0]
        self._image = None
        self._filename = None
        self._texture = None
        self.anim_frame_delay = .2
        #^- lower means faster animation
        self._anim_possible = False
        #^- indicates more than one image if true
        self._anim_counter = 0
        #^- animation counter starts with 0
        self._iteration_done = False
        #^- indicator of images having been loded in cache

        self.register_event_type('on_texture_changed')
        #^- fire a event on animation of sequenced img's

        if isinstance(arg, Image):
            for attr in Image.copy_attributes:
                self.__setattr__(attr, arg.__getattribute__(attr))
        elif type(arg) in (Texture, TextureRegion):
            self._texture = arg
            self._size = self.texture.size
        elif isinstance(arg, ImageLoaderBase):
            self.image = arg
        elif isinstance(arg, basestring):
            self.filename = arg
        else:
            raise Exception('Unable to load image type %s' % str(type(arg)))

        self._img_iterate()
        # called after image is loaded/cached

    #---Animated Gif, zip imgs (001.ext, 002.ext...  in order of name )
    def _anim(self, *largs ):
        uid = '%s|%s|%s' % ( self._filename,
            self._mipmap, self._anim_counter)
        _tex = Cache.get('kv.texture', uid)
        if _tex:
            # <-if not last frame
            self._texture = _tex
            self._anim_counter += 1
            self.dispatch('on_texture_changed')
            # ^-fire a texture update(to be handled bu widget/s)
        else:
            # <-Restart animation from first Frame
            self._anim_counter = 0
            self._anim()

    #-------------------------------------------------------------------
    def reset_anim (self, allow_anim):
        # <- reset animation
        Clock.unschedule(self._anim)
        # <-stop animation
        if allow_anim and self._anim_possible:
            Clock.schedule_interval(
                self._anim,
                # <-function to animate
                self.anim_frame_delay)
                # <-frame delay .20secs by default
    #-------------------------------------------------------------------

    #-------------------------------------------------------------------#
    def _img_iterate(self, *largs):
    # Purpose: check if image has sequences then animate
        self._iteration_done = True
        imgcount = count = 0
        try:
            imgcount = len(self.image._data)
            # ^- length of sequence
        except:
            # <- this is raised when image is none and in cache
            pass
        uid = '%s|%s|%s' % ( self.filename, self._mipmap, count )
        _texture = Cache.get('kv.texture', uid)
        # ^-get texture for first image
        if not _texture:
            # -----if texture is not in cache
            while count < imgcount:
                # <-append the sequence of images to cache
                _texture  = Texture.create_from_data(
                        self.image._data[count], mipmap=self._mipmap)
                if not self.image.keep_data:
                    self.image._data[count].release_data()
                    # ^-release excess memory
                Cache.append('kv.texture', uid, _texture)
                # ^-Cache texture
                count += 1
                uid = '%s|%s|%s' % ( self.filename, self._mipmap, count)
        else:
            # <-texture already in cache for first image
            self._texture = _texture
            # ^-assign texture for non sequenced cached images
            self._size = self.texture.size
            uid = '%s|%s|%s' % ( self.filename, self._mipmap, 1)
            # ^-check if image has sequence in cache
            _texture = Cache.get('kv.texture', uid)
            # ^-get texture for second image
            if _texture:
                imgcount = 2
                # ^-enable animation (cached sequence img)
        if imgcount > 1:
            self._anim_possible = True
            # image sequence, animate
            self.reset_anim( True )
            self._texture = _texture
        if self.image: self.image._texture = self._texture = _texture
        # ^-image loaded for the first time
        _texture = None
    #------------------------------------------------------------------

    def on_texture_changed(self, *largs):
        pass
    #-------------------------------------------------------------------

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
            self._size[0] = self.image.width
            self._size[1] = self.image.height

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
        uid = '%s|%s|%s' % ( self.filename, self._mipmap, 0 )
        _texture = Cache.get('kv.texture', uid)
        if _texture:
            #if image in cache
            _texture = None
            pass
            # ^-img_iterate is going to be called after this in init
        else:
            # if image not already in cache then load
            _texture = None
            self.image = ImageLoader.load(
                    self._filename, keep_data=self._keep_data,
                    mipmap=self._mipmap)

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
            if not self._iteration_done:
                self._img_iterate()
            #return self.image.texture
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
        data = self.image._data[0]

        # can't use this function without ImageData
        if data.data is None:
            raise EOFError('Image data is missing, make sure that image is'
                           'loaded with keep_data=True keyword.')

        # check bounds
        x, y = int(x), int(y)
        if not (0 <= x < data.width and 0 <= y < data.height):
            raise IndexError('Position (%d, %d) is out of range.' % (x, y))

        assert data.fmt in ImageData._supported_fmts
        size = 3 if data.fmt in ('rgb', 'bgr') else 4
        index = y * data.width * size + x * size
        raw = data.data[index:index+size]
        color = map(lambda c: ord(c) / 255.0, raw)

        # conversion for BGR->RGB, BGR->RGBA format
        if data.fmt in ('bgr', 'bgra'):
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

# resolve binding.
from kivy.graphics.texture import Texture, TextureRegion

