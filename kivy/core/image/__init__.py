'''
Image
=====

Core classes for loading images and converting them to a
:class:`~kivy.graphics.texture.Texture`. The raw image data can be keep in
memory for further access.

.. versionchanged:: 1.11.0

    Add support for argb and abgr image data

In-memory image loading
-----------------------

.. versionadded:: 1.9.0

    Official support for in-memory loading. Not all the providers support it,
    but currently SDL2, pygame, pil and imageio work.

To load an image with a filename, you would usually do::

    from kivy.core.image import Image as CoreImage
    im = CoreImage("image.png")

You can also load the image data directly from a memory block. Instead of
passing the filename, you'll need to pass the data as a BytesIO object
together with an "ext" parameter. Both are mandatory::

    import io
    from kivy.core.image import Image as CoreImage
    data = io.BytesIO(open("image.png", "rb").read())
    im = CoreImage(data, ext="png")

By default, the image will not be cached as our internal cache requires a
filename. If you want caching, add a filename that represents your file (it
will be used only for caching)::

    import io
    from kivy.core.image import Image as CoreImage
    data = io.BytesIO(open("image.png", "rb").read())
    im = CoreImage(data, ext="png", filename="image.png")

Saving an image
---------------

A CoreImage can be saved to a file::

    from kivy.core.image import Image as CoreImage
    image = CoreImage(...)
    image.save("/tmp/test.png")

Or you can get the bytes (new in `1.11.0`):

    import io
    from kivy.core.image import Image as CoreImage
    data = io.BytesIO()
    image = CoreImage(...)
    image.save(data, fmt="png")
    png_bytes = data.read()

'''
import re
from base64 import b64decode
import imghdr

__all__ = ('Image', 'ImageLoader', 'ImageData')

from kivy.event import EventDispatcher
from kivy.core import core_register_libs
from kivy.logger import Logger
from kivy.cache import Cache
from kivy.clock import Clock
from kivy.atlas import Atlas
from kivy.resources import resource_find
from kivy.utils import platform
from kivy.compat import string_types
from kivy.setupconfig import USE_SDL2
import zipfile
from io import BytesIO


# late binding
Texture = TextureRegion = None


# register image caching only for keep_data=True
Cache.register('kv.image', timeout=60)
Cache.register('kv.atlas')


class ImageData(object):
    '''Container for images and mipmap images.
    The container will always have at least the mipmap level 0.
    '''

    __slots__ = ('fmt', 'mipmaps', 'source', 'flip_vertical', 'source_image')
    _supported_fmts = ('rgb', 'bgr', 'rgba', 'bgra', 'argb', 'abgr',
                       's3tc_dxt1', 's3tc_dxt3', 's3tc_dxt5', 'pvrtc_rgb2',
                       'pvrtc_rgb4', 'pvrtc_rgba2', 'pvrtc_rgba4', 'etc1_rgb8')

    def __init__(self, width, height, fmt, data, source=None,
                 flip_vertical=True, source_image=None,
                 rowlength=0):
        assert fmt in ImageData._supported_fmts

        #: Decoded image format, one of a available texture format
        self.fmt = fmt

        #: Data for each mipmap.
        self.mipmaps = {}
        self.add_mipmap(0, width, height, data, rowlength)

        #: Image source, if available
        self.source = source

        #: Indicate if the texture will need to be vertically flipped
        self.flip_vertical = flip_vertical

        # the original image, which we might need to save if it is a memoryview
        self.source_image = source_image

    def release_data(self):
        mm = self.mipmaps
        for item in mm.values():
            item[2] = None
            self.source_image = None

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
    def rowlength(self):
        '''Image rowlength.
        (If the image is mipmapped, it will use the level 0)

        .. versionadded:: 1.9.0
        '''
        return self.mipmaps[0][3]

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
        return ('<ImageData width=%d height=%d fmt=%s '
                'source=%r with %d images>' % (
                    self.width, self.height, self.fmt,
                    self.source, len(self.mipmaps)))

    def add_mipmap(self, level, width, height, data, rowlength):
        '''Add a image for a specific mipmap level.

        .. versionadded:: 1.0.7
        '''
        self.mipmaps[level] = [int(width), int(height), data, rowlength]

    def get_mipmap(self, level):
        '''Get the mipmap image at a specific level if it exists

        .. versionadded:: 1.0.7
        '''
        if level == 0:
            return (self.width, self.height, self.data, self.rowlength)
        assert(level < len(self.mipmaps))
        return self.mipmaps[level]

    def iterate_mipmaps(self):
        '''Iterate over all mipmap images available.

        .. versionadded:: 1.0.7
        '''
        mm = self.mipmaps
        for x in range(len(mm)):
            item = mm.get(x, None)
            if item is None:
                raise Exception('Invalid mipmap level, found empty one')
            yield x, item[0], item[1], item[2], item[3]


