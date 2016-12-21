'''
Image
=====

The :class:`Image` widget is used to display an image::

    wimg = Image(source='mylogo.png')

Asynchronous Loading
--------------------

To load an image asynchronously (for example from an external webserver), use
the :class:`AsyncImage` subclass::

    aimg = AsyncImage(source='http://mywebsite.com/logo.png')

This can be useful as it prevents your application from waiting until the image
is loaded. If you want to display large images or retrieve them from URL's,
using :class:`AsyncImage` will allow these resources to be retrieved on a
background thread without blocking your application.

Alignment
---------

By default, the image is centered and fits inside the widget bounding box.
If you don't want that, you can set `allow_stretch` to True and `keep_ratio`
to False.

You can also inherit from Image and create your own style. For example, if you
want your image to be greater than the size of your widget, you could do::

    class FullImage(Image):
        pass

And in your kivy language file::

    <-FullImage>:
        canvas:
            Color:
                rgb: (1, 1, 1)
            Rectangle:
                texture: self.texture
                size: self.width + 20, self.height + 20
                pos: self.x - 10, self.y - 10

'''
__all__ = ('Image', 'AsyncImage')

from kivy.uix.widget import Widget
from kivy.core.image import Image as CoreImage
from kivy.resources import resource_find
from kivy.properties import StringProperty, ObjectProperty, ListProperty, \
    AliasProperty, BooleanProperty, NumericProperty
from kivy.logger import Logger
from kivy.compat import PY2

# delayed imports
Loader = None


