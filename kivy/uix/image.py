'''
Image
=====
'''

__all__ = ('Image', 'AsyncImage')

from kivy.uix.widget import Widget
from kivy.core.image import Image as CoreImage
from kivy.resources import resource_find
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.loader import Loader


class Image(Widget):

    #: Filename of the image
    source = StringProperty(None)

    #: Texture of the label
    texture = ObjectProperty(None, allownone=True)

    #: Texture size of the label
    texture_size = ListProperty([0, 0])

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