class ImageLoaderBase(object):
    '''Base to implement an image loader.'''

    __slots__ = ('_texture', '_data', 'filename', 'keep_data',
                 '_mipmap', '_nocache', '_ext', '_inline')

    def __init__(self, filename, **kwargs):
        self._mipmap = kwargs.get('mipmap', False)
        self.keep_data = kwargs.get('keep_data', False)
        self._nocache = kwargs.get('nocache', False)
        self._ext = kwargs.get('ext')
        self._inline = kwargs.get('inline')
        self.filename = filename
        if self._inline:
            self._data = self.load(kwargs.get('rawdata'))
        else:
            self._data = self.load(filename)
        self._textures = None

    def load(self, filename):
        '''Load an image'''
        return None

    @staticmethod
    def can_save(fmt, is_bytesio=False):
        '''Indicate if the loader can save the Image object

        .. versionchanged:: 1.11.0
            Parameter `fmt` and `is_bytesio` added
        '''
        return False

    @staticmethod
    def can_load_memory():
        '''Indicate if the loader can load an image by passing data
        '''
        return False

    @staticmethod
    def save(*largs, **kwargs):
        raise NotImplementedError()

    def populate(self):
        self._textures = []
        fname = self.filename
        if __debug__:
            Logger.trace('Image: %r, populate to textures (%d)' %
                         (fname, len(self._data)))

        for count in range(len(self._data)):

            # first, check if a texture with the same name already exist in the
            # cache
            chr = type(fname)
            uid = chr(u'%s|%d|%d') % (fname, self._mipmap, count)
            texture = Cache.get('kv.texture', uid)

            # if not create it and append to the cache
            if texture is None:
                imagedata = self._data[count]
                source = '{}{}|'.format(
                    'zip|' if fname.endswith('.zip') else '',
                    self._nocache)
                imagedata.source = chr(source) + uid
                texture = Texture.create_from_data(
                    imagedata, mipmap=self._mipmap)
                if not self._nocache:
                    Cache.append('kv.texture', uid, texture)
                if imagedata.flip_vertical:
                    texture.flip_vertical()

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

    @property
    def nocache(self):
        '''Indicate if the texture will not be stored in the cache

        .. versionadded:: 1.6.0
        '''
        return self._nocache