class Image(Widget):
    '''Image class, see module documentation for more information.
    '''

    source = StringProperty(None)
    '''Filename / source of your image.

    :attr:`source` is a :class:`~kivy.properties.StringProperty` and
    defaults to None.
    '''

    texture = ObjectProperty(None, allownone=True)
    '''Texture object of the image. The texture represents the original, loaded
    image texture. It is stretched and positioned during rendering according to
    the :attr:`allow_stretch` and :attr:`keep_ratio` properties.

    Depending of the texture creation, the value will be a
    :class:`~kivy.graphics.texture.Texture` or a
    :class:`~kivy.graphics.texture.TextureRegion` object.

    :attr:`texture` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    texture_size = ListProperty([0, 0])
    '''Texture size of the image. This represents the original, loaded image
    texture size.

    .. warning::

        The texture size is set after the texture property. So if you listen to
        the change on :attr:`texture`, the property texture_size will not be
        up-to-date. Use self.texture.size instead.
    '''

    def get_image_ratio(self):
        if self.texture:
            return self.texture.width / float(self.texture.height)
        return 1.

    mipmap = BooleanProperty(False)
    '''Indicate if you want OpenGL mipmapping to be applied to the texture.
    Read :ref:`mipmap` for more information.

    .. versionadded:: 1.0.7

    :attr:`mipmap` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    image_ratio = AliasProperty(get_image_ratio, None, bind=('texture', ))
    '''Ratio of the image (width / float(height).

    :attr:`image_ratio` is an :class:`~kivy.properties.AliasProperty` and is
    read-only.
    '''

    color = ListProperty([1, 1, 1, 1])
    '''Image color, in the format (r, g, b, a). This attribute can be used to
    'tint' an image. Be careful: if the source image is not gray/white, the
    color will not really work as expected.

    .. versionadded:: 1.0.6

    :attr:`color` is a :class:`~kivy.properties.ListProperty` and defaults to
    [1, 1, 1, 1].
    '''

    allow_stretch = BooleanProperty(False)
    '''If True, the normalized image size will be maximized to fit in the image
    box. Otherwise, if the box is too tall, the image will not be
    stretched more than 1:1 pixels.

    .. versionadded:: 1.0.7

    :attr:`allow_stretch` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    keep_ratio = BooleanProperty(True)
    '''If False along with allow_stretch being True, the normalized image
    size will be maximized to fit in the image box and ignores the aspect
    ratio of the image.
    Otherwise, if the box is too tall, the image will not be stretched more
    than 1:1 pixels.

    .. versionadded:: 1.0.8

    :attr:`keep_ratio` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    keep_data = BooleanProperty(False)
    '''If True, the underlaying _coreimage will store the raw image data.
    This is useful when performing pixel based collision detection.

    .. versionadded:: 1.3.0

    :attr:`keep_data` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    anim_delay = NumericProperty(.25)
    '''Delay the animation if the image is sequenced (like an animated gif).
    If anim_delay is set to -1, the animation will be stopped.

    .. versionadded:: 1.0.8

    :attr:`anim_delay` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.25 (4 FPS).
    '''

    anim_loop = NumericProperty(0)
    '''Number of loops to play then stop animating. 0 means keep animating.

    .. versionadded:: 1.9.0

    :attr:`anim_loop` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    nocache = BooleanProperty(False)
    '''If this property is set True, the image will not be added to the
    internal cache. The cache will simply ignore any calls trying to
    append the core image.

    .. versionadded:: 1.6.0

    :attr:`nocache` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    def get_norm_image_size(self):
        if not self.texture:
            return self.size
        ratio = self.image_ratio
        w, h = self.size
        tw, th = self.texture.size

        # ensure that the width is always maximized to the containter width
        if self.allow_stretch:
            if not self.keep_ratio:
                return w, h
            iw = w
        else:
            iw = min(w, tw)
        # calculate the appropriate height
        ih = iw / ratio
        # if the height is too higher, take the height of the container
        # and calculate appropriate width. no need to test further. :)
        if ih > h:
            if self.allow_stretch:
                ih = h
            else:
                ih = min(h, th)
            iw = ih * ratio

        return iw, ih

    norm_image_size = AliasProperty(get_norm_image_size, None, bind=(
        'texture', 'size', 'image_ratio', 'allow_stretch'))
    '''Normalized image size within the widget box.

    This size will always fit the widget size and will preserve the image
    ratio.

    :attr:`norm_image_size` is an :class:`~kivy.properties.AliasProperty` and
    is read-only.
    '''

    def __init__(self, **kwargs):
        self._coreimage = None
        self._loops = 0
        super(Image, self).__init__(**kwargs)
        fbind = self.fbind
        update = self.texture_update
        fbind('source', update)
        fbind('mipmap', update)
        if self.source:
            update()
        self.on_anim_delay(self, kwargs.get('anim_delay', .25))

    def texture_update(self, *largs):
        if not self.source:
            self.texture = None
        else:
            filename = resource_find(self.source)
            self._loops = 0
            if filename is None:
                return Logger.error('Image: Error reading file {filename}'.
                                    format(filename=self.source))
            mipmap = self.mipmap
            if self._coreimage is not None:
                self._coreimage.unbind(on_texture=self._on_tex_change)
            try:
                if PY2:
                    filename = filename.decode('utf-8')
                self._coreimage = ci = CoreImage(filename, mipmap=mipmap,
                                                 anim_delay=self.anim_delay,
                                                 keep_data=self.keep_data,
                                                 nocache=self.nocache)
            except:
                Logger.error('Image: Error loading texture {filename}'.
                                    format(filename=self.source))
                self._coreimage = ci = None

            if ci:
                ci.bind(on_texture=self._on_tex_change)
                self.texture = ci.texture

    def on_anim_delay(self, instance, value):
        self._loop = 0
        if self._coreimage is None:
            return
        self._coreimage.anim_delay = value
        if value < 0:
            self._coreimage.anim_reset(False)

    def on_texture(self, instance, value):
        if value is not None:
            self.texture_size = list(value.size)

    def _on_tex_change(self, *largs):
        # update texture from core image
        self.texture = self._coreimage.texture
        ci = self._coreimage
        if self.anim_loop and ci._anim_index == len(ci._image.textures) - 1:
            self._loops += 1
            if self.anim_loop == self._loops:
                ci.anim_reset(False)
                self._loops = 0

    def reload(self):
        '''Reload image from disk. This facilitates re-loading of
        images from disk in case the image content changes.

        .. versionadded:: 1.3.0

        Usage::

            im = Image(source = '1.jpg')
            # -- do something --
            im.reload()
            # image will be re-loaded from disk

        '''
        try:
            self._coreimage.remove_from_cache()

        except AttributeError:
            pass

        oldsource = self.source
        self.source = ''
        self.source = oldsource

    def on_nocache(self, *args):
        if self.nocache and self._coreimage:
            self._coreimage.remove_from_cache()
            self._coreimage._nocache = True


class AsyncImage(Image):
    '''Asynchronous Image class. See the module documentation for more
    information.

    .. note::

        The AsyncImage is a specialized form of the Image class. You may
        want to refer to the :mod:`~kivy.loader` documentation and in
        particular, the :class:`~kivy.loader.ProxyImage` for more detail
        on how to handle events around asynchronous image loading.
    '''

    __events__ = ('on_error', )

    def __init__(self, **kwargs):
        self._coreimage = None
        super(AsyncImage, self).__init__(**kwargs)
        global Loader
        if not Loader:
            from kivy.loader import Loader
        self.fbind('source', self._load_source)
        if self.source:
            self._load_source()
        self.on_anim_delay(self, kwargs.get('anim_delay', .25))

    def _load_source(self, *args):
        source = self.source
        if not source:
            if self._coreimage is not None:
                self._coreimage.unbind(on_texture=self._on_tex_change)
            self.texture = None
            self._coreimage = None
        else:
            if not self.is_uri(source):
                source = resource_find(source)
            self._coreimage = image = Loader.image(source,
                nocache=self.nocache, mipmap=self.mipmap,
                anim_delay=self.anim_delay)

            image.bind(on_load=self._on_source_load)
            image.bind(on_error=self._on_source_error)
            image.bind(on_texture=self._on_tex_change)
            self.texture = image.texture

    def _on_source_load(self, value):
        image = self._coreimage.image
        if not image:
            return
        self.texture = image.texture

    def _on_source_error(self, instance, error=None):
        self.dispatch('on_error', error)

    def on_error(self, error):
        pass

    def is_uri(self, filename):
        proto = filename.split('://', 1)[0]
        return proto in ('http', 'https', 'ftp', 'smb')

    def _on_tex_change(self, *largs):
        if self._coreimage:
            self.texture = self._coreimage.texture

    def texture_update(self, *largs):
        pass
