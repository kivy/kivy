'''
Image
=====

Use an image as a Widget. ::

    wimg = Image(source='mylogo.png')

Asynchronous loading
--------------------

If you want to load your image in an asynchronous way, you may use the
:class:`AsyncImage` class. You can use it for loading external images on the
web. ::

    image = AsyncImage(source='http://mywebsite.com/logo.png')

Alignement
----------

By default, the image is centered and fitted inside the widget bounding box.
If you don't want that, we suggest you to inherit from :class:`Image`, and
create your own style.

For example, if you want your image to take the same size of your widget, you
can do ::

    class FullImage(Image):
        pass

And in your kivy language file, you can do ::

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
from kivy.cache import Cache
from kivy.core.image import Image as CoreImage
from kivy.resources import resource_find
from kivy.properties import StringProperty, ObjectProperty, ListProperty, \
        AliasProperty, BooleanProperty
from kivy.loader import Loader


class Image(Widget):
    '''Image class, see module documentation for more information.
    '''

    source = StringProperty(None)
    '''Filename / source of your image.

    :data:`source` a :class:`~kivy.properties.StringProperty`, default to None.
    '''

    texture = ObjectProperty(None, allownone=True)
    '''Texture object of the image.

    Depending of the texture creation, the value will be a
    :class:`~kivy.graphics.texture.Texture` or
    :class:`~kivy.graphics.texture.TextureRegion` object.

    :data:`texture` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    texture_size = ListProperty([0, 0])
    '''Texture size of the image.

    .. warning::

        The texture size is set after the texture property. So if you listen on
        the change to :data:`texture`, the property texture_size will be not yet
        updated. Use self.texture.size instead.
    '''

    def get_image_ratio(self):
        if self.texture:
            return self.texture.width / float(self.texture.height)
        return 1.

    mipmap = BooleanProperty(False)
    '''Indicate if you want OpenGL mipmapping to be apply on the texture or not.
    Read :ref:`mipmap` for more informations.

    .. versionadded:: 1.0.7

    :data:`mipmap` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.
    '''

    image_ratio = AliasProperty(get_image_ratio, None, bind=('texture', ))
    '''Ratio of the image (width / float(height)

    :data:`image_ratio` is a :class:`~kivy.properties.AliasProperty`, and is
    read-only.
    '''

    color = ListProperty([1, 1, 1, 1])
    '''Image color, in the format (r, g, b, a). This attribute can be used for
    'tint' an image. Be careful, if the source image is not gray/white, the
    color will not really work as expected.

    .. versionadded:: 1.0.6

    :data:`color` is a :class:`~kivy.properties.ListProperty`, default to [1, 1,
    1, 1].
    '''

    allow_stretch = BooleanProperty(False)
    '''If True, the normalized image size will be maximized to fit in the image
    box. Otherwise, if the box is too higher, the image will be not strech more
    that 1:1 pixels

    .. versionadded:: 1.0.7

    :data:`allow_stretch` is a :class:`~kivy.properties.BooleanProperty`,
    default to False
    '''

    def get_norm_image_size(self):
        if not self.texture:
            return self.size
        ratio = self.image_ratio
        w, h = self.size
        tw, th = self.texture.size

        # ensure that the width is always maximized to the containter width
        if self.allow_stretch:
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
    '''Normalized image size withing the widget box.

    This size will be always fitted to the widget size, and preserve the image
    ratio.

    :data:`norm_image_size` is a :class:`~kivy.properties.AliasProperty`, and is
    read-only.
    '''

    def __init__(self, **kwargs):
        super(Image, self).__init__(**kwargs)
        self.bind(source=self.texture_update,
                  mipmap=self.texture_update)
        if self.source is not None:
            self.texture_update()

    def texture_update(self, *largs):
        if not self.source:
            self.texture = None
        else:
            filename = resource_find(self.source)
            if filename is None:
                return
            mipmap = self.mipmap
            #call on_tex_change when coreimage.on_texture_chagnged is called
            try:
                self._coreimage.unbind(on_texture_changed, self.on_tex_changed)
            except:
                pass
            self._coreimage = CoreImage(filename, mipmap=mipmap)
            self._coreimage.bind(on_texture_changed = self._on_tex_change)
            self.texture = self._coreimage.texture

    def anim_reset(self, allowanim = True, anim_delay = .25):
        '''Enable/Disable animation of sequenced images

        Usage:

        anim_reset(False)to stop animation
        anim_reset(True) to start/reset animation with default speed
        anim_reset(True, .1) to start/reset animation with
        slightly faster speed than default.

        anim_delay is in seconds
        As a referance '.25' seconds = (1/.25) 4 fps
        '''
        if self._coreimage:
            self._coreimage.anim_delay = anim_delay
            self._coreimage.anim_reset(allowanim)

    def on_texture(self, instance, value):
        if value is not None:
            self.texture_size = list(value.size)

    def _on_tex_change(self, *largs):
        # update texture from core image
        self.texture = self._coreimage.texture


class AsyncImage(Image):
    '''Asynchronous Image class, see module documentation for more information.
    '''

    def __init__(self, **kwargs):
        self._coreimage = None
        super(AsyncImage, self).__init__(**kwargs)
        self.unbind(source=self.texture_update,
                    mipmap=self.texture_update)

    def on_source(self, instance, value):
        if not value:
            self.texture = None
            self._coreimage = None
        else:
            if not self.is_uri(value):
                value = resource_find(value)
            self._coreimage = image = Loader.image(value)
            image.bind(on_load=self.on_source_load)
            image.bind(on_texture_changed = self._on_tex_change)
            self.texture = image.texture

    def on_source_load(self, value):
        image = self._coreimage
        if not image:
            return
        self.texture = image.texture

    def is_uri(self, filename):
        proto = filename.split('://', 1)[0]
        return proto in ('http', 'https', 'ftp')

    def _on_tex_change(self, *largs):
        self.texture = self._coreimage.texture