class ImageLoader(object):

    loaders = []

    @staticmethod
    def zip_loader(filename, **kwargs):
        '''Read images from an zip file.

        .. versionadded:: 1.0.8

        Returns an Image with a list of type ImageData stored in Image._data
        '''
        # read zip in memory for faster access
        _file = BytesIO(open(filename, 'rb').read())
        # read all images inside the zip
        z = zipfile.ZipFile(_file)
        image_data = []
        # sort filename list
        znamelist = z.namelist()
        znamelist.sort()
        image = None
        for zfilename in znamelist:
            try:
                # read file and store it in mem with fileIO struct around it
                tmpfile = BytesIO(z.read(zfilename))
                ext = zfilename.split('.')[-1].lower()
                im = None
                for loader in ImageLoader.loaders:
                    if (ext not in loader.extensions() or
                            not loader.can_load_memory()):
                        continue
                    Logger.debug('Image%s: Load <%s> from <%s>' %
                                 (loader.__name__[11:], zfilename, filename))
                    try:
                        im = loader(zfilename, ext=ext, rawdata=tmpfile,
                                    inline=True, **kwargs)
                    except:
                        # Loader failed, continue trying.
                        continue
                    break
                if im is not None:
                    # append ImageData to local variable before its
                    # overwritten
                    image_data.append(im._data[0])
                    image = im
                # else: if not image file skip to next
            except:
                Logger.warning('Image: Unable to load image'
                               '<%s> in zip <%s> trying to continue...'
                               % (zfilename, filename))
        z.close()
        if len(image_data) == 0:
            raise Exception('no images in zip <%s>' % filename)
        # replace Image.Data with the array of all the images in the zip
        image._data = image_data
        image.filename = filename
        return image

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
                raise ValueError(
                    'Image: Invalid %s name for atlas' % filename)

            # search if we already got the atlas loaded
            atlas = Cache.get('kv.atlas', rfn)

            # atlas already loaded, so reupload the missing texture in cache,
            # because when it's not in use, the texture can be removed from the
            # kv.texture cache.
            if atlas:
                texture = atlas[uid]
                fn = 'atlas://%s/%s' % (rfn, uid)
                cid = '{}|{:d}|{:d}'.format(fn, False, 0)
                Cache.append('kv.texture', cid, texture)
                return Image(texture)

            # search with resource
            afn = rfn
            if not afn.endswith('.atlas'):
                afn += '.atlas'
            afn = resource_find(afn)
            if not afn:
                raise Exception('Unable to found %r atlas' % afn)
            atlas = Atlas(afn)
            Cache.append('kv.atlas', rfn, atlas)
            # first time, fill our texture cache.
            for nid, texture in atlas.textures.items():
                fn = 'atlas://%s/%s' % (rfn, nid)
                cid = '{}|{:d}|{:d}'.format(fn, False, 0)
                Cache.append('kv.texture', cid, texture)
            return Image(atlas[uid])

        # extract extensions
        ext = filename.split('.')[-1].lower()

        # prevent url querystrings
        if filename.startswith((('http://', 'https://'))):
            ext = ext.split('?')[0]

        filename = resource_find(filename)

        # special case. When we are trying to load a "zip" file with image, we
        # will use the special zip_loader in ImageLoader. This might return a
        # sequence of images contained in the zip.
        if ext == 'zip':
            return ImageLoader.zip_loader(filename)
        else:
            im = None
            # Get actual image format instead of extension if possible
            ext = imghdr.what(filename) or ext
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
    '''Load an image and store the size and texture.

    .. versionchanged:: 1.0.7

        `mipmap` attribute has been added. The `texture_mipmap` and
        `texture_rectangle` have been deleted.

    .. versionchanged:: 1.0.8

        An Image widget can change its texture. A new event 'on_texture' has
        been introduced. New methods for handling sequenced animation have been
        added.

    :Parameters:
        `arg`: can be a string (str), Texture, BytesIO or Image object
            A string path to the image file or data URI to be loaded; or a
            Texture object, which will be wrapped in an Image object; or a
            BytesIO object containing raw image data; or an already existing
            image object, in which case, a real copy of the given image object
            will be returned.
        `keep_data`: bool, defaults to False
            Keep the image data when the texture is created.
        `mipmap`: bool, defaults to False
            Create mipmap for the texture.
        `anim_delay`: float, defaults to .25
            Delay in seconds between each animation frame. Lower values means
            faster animation.
        `ext`: str, only with BytesIO `arg`
            File extension to use in determining how to load raw image data.
        `filename`: str, only with BytesIO `arg`
            Filename to use in the image cache for raw image data.
    '''

    copy_attributes = ('_size', '_filename', '_texture', '_image',
                       '_mipmap', '_nocache')

    data_uri_re = re.compile(r'^data:image/([^;,]*)(;[^,]*)?,(.*)$')

    _anim_ev = None

    def __init__(self, arg, **kwargs):
        # this event should be fired on animation of sequenced img's
        self.register_event_type('on_texture')

        super(Image, self).__init__()

        self._mipmap = kwargs.get('mipmap', False)
        self._keep_data = kwargs.get('keep_data', False)
        self._nocache = kwargs.get('nocache', False)
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
            if not hasattr(self, 'textures'):
                self.textures = []
                self.textures.append(arg)
            self._texture = arg
            self._size = self.texture.size
        elif isinstance(arg, ImageLoaderBase):
            self.image = arg
        elif isinstance(arg, BytesIO):
            ext = kwargs.get('ext', None)
            if not ext:
                raise Exception('Inline loading require "ext" parameter')
            filename = kwargs.get('filename')
            if not filename:
                self._nocache = True
                filename = '__inline__'
            self.load_memory(arg, ext, filename)
        elif isinstance(arg, string_types):
            groups = self.data_uri_re.findall(arg)
            if groups:
                self._nocache = True
                imtype, optstr, data = groups[0]
                options = [o for o in optstr.split(';') if o]
                ext = imtype
                isb64 = 'base64' in options
                if data:
                    if isb64:
                        data = b64decode(data)
                    self.load_memory(BytesIO(data), ext)
            else:
                self.filename = arg
        else:
            raise Exception('Unable to load image type {0!r}'.format(arg))

    def remove_from_cache(self):
        '''Remove the Image from cache. This facilitates re-loading of
        images from disk in case the image content has changed.

        .. versionadded:: 1.3.0

        Usage::

            im = CoreImage('1.jpg')
            # -- do something --
            im.remove_from_cache()
            im = CoreImage('1.jpg')
            # this time image will be re-loaded from disk

        '''
        count = 0
        f = self.filename
        pat = type(f)(u'%s|%d|%d')
        uid = pat % (f, self._mipmap, count)
        Cache.remove("kv.image", uid)
        while Cache.get("kv.texture", uid):
            Cache.remove("kv.texture", uid)
            count += 1
            uid = pat % (f, self._mipmap, count)

    def _anim(self, *largs):
        if not self._image:
            return
        textures = self.image.textures
        if self._anim_index >= len(textures):
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
                Indicate whether the animation should restart playing or not.

        Usage::

            # start/reset animation
            image.anim_reset(True)

            # or stop the animation
            image.anim_reset(False)

        You can change the animation speed whilst it is playing::

            # Set to 20 FPS
            image.anim_delay = 1 / 20.

        '''
        # stop animation
        if self._anim_ev is not None:
            self._anim_ev.cancel()
            self._anim_ev = None

        if allow_anim and self._anim_available and self._anim_delay >= 0:
            self._anim_ev = Clock.schedule_interval(self._anim,
                                                    self.anim_delay)
            self._anim()

    def _get_anim_delay(self):
        return self._anim_delay

    def _set_anim_delay(self, x):
        if self._anim_delay == x:
            return
        self._anim_delay = x
        if self._anim_available:
            if self._anim_ev is not None:
                self._anim_ev.cancel()
                self._anim_ev = None

            if self._anim_delay >= 0:
                self._anim_ev = Clock.schedule_interval(self._anim,
                                                        self._anim_delay)

    anim_delay = property(_get_anim_delay, _set_anim_delay)
    '''Delay between each animation frame. A lower value means faster
    animation.

    .. versionadded:: 1.0.8
    '''

    @property
    def anim_available(self):
        '''Return True if this Image instance has animation available.

        .. versionadded:: 1.0.8
        '''
        return self._anim_available

    @property
    def anim_index(self):
        '''Return the index number of the image currently in the texture.

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
        '''This event is fired when the texture reference or content has
           changed. It is normally used for sequenced images.

        .. versionadded:: 1.0.8
        '''
        pass

    @staticmethod
    def load(filename, **kwargs):
        '''Load an image

        :Parameters:
            `filename`: str
                Filename of the image.
            `keep_data`: bool, defaults to False
                Keep the image data when the texture is created.
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
        f = self.filename
        uid = type(f)(u'%s|%d|%d') % (f, self._mipmap, 0)

        # in case of Image have been asked with keep_data
        # check the kv.image cache instead of texture.
        image = Cache.get('kv.image', uid)
        if image:
            # we found an image, yeah ! but reset the texture now.
            self.image = image
            # if image.__class__ is core image then it's a texture
            # from atlas or other sources and has no data so skip
            if (image.__class__ != self.__class__ and
                    not image.keep_data and self._keep_data):
                self.remove_from_cache()
                self._filename = ''
                self._set_filename(value)
            else:
                self._texture = None
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
            mipmap=self._mipmap, nocache=self._nocache)
        self._filename = tmpfilename
        # put the image into the cache if needed
        if isinstance(image, Texture):
            self._texture = image
            self._size = image.size
        else:
            self.image = image
            if not self._nocache:
                Cache.append('kv.image', uid, self.image)

    filename = property(_get_filename, _set_filename,
                        doc='Get/set the filename of image')

    def load_memory(self, data, ext, filename='__inline__'):
        '''(internal) Method to load an image from raw data.
        '''
        self._filename = filename

        # see if there is a available loader for it
        loaders = [loader for loader in ImageLoader.loaders if
                   loader.can_load_memory() and
                   ext in loader.extensions()]
        if not loaders:
            raise Exception('No inline loader found to load {}'.format(ext))
        image = loaders[0](filename, ext=ext, rawdata=data, inline=True,
                nocache=self._nocache, mipmap=self._mipmap,
                keep_data=self._keep_data)
        if isinstance(image, Texture):
            self._texture = image
            self._size = image.size
        else:
            self.image = image

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

    @property
    def nocache(self):
        '''Indicate whether the texture will not be stored in the cache or not.

        .. versionadded:: 1.6.0
        '''
        return self._nocache

    def save(self, filename, flipped=False, fmt=None):
        '''Save image texture to file.

        The filename should have the '.png' extension because the texture data
        read from the GPU is in the RGBA format. '.jpg' might work but has not
        been heavily tested so some providers might break when using it.
        Any other extensions are not officially supported.

        The flipped parameter flips the saved image vertically, and
        defaults to False.

        Example::

            # Save an core image object
            from kivy.core.image import Image
            img = Image('hello.png')
            img.save('hello2.png')

            # Save a texture
            texture = Texture.create(...)
            img = Image(texture)
            img.save('hello3.png')

        .. versionadded:: 1.7.0

        .. versionchanged:: 1.8.0
            Parameter `flipped` added to flip the image before saving, default
            to False.

        .. versionchanged:: 1.11.0
            Parameter `fmt` added to force the output format of the file
            Filename can now be a BytesIO object.

        '''
        is_bytesio = False
        if isinstance(filename, BytesIO):
            is_bytesio = True
            if not fmt:
                raise Exception(
                    "You must specify a format to save into a BytesIO object")
        elif fmt is None:
            fmt = self._find_format_from_filename(filename)

        pixels = None
        size = None
        loaders = [
            x for x in ImageLoader.loaders
            if x.can_save(fmt, is_bytesio=is_bytesio)
        ]
        if not loaders:
            return False
        loader = loaders[0]

        if self.image:
            # we might have a ImageData object to use
            data = self.image._data[0]
            if data.data is not None:
                if data.fmt in ('rgba', 'rgb'):
                    # fast path, use the "raw" data when keep_data is used
                    size = data.width, data.height
                    pixels = data.data

                else:
                    # the format is not rgba, we need to convert it.
                    # use texture for that.
                    self.populate()

        if pixels is None and self._texture:
            # use the texture pixels
            size = self._texture.size
            pixels = self._texture.pixels

        if pixels is None:
            return False

        l_pixels = len(pixels)
        if l_pixels == size[0] * size[1] * 3:
            pixelfmt = 'rgb'
        elif l_pixels == size[0] * size[1] * 4:
            pixelfmt = 'rgba'
        else:
            raise Exception('Unable to determine the format of the pixels')
        return loader.save(
            filename, size[0], size[1], pixelfmt, pixels, flipped, fmt)

    def _find_format_from_filename(self, filename):
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext in {
                'bmp', 'jpe', 'lbm', 'pcx', 'png', 'pnm',
                'tga', 'tiff', 'webp', 'xcf', 'xpm', 'xv'}:
            return ext
        elif ext in ('jpg', 'jpeg'):
            return 'jpg'
        elif ext in ('b64', 'base64'):
            return 'base64'
        return None

    def read_pixel(self, x, y):
        '''For a given local x/y position, return the pixel color at that
        position.

        .. warning::
            This function can only be used with images loaded with the
            keep_data=True keyword. For example::

                m = Image.load('image.png', keep_data=True)
                color = m.read_pixel(150, 150)

        :Parameters:
            `x`: int
                Local x coordinate of the pixel in question.
            `y`: int
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
        raw = bytearray(data.data[index:index + size])
        color = [c / 255.0 for c in raw]

        bgr_flag = False
        if data.fmt == 'argb':
            color.reverse()  # bgra
            bgr_flag = True
        elif data.fmt == 'abgr':
            color.reverse()  # rgba

        # conversion for BGR->RGB, BGRA->RGBA format
        if bgr_flag or data.fmt in ('bgr', 'bgra'):
            color[0], color[2] = color[2], color[0]

        return color


def load(filename):
    '''Load an image'''
    return Image.load(filename)


# load image loaders
image_libs = []

if platform in ('macosx', 'ios'):
    image_libs += [('imageio', 'img_imageio')]

image_libs += [
    ('tex', 'img_tex'),
    ('dds', 'img_dds')]
if USE_SDL2:
    image_libs += [('sdl2', 'img_sdl2')]
else:
    image_libs += [('pygame', 'img_pygame')]
image_libs += [
    ('ffpy', 'img_ffpyplayer'),
    ('pil', 'img_pil')]

libs_loaded = core_register_libs('image', image_libs)

from os import environ
if 'KIVY_DOC' not in environ and not libs_loaded:
    import sys

    Logger.critical('App: Unable to get any Image provider, abort.')
    sys.exit(1)

# resolve binding.
from kivy.graphics.texture import Texture, TextureRegion
