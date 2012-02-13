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
from kivy.atlas import Atlas
from kivy.resources import resource_find
import zipfile
try:
    SIO = __import__('cStringIO')
except ImportError:
    SIO = __import__('StringIO')


# late binding
Texture = TextureRegion = None


# register image caching only for keep_data=True
Cache.register('kv.image', timeout=60)
Cache.register('kv.atlas')


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
        self._data = self.load(filename)
        self._textures = None

    def load(self, filename):
        '''Load an image'''
        return None

    def populate(self):
        self._textures = []
        if __debug__:
            Logger.trace('Image: %r, populate to textures (%d)' %
                    (self.filename, len(self._data)))

        for count in xrange(len(self._data)):

            # first, check if a texture with the same name already exist in the
            # cache
            uid = '%s|%s|%s' % (self.filename, self._mipmap, count)
            texture = Cache.get('kv.texture', uid)

            # if not create it and append to the cache
            if texture is None:
                texture = Texture.create_from_data(
                        self._data[count], mipmap=self._mipmap)
                Cache.append('kv.texture', uid, texture)

            # set as our current texture
            self._textures.append(texture)

            # release data if ask
            if not self.keep_data:
                self._data[count].release_data()

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
        if self._textures is None:
            self.populate()
        if self._textures is None:
            return None
        return self._textures[0]

    @property
    def textures(self):
        '''Get the textures list (for mipmapped image or animated image)

        .. versionadded:: 1.0.8
        '''
        if self._textures is None:
            self.populate()
        return self._textures


class ImageLoader(object):
    __slots__ = ('loaders')
    loaders = []

    @staticmethod
    def zip_loader(filename, **kwargs):
        '''Read images from an zip file.

        .. versionadded:: 1.0.8

        Returns an Image with a list/array of type ImageData stored in
        Image._data
        '''
        # read all images inside the zip
        z = zipfile.ZipFile(filename, 'r')
        image_data = []
        # sort filename list
        znamelist = z.namelist()
        znamelist.sort()
        for zfilename in znamelist:
            try:
                #read file and store it in mem with fileIO struct around it
                tmpfile = SIO.StringIO(z.read(zfilename))
                ext = zfilename.split('.')[-1].lower()
                im = None
                for loader in ImageLoader.loaders:
                    if ext not in loader.extensions():
                        continue
                    Logger.debug('Image%s: Load <%s> from <%s>' %
                            (loader.__name__[11:], zfilename, filename))
                    im = loader(tmpfile, **kwargs)
                    break
                if im is not None:
                    # append ImageData to local variable before it's overwritten
                    image_data.append(im._data[0])
                #else: if not image file skip to next
            except:
                Logger.warning('Image: Unable to load image' +
                    '<%s> in zip <%s> trying to continue...'
                    % (zfilename, filename))
        z.close()
        if len(image_data) == 0:
            raise Exception('no images in zip <%s>' % filename)
        # replace Image.Data with the array of all the images in the zip
        im._data = image_data
        im.filename = filename
        return im

    @staticmethod
    def register(defcls):
        ImageLoader.loaders.append(defcls)

    @staticmethod
    def load(filename, **kwargs):

        # atlas ?
        if filename[:8] == 'atlas://':
            # remove the url
            rfn = filename[8:]
            # last field is the ID
            try:
                rfn, uid = rfn.rsplit('/', 1)
            except ValueError:
                raise ValueError('Image: Invalid %s name for atlas' % filename)

            # search if we already got the atlas loaded
            atlas = Cache.get('kv.atlas', rfn)

            # atlas already loaded, so reupload the missing texture in cache,
            # because when it's not in use, the texture can be removed from the
            # kv.texture cache.
            if atlas:
                #print 'ATLAS REUSE', filename
                texture = atlas[uid]
                fn = 'atlas://%s/%s' % (rfn, uid)
                cid = '%s|%s|%s' % (fn, False, 0)
                Cache.append('kv.texture', cid, texture)
                return texture

            # search with resource
            afn = rfn
            if not afn.endswith('.atlas'):
                afn += '.atlas'
            afn = resource_find(afn)
            if not afn:
                raise Exception('Unable to found %r atlas' % afn)
            #print 'ATLAS LOAD', filename
            atlas = Atlas(afn)
            Cache.append('kv.atlas', rfn, atlas)
            # first time, fill our texture cache.
            for nid, texture in atlas.textures.iteritems():
                fn = 'atlas://%s/%s' % (rfn, nid)
                cid = '%s|%s|%s' % (fn, False, 0)
                #print 'register', cid
                Cache.append('kv.texture', cid, texture)
            return atlas[uid]

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
                Logger.debug('Image%s: Load <%s>' %
                        (loader.__name__[11:], filename))
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
        # this event should be fired on animation of sequenced img's
        self.register_event_type('on_texture')

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
        if not self._image:
            return
        textures = self.image.textures
        if self._anim_index >= len(textures):
            self.anim_reset(False)
            self._anim_index = 0
        self._texture = self.image.textures[self._anim_index]
        self.dispatch('on_texture')
        self._anim_index += 1
        self._anim_index %= len(self._image.textures)

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
            self._anim()

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
        if not self.image or self._iteration_done:
            return
        self._iteration_done = True
        imgcount = len(self.image.textures)
        if imgcount > 1:
            self._anim_available = True
            self.anim_reset(True)
        self._texture = self.image.textures[0]

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

        # in case of Image have been asked with keep_data
        # check the kv.image cache instead of texture.
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
                self._texture = _texture
                return

        # if image not already in cache then load
        tmpfilename = self._filename
        image = ImageLoader.load(
                self._filename, keep_data=self._keep_data,
                mipmap=self._mipmap)
        self._filename = tmpfilename

        # put the image into the cache if needed
        if isinstance(image, Texture):
            self._texture = image
            self._size = image.size
        else:
            self.image = image
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

