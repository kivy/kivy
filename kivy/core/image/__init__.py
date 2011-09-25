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
from kivy.core import core_register_libs
from kivy.logger import Logger
from kivy.cache import Cache
from kivy.clock import Clock
import zipfile
try:
    import cStringIO as SIO
except ImportError:
    import StringIO as SIO


# late binding
Texture = TextureRegion = None


# register image caching only for keep_data=True
Cache.register('kv.image', timeout=60)


class ImageData(object):
    '''Container for image and mipmap images.
    The container will always have at least the mipmap level 0.
    '''

    __slots__ = ('fmt', 'mipmaps')
    _supported_fmts = ('rgb', 'rgba', 'bgr', 'bgra',
            's3tc_dxt1', 's3tc_dxt3', 's3tc_dxt5')

    def __init__(self, width, height, fmt, data):
        assert fmt in ImageData._supported_fmts

        #: Decoded image format, one of a available texture format
        self.fmt = fmt

        #: Data for each mipmap.
        self.mipmaps = {}
        self.add_mipmap(0, width, height, data)

    def release_data(self):
        mm = self.mipmaps
        for item in mm.itervalues():
            item[2] = None

    @property
    def width(self):
        '''Image width in pixels.
        (If the image is mipmapped, it will use the level 0)
        '''
        return self.mipmaps[0][0]

    @property
    def height(self):
        '''Image height in pixels.
        (If the image is mipmapped, it will use the level 0)
        '''
        return self.mipmaps[0][1]

    @property
    def data(self):
        '''Image data.
        (If the image is mipmapped, it will use the level 0)
        '''
        return self.mipmaps[0][2]

    @property
    def size(self):
        '''Image (width, height) in pixels.
        (If the image is mipmapped, it will use the level 0)
        '''
        mm = self.mipmaps[0]
        return mm[0], mm[1]

    @property
    def have_mipmap(self):
        return len(self.mipmaps) > 1

    def __repr__(self):
        return '<ImageData width=%d height=%d fmt=%s with %d images>' % (
                self.width, self.height, self.fmt, len(self.mipmaps))

    def add_mipmap(self, level, width, height, data):
        '''Add a image for a specific mipmap level.

        .. versionadded:: 1.0.7
        '''
        self.mipmaps[level] = [int(width), int(height), data]

    def get_mipmap(self, level):
        '''Get the mipmap image at a specific level if exist

        .. versionadded:: 1.0.7
        '''
        if level == 0:
            return (self.width, self.height, self.data)
        assert(level < len(self.mipmaps))
        return self.mipmaps[level]

    def iterate_mipmaps(self):
        '''Iterate over all mipmap images available

        .. versionadded:: 1.0.7
        '''
        mm = self.mipmaps
        for x in xrange(len(mm)):
            item = mm.get(x, None)
            if item is None:
                raise Exception('Invalid mipmap level, found empty one')
            yield x, item[0], item[1], item[2]


