'''
Image
=====

The :class:`Image` widget is used to display an image::

Example in python::

    wimg = Image(source='mylogo.png')

Kv Example::

    Image:
        source: 'mylogo.png'
        size: self.texture_size


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

By default, the image is centered inside the widget bounding box.

Adjustment
----------

To control how the image should be adjusted to fit inside the widget box, you
should use the :attr:`~kivy.uix.image.Image.fit_mode` property. Available
options include:

- ``"scale-down"``: maintains aspect ratio without stretching.
- ``"fill"``: stretches to fill widget, may cause distortion.
- ``"contain"``: maintains aspect ratio and resizes to fit inside widget.
- ``"cover"``: maintains aspect ratio and stretches to fill widget, may clip
image.

For more details, refer to the :attr:`~kivy.uix.image.Image.fit_mode`.


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
from kivy.properties import (
    StringProperty,
    ObjectProperty,
    ListProperty,
    AliasProperty,
    BooleanProperty,
    NumericProperty,
    ColorProperty,
    OptionProperty
)
from kivy.logger import Logger

# delayed imports
Loader = None


class Image(Widget):
    '''Image class, see module documentation for more information.'''

    source = StringProperty(None)
    '''Filename / source of your image.

    :attr:`source` is a :class:`~kivy.properties.StringProperty` and
    defaults to None.
    '''

    texture = ObjectProperty(None, allownone=True)
    '''Texture object of the image. The texture represents the original, loaded
    image texture. It is stretched and positioned during rendering according to
    the :attr:`fit_mode` property.

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
        return 1.0

    mipmap = BooleanProperty(False)
    '''Indicate if you want OpenGL mipmapping to be applied to the texture.
    Read :ref:`mipmap` for more information.

    .. versionadded:: 1.0.7

    :attr:`mipmap` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    image_ratio = AliasProperty(get_image_ratio, bind=('texture',), cache=True)
    '''Ratio of the image (width / float(height).

    :attr:`image_ratio` is an :class:`~kivy.properties.AliasProperty` and is
    read-only.
    '''

    color = ColorProperty([1, 1, 1, 1])
    '''Image color, in the format (r, g, b, a). This attribute can be used to
    'tint' an image. Be careful: if the source image is not gray/white, the
    color will not really work as expected.

    .. versionadded:: 1.0.6

    :attr:`color` is a :class:`~kivy.properties.ColorProperty` and defaults to
    [1, 1, 1, 1].

    .. versionchanged:: 2.0.0
        Changed from :class:`~kivy.properties.ListProperty` to
        :class:`~kivy.properties.ColorProperty`.
    '''

    allow_stretch = BooleanProperty(False, deprecated=True)
    '''If True, the normalized image size will be maximized to fit in the image
    box. Otherwise, if the box is too tall, the image will not be
    stretched more than 1:1 pixels.

    .. versionadded:: 1.0.7

    .. deprecated:: 2.2.0
        :attr:`allow_stretch` have been deprecated. Please use `fit_mode`
        instead.

    :attr:`allow_stretch` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    keep_ratio = BooleanProperty(True, deprecated=True)
    '''If False along with allow_stretch being True, the normalized image
    size will be maximized to fit in the image box and ignores the aspect
    ratio of the image.
    Otherwise, if the box is too tall, the image will not be stretched more
    than 1:1 pixels.

    .. versionadded:: 1.0.8

    .. deprecated:: 2.2.0
        :attr:`keep_ratio` have been deprecated. Please use `fit_mode`
        instead.

    :attr:`keep_ratio` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    fit_mode = OptionProperty(
        "scale-down", options=["scale-down", "fill", "contain", "cover"]
    )
    '''If the size of the image is different than the size of the widget,
    determine how the image should be resized to fit inside the widget box.

    Available options:

    - ``"scale-down"``: the image will be scaled down to fit inside the widget
    box, **maintaining its aspect ratio and without stretching**. If the size
    of the image is smaller than the widget, it will be displayed at its
    original size. If the image has a different aspect ratio than the widget,
    there will be blank areas on the widget box.

    - ``"fill"``: the image is stretched to fill the widget, **regardless of
    its aspect ratio or dimensions**. If the image has a different aspect ratio
    than the widget, this option can lead to distortion of the image.

    - ``"contain"``: the image is resized to fit inside the widget box,
    **maintaining its aspect ratio**. If the image size is larger than the
    widget size, the behavior will be similar to ``"scale-down"``. However, if
    the size of the image size is smaller than the widget size, unlike
    ``"scale-down``, the image will be resized to fit inside the widget.
    If the image has a different aspect ratio than the widget, there will be
    blank areas on the widget box.

    - ``"cover"``: the image will be stretched horizontally or vertically to
    fill the widget box, **maintaining its aspect ratio**. If the image has a
    different aspect ratio than the widget, then the image will be clipped to
    fit.

    :attr:`fit_mode` is a :class:`~kivy.properties.OptionProperty` and
    defaults to ``"scale-down"``.
    '''

    keep_data = BooleanProperty(False)
    '''If True, the underlying _coreimage will store the raw image data.
    This is useful when performing pixel based collision detection.

    .. versionadded:: 1.3.0

    :attr:`keep_data` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    anim_delay = NumericProperty(0.25)
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
            return list(self.size)

        ratio = self.image_ratio
        w, h = self.size
        tw, th = self.texture.size

        if self.fit_mode == "cover":
            widget_ratio = w / max(1, h)
            if widget_ratio > ratio:
                return [w, (w * th) / tw]
            else:
                return [(h * tw) / th, h]
        elif self.fit_mode == "fill":
            return [w, h]
        elif self.fit_mode == "contain":
            iw = w
        else:
            iw = min(w, tw)

        # calculate the appropriate height
        ih = iw / ratio
        # if the height is too higher, take the height of the container
        # and calculate appropriate width. no need to test further. :)
        if ih > h:
            if self.fit_mode == "contain":
                ih = h
            else:
                ih = min(h, th)
            iw = ih * ratio
        return [iw, ih]

    norm_image_size = AliasProperty(
        get_norm_image_size,
        bind=(
            'texture',
            'size',
            'image_ratio',
            'fit_mode',
        ),
        cache=True,
    )
    '''Normalized image size within the widget box.

    This size will always fit the widget size and will preserve the image
    ratio.

    :attr:`norm_image_size` is an :class:`~kivy.properties.AliasProperty` and
    is read-only.
    '''

    def __init__(self, **kwargs):
        self._coreimage = None
        self._loops = 0
        update = self.texture_update
        fbind = self.fbind
        fbind('source', update)
        fbind('mipmap', update)

        # NOTE: Compatibility code due to deprecated properties.
        fbind('keep_ratio', self._update_fit_mode)
        fbind('allow_stretch', self._update_fit_mode)
        super().__init__(**kwargs)

    def _update_fit_mode(self, *args):
        keep_ratio = self.keep_ratio
        allow_stretch = self.allow_stretch
        if (
            not keep_ratio and not allow_stretch
            or keep_ratio and not allow_stretch
        ):
            self.fit_mode = "scale-down"
        elif not keep_ratio and allow_stretch:
            self.fit_mode = "fill"
        elif keep_ratio and allow_stretch:
            self.fit_mode = "contain"

    def texture_update(self, *largs):
        self.set_texture_from_resource(self.source)

    def set_texture_from_resource(self, resource):
        if not resource:
            self._clear_core_image()
            return
        source = resource_find(resource)
        if not source:
            Logger.error('Image: Not found <%s>' % resource)
            self._clear_core_image()
            return
        if self._coreimage:
            self._coreimage.unbind(on_texture=self._on_tex_change)
        try:
            self._coreimage = image = CoreImage(
                source,
                mipmap=self.mipmap,
                anim_delay=self.anim_delay,
                keep_data=self.keep_data,
                nocache=self.nocache
            )
        except Exception:
            Logger.error('Image: Error loading <%s>' % resource)
            self._clear_core_image()
            image = self._coreimage
        if image:
            image.bind(on_texture=self._on_tex_change)
            self.texture = image.texture

    def on_anim_delay(self, instance, value):
        if self._coreimage is None:
            return
        self._coreimage.anim_delay = value
        if value < 0:
            self._coreimage.anim_reset(False)

    def on_texture(self, instance, value):
        self.texture_size = value.size if value else [0, 0]

    def _clear_core_image(self):
        if self._coreimage:
            self._coreimage.unbind(on_texture=self._on_tex_change)
        self.texture = None
        self._coreimage = None
        self._loops = 0

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
        self.remove_from_cache()
        old_source = self.source
        self.source = ''
        self.source = old_source

    def remove_from_cache(self):
        '''Remove image from cache.

        .. versionadded:: 2.0.0
        '''
        if self._coreimage:
            self._coreimage.remove_from_cache()

    def on_nocache(self, *args):
        if self.nocache:
            self.remove_from_cache()
            if self._coreimage:
                self._coreimage._nocache = True


class AsyncImage(Image):
    '''Asynchronous Image class. See the module documentation for more
    information.

    .. note::

        The AsyncImage is a specialized form of the Image class. You may
        want to refer to the :mod:`~kivy.loader` documentation and in
        particular, the :class:`~kivy.loader.ProxyImage` for more detail
        on how to handle events around asynchronous image loading.

    .. note::

        AsyncImage currently does not support properties
        :attr:`anim_loop` and :attr:`mipmap` and setting those properties will
        have no effect.
    '''

    __events__ = ('on_error', 'on_load')

    def __init__(self, **kwargs):
        self._found_source = None
        self._coreimage = None
        global Loader
        if not Loader:
            from kivy.loader import Loader
        self.fbind('source', self._load_source)
        super().__init__(**kwargs)

    def _load_source(self, *args):
        source = self.source
        if not source:
            self._clear_core_image()
            return
        if not self.is_uri(source):
            source = resource_find(source)
            if not source:
                Logger.error('AsyncImage: Not found <%s>' % self.source)
                self._clear_core_image()
                return
        self._found_source = source
        self._coreimage = image = Loader.image(
            source,
            nocache=self.nocache,
            mipmap=self.mipmap,
            anim_delay=self.anim_delay
        )
        image.bind(
            on_load=self._on_source_load,
            on_error=self._on_source_error,
            on_texture=self._on_tex_change
        )
        self.texture = image.texture

    def _on_source_load(self, value):
        image = self._coreimage.image
        if not image:
            return
        self.texture = image.texture
        self.dispatch('on_load')

    def _on_source_error(self, instance, error=None):
        self.dispatch('on_error', error)

    def on_error(self, error):
        pass

    def on_load(self, *args):
        pass

    def is_uri(self, filename):
        proto = filename.split('://', 1)[0]
        return proto in ('http', 'https', 'ftp', 'smb')

    def _clear_core_image(self):
        if self._coreimage:
            self._coreimage.unbind(on_load=self._on_source_load)
        super()._clear_core_image()
        self._found_source = None

    def _on_tex_change(self, *largs):
        if self._coreimage:
            self.texture = self._coreimage.texture

    def texture_update(self, *largs):
        pass

    def remove_from_cache(self):
        if self._found_source:
            Loader.remove_from_cache(self._found_source)
        super().remove_from_cache()
