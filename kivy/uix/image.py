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
from kivy.core.image import Image as CoreImage
from kivy.resources import resource_find
from kivy.properties import StringProperty, ObjectProperty, ListProperty, \
        AliasProperty
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

    image_ratio = AliasProperty(get_image_ratio, None, bind=('texture', ))
    '''Ratio of the image (width / float(height)

    :data:`image_ratio` is a :class:`~kivy.properties.AliasProperty`, and is
    read-only.
    '''

    def get_norm_image_size(self):
        if not self.texture:
            return self.size
        ratio = self.image_ratio
        w, h = self.size
        tw, th = self.texture.size
        iw, ih = 0, 0
        # cases if the image is lower than the widget
        if iw < w and ih < h:
            if iw < w:
                iw = w
                ih = iw / ratio
            elif ih < h:
                ih = h
                iw = ih * ratio
        # cases if the image is bigger than the widget
        if iw > w:
            iw = w
            ih = iw * ratio
        if ih > h:
            ih = h
            iw = ih / ratio
        return iw, ih


    norm_image_size = AliasProperty(get_norm_image_size, None, bind=(
        'texture', 'size', 'image_ratio'))
    '''Normalized image size withing the widget box.

    This size will be always fitted to the widget size, and preserve the image
    ratio.

    :data:`norm_image_size` is a :class:`~kivy.properties.AliasProperty`, and is
    read-only.
    '''

    def on_source(self, instance, value):
        if not value:
            self.texture = None
        else:
            filename = resource_find(value)
            image = CoreImage(filename)
            self.texture = image.texture

    def on_texture(self, instance, value):
        if value is not None:
            self.texture_size = list(value.size)


class AsyncImage(Image):
    '''Asynchronous Image class, see module documentation for more information.
    '''

    def __init__(self, **kwargs):
        self._coreimage = None
        super(AsyncImage, self).__init__(**kwargs)

    def on_source(self, instance, value):
        if not value:
            self.texture = None
            self._coreimage = None
        else:
            filename = resource_find(value)
            self._coreimage = image = Loader.image(filename)
            image.bind(on_load=self.on_source_load)
            self.texture = image.texture

    def on_source_load(self, value):
        image = self._coreimage
        if not image:
            return
        self.texture = image.texture

