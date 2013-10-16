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

Alignment
---------

By default, the image is centered and fits inside the widget bounding box.
If you don't want that, you can inherit from Image and create your own style.

For example, if you want your image to be the same size as your widget, you
could do::

    class FullImage(Image):
        pass

And in your kivy language file::

    <FullImage>:
        canvas:
            Color:
                rgb: (1, 1, 1)
            Rectangle:
                texture: self.texture
                size: self.size
                pos: self.pos

'''

__all__ = ('Image', 'AsyncImage')

from kivy.uix.widget import Widget
from kivy.core.image import Image as CoreImage
from kivy.resources import resource_find
from kivy.properties import StringProperty, ObjectProperty, ListProperty, \
        AliasProperty, BooleanProperty, NumericProperty
from kivy.loader import Loader
from kivy.logger import Logger


class Image(Widget):
    '''Image class, see module documentation for more information.
    '''

    source = StringProperty(None)
    '''Filename / source of your image.

    :data:`source` is a :class:`~kivy.properties.StringProperty` and defaults to
    None.
    '''

    texture = ObjectProperty(None, allownone=True)
    '''Texture object of the image.

    Depending of the texture creation, the value will be a
    :class:`~kivy.graphics.texture.Texture` or a
    :class:`~kivy.graphics.texture.TextureRegion` object.

    :data:`texture` is a :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    texture_size = ListProperty([0, 0])
    '''Texture size of the image.

    .. warning::

        The texture size is set after the texture property. So if you listen to
        the change on :data:`texture`, the property texture_size will not be
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

    :data:`mipmap` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    image_ratio = AliasProperty(get_image_ratio, None, bind=('texture', ))
    '''Ratio of the image (width / float(height).

    :data:`image_ratio` is a :class:`~kivy.properties.AliasProperty` and is
    read-only.
    '''

    color = ListProperty([1, 1, 1, 1])
    '''Image color, in the format (r, g, b, a). This attribute can be used to
    'tint' an image. Be careful: if the source image is not gray/white, the
    color will not really work as expected.

    .. versionadded:: 1.0.6

    :data:`color` is a :class:`~kivy.properties.ListProperty` and defaults to
    [1, 1, 1, 1].
    '''

    allow_stretch = BooleanProperty(False)
    '''If True, the normalized image size will be maximized to fit in the image
    box. Otherwise, if the box is too tall, the image will not be stretched more
    than 1:1 pixels.

    .. versionadded:: 1.0.7

    :data:`allow_stretch` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    keep_ratio = BooleanProperty(True)
    '''If False along with allow_stretch being True, the normalized image
    size will be maximized to fit in the image box and ignores the aspect
    ratio of the image.
    Otherwise, if the box is too tall, the image will not be stretched more
    than 1:1 pixels.

    .. versionadded:: 1.0.8

    :data:`keep_ratio` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    keep_data = BooleanProperty(False)
    '''If True, the underlaying _coreimage will store the raw image data.
    This is useful when performing pixel based collision detection.

    .. versionadded:: 1.3.0

    :data:`keep_data` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    anim_delay = NumericProperty(.25)
    '''Delay the animation if the image is sequenced (like an animated gif).
    If anim_delay is set to -1, the animation will be stopped.

    .. versionadded:: 1.0.8

    :data:`anim_delay` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.25 (4 FPS).
    '''

    nocache = BooleanProperty(False)
    '''If this property is set True, the image will not be added to the
    internal cache. The cache will simply ignore any calls trying to
    append the core image.

    .. versionadded:: 1.6.0

    :data:`nocache` is a :class:`~kivy.properties.BooleanProperty` and defaults
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

    :data:`norm_image_size` is a :class:`~kivy.properties.AliasProperty` and is
    read-only.
    '''

    def __init__(self, **kwargs):
        self._coreimage = None
        super(Image, self).__init__(**kwargs)
        self.bind(source=self.texture_update,
                  mipmap=self.texture_update)
        if self.source:
            self.texture_update()

    def texture_update(self, *largs):
        if not self.source:
            self.texture = None
        else:
            filename = resource_find(self.source)
            if filename is None:
                return Logger.error('Image: Error reading file {filename}'.
                                    format(filename=self.source))
            mipmap = self.mipmap
            if self._coreimage is not None:
                self._coreimage.unbind(on_texture=self._on_tex_change)
            try:
                self._coreimage = ci = CoreImage(filename, mipmap=mipmap,
                        anim_delay=self.anim_delay, keep_data=self.keep_data,
                        nocache=self.nocache)
            except:
                self._coreimage = ci = None

            if ci:
                ci.bind(on_texture=self._on_tex_change)
                self.texture = ci.texture

    def on_anim_delay(self, instance, value):
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
        self._coreimage.remove_from_cache()
        olsource = self.source
        self.source = ''
        self.source = olsource

    def on_nocache(self, *args):
        if self.nocache and self._coreimage:
            self._coreimage.remove_from_cache()
            self._coreimage._nocache = True


class AsyncImage(Image):
    '''Asynchronous Image class. See the module documentation for more
    information.

    .. note::

        The AsyncImage is a specialized form of the Image class. You may want to
        refer to the :mod:`~kivy.loader` documentation and in particular, the
        :class:`~kivy.loader.ProxyImage` for more detail on how to handle events
        around asynchronous image loading.
    '''

    def __init__(self, **kwargs):
        self._coreimage = None
        super(AsyncImage, self).__init__(**kwargs)
        self.bind(source=self._load_source)
        if self.source:
            self._load_source()

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
                    nocache=self.nocache, mipmap=self.mipmap)
            image.bind(on_load=self._on_source_load)
            image.bind(on_texture=self._on_tex_change)
            self.texture = image.texture

    def _on_source_load(self, value):
        image = self._coreimage.image
        if not image:
            return
        self.texture = image.texture

    def is_uri(self, filename):
        proto = filename.split('://', 1)[0]
        return proto in ('http', 'https', 'ftp', 'smb')

    def _on_tex_change(self, *largs):
        if self._coreimage:
            self.texture = self._coreimage.texture

    def texture_update(self, *largs):
        pass