class ImageLoaderBase(object):
    '''Base to implement an image loader.'''

    __slots__ = ('_texture', '_data', 'filename', 'keep_data',
                '_mipmap')

    def __init__(self, filename, **kwargs):
        self._mipmap = kwargs.get('mipmap', False)
        self.keep_data = kwargs.get('keep_data', False)
        self.filename = filename
        self._texture = None
        self._data = self.load(filename)

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
    def zip_loader(_filename, **kwargs):
        '''Read images from an zip file.

        .. versionadded:: 1.0.8

        Returns an Image with a list/array of type ImageData stored in
        Image._data
        '''
        # Read all images inside
        z = zipfile.ZipFile(_filename, 'r')
        image_data = []
        #sort filename list
        znamelist = z.namelist()
        znamelist.sort()
        #for each file in zip
        for zfilename in znamelist:
            try:
                #read file and store it in mem with fileIO struct around it
                tmpfile = SIO.StringIO(z.read(zfilename))
                ext = zfilename.split('.')[-1].lower()
                im = None
                for loader in ImageLoader.loaders:
                    if ext not in loader.extensions():
                        continue
                    im = loader(tmpfile, **kwargs)
                    break
                if im is not None:
                    #append ImageData to local variable before it's overwritten
                    image_data.append(im._data[0])
                #else: if not image file skip to next
            except:
                Logger.warning('Image: Unable to load image' +
                    '<%s> in zip <%s> trying to continue...'
                    % (zfilename, _filename))
                #raise# return the data read till now
                #this should Ideally handle truncated zips
        z.close()
        if len(image_data) == 0:
            raise Exception('no images in zip <%s>' % _filename)
        #replace Image.Data with the array of all the images in the zip
        im._data = image_data
        # Done
        return im

    @staticmethod
    def register(defcls):
        ImageLoader.loaders.append(defcls)

    @staticmethod
    def load(filename, **kwargs):
        # extract extensions
        ext = filename.split('.')[-1].lower()

        # special case. When we are trying to load a "zip" file with image, we
        # will use the special zip_loader in ImageLoader. This might return a
        # sequence of images contained in the zip.
        if ext == 'zip':
            return ImageLoader.zip_loader(filename)
        else:
            im = None
            for loader in ImageLoader.loaders:
                if ext not in loader.extensions():
                    continue
                im = loader(filename, **kwargs)
                break
            if im is None:
                raise Exception('Unknown <%s> type, no loader found.' % ext)
            return im


class Image(EventDispatcher):
    '''Load an image, and store the size and texture.

    .. versionadded::
        In 1.0.7, mipmap attribute have been added, texture_mipmap and
        texture_rectangle have been deleted.

    .. versionadded::
        In 1.0.8, Image widget might change itself the texture. A new event
        'on_texture' have been introduced. New methods for handling sequenced
        animation too.

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
        `anim_delay`: float, default to .25
            Delay in seconds between each animation frame. Lower means faster
            animation.
    '''

    copy_attributes = ('_size', '_filename', '_texture', '_image',
                       '_mipmap')

    def __init__(self, arg, **kwargs):
        super(Image, self).__init__()

        self._mipmap = kwargs.get('mipmap', False)
        self._keep_data = kwargs.get('keep_data', False)
        self._size = [0, 0]
        self._image = None
        self._filename = None
        self._texture = None
        self._anim_available = False
        self._anim_index = 0
        self._anim_delay = 0
        self.anim_delay = kwargs.get('anim_delay', .25)
        # indicator of images having been loded in cache
        self._iteration_done = False
        # this event should be fired on animation of sequenced img's
        self.register_event_type('on_texture')

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

        # check if the image hase sequences for animation in it
        self._img_iterate()

    def _anim(self, *largs):
        # called on every interval of clock as set by anim_reset
        uid = '%s|%s|%s' % (self._filename, self._mipmap, self._anim_index)
        _tex = Cache.get('kv.texture', uid)
        if _tex:
            # if not last frame
            self._texture = _tex
            self._anim_index += 1
            # fire a texture update(to be handled by widget/s)
            self.dispatch('on_texture')
        else:
            # Prevent infinite looping in case we set manually an image
            if self._anim_index == 0:
                return False
            # Restart animation from first Frame
            self._anim_index = 0
            self._anim()

    def anim_reset(self, allow_anim):
        '''Reset an animation if available.

        .. versionadded:: 1.0.8

        :Parameters:
            `allow_anim`: bool
                Indicate if the animation should restart playing or not.

        Usage::

            # start/reset animation
            image.anim_reset(True)

            # or stop the animation
            image.anim_reset(False)

        You can change the animation speed in live::

            # Set to 20 FPS
            image.anim_delay = 1 / 20.

        '''
        # stop animation
        Clock.unschedule(self._anim)
        if allow_anim and self._anim_available:
            Clock.schedule_interval(self._anim, self.anim_delay)

    def _get_anim_delay(self):
        return self._anim_delay

    def _set_anim_delay(self, x):
        if self._anim_delay == x:
            return
        self._anim_delay = x
        if self._anim_available:
            Clock.unschedule(self._anim)
            if self._anim_delay >= 0:
                Clock.schedule_interval(self._anim, self._anim_delay)

    anim_delay = property(_get_anim_delay, _set_anim_delay)
    '''Delay betwean each animation frame. Lower means faster animation.

    .. versionadded:: 1.0.8
    '''

    @property
    def anim_available(self):
        '''Return True if this Image instance have animation available.

        .. versionadded:: 1.0.8
        '''
        return self._anim_available

    @property
    def anim_index(self):
        '''Return the index number of the image currently in the texture

        .. versionadded:: 1.0.8
        '''
        return self._anim_index

    def _img_iterate(self, *largs):
        # Purpose: check if image has sequences then animate
        self._iteration_done = True
        imgcount = count = 0
        if self.image:
            imgcount = len(self.image._data)
        # get texture for first image from cache
        uid = '%s|%s|%s' % (self.filename, self._mipmap, count)
        _texture = Cache.get('kv.texture', uid)
        if not _texture:
            # if texture is not in cache
            while count < imgcount:
                # append the sequence of images to cache
                _texture= Texture.create_from_data(
                        self.image._data[count], mipmap=self._mipmap)
                if not self.image.keep_data:
                    # release excess memory
                    self.image._data[count].release_data()
                # Cache texture
                Cache.append('kv.texture', uid, _texture)
                count += 1
                uid = '%s|%s|%s' % (self.filename, self._mipmap, count)
        else:
            # texture already in cache for first image
            # assign texture for non sequenced cached images
            self._texture = _texture
            self._size = self.texture.size
            # check if image has sequence in cache
            uid = '%s|%s|%s' % (self.filename, self._mipmap, 1)
            # get texture for second image in sequence
            _texture_next = Cache.get('kv.texture', uid)
            if _texture_next:
                # enable animation (cached sequence img)
                imgcount = 2
                _texture = _texture_next
        if imgcount > 1:
            self._anim_available = True
            # image sequence, animate
            self.anim_reset(True)
            self._texture = _texture
        # image loaded for the first time
        if self.image:
            self.image._texture = self._texture = _texture

    def on_texture(self, *largs):
        '''This event is fired when the texture reference or content have been
        changed. It's actually used for sequenced images.

        .. versionadded:: 1.0.8
        '''
        pass

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
        if hasattr(image, 'filename'):
            self._filename = image.filename
        if image:
            self._size = (self.image.width, self.image.height)

    image = property(_get_image, _set_image,
            doc='Get/set the data image object')

    def _get_filename(self):
        return self._filename

    def _set_filename(self, value):
        if value is None or value == self._filename:
            return
        self._filename = value

        # construct uid as a key for Cache
        uid = '%s|%s|%s' % (self.filename, self._mipmap, 0)
        keep_data = self._keep_data

        # in case of Image have been asked with keep_data
        # check the kv.image cache instead of texture.
        if keep_data:
            image = Cache.get('kv.image', uid)
            if image:
                # we found an image, yeah ! but reset the texture now.
                self.image = image
                self._texture = None
                self._img_iterate()
                return
        else:
            # if we already got a texture, it will be automatically reloaded.
            _texture = Cache.get('kv.texture', uid)
            if _texture:
                return

        # if image not already in cache then load
        tmpfilename = self._filename
        self.image = ImageLoader.load(
                self._filename, keep_data=self._keep_data,
                mipmap=self._mipmap)
        self._filename = tmpfilename
        # put the image into the cache if needed
        if keep_data:
            Cache.append('kv.image', uid, self.image)

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

        # can't use this fonction without ImageData
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
    ('dds', 'img_dds'),
    ('pygame', 'img_pygame'),
    ('pil', 'img_pil'),
    ('gif', 'img_gif'),
))

# resolve binding.
from kivy.graphics.texture import Texture, TextureRegion

